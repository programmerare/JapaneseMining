"""Bridge JapaneseMining Config → flat AJC runtime dict.

AJC's editor hooks and field processor expect a flat dict
(search_field, mappings, …). JapaneseMining stores per–note-type
profiles under config.jisho_profiles.

This module is the single place that builds the flat shape AJC understands.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .config import Config, default_jisho_profile


def to_ajc_runtime_config(
    config: Config,
    profile: dict | None = None,
    note_type_name: str | None = None,
) -> dict[str, Any]:
    """
    Build the flat dict AJC's load_config() consumers expect.

    Parameters
    ----------
    config:
        Full JapaneseMining Config (account-level + jisho_profiles).
    profile:
        One entry from config.jisho_profiles. If None, falls back to the
        active / first profile, then to legacy flat fields on Config.
    note_type_name:
        Note type this profile belongs to (written as card_type for AJC).
    """
    resolved_name, resolved_profile = _pick_profile(config, profile, note_type_name)

    return {
        # Account-level (not per note type)
        "language": getattr(config, "language", "en") or "en",
        "editor_button_position": getattr(config, "editor_button_position", "toolbar")
        or "toolbar",
        "show_welcome_dialog": bool(getattr(config, "show_welcome_dialog", False)),
        "open_shortcut": getattr(config, "jisho_shortcut", "Ctrl+J") or "Ctrl+J",
        "quick_fill_shortcut": getattr(config, "jisho_fastfill_shortcut", "Ctrl+Shift+J")
        or "Ctrl+Shift+J",
        # Profile-level (resolved for one note type)
        "card_type": resolved_name or "",
        "target_deck": resolved_profile.get("target_deck", "") or "",
        "search_field": resolved_profile.get("search_field", "Word") or "Word",
        "mappings": deepcopy(resolved_profile.get("mappings") or []),
        "fill_mode": resolved_profile.get("fill_mode", "replace") or "replace",
        "multi_meaning_format": resolved_profile.get(
            "multi_meaning_format", "semicolon_merged"
        )
        or "semicolon_merged",
        "multi_word_format": resolved_profile.get("multi_word_format", "inline")
        or "inline",
        "remove_pos_ending": bool(resolved_profile.get("remove_pos_ending", True)),
        "remove_furigana_search": bool(
            resolved_profile.get("remove_furigana_search", True)
        ),
        "disable_multi_word_warning": bool(
            resolved_profile.get("disable_multi_word_warning", False)
        ),
        "quick_fill_mode": resolved_profile.get("quick_fill_mode", "all") or "all",
        "show_quick_fill_success": bool(
            resolved_profile.get("show_quick_fill_success", False)
        ),
    }


def _pick_profile(
    config: Config,
    profile: dict | None,
    note_type_name: str | None,
) -> tuple[str, dict]:
    """Return (note_type_name, merged profile dict)."""
    profiles = getattr(config, "jisho_profiles", None) or {}

    if isinstance(profile, dict):
        name = (note_type_name or "").strip()
        merged = default_jisho_profile()
        merged.update({k: profile[k] for k in default_jisho_profile() if k in profile})
        return name, merged

    # Prefer explicit note type key
    name = (note_type_name or "").strip()
    if name and name in profiles and isinstance(profiles[name], dict):
        merged = default_jisho_profile()
        raw = profiles[name]
        merged.update({k: raw[k] for k in default_jisho_profile() if k in raw})
        return name, merged

    # Fall back to active profile (UI selection), then first profile
    active = (getattr(config, "active_jisho_profile", None) or "").strip()
    if active and active in profiles and isinstance(profiles[active], dict):
        merged = default_jisho_profile()
        raw = profiles[active]
        merged.update({k: raw[k] for k in default_jisho_profile() if k in raw})
        return active, merged

    if profiles:
        first_name = next(iter(profiles))
        raw = profiles[first_name]
        if isinstance(raw, dict):
            merged = default_jisho_profile()
            merged.update({k: raw[k] for k in default_jisho_profile() if k in raw})
            return str(first_name), merged

    # Last resort: legacy flat fields on Config (pre-profile installs)
    legacy = default_jisho_profile()
    for key in default_jisho_profile():
        if hasattr(config, key):
            legacy[key] = getattr(config, key)
    legacy_name = (
        getattr(config, "card_type", None)
        or getattr(config, "mining_note_type", None)
        or ""
    )
    return str(legacy_name or ""), legacy
