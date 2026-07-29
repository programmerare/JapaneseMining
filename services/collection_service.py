from aqt import mw
from anki.notes import Note

from config import Config
from domain.kanji import is_kanji


class CollectionService:
    def __init__(self, config: Config):
        self._config = config

    def fetch_kanji_keyword(self, kanji: str) -> str:
        """Returns one learned keyword associated with kanji from RTK deck"""
        col = mw.col
        deck = self._config.rtk_deck

        card_ids = col.find_cards(f'deck:"{deck}" Kanji:{kanji}')
        if not card_ids:
            card_ids = col.find_cards(f'deck:"{deck}" "Alternative Kanji:{kanji}"')

        if not card_ids:
            return ""

        card = col.get_card(card_ids[0])
        note = card.note()
        return f"{kanji} {note['Keyword']}"

    def find_unknown_kanji(self) -> list[str]:
        """Find all unknown Kanji in JapaneseMining cards"""
        col = mw.col

        rtk_note_ids = mw.col.find_notes('note:"Remembering the Kanji"')
        mining_note_ids = mw.col.find_notes(f'note:{self._config.note_type} -is:suspended')

        known = set()
        for note_id in rtk_note_ids:
            note = col.get_note(note_id)
            if note["Kanji"]:
                known.add(note["Kanji"])
            if note["Alternative Kanji"]:
                known.add(note["Alternative Kanji"])

        unknown = []
        for note_id in mining_note_ids:
            note = col.get_note(note_id)
            for ch in note["Word"]:
                if is_kanji(ch) and ch not in known and ch not in unknown:
                    unknown.append(ch)
        
        return unknown

    def create_rtk_note(self, kanji: str, alt_kanji: str = "", tags=None, heisig_kanjis=None):
        """Create a new Remembering the Kanji note"""
        tags = tags or []
        model = mw.col.models.by_name("Remembering the Kanji")
        if model is None:
            raise RuntimeError("Note type 'Remembering the Kanji' not found")

        note = Note(mw.col, model)
        note["Kanji"] = kanji
        note["Alternative Kanji"] = alt_kanji
        note.tags.extend(tags)

        if heisig_kanjis is not None:
            row = heisig_kanjis.get(kanji)
            if row:
                note["Heisig Number"] = row["id_6th_ed"]
                note["Keyword"] = row["keyword_6th_ed"]
                note["Stroke Count"] = row["stroke_count"]

        if note.dupeOrEmpty():
            return False
        return note