from dataclasses import asdict
from copy import deepcopy
from .config import Config


def to_ajc_runtime_config(cfg: Config) -> dict:
    """Turn our Config into the exact shape the foreign runtime expects."""
    d = asdict(cfg)

    # Map our names → foreign names
    d["open_shortcut"] = d.get("jisho_shortcut") or "Ctrl+J"
    d["quick_fill_shortcut"] = d.get("jisho_fastfill_shortcut") or "Ctrl+Shift+J"

    # Ensure required keys exist with safe defaults
    d.setdefault("mappings", [])
    d.setdefault("fill_mode", "replace")
    d.setdefault("multi_meaning_format", "semicolon_merged")
    d.setdefault("multi_word_format", "inline")
    d.setdefault("remove_pos_ending", True)
    d.setdefault("remove_furigana_search", True)
    d.setdefault("disable_multi_word_warning", False)
    d.setdefault("show_quick_fill_success", True)
    d.setdefault("quick_fill_mode", "all")
    d.setdefault("editor_button_position", "toolbar")
    d.setdefault("language", "en")
    d.setdefault("show_welcome_dialog", False)
    d.setdefault("card_type", d.get("mining_note_type") or "JapaneseMining")
    d.setdefault("search_field", "Word")
    d.setdefault("target_deck", "")

    return d
