import unicodedata

import aqt
from aqt import mw
from anki.notes import Note

from . import globals


def fetch_kanji_meanings(kanji: str) -> list[str]:
    """Fetch English meanings for a kanji from Jamdict's Chars section."""
    if not kanji:
        return []

    meanings = globals.kanji_dictionary.get(kanji)

    if not meanings:
        return []

    return meanings


def is_kanji(char):
    """Return True if char is a kanji."""
    try:
        return unicodedata.name(char).startswith("CJK UNIFIED IDEOGRAPH")
    except ValueError:
        return False


def fetch_kanji_keyword(kanji):
    """Returns one learned keyword associated with kanji from RTK deck"""
    col = mw.col
    search_query = f'deck:"{globals.rtk_deck}" Kanji:{kanji}'
    card_ids = col.find_cards(search_query)

    if not card_ids:
        search_query = f'deck:"{globals.rtk_deck}" "Alternative Kanji:{kanji}"'
        card_ids = col.find_cards(search_query)

    if not card_ids:
        return ""

    card = col.get_card(card_ids[0])
    rtk_note = card.note()
    return f"{kanji} {rtk_note['Keyword']}"


def find_unknown_kanji():
    """Find all unknown Kanji in JapaneseMining cards"""
    search_query_rtk = 'note:"Remembering the Kanji"'
    search_query_jm = f'note:{globals.note_type} -is:suspended'

    notes_rtk = mw.col.find_notes(search_query_rtk)
    notes_jm = mw.col.find_notes(search_query_jm)

    rtk_kanji = []
    unknown_kanji = []

    for note_id in notes_rtk:
        note = mw.col.get_note(note_id)
        kanji = note["Kanji"]
        alt_kanji = note["Alternative Kanji"]

        if kanji and kanji not in rtk_kanji:
            rtk_kanji.append(kanji)
        
        if alt_kanji and alt_kanji not in rtk_kanji:
            rtk_kanji.append(alt_kanji)

    for note_id in notes_jm:
        note = mw.col.get_note(note_id)

        for ch in note["Word"]:
            if is_kanji(ch) and ch not in rtk_kanji and ch not in unknown_kanji:
                unknown_kanji.append(ch)
    
    return unknown_kanji


def create_rtk_note(kanji, alt_kanji="", tags=None, heisig_kanjis=None):
    """Create a new Remembering the Kanji note"""
    tags = tags or []

    model = mw.col.models.by_name("Remembering the Kanji")
    if model is None:
        raise RuntimeError("Note type not found")

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


def ensure_collection_loaded():
    if globals.collection_future is not None:
        (
            globals.learned_kanji,
            globals.current_day,
            globals.learned_kanji_file_path,
            globals.todays_words_file_path,
        ) = globals.collection_future.result()
        globals.collection_future = None

    if globals.kanji_future is not None:
        globals.kanji_dictionary = globals.kanji_future.result()
        globals.kanji_future = None


def set_focused_field_index(note, index):
    """Set the index of the currently focused field (editor) in the globals module."""
    globals.focused_field_index = str(index)


def get_hypertts():
    """Return the running HyperTTS instance, or None if not available."""
    for player in aqt.sound.av_player.players:
        if isinstance(player, aqt.tts.TTSProcessPlayer) and hasattr(player, "hypertts"):
            return player.hypertts
    return None

def set_hypertts(editor):
    """Set the HyperTTS instance in the globals module."""
    if globals.hypertts is None:
        globals.hypertts = get_hypertts()


def safe_current_editor(editor) -> None:
    globals.current_editor = editor


def on_card_will_add_note(problem, note) -> str | None:
    if not globals.use_hypertts:
        return

    if note is None or note.note_type()["name"] != globals.note_type:
        return

    if globals.hypertts is None:
        return

    try:
        editor_context = globals.hypertts.get_editor_context(globals.current_editor)
        globals.hypertts.apply_all_mapping_rules(editor_context)
    except Exception as e:
        print(f"Error applying mapping rules: {e}")

    return None