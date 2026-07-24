# -*- coding: utf-8 -*-
"""Jisho API client: Requests and background worker."""

import json
from copy import deepcopy
import requests
import urllib.parse
from typing import List, Dict, Any

from aqt.qt import QObject, pyqtSignal, pyqtSlot

from .constants import DEFAULT_CONFIG, JISHO_MAPPING_OPTIONS
from .logger import logger
from .paths import CONFIG_PATH, LEGACY_CONFIG_PATH

LEGACY_REMOVED_KEYS = (
    "dictionary_source",
    "krdict_api_key",
)

PROFILE_KEYS = (
    "card_type",
    "target_deck",
    "search_field",
    "mappings",
    "fill_mode",
    "multi_meaning_format",
    "disable_multi_word_warning",
    "remove_pos_ending",
    "remove_furigana_search",
    "multi_word_format",
    "open_shortcut",
    "quick_fill_shortcut",
    "quick_fill_mode",
    "show_quick_fill_success",
)


def _detect_anki_language() -> str:
    try:
        from anki.lang import currentLang
        if currentLang:
            return currentLang
    except Exception as exc:
        logger.debug("Failed to read Anki UI language", extra={"error": str(exc)})
    try:
        from aqt import mw
        if mw and mw.pm:
            lang = mw.pm.profileLanguage()
            if lang:
                return lang
    except Exception as exc:
        logger.debug("Failed to read Anki UI language", extra={"error": str(exc)})
    return ""


def _default_language() -> str:
    lang = (_detect_anki_language() or "").lower()
    if lang.startswith("pt"):
        return "pt"
    return "en"


def _default_profile() -> Dict[str, Any]:
    profile = {}
    for key in PROFILE_KEYS:
        profile[key] = deepcopy(DEFAULT_CONFIG.get(key))
    return profile


def _normalize_mappings(raw: Any) -> list[dict[str, Any]]:
    allowed_keys = set(JISHO_MAPPING_OPTIONS)
    if isinstance(raw, dict):
        mappings = [{"jisho": jisho, "field": field} for field, jisho in raw.items()]
    elif isinstance(raw, list):
        mappings = [m for m in raw if isinstance(m, dict)]
    else:
        mappings = []
    normalized = []
    for mapping in mappings:
        if mapping.get("jisho") == "Is_Common":
            mapping["jisho"] = "Is Common"
        key = str(mapping.get("jisho", "") or "")
        if key not in allowed_keys:
            continue
        normalized.append(
            {
                "jisho": key,
                "field": str(mapping.get("field", "") or ""),
            }
        )
    return normalized


def _normalize_profile(raw_profile: Any) -> Dict[str, Any]:
    profile = _default_profile()
    if isinstance(raw_profile, dict):
        for key in PROFILE_KEYS:
            if key in raw_profile:
                profile[key] = deepcopy(raw_profile.get(key))
    profile["mappings"] = _normalize_mappings(profile.get("mappings"))
    multi_word_format = profile.get("multi_word_format")
    if multi_word_format == "separate":
        profile["multi_word_format"] = "basic"
    return profile


def _normalize_full_config(raw: Any) -> Dict[str, Any]:
    config: Dict[str, Any] = raw if isinstance(raw, dict) else {}
    had_button_position = isinstance(config, dict) and "editor_button_position" in config
    normalized = {}

    # Keep all unknown keys to avoid dropping user data.
    normalized.update(config)
    for key in LEGACY_REMOVED_KEYS:
        normalized.pop(key, None)

    for key, value in DEFAULT_CONFIG.items():
        if key not in normalized:
            normalized[key] = deepcopy(value)

    language = normalized.get("language")
    if language not in ("en", "pt"):
        normalized["language"] = _default_language()

    button_position = str(normalized.get("editor_button_position", "") or "").strip().lower()
    if button_position not in {"toolbar", "field_label", "both"}:
        normalized["editor_button_position"] = "field_label" if config else "toolbar"
    else:
        normalized["editor_button_position"] = button_position
    if not had_button_position and config:
        normalized["editor_button_position"] = "field_label"

    normalized["style_mode"] = "legacy_and_stable"

    raw_profiles = normalized.get("profiles")
    profiles: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw_profiles, dict):
        for profile_name, profile_payload in raw_profiles.items():
            name = str(profile_name or "").strip()
            if not name:
                continue
            profiles[name] = _normalize_profile(profile_payload)

    # Migration path from legacy single-profile config.
    if not profiles:
        legacy_payload = {key: normalized.get(key, deepcopy(DEFAULT_CONFIG.get(key))) for key in PROFILE_KEYS}
        profiles = {"Default": _normalize_profile(legacy_payload)}

    active_profile = str(normalized.get("active_profile", "") or "").strip()
    if active_profile not in profiles:
        active_profile = next(iter(profiles.keys()))

    normalized["profiles"] = profiles
    normalized["active_profile"] = active_profile

    # Keep top-level active values synchronized for backward compatibility.
    active_payload = profiles[active_profile]
    for key in PROFILE_KEYS:
        normalized[key] = deepcopy(active_payload.get(key))

    return normalized


def _load_raw_config() -> tuple[dict[str, Any], Any]:
    for candidate in (CONFIG_PATH, LEGACY_CONFIG_PATH):
        if not candidate.exists():
            continue
        return json.loads(candidate.read_text(encoding="utf-8")), candidate
    return {}, None


def load_full_config() -> Dict[str, Any]:
    """Load canonical config (with profiles) from disk."""
    try:
        raw, source_path = _load_raw_config()
        normalized = _normalize_full_config(raw)
        if source_path != CONFIG_PATH or not CONFIG_PATH.exists() or normalized != raw:
            save_full_config(normalized)
        return normalized
    except (json.JSONDecodeError, OSError):
        logger.exception("Error loading config")
        fallback = _normalize_full_config({})
        fallback["language"] = _default_language()
        save_full_config(fallback)
        return fallback


def load_config() -> Dict[str, Any]:
    """Load active profile config (plus global fields used by runtime)."""
    full = load_full_config()
    active_profile = str(full.get("active_profile") or "Default")
    profiles = full.get("profiles") or {}
    active_payload = profiles.get(active_profile) or _default_profile()

    config = {}
    # Keep global keys currently used by runtime.
    for key in ("language", "style_mode", "show_welcome_dialog", "active_profile", "editor_button_position"):
        config[key] = deepcopy(full.get(key))
    for key in PROFILE_KEYS:
        config[key] = deepcopy(active_payload.get(key))
    return config


def save_full_config(config: Dict[str, Any]) -> None:
    """Save canonical config to disk."""
    try:
        normalized = _normalize_full_config(config)
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(normalized, indent=4, ensure_ascii=False), encoding="utf-8")
    except OSError:
        logger.exception("Error saving config")


def save_config(config: Dict[str, Any]):
    """Save settings to file (accepts full or active-profile payload)."""
    if not isinstance(config, dict):
        return

    # Full payload path (settings dialog).
    if "profiles" in config or "active_profile" in config:
        save_full_config(config)
        return

    # Runtime payload path (results dialog / quick updates).
    full = load_full_config()
    for key in ("language", "style_mode", "show_welcome_dialog", "editor_button_position"):
        if key in config:
            full[key] = deepcopy(config.get(key))

    active_profile = str(full.get("active_profile") or "Default")
    profiles = full.get("profiles") or {}
    profile_payload = _normalize_profile(profiles.get(active_profile))
    for key in PROFILE_KEYS:
        if key in config:
            profile_payload[key] = deepcopy(config.get(key))
    profiles[active_profile] = _normalize_profile(profile_payload)
    full["profiles"] = profiles
    save_full_config(full)


def fetch_from_jisho(term: str) -> List[Dict[str, Any]]:
    """Fetch results from Jisho API."""
    if not term:
        return []
    url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(term)}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    status = data.get("meta", {}).get("status")
    if status != 200:
        raise RuntimeError(f"Jisho API error (status {status})")
    return data.get("data", [])


def fetch_dictionary_entries(term: str) -> List[Dict[str, Any]]:
    """Fetch entries from the fixed Jisho source."""
    return fetch_from_jisho(term)


class JishoFetchWorker(QObject):
    """Background worker thread for dictionary requests."""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, term: str):
        super().__init__()
        self.term = term

    @pyqtSlot()
    def run(self):
        """Execute dictionary fetch."""
        try:
            entries = fetch_dictionary_entries(self.term)
            self.finished.emit(entries)
        except Exception as e:
            logger.exception("Jisho fetch error")
            self.error.emit(str(e))
