import csv
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from aqt import gui_hooks

from . import globals, helpers
from .AJC.runtime.bootstrap import initialize_ajc

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULT_CONFIG = {
    "note_type": globals.note_type,
    "rtk_deck": globals.rtk_deck,
    "deepl_api_key": globals.deepl_api_key,
    "deepl_url": globals.deepl_url,
}


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)
    if not CONFIG_PATH.exists() or not config:
        save_config(merged_config)
    return merged_config


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    apply_config(config)


def apply_config(config):
    globals.addon_config = config
    globals.note_type = config.get("note_type", DEFAULT_CONFIG["note_type"])
    globals.rtk_deck = config.get("rtk_deck", DEFAULT_CONFIG["rtk_deck"])
    globals.deepl_api_key = config.get("deepl_api_key", DEFAULT_CONFIG["deepl_api_key"])
    globals.deepl_url = config.get("deepl_url", DEFAULT_CONFIG["deepl_url"])


def setup_addon():
    """Register addon hooks and initialize collection-dependent globals later."""
    future = globals.executor.submit(load_config) # Run load_config in a separate thread to avoid blocking the main thread
    config = future.result()
    apply_config(config)
    gui_hooks.collection_did_load.append(_setup_collection)
    from . import gui   # Import gui to ensure that the GUI hooks are registered when the addon is loaded
    initialize_ajc()  # Call initialize_ajc to set up AJC


def _setup_collection(col):
    """Initialize collection-dependent globals after the collection is loaded."""
    globals.show_tooltip = True
    globals.seen_words = set()

    globals.collection_future = globals.executor.submit(    # Run _load_collection_data in a separate thread to avoid blocking the main thread
        _load_collection_data,
        col.media.dir(),
    )

    globals.kanji_future = globals.executor.submit(
        load_kanji_dictionary,
        col.media.dir(),
    )

    helpers.ensure_collection_loaded()


def _load_collection_data(media_dir):
    """Load learned kanji and today's words from CSV files."""
    learned_kanji_file_path = os.path.join(media_dir, globals.learned_kanji_file)
    todays_words_file_path = os.path.join(media_dir, globals.todays_words_file)

    learned_kanji = {}
    current_day = None

    try:
        with open(learned_kanji_file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            learned_kanji = {
                row["Kanji"]: {
                    "Keyword": row.get("Keyword", ""),
                    "Learned": str(row.get("Learned", "1")).lower() in {"1", "true", "yes"},
                }
                for row in reader
                if row.get("Kanji")
            }
    except FileNotFoundError:
        pass

    try:
        with open(todays_words_file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            if row:
                current_day = row[0]
    except (FileNotFoundError, StopIteration):
        pass

    return (
        learned_kanji,
        current_day,
        learned_kanji_file_path,
        todays_words_file_path,
    )

def load_kanji_dictionary(media_dir):
    """Load the kanji dictionary from the XML file."""
    file_path = globals.kanji_dictionary_file_path or os.path.join(globals.vendor_path, globals.kanji_dictionary_file)

    dictionary = {}

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for kanji in root.findall("kanji"):
            character = kanji.get("char")
            meanings = [meaning.text for meaning in kanji.findall("meaning") if meaning.text]
            dictionary[character] = meanings
    except FileNotFoundError:
        pass

    return dictionary