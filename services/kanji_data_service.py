from aqt import mw
from aqt.utils import showWarning
import csv
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

from ..domain.errors import JapaneseMiningError
from ..config import ConfigHolder, profile_user_dir, is_valid_mining_note_type


class KanjiDataService:
    _LEARNED_KANJI_FILE = "learned_kanji.csv"
    _KANJI_MEANINGS_FILE = "kanji_meanings.xml"
    _TODAYS_WORDS_FILE = "todays_words.csv"
    _TODAYS_KANJI_FILE = "todays_kanji.csv"
    _TODAYS_KNOWN_CARDS_FILE = "todays_known_cards.csv"
    _FLAGGED_KANJI_FILE = "flagged_kanji.csv"

    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder
        self._learned_kanji: dict[str, dict] = {}
        self._kanji_meanings: dict[str, list[str]] = {}
        self._todays_words: list[tuple[str, str, str]] = []
        self._todays_kanji: list[tuple[str, str]] = []
        self._todays_known_cards: list[tuple[str, str, str]] = []
        self._flagged_kanji: list[tuple[str, str, str]] = []
        self._seen_words: set[tuple[str, str]] = set()
        self._seen_kanji: set[str] = set()
        self._seen_known_cards: set[tuple[str, str]] = set()
        self._seen_flagged_kanji: set[str] = set()
        # Calendar day for which the three progress caches are valid.
        self._progress_day: str | None = None
        self.needs_update: bool = False
        self._warned_missing_meanings = False

    @property
    def _config(self):
        return self._config_holder.config

    # --- PUBLIC METHODS --- #
    # --- GETTERS --- #
    def get_learned_kanji(self) -> dict[str, dict]:
        """Return the learned kanji cache."""
        return self._learned_kanji

    def get_kanji_meanings(self, kanji: str) -> list[str]:
        """Return the meanings for a kanji from the cache."""
        return self._kanji_meanings.get(kanji, [])

    def get_todays_words(self) -> list[tuple[str, str, str]]:
        """Return the words learned today from the cache."""
        self.ensure_todays_progress()
        return self._todays_words

    def get_todays_kanji(self) -> list[tuple[str, str]]:
        """Return the kanji learned today from the cache."""
        self.ensure_todays_progress()
        return self._todays_kanji

    def get_todays_known_cards(self) -> list[tuple[str, str, str]]:
        """Return the known cards learned today from the cache."""
        self.ensure_todays_progress()
        return self._todays_known_cards

    def get_flagged_kanji(self) -> list[tuple[str, str, str]]:
        """Return the flagged kanji from the cache."""
        return self._flagged_kanji

    def get_todays_summary(self) -> dict[str, int]:
        """Return a summary of the words, kanji, and known cards learned today."""
        self.ensure_todays_progress()
        return {
            "words": len(self._todays_words),
            "kanji": len(self._todays_kanji),
            "known_cards": len(self._todays_known_cards),
        }

    def ensure_todays_progress(self) -> None:
        """
        Roll today's progress caches forward when the calendar day changes.

        Only touches words / kanji / known-cards. Learned kanji, meanings, and
        flagged kanji are loaded on collection_did_load via load_profile_data.
        """
        today = str(date.today())
        if self._progress_day == today:
            return

        self.load_todays_words()
        self.load_todays_kanji()
        self.load_todays_known_cards()
        self._progress_day = today

    def get_heatmap_data(
        self,
    ) -> tuple[list[str], list[str], int, int, dict[str, str], dict[str, float]]:
        """Return the learned and remaining kanji for the heatmap."""
        data = self._learned_kanji

        learned = [k for k, v in data.items() if v.get("Learned")]
        remaining = [k for k, v in data.items() if not v.get("Learned")]

        learned.sort(key=lambda k: (-data[k].get("Knowledge", 0.0), k))
        remaining.sort()

        keywords = {k: v.get("Keyword", "") for k, v in data.items()}
        knowledge = {
            k: float(v.get("Knowledge", 0.0))
            for k, v in data.items()
            if v.get("Learned")
        }

        return (
            learned,
            remaining,
            len(learned),
            len(learned) + len(remaining),
            keywords,
            knowledge,
        )

    # --- LOADERS AND SAVERS --- #
    def load_profile_data(self) -> None:
        """
        Full cache rebuild for the current profile.

        Called from collection_did_load only. Always reloads — do not day-gate
        here, or profile switches on the same calendar day will keep stale data.
        """
        self.load_learned_kanji()
        try:
            self.load_kanji_meanings()
        except JapaneseMiningError as e:
            if not self._warned_missing_meanings:
                self._warned_missing_meanings = True
                mw.taskman.run_on_main(
                    lambda e=e: showWarning(
                        e.full_message(),
                        parent=mw,
                        title="JapaneseMining",
                    )
                )
        self.load_flagged_kanji()
        self.load_todays_words()
        self.load_todays_kanji()
        self.load_todays_known_cards()
        self._progress_day = str(date.today())

    def load_kanji_meanings(self) -> None:
        """Load the kanji meanings dictionary from the XML file."""
        file_path = self._vendor_path(self._KANJI_MEANINGS_FILE)

        dictionary = {}

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for kanji in root.findall("kanji"):
                character = kanji.get("char")
                meanings = [
                    meaning.text for meaning in kanji.findall("meaning") if meaning.text
                ]
                dictionary[character] = meanings
            self._kanji_meanings = dictionary
        except FileNotFoundError:
            self._kanji_meanings = {}
            raise JapaneseMiningError(
                "Kanji meanings data is missing.",
                details=(
                    f"Expected file:\n{file_path}\n\n"
                    "Hover tooltips for kanji meanings will not work until this is fixed.\n"
                    "Reinstall the JapaneseMining add-on (or restore the vendor folder)."
                ),
            )
        except ET.ParseError as e:
            self._kanji_meanings = {}
            raise JapaneseMiningError(
                "Kanji meanings data is corrupt.",
                details=f"{file_path}\n\n{e}",
            )

    def load_learned_kanji(self) -> None:
        """Load learned kanji and their keywords from a csv file."""
        file_path = self._user_data_path(self._LEARNED_KANJI_FILE)
        try:
            with file_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._learned_kanji = {}
                for row in reader:
                    kanji = row.get("Kanji")
                    if not kanji:
                        continue
                    knowledge_raw = row.get("Knowledge", "")
                    try:
                        knowledge = (
                            float(knowledge_raw)
                            if knowledge_raw not in (None, "")
                            else 0.0
                        )
                    except ValueError:
                        knowledge = 0.0

                    self._learned_kanji[kanji] = {
                        "Keyword": row.get("Keyword", ""),
                        "Learned": str(row.get("Learned", "1")).lower()
                        in {"1", "true", "yes"},
                        "Knowledge": knowledge,
                    }
        except FileNotFoundError:
            self._learned_kanji = {}

    def load_todays_words(self) -> None:
        """Load words learned today from the CSV file."""
        today = str(date.today())
        items: list[tuple[str, str, str]] = []
        file_path = self._user_data_path(self._TODAYS_WORDS_FILE)

        try:
            with file_path.open(encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 4 and row[0] == today:
                        items.append((row[1], row[2], row[3]))
        except FileNotFoundError:
            pass
        self._todays_words = items
        self._seen_words = {(w, r) for w, r, _ in items}

    def load_todays_kanji(self) -> None:
        """Load kanji learned today from CSV."""
        today = str(date.today())
        items: list[tuple[str, str]] = []
        file_path = self._user_data_path(self._TODAYS_KANJI_FILE)

        try:
            with file_path.open(encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 2 and row[0] == today:
                        items.append((row[1], row[2] if len(row) > 2 else ""))
        except FileNotFoundError:
            pass
        self._todays_kanji = items
        self._seen_kanji = {k for k, _ in items}

    def load_todays_known_cards(self) -> None:
        """Load cards that became known today from CSV."""
        today = str(date.today())
        items: list[tuple[str, str, str]] = []
        file_path = self._user_data_path(self._TODAYS_KNOWN_CARDS_FILE)

        try:
            with file_path.open(encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 4 and row[0] == today:
                        items.append((row[1], row[2], row[3]))
        except FileNotFoundError:
            pass
        self._todays_known_cards = items
        self._seen_known_cards = {(w, r) for w, r, _ in items}

    def load_flagged_kanji(self) -> None:
        """Load flagged kanji from CSV. Columns: Heisig Number, Kanji, Keyword."""
        items: list[tuple[str, str, str]] = []
        file_path = self._user_data_path(self._FLAGGED_KANJI_FILE)

        try:
            with file_path.open(encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 2:
                        continue
                    heisig, kanji, keyword = (
                        row[0],
                        row[1],
                        row[2] if len(row) > 2 else "",
                    )
                    if kanji:
                        items.append((kanji, keyword, heisig))
        except FileNotFoundError:
            pass
        self._flagged_kanji = items
        self._seen_flagged_kanji = {k for k, _, _ in items}

    def save_learned_kanji(self, rows: list[dict], cache: dict) -> None:
        """Save all Kanji, keywords, and learned status in a csv file."""
        self._learned_kanji = cache

        file_path = self._user_data_path(self._LEARNED_KANJI_FILE)
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["Kanji", "Keyword", "Learned", "Knowledge"]
            )
            writer.writeheader()
            writer.writerows(rows)

    def save_todays_word(self, word: str, reading: str, meaning: str) -> None:
        """Save a word to the todays_words.csv file."""
        today = str(date.today())
        if self._progress_day != today:
            self._progress_day = today
            self._todays_words = []
            self._todays_kanji = []
            self._todays_known_cards = []
            self._seen_words.clear()
            self._seen_kanji.clear()
            self._seen_known_cards.clear()
            self._overwrite_todays_files()

        key = (word, reading)
        if key in self._seen_words:
            return
        self._seen_words.add(key)
        self._todays_words.append((word, reading, meaning))

        file_path = self._user_data_path(self._TODAYS_WORDS_FILE)
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([today, word, reading, meaning])

    def save_todays_kanji(self, kanji: str, keyword: str = "") -> None:
        """Record a kanji the first time its RTK card is answered today."""
        today = str(date.today())
        if self._progress_day != today:
            self._progress_day = today
            self._todays_words = []
            self._todays_kanji = []
            self._todays_known_cards = []
            self._seen_words.clear()
            self._seen_kanji.clear()
            self._seen_known_cards.clear()
            self._overwrite_todays_files()

        if kanji in self._seen_kanji:
            return
        self._seen_kanji.add(kanji)
        self._todays_kanji.append((kanji, keyword))

        file_path = self._user_data_path(self._TODAYS_KANJI_FILE)
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([today, kanji, keyword])

    def save_todays_known_card(self, word: str, reading: str, meaning: str) -> None:
        """Record a mining card that flipped to 'Kanji is known' today."""
        today = str(date.today())
        if self._progress_day != today:
            self._progress_day = today
            self._todays_words = []
            self._todays_kanji = []
            self._todays_known_cards = []
            self._seen_words.clear()
            self._seen_kanji.clear()
            self._seen_known_cards.clear()
            self._overwrite_todays_files()

        key = (word, reading)
        if key in self._seen_known_cards:
            return
        self._seen_known_cards.add(key)
        self._todays_known_cards.append((word, reading, meaning))

        file_path = self._user_data_path(self._TODAYS_KNOWN_CARDS_FILE)
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([today, word, reading, meaning])

    def save_flagged_kanji(
        self, kanji: str, keyword: str = "", heisig_number: str = ""
    ) -> None:
        """Record a kanji that was flagged (red) in the RTK deck. Idempotent."""
        kanji = (kanji or "").strip()
        if not kanji or kanji in self._seen_flagged_kanji:
            return

        keyword = (keyword or "").strip()
        heisig_number = (heisig_number or "").strip()

        self._seen_flagged_kanji.add(kanji)
        self._flagged_kanji.append((kanji, keyword, heisig_number))

        file_path = self._user_data_path(self._FLAGGED_KANJI_FILE)
        write_header = not file_path.exists() or file_path.stat().st_size == 0

        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["Heisig Number", "Kanji", "Keyword"])
            writer.writerow([heisig_number, kanji, keyword])

    def sync_flagged_kanji_from_collection(self) -> int:
        """
        Scan the collection for red-flagged RTK cards and make the
        flagged_kanji.csv + in-memory cache match exactly.

        Returns the number of kanji now in the list.
        """
        if not mw.col:
            return len(self._flagged_kanji)

        config = self._config
        deck = (config.rtk_deck or "").strip()
        note_type = (config.rtk_note_type or "").strip()
        kanji_field = config.rtk_kanji_field or "Kanji"
        keyword_field = config.rtk_keyword_field or "Keyword"
        heisig_field = config.rtk_heisig_number_field or "Heisig Number"

        if not deck:
            return len(self._flagged_kanji)

        query = f'deck:"{deck}" flag:1'
        if note_type:
            query += f' note:"{note_type}"'

        card_ids = mw.col.find_cards(query)

        seen: set[str] = set()
        items: list[tuple[str, str, str]] = []

        for cid in card_ids:
            card = mw.col.get_card(cid)
            note = card.note()

            kanji = note[kanji_field].strip() if kanji_field in note else ""
            if not kanji or kanji in seen:
                continue
            seen.add(kanji)

            keyword = note[keyword_field].strip() if keyword_field in note else ""
            heisig = note[heisig_field].strip() if heisig_field in note else ""
            items.append((kanji, keyword, heisig))

        def sort_key(item):
            kanji, keyword, heisig = item
            try:
                return (0, int(heisig))
            except (TypeError, ValueError):
                return (1, kanji)

        items.sort(key=sort_key)

        self._flagged_kanji = items
        self._seen_flagged_kanji = {k for k, _, _ in items}

        file_path = self._user_data_path(self._FLAGGED_KANJI_FILE)
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Heisig Number", "Kanji", "Keyword"])
            for kanji, keyword, heisig in items:
                writer.writerow([heisig, kanji, keyword])

        return len(items)

    # --- EVENT HANDLERS --- #
    def handle_card_answered(self, reviewer, card, ease) -> None:
        """
        Handles both mining cards (today's words) and RTK cards (today's kanji).
        Silent on note-type mismatch so we never interrupt the user.
        """
        if card.reps != 1:
            return

        note = card.note()
        note_type_name = note.note_type()["name"]

        if is_valid_mining_note_type(note_type_name, self._config):
            word = note["Word"] if "Word" in note else ""
            if not word:
                return
            reading = note["Reading"] if "Reading" in note else ""
            meaning = note["Meaning"] if "Meaning" in note else ""
            self.save_todays_word(word, reading, meaning)
            return

        if note_type_name == self._config.rtk_note_type:
            kanji_field = self._config.rtk_kanji_field or "Kanji"
            keyword_field = self._config.rtk_keyword_field or "Keyword"
            kanji = note[kanji_field].strip() if kanji_field in note else ""
            if not kanji:
                return
            keyword = note[keyword_field].strip() if keyword_field in note else ""
            self.save_todays_kanji(kanji, keyword)

        if note_type_name == self._config.rtk_note_type:
            if card.user_flag() == 1:
                kanji_field = self._config.rtk_kanji_field or "Kanji"
                keyword_field = self._config.rtk_keyword_field or "Keyword"
                heisig_field = self._config.rtk_heisig_number_field or "Heisig Number"

                kanji = note[kanji_field].strip() if kanji_field in note else ""
                if not kanji:
                    return
                keyword = note[keyword_field].strip() if keyword_field in note else ""
                heisig = note[heisig_field].strip() if heisig_field in note else ""
                self.save_flagged_kanji(kanji, keyword, heisig)

        try:
            deck_name = mw.col.decks.name(card.did)
            rtk_deck = self._config_holder.config.rtk_deck
            if deck_name == rtk_deck or deck_name.startswith(rtk_deck + "::"):
                self.mark_update_needed()
        except Exception:
            pass

    # --- UPDATE INDICATOR --- #
    def mark_update_needed(self) -> None:
        if self._config_holder.config.show_update_needed and not self.needs_update:
            self.needs_update = True
            from ..ui.update_indicator import refresh_deck_browser

            refresh_deck_browser()

    def clear_update_needed(self) -> None:
        if self.needs_update:
            self.needs_update = False
            from ..ui.update_indicator import refresh_deck_browser

            refresh_deck_browser()

    # --- PRIVATE METHODS --- #
    def _overwrite_todays_files(self) -> None:
        """Reset all three today files with headers (called on day change)."""
        for filename, header in (
            (self._TODAYS_WORDS_FILE, ["Date", "Word", "Reading", "Meaning"]),
            (self._TODAYS_KANJI_FILE, ["Date", "Kanji", "Keyword"]),
            (self._TODAYS_KNOWN_CARDS_FILE, ["Date", "Word", "Reading", "Meaning"]),
        ):
            path = self._user_data_path(filename)
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)

    # --- PATH HELPERS --- #
    def _user_data_path(self, filename: str) -> Path:
        """Return the full path to a file in the user data directory."""
        return profile_user_dir() / filename

    def _media_path(self, filename: str) -> Path:
        """Return the full path to a file in the Anki media directory."""
        return Path(mw.col.media.dir()) / filename

    def _vendor_path(self, filename: str) -> Path:
        """Return the full path to a file in the vendor directory."""
        return Path(__file__).resolve().parent.parent / "vendor" / filename
