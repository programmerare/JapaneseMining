from aqt import mw
from copy import deepcopy
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json
import uuid

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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

TRANSLATE_PROFILE_KEYS = (
    "source_field",
    "target_field",
    "source_lang",
    "target_lang",
)

# Canonical list of fields every mining note type must have.
# Used by CollectionService, General tab completeness checks, and Help.
REQUIRED_MINING_FIELDS = [
    "Word",
    "Reading",
    "Meaning",
    "Example Sentence",
    "Translation",
    "Note",
    "Mnemonic",
    "Audio",
    "Other forms",
    "Tags",
    "Part of speech",
    "Info",
    "See also",
    "JLPT Level",
    "Wanikani Level",
    "Is Common",
    "Kanji is known",
    "No Kanji",
    "Usually Kana",
    "Kanji Keywords",
    "Kanji Meanings",
]

# Key stored inside Anki's profile data so we survive renames.
_PROFILE_ID_KEY = "japanese_mining_profile_id"

ALLOWED_FILL_MODES = {"replace", "append"}
ALLOWED_MULTI_MEANING = {"pipe_merged", "numbered", "semicolon_merged"}
ALLOWED_MULTI_WORD = {"basic", "inline", "tagged", "numbered", "tagged_numbered"}
ALLOWED_QUICK_FILL = {"all", "first"}
ALLOWED_BUTTON_POS = {"toolbar", "field_label", "both"}
ALLOWED_LANG = {"en", "pt"}

JISHO_MAPPING_OPTIONS = {
    "",
    "Word",
    "Reading",
    "Meaning",
    "Part of speech",
    "Info",
    "Tags",
    "See also",
    "Other forms",
    "JLPT Level",
    "Wanikani Level",
    "Is Common",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class Config:
    # --- GENERAL ---
    show_tooltip: bool = True
    show_update_needed: bool = True
    mining_note_types: list[str] = field(default_factory=list)
    mining_note_type: str = "JapaneseMining"
    rtk_deck: str = ""
    rtk_note_type: str = ""
    rtk_kanji_field: str = ""
    rtk_alternative_kanji_field: str = ""
    rtk_keyword_field: str = ""
    rtk_meanings_field: str = ""
    rtk_note_field: str = ""
    rtk_heisig_number_field: str = ""
    rtk_stroke_count_field: str = ""

    # --- TRANSLATE (account-level) ---
    use_deepl: bool = False
    deepl_api_key: str = ""
    deepl_url: str = "https://api-free.deepl.com"
    deepl_shortcut: str = "Ctrl+T"

    # --- TRANSLATE (per note-type profiles) ---
    translate_profiles: dict = field(default_factory=dict)  # {note_type: {...}}
    active_translate_profile: str = ""

    # --- JISHO ---
    use_jisho: bool = True
    jisho_shortcut: str = "Ctrl+J"
    jisho_fastfill_shortcut: str = "Ctrl+Shift+J"
    editor_button_position: str = "toolbar"  # toolbar | field_label | both
    language: str = "en"
    show_welcome_dialog: bool = False

    jisho_profiles: dict = field(default_factory=dict)  # {note_type: {...}}
    active_jisho_profile: str = ""  # UI selection only; runtime resolves by note type

    # Legacy flat fields (still written for AJC / older paths; prefer profiles)
    card_type: str = "JapaneseMining"
    target_deck: str = ""
    search_field: str = "Word"
    mappings: list = field(default_factory=list)
    fill_mode: str = "replace"
    multi_meaning_format: str = "semicolon_merged"
    multi_word_format: str = "inline"
    remove_pos_ending: bool = True
    remove_furigana_search: bool = True
    disable_multi_word_warning: bool = False
    show_quick_fill_success: bool = False
    quick_fill_mode: str = "all"

    # --- HYPERTTS ---
    use_hypertts: bool = False


class ConfigHolder:
    """Single source of truth for the current profile's Config."""

    def __init__(self, config: Config):
        self.config = config

    def reload(self) -> Config:
        """Load the config for the current Anki profile and replace self.config."""
        self.config = load_config()
        return self.config


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def is_valid_mining_note_type(note_type: str, config: Config) -> bool:
    """Check if the given note type is a valid JapaneseMining note type."""
    return note_type in config.mining_note_types

# ---------------------------------------------------------------------------
# Profile-aware paths
# ---------------------------------------------------------------------------


def _addon_root() -> Path:
    return Path(__file__).resolve().parent


def _user_files_root() -> Path:
    return _addon_root() / "user_files"


def _get_or_create_profile_id() -> str:
    """Stable ID for the current Anki profile (survives renames)."""
    try:
        pm = mw.pm
        profile = getattr(pm, "profile", None)
        if isinstance(profile, dict):
            existing = profile.get(_PROFILE_ID_KEY)
            if isinstance(existing, str) and existing.strip():
                return existing.strip()

            new_id = str(uuid.uuid4())
            profile[_PROFILE_ID_KEY] = new_id
            try:
                pm.save()
            except Exception:
                pass
            return new_id
    except Exception:
        pass

    try:
        name = (mw.pm.name or "default").strip() or "default"
    except Exception:
        name = "default"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return f"name_{safe}"


def _profile_config_path() -> Path:
    profile_id = _get_or_create_profile_id()
    path = _user_files_root() / "profiles" / profile_id / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def profile_user_dir() -> Path:
    """Per-profile durable storage under user_files/."""
    root = _user_files_root() / "profiles" / _get_or_create_profile_id()
    root.mkdir(parents=True, exist_ok=True)
    return root


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


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


def default_translate_profile() -> dict:
    return {
        "source_field": "Example Sentence",
        "target_field": "Translation",
        "source_lang": "JA",
        "target_lang": "EN-US",
    }


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------


def load_config() -> Config:
    """Load config for the current Anki profile. Always returns a complete Config."""
    defaults = Config()
    path = _profile_config_path()

    if not path.exists():
        save_config(defaults)
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        save_config(defaults)
        return defaults

    if not isinstance(raw, dict):
        save_config(defaults)
        return defaults

    normalized = _normalize_config_dict(raw)
    config = Config(**normalized)

    if normalized != raw:
        save_config(config)

    return config


def save_config(config: Config) -> None:
    """Persist config for the current Anki profile under user_files/."""
    data = _normalize_config_dict(asdict(config))
    path = _profile_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Japanese Mining: failed to write profile config: {e}")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def _normalize_mappings(raw: Any) -> list[dict[str, str]]:
    """Accept both old dict style and new list style. Keep only valid entries."""
    if isinstance(raw, dict):
        items = [
            {"jisho": jisho, "field": field_name} for field_name, jisho in raw.items()
        ]
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

    for key in defaults:
        if key not in data:
            continue
        result[key] = data[key]

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

    for bool_key in (
        "use_jisho",
        "remove_pos_ending",
        "remove_furigana_search",
        "disable_multi_word_warning",
        "show_quick_fill_success",
        "show_welcome_dialog",
        "use_deepl",
        "use_hypertts",
        "show_tooltip",
        "show_update_needed",
    ):
        result[bool_key] = bool(result.get(bool_key, defaults[bool_key]))

    if not str(result.get("jisho_shortcut") or "").strip():
        result["jisho_shortcut"] = defaults["jisho_shortcut"]
    if not str(result.get("jisho_fastfill_shortcut") or "").strip():
        result["jisho_fastfill_shortcut"] = defaults["jisho_fastfill_shortcut"]
    if not str(result.get("deepl_shortcut") or "").strip():
        result["deepl_shortcut"] = defaults["deepl_shortcut"]

    _migrate_to_jisho_profiles(result)
    _migrate_to_translate_profiles(result)

    return result


def _migrate_to_jisho_profiles(data: dict) -> dict:
    profiles = data.get("jisho_profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    if not profiles:
        old_note_type = (
            data.get("card_type") or data.get("mining_note_type") or "JapaneseMining"
        )
        profile = default_jisho_profile()
        for key in JISHO_PROFILE_KEYS:
            if key in data:
                profile[key] = data[key]
        profile["mappings"] = _normalize_mappings(profile.get("mappings"))
        profiles[old_note_type] = profile

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


def _migrate_to_translate_profiles(data: dict) -> dict:
    """Ensure translate_profiles is complete. Seed from legacy flat fields if empty."""
    profiles = data.get("translate_profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    if not profiles:
        old_note_type = (
            data.get("mining_note_type") or data.get("card_type") or "JapaneseMining"
        )
        profile = default_translate_profile()
        # Honour any leftover flat target language from older configs
        legacy_target = str(data.get("deepl_target_lang") or "").strip()
        if legacy_target:
            profile["target_lang"] = legacy_target
        profiles[old_note_type] = profile

    clean_profiles = {}
    for name, raw in profiles.items():
        name = str(name or "").strip()
        if not name:
            continue
        p = default_translate_profile()
        if isinstance(raw, dict):
            for key in TRANSLATE_PROFILE_KEYS:
                if key in raw and raw[key] is not None:
                    p[key] = (
                        str(raw[key]).strip() if isinstance(raw[key], str) else raw[key]
                    )
        # Guard empty critical fields
        if not p.get("source_field"):
            p["source_field"] = "Example Sentence"
        if not p.get("target_field"):
            p["target_field"] = "Translation"
        if not p.get("source_lang"):
            p["source_lang"] = "JA"
        if not p.get("target_lang"):
            p["target_lang"] = "EN-US"
        clean_profiles[name] = p

    if not clean_profiles:
        clean_profiles["JapaneseMining"] = default_translate_profile()

    data["translate_profiles"] = clean_profiles

    active = str(data.get("active_translate_profile") or "").strip()
    if active not in clean_profiles:
        active = next(iter(clean_profiles))
    data["active_translate_profile"] = active

    # Drop legacy key from the normalized dict so it is not re-persisted
    data.pop("deepl_target_lang", None)

    return data
