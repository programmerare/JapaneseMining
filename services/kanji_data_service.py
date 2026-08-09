from aqt import mw
import csv
from datetime import date
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from ..config import Config


class KanjiDataService:
    _LEARNED_KANJI_FILE = "learned_kanji.csv"
    _KANJI_MEANINGS_FILE = "kanji_meanings.xml"
    _TODAYS_WORDS_FILE = "todays_words.csv"

    def __init__(self, config: Config):
        self._config = config
        self._learned_kanji: dict[str, dict] = {}
        self._kanji_meanings: dict[str, list[str]] = {}
        self._todays_words: list[tuple[str, str, str]] = []
        self._seen_words: set[tuple[str, str]] = set()
        self._current_day: str | None = None

    # --- PUBLIC METHODS --- #
    def get_learned_kanji(self) -> dict[str, dict]:
        """Return the learned kanji cache."""
        return self._learned_kanji

    def get_kanji_meanings(self, kanji: str) -> list[str]:
        """Return the meanings for a kanji from the cache."""
        return self._kanji_meanings.get(kanji, [])

    def get_todays_words(self) -> list[tuple[str, str, str]]:
        """Return the words learned today from the cache."""
        return self._todays_words

    def get_heatmap_data(self) -> tuple[list[str], list[str], int, int]:
        """Return the learned and remaining kanji for the heatmap."""
        data = self._learned_kanji
        learned = [k for k, v in data.items() if v.get("Learned")]
        remaining = [k for k, v in data.items() if not v.get("Learned")]

        learned.sort()
        remaining.sort()

        keywords = {k: v.get("Keyword", "") for k, v in data.items()}

        return learned, remaining, len(learned), len(learned) + len(remaining), keywords

    def load_learned_kanji(self) -> None:
        """Load learned kanji and their keywords from a csv file."""
        file_path = self._media_path(self._LEARNED_KANJI_FILE)
        try:
            with file_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._learned_kanji = {
                    row["Kanji"]: {
                        "Keyword": row.get("Keyword", ""),
                        "Learned": str(row.get("Learned", "1")).lower() in {"1", "true", "yes"},
                    }
                    for row in reader
                    if row.get("Kanji")
                }
        except FileNotFoundError:
            self._learned_kanji = {}

    def save_learned_kanji(self, rows: list[dict], cache: dict) -> None:
        """Save all Kanji, keywords, and learned status in a csv file."""
        self._learned_kanji = cache

        file_path = self._media_path(self._LEARNED_KANJI_FILE)
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Kanji", "Keyword", "Learned"])
            writer.writeheader()
            writer.writerows(rows)

    def load_kanji_meanings(self) -> None:
        """Load the kanji meanings dictionary from the XML file."""
        file_path = self._vendor_path(self._KANJI_MEANINGS_FILE)

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

        self._kanji_meanings = dictionary

    def load_todays_words(self) -> None:
        """Load words learned today from the CSV file."""
        today = str(date.today())
        words = []

        file_path = self._media_path(self._TODAYS_WORDS_FILE)
        try:
            with file_path.open(encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if self._current_day is None:
                        self._current_day = row[0]
                    if self._current_day == today:
                        words.append((row[1], row[2], row[3]))
        except FileNotFoundError:
            pass
        self._todays_words = words

    def save_todays_word(self, word: str, reading: str, meaning: str) -> None:
        """Save a word to the todays_words.csv file."""
        today = str(date.today())

        if self._current_day != today:
            self._current_day = today
            self._todays_words = []
            self._overwrite_file()

        self._append_word(word, reading, meaning)

    # --- PRIVATE METHODS --- #
    def _overwrite_file(self) -> None:
        """Overwrite the todays_words.csv file with a new header."""
        file_path = self._media_path(self._TODAYS_WORDS_FILE)
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Word", "Reading", "Meaning"])

    def _append_word(self, word: str, reading: str, meaning: str) -> None:
        """Append a word to the todays_words.csv file if it hasn't been seen today."""
        key = (word, reading)

        if key in self._seen_words:
            return
        self._seen_words.add(key)

        self._todays_words.append((word, reading, meaning))

        file_path = self._media_path(self._TODAYS_WORDS_FILE)
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                date.today(),
                word,
                reading,
                meaning,
            ])

    def _media_path(self, filename: str) -> Path:
        """Return the full path to a file in the Anki media directory."""
        return Path(mw.col.media.dir()) / filename

    def _vendor_path(self, filename: str) -> Path:
        """Return the full path to a file in the vendor directory."""
        return Path(__file__).resolve().parent.parent / "vendor" / filename