from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import QAction, QMenu
from concurrent.futures import ThreadPoolExecutor

from .config import load_config, save_config
from .services.collection_service import CollectionService
from .services.deepl_service import DeeplService
from .services.jisho_service import JishoService
from .services.hypertts_service import HyperTTSService
from .services.kanji_data_service import KanjiDataService
from .ui.settings.dialog import make_show_settings
from .ui.todays_words import make_show_todays_words
from .ui.editor import make_translate_btn_setup, inject_editor_css, make_segment_sentence
from .ui.menu import setup_menu


_executor = ThreadPoolExecutor(max_workers=2)

_current_editor: Editor | None = None

def _set_current_editor(editor: Editor) -> None:
    global _current_editor
    _current_editor = editor

def _get_current_editor():
    return _current_editor

_focused_field_index: str | None = None

def _set_focused_field(note, index):
    global _focused_field_index
    _focused_field_index = str(index) if index is not None else None

def _get_focused_field_index():
    return _focused_field_index

def setup_addon():
    """Set up the JapaneseMining add-on, including services, hooks, and menu actions."""
    print("Setting up new JapaneseMining add-on...")
    config = load_config()

    # Create services
    kanji_data_service = KanjiDataService(config)
    collection_service = CollectionService(config, kanji_data_service)
    deepl_service = DeeplService(config)
    jisho_service = JishoService(config)
    hypertts_service = HyperTTSService(config)

    # --- Initialize services that require it ---
    jisho_service.initialize()

    # --- data loading in background (must run after collection is ready) ---
    def on_collection_loaded(col):
        def load():
            kanji_data_service.load_learned_kanji()
            kanji_data_service.load_kanji_meanings()
            kanji_data_service.load_todays_words()
        _executor.submit(load)

    # --- HOOKS ---
    gui_hooks.collection_did_load.append(on_collection_loaded)

    # --- editor tracking ---
    gui_hooks.editor_did_init.append(_set_current_editor)

    # --- focused field tracking ---
    gui_hooks.editor_did_focus_field.append(_set_focused_field)

    def on_note_added(note: Note):
        collection_service.update_single_note_kanji_knowledge(note)

    def on_will_add_note(problem: str | None, note: Note):
        editor = _get_current_editor()
        hypertts_service.add_audio(problem, note, editor)

    gui_hooks.add_cards_did_add_note.append(on_note_added)
    gui_hooks.add_cards_will_add_note.append(on_will_add_note)

    gui_hooks.editor_did_init.append(inject_editor_css)

    set_translate_btn = make_translate_btn_setup(deepl_service, config)
    gui_hooks.editor_did_init_buttons.append(set_translate_btn)

    segment_sentence = make_segment_sentence(config, _get_focused_field_index)
    gui_hooks.editor_did_fire_typing_timer.append(segment_sentence)

    def on_card_answered(reviewer, card, ease):
        if card.reps != 1:
            return
        note = card.note()
        if note.note_type()["name"] != config.mining_note_type:
            return
        word = note["Word"] if "Word" in note else ""
        reading = note["Reading"] if "Reading" in note else ""
        meaning = note["Meaning"] if "Meaning" in note else ""
        if word:
            kanji_data_service.save_todays_word(word, reading, meaning)

    gui_hooks.reviewer_did_answer_card.append(on_card_answered)

    # --- Setup menu actions ---
    show_todays_words = make_show_todays_words(kanji_data_service)
    show_settings = make_show_settings(config, save_config)

    setup_menu(
        config,
        collection_service,
        show_todays_words,
        show_settings,
    )
