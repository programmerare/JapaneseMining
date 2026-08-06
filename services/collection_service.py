from aqt import mw
from aqt.utils import tooltip
from anki.notes import Note
import csv
import os
from pathlib import Path

from ..config import Config
from .kanji_data_service import KanjiDataService
from ..domain.kanji import is_kanji


class CollectionService:
    _HEISIG_KANJIS_FILE = "heisig-kanjis.csv"
    _REQUIRED_MINING_FIELDS = [
        "Word",
        "Kanji is known",
        "No Kanji",
        "Usually Kana",
        "Kanji Keywords",
        "Kanji Meanings",
    ]

    def __init__(self, config: Config, kanji_data: KanjiDataService):
        self._config = config
        self._kanji_data = kanji_data

    # --- PUBLIC METHODS --- #
    def force_update_keywords(self) -> None:
        self.update_japanese_mining_cards(force_update_keywords=True)

    def force_update_meanings(self) -> None:
        self.update_japanese_mining_cards(force_update_meanings=True)

    def force_update_everything(self) -> None:
        self.update_japanese_mining_cards(force_update_meanings=True, force_update_keywords=True)

    def fetch_kanji_keyword(self, kanji: str) -> str:
        """Returns one learned keyword associated with kanji from RTK deck"""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return ""

        col = mw.col
        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field
        keyword_field = self._config.rtk_keyword_field

        card_ids = col.find_cards(f'deck:"{deck}" {kanji_field}:{kanji}')
        if not card_ids:
            card_ids = col.find_cards(f'deck:"{deck}" "{alt_kanji_field}:{kanji}"')

        if not card_ids:
            return ""

        card = col.get_card(card_ids[0])
        note = card.note()
        return f"{kanji} {self._get_field(note, keyword_field)}"

    def add_unknown_kanji(self) -> int:
        """Add missing Kanji to the RTK deck"""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return 0

        col = mw.col
        deck = self._config.rtk_deck

        unknown_kanji = self._find_unknown_kanji()
        deck_id = col.decks.id(deck)

        path = self._media_path(self._HEISIG_KANJIS_FILE)
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            kanji_rows = {row["kanji"]: row for row in reader}

        for kanji in unknown_kanji:
            note = self._create_rtk_note(kanji=kanji, tags=["Self-Added"], heisig_kanjis=kanji_rows)
            if note:
                col.add_note(note, deck_id)

        if self._config.show_tooltip:
            tooltip(f"Added {len(unknown_kanji)} unknown kanji to the RTK deck.")

        return len(unknown_kanji)

    def export_learned_kanji(self) -> tuple[int, int]:
        """Save all Kanji, keywords, and learned status in a csv file."""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return 0, 0

        col = mw.col
        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        all_card_ids = col.find_cards(f'deck:"{deck}"')
        learned_card_ids = set(col.find_cards(f'deck:"{deck}" -is:new'))

        kanji_list = []
        count_unknown_kanji = 0
        count_learned_kanji = 0
        count_learned_alternative_kanji = 0

        for cid in all_card_ids:
            card = col.get_card(cid)
            note = card.note()
            is_learned = cid in learned_card_ids

            if kanji_field in note:
                kanji = self._get_field(note, kanji_field)
                if kanji:
                    kanji_list.append((kanji, is_learned))
                    if is_learned:
                        count_learned_kanji += 1
                    else:
                        count_unknown_kanji += 1

            if alt_kanji_field in note:
                kanji = self._get_field(note, alt_kanji_field).strip()
                if kanji:
                    kanji_list.append((kanji, is_learned))
                    if is_learned:
                        count_learned_alternative_kanji += 1
                    else:
                        count_unknown_kanji += 1

        kanji_rows = {}
        for kanji, is_learned in kanji_list:
            kanji_rows[kanji] = kanji_rows.get(kanji, False) or is_learned

        learned_kanji_rows = []
        learned_kanji_cache = {}

        for kanji in sorted(kanji_rows, key=lambda item: (not kanji_rows[item], item)):
            keyword = self.fetch_kanji_keyword(kanji)
            learned = kanji_rows[kanji]
            learned_kanji_rows.append({"Kanji": kanji, "Keyword": keyword, "Learned": "1" if learned else ""})
            learned_kanji_cache[kanji] = {"Keyword": keyword, "Learned": learned}

        if self._kanji_data:
            self._kanji_data.save_learned_kanji(learned_kanji_rows, learned_kanji_cache)

        if self._config.show_tooltip:
            tooltip(f"Exported {count_learned_kanji + count_learned_alternative_kanji} learned kanji and {count_unknown_kanji} unknown kanji.")

        return count_learned_kanji + count_learned_alternative_kanji, count_unknown_kanji

    def update_single_note_kanji_knowledge(self, note: Note, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update kanji fields for a single note added from the editor."""
        if note is None:
            return 0, 0

        if note.note_type()["name"] != self._config.mining_note_type:
            if self._config.show_tooltip:
                tooltip(f"The note is not a {self._config.mining_note_type} note. Please check your settings.")
            return 0, 0

        newly_known_count, updated_count = self._update_kanji_knowledge(
            note=note,
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        return newly_known_count, updated_count

    def update_japanese_mining_cards(self, force_update_meanings: bool = False, force_update_keywords: bool = False) -> None:
        """Update all JapaneseMining cards in a single pass over each word."""
        number_learned_kanji, count_unknown_kanji = self.export_learned_kanji()
        newly_known_count, number_updated_cards = self._update_kanji_knowledge(
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        number_unknown_kanji = self.add_unknown_kanji()

        if self._config.show_tooltip:
            tooltip(
                f"Exported {number_learned_kanji} learned and {count_unknown_kanji} not learned kanji. "
                f"{newly_known_count} card(s) became known. "
                f"{number_updated_cards} card(s) were updated. {number_unknown_kanji} unknown kanji were added."
            )

    # --- PRIVATE METHODS --- #
    def _find_unknown_kanji(self) -> list[str]:
        """Find all unknown Kanji in JapaneseMining cards"""
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        rtk_note_ids = mw.col.find_notes(f'note:"{self._config.rtk_note_type}"')
        mining_note_ids = mw.col.find_notes(f'note:{self._config.mining_note_type} -is:suspended')

        known = set()
        for note_id in rtk_note_ids:
            note = col.get_note(note_id)
            known.add(self._get_field(note, kanji_field))
            known.add(self._get_field(note, alt_kanji_field))

        unknown = []
        for note_id in mining_note_ids:
            note = col.get_note(note_id)
            for ch in self._get_field(note, "Word"):
                if is_kanji(ch) and ch not in known and ch not in unknown:
                    unknown.append(ch)
        
        return unknown

    def _create_rtk_note(self, kanji: str, alt_kanji: str = "", tags=None, heisig_kanjis=None) -> Note | None:
        """Create a new Remembering the Kanji note"""
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        tags = tags or []
        model = col.models.by_name(self._config.rtk_note_type)
        if model is None:
            raise RuntimeError(f"Note type '{self._config.rtk_note_type}' not found")

        note = Note(col, model)
        note[kanji_field] = kanji
        note[alt_kanji_field] = alt_kanji
        note.tags.extend(tags)

        if heisig_kanjis is not None:
            row = heisig_kanjis.get(kanji)
            if row:
                note[self._config.rtk_keyword_field] = row["keyword_6th_ed"]
            if row and self._has_field(note, self._config.rtk_heisig_number_field):
                note[self._config.rtk_heisig_number_field] = row["id_6th_ed"]    # Optional
            if row and self._has_field(note, self._config.rtk_stroke_count_field):
                note[self._config.rtk_stroke_count_field] = row["stroke_count"]  # Optional

        if note.dupeOrEmpty():
            return None
        return note

    def _update_note_kanji_knowledge(self, note: Note, learned_kanji: dict, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update kanji knowledge fields for one note."""
        if not self._mining_fields_ok(note):
            if self._config.show_tooltip:
                tooltip(f"Note {note.id} is missing required fields. Please check your note and you notetype {self._config.mining_note_type}.")
            return 0, 0

        col = mw.col
        should_update = False
        all_known = True
        no_kanji = True

        keywords = []
        meanings = []
        keywords_present = bool(self._get_field(note, "Kanji Keywords"))
        meanings_present = bool(self._get_field(note, "Kanji Meanings"))

        for ch in self._get_field(note, "Word"):
            if not is_kanji(ch):
                continue

            no_kanji = False
            kanji_entry = learned_kanji.get(ch)
            if not kanji_entry or not kanji_entry.get("Learned"):
                all_known = False

            if not keywords_present or force_update_keywords:
                kanji_keyword = kanji_entry.get("Keyword", "") if kanji_entry else ""
                if kanji_keyword and kanji_keyword not in keywords:
                    keywords.append(kanji_keyword)

            if not meanings_present or force_update_meanings:
                tmp = self._kanji_data.get_kanji_meanings(ch)
                tmp = " · ".join(tmp)
                tmp = ch + ": " + tmp
                if tmp not in meanings:
                    meanings.append(tmp)

        if no_kanji and self._get_field(note, "No Kanji") != "1":
            note["No Kanji"] = "1"
            note["Usually Kana"] = "1"
            should_update = True

        previous_value = self._get_field(note, "Kanji is known")
        new_value = "1" if all_known else ""
        newly_known = 0

        if previous_value != new_value:
            if previous_value != "1" and new_value == "1":
                newly_known = 1
            note["Kanji is known"] = new_value
            should_update = True

        if keywords:
            note["Kanji Keywords"] = " · ".join(keywords)
            should_update = True

        if meanings:
            note["Kanji Meanings"] = " | ".join(meanings)
            should_update = True

        tags = self._get_field(note, "Tags")
        if self._get_field(note, "Usually Kana") != "1" and "Usually written using kana alone" in tags:
            note["Usually Kana"] = "1"
            should_update = True

        if should_update:
            col.update_note(note)

        return newly_known, int(should_update)


    def _update_kanji_knowledge(self, note: Note = None, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update JapaneseMining cards in a single pass over each word."""
        col = mw.col

        learned_kanji = self._kanji_data.get_learned_kanji()
        if note is not None:
            notes = [note]
        else:
            notes = (col.get_note(note_id) for note_id in col.find_notes(f"note:{self._config.mining_note_type}"))

        newly_known_count = 0
        updated_count = 0

        for current_note in notes:
            note_newly_known, note_updated = self._update_note_kanji_knowledge(
                current_note,
                learned_kanji,
                force_update_meanings=force_update_meanings,
                force_update_keywords=force_update_keywords,
            )
            newly_known_count += note_newly_known
            updated_count += note_updated

        if note is None and self._config.show_tooltip:
            tooltip(
                f"Rechecked kanji knowledge. {newly_known_count} card(s) became known. "
                f"Updated kanji details for {updated_count} card(s)."
            )

        return newly_known_count, updated_count

    def _has_field(self, note: Note, name: str) -> bool:
        """Check if a note has a field with the given name."""
        return name in note

    def _get_field(self, note: Note, name: str, default: str = "") -> str:
        """Get the value of a field in a note."""
        return note[name] if name in note else default

    def _mining_fields_ok(self, note: Note) -> bool:
        """Check if a JapaneseMining note has all required fields."""
        return all(name in note for name in self._REQUIRED_MINING_FIELDS)

    def _rtk_configured(self) -> bool:
        return bool(
            self._config.rtk_deck
            and self._config.rtk_note_type
            and self._config.rtk_kanji_field
            and self._config.rtk_keyword_field
        )

    def _media_path(self, filename: str) -> Path:
        """Return the full path to a file in the Anki media directory."""
        return Path(mw.col.media.dir()) / filename