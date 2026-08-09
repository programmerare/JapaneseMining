from copy import deepcopy
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path
from typing import Any
import json


CONFIG_PATH = Path(__file__).parent / "config.json"

JISHO_PROFILE_KEYS = (
    "search_field",
    "target_deck",
    "mappings",
    "fill_mode",
    "multi_meaning_format",
    "multi_word_format",
    "remove_pos_ending",
    "remove_furigana_search",
    "disable_multi_word_warning",
    "quick_fill_mode",
    "show_quick_fill_success",
)


@dataclass
class Config:
    # --- GENERAL ---
    show_tooltip: bool = True
    mining_note_type: str = "JapaneseMining"
    rtk_deck: str = ""
    rtk_note_type: str = ""
    rtk_kanji_field: str = ""
    rtk_alternative_kanji_field: str = ""
    rtk_keyword_field: str = ""
    rtk_heisig_number_field: str = ""
    rtk_stroke_count_field: str = ""

    # --- TRANSLATE ---
    use_deepl: bool = False
    deepl_api_key: str = ""
    deepl_url: str = "https://api-free.deepl.com/v2/translate"
    deepl_shortcut: str = "Ctrl+T"
    deepl_target_lang: str = "EN-US"

    # --- JISHO ---
    use_jisho: bool = True
    jisho_shortcut: str = "Ctrl+J"
    jisho_fastfill_shortcut: str = "Ctrl+Shift+J"
    editor_button_position: str = "toolbar" # toolbarl | field_label | both
    language: str = "en"
    show_welcome_dialog: bool = False

    jisho_profiles: dict = field(default_factory=dict)  # {note_type: {profile_fields}}
    active_jisho_profile: str = ""  # last selected / fallback name

    card_type: str = "JapaneseMining"   # note type
    target_deck: str = ""
    search_field: str = "Word"
    mappings: list = field(default_factory=list)    # list[{"jisho": str "field": str}]
    fill_mode: str = "replace"  # replace | append
    multi_meaning_format: str = "semicolon_merged"
    multi_word_format: str = "inline"
    remove_pos_ending: bool = True
    remove_furigana_search: bool = True
    disable_multi_word_warning: bool = False
    show_quick_fill_success: bool = True
    quick_fill_mode: str = "all"    # all | first

    # --- HYPERTTS ---
    use_hypertts: bool = False


def load_config() -> Config:
    """Load config from disk. Always returns a complete, normalized Config."""
    defaults = Config()

    if not CONFIG_PATH.exists():
        save_config(defaults)
        return defaults

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        save_config(defaults)
        return defaults

    if not isinstance(raw, dict):
        save_config(defaults)
        return defaults

    normalized = _normalize_config_dict(raw)
    config = Config(**normalized)

    # Keep the file on disk clean (optional but recommended)
    if normalized != raw:
        save_config(config)

    return config


def save_config(config: Config) -> None:
    """Persist a clean, normalized config."""
    data = _normalize_config_dict(asdict(config))
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


ALLOWED_FILL_MODES = {"replace", "append"}
ALLOWED_MULTI_MEANING = {"pipe_merged", "numbered", "semicolon_merged"}
ALLOWED_MULTI_WORD = {"basic", "inline", "tagged", "numbered", "tagged_numbered"}
ALLOWED_QUICK_FILL = {"all", "first"}
ALLOWED_BUTTON_POS = {"toolbar", "field_label", "both"}
ALLOWED_LANG = {"en", "pt"}

JISHO_MAPPING_OPTIONS = {
    "", "Word", "Reading", "Meaning", "Part of speech", "Info", "Tags",
    "See also", "Other forms", "JLPT Level", "Wanikani Level", "Is Common"
}


def _normalize_mappings(raw: Any) -> list[dict[str, str]]:
    """Accept both old dict style and new list style. Keep only valid entries."""
    if isinstance(raw, dict):
        items = [{"jisho": jisho, "field": field} for field, jisho in raw.items()]
    elif isinstance(raw, list):
        items = [m for m in raw if isinstance(m, dict)]
    else:
        items = []

    normalized = []
    for m in items:
        jisho = str(m.get("jisho", "") or "").strip()
        field_name = str(m.get("field", "") or "").strip()

        if jisho == "Is_Common":
            jisho = "Is Common"

        if jisho not in JISHO_MAPPING_OPTIONS:
            continue

        normalized.append({"jisho": jisho, "field": field_name})
    return normalized


def _normalize_config_dict(data: dict) -> dict:
    """Make any raw dict safe and complete."""
    defaults = asdict(Config())
    result = deepcopy(defaults)

    # Only keep keys that exist on Config
    for key in defaults:
        if key not in data:
            continue
        result[key] = data[key]

    # --- force correct types / allowed values ---
    result["mappings"] = _normalize_mappings(result.get("mappings"))

    if result["fill_mode"] not in ALLOWED_FILL_MODES:
        result["fill_mode"] = "replace"

    if result["multi_meaning_format"] not in ALLOWED_MULTI_MEANING:
        result["multi_meaning_format"] = "semicolon_merged"

    if result["multi_word_format"] not in ALLOWED_MULTI_WORD:
        result["multi_word_format"] = "inline"

    if result["quick_fill_mode"] not in ALLOWED_QUICK_FILL:
        result["quick_fill_mode"] = "all"

    if result["editor_button_position"] not in ALLOWED_BUTTON_POS:
        result["editor_button_position"] = "toolbar"

    if result["language"] not in ALLOWED_LANG:
        result["language"] = "en"

    # Booleans
    for bool_key in (
        "use_jisho", "remove_pos_ending", "remove_furigana_search",
        "disable_multi_word_warning", "show_quick_fill_success",
        "show_welcome_dialog", "use_deepl", "use_hypertts", "show_tooltip"
    ):
        result[bool_key] = bool(result.get(bool_key, defaults[bool_key]))

    # Shortcuts – never empty
    if not str(result.get("jisho_shortcut") or "").strip():
        result["jisho_shortcut"] = defaults["jisho_shortcut"]
    if not str(result.get("jisho_fastfill_shortcut") or "").strip():
        result["jisho_fastfill_shortcut"] = defaults["jisho_fastfill_shortcut"]

    _migrate_to_jisho_profiles(result)

    return result


def default_jisho_profile() -> dict:
    return {
        "search_field": "Word",
        "target_deck": "",
        "mappings": [],
        "fill_mode": "replace",
        "multi_meaning_format": "semicolon_merged",
        "multi_word_format": "inline",
        "remove_pos_ending": True,
        "remove_furigana_search": True,
        "disable_multi_word_warning": False,
        "quick_fill_mode": "all",
        "show_quick_fill_success": False,
    }


def _migrate_to_jisho_profiles(data: dict) -> dict:
    profiles = data.get("jisho_profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    # If we still have old flat fields, turn them into the first profile
    if not profiles:
        old_note_type = (
            data.get("card_type")
            or data.get("mining_note_type")
            or "JapaneseMining"
        )
        profile = default_jisho_profile()
        for key in JISHO_PROFILE_KEYS:
            if key in data:
                profile[key] = data[key]
        # mappings need the same cleaning you already do
        profile["mappings"] = _normalize_mappings(profile.get("mappings"))
        profiles[old_note_type] = profile

    # Make sure every profile is complete
    clean_profiles = {}
    for name, raw in profiles.items():
        name = str(name or "").strip()
        if not name:
            continue
        p = default_jisho_profile()
        if isinstance(raw, dict):
            for key in JISHO_PROFILE_KEYS:
                if key in raw:
                    p[key] = raw[key]
        p["mappings"] = _normalize_mappings(p.get("mappings"))
        clean_profiles[name] = p

    if not clean_profiles:
        clean_profiles["JapaneseMining"] = default_jisho_profile()

    data["jisho_profiles"] = clean_profiles

    active = str(data.get("active_jisho_profile") or "").strip()
    if active not in clean_profiles:
        active = next(iter(clean_profiles))
    data["active_jisho_profile"] = active

    return data