from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json


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
    use_deepL: bool = False
    deepl_api_key: str = ""
    deepl_url: str = "https://api-free.deepl.com/v2/translate"
    deepl_shortcut: str = "Ctrl+T"
    target_lang: str = "EN-US"

    # --- JISHO ---
    use_jisho: bool = True
    jisho_shortcut: str = "Ctrl+J"
    jisho_fastfill_shortcut: str = "Ctrl+Shift+J"

    # --- HYPERTTS ---
    use_hypertts: bool = False


CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> Config:
    """Load config from disk, falling back to defaults."""
    defaults = Config()
    if not CONFIG_PATH.exists():
        save_config(defaults)
        return defaults

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        save_config(defaults)
        return defaults

    valid = {f.name for f in fields(Config)}
    filtered_data = {k: v for k, v in data.items() if k in valid}
    return Config(**{**asdict(defaults), **filtered_data})


def save_config(config: Config):
    """Persist the given config to disk."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2, ensure_ascii=False)