# -*- coding: utf-8 -*-
"""Jisho API client: Requests and background worker."""

import json
from copy import deepcopy
import requests
import urllib.parse
from typing import List, Dict, Any

from aqt.qt import QObject, pyqtSignal, pyqtSlot

from .config_holder import get_runtime_config, set_runtime_config
from .logger import logger

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


def load_full_config() -> Dict[str, Any]:
    return get_runtime_config()


def load_config() -> Dict[str, Any]:
    return get_runtime_config()


def save_full_config(config: Dict[str, Any]) -> None:
    set_runtime_config(config)


def save_config(config: Dict[str, Any]):
    set_runtime_config(config)


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
