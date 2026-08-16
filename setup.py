from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import QAction, QMenu
from aqt.utils import showWarning
from concurrent.futures import ThreadPoolExecutor

from .config import ConfigHolder, load_config, save_config
from .domain.errors import JapaneseMiningError
from .domain.media_sync import ensure_reference_files
from .services.collection_service import CollectionService
from .services.deepl_service import DeeplService
from .services.jisho_service import JishoService
from .services.hypertts_service import HyperTTSService
from .services.kanji_data_service import KanjiDataService
from .ui.settings.dialog import make_show_settings
from .ui.editor import (
    make_translate_btn_setup,
    inject_editor_css,
    make_segment_sentence,
)
from .ui.menu import setup_menu
from .ui.update_indicator import setup_update_indicator

_executor = ThreadPoolExecutor(max_workers=2)

_current_editor: Editor | None = None

_warned_missing_meanings = False


def _set_current_editor(editor: Editor) -> None:
    global _current_editor
    _current_editor = editor


def _get_current_editor():
    return _current_editor


def _get_live_add_cards_editor() -> Editor | None:
    # AddCards window keeps a reference to its editor
    from aqt.addcards import AddCards
    for widget in mw.app.topLevelWidgets():
        if isinstance(widget, AddCards) and widget.isVisible():
            editor = getattr(widget, "editor", None)
            if editor is not None and getattr(editor, "web", None) is not None:
                return editor
    return None


_focused_field_index: str | None = None


def _set_focused_field(note, index):
    global _focused_field_index
    _focused_field_index = str(index) if index is not None else None


def _get_focused_field_index():
    return _focused_field_index


def setup_addon():
    """Set up the JapaneseMining add-on, including services, hooks, and menu actions."""
    print("Setting up new JapaneseMining add-on...")
    config_holder = ConfigHolder(load_config())

    # Create services
    kanji_data_service = KanjiDataService(config_holder)
    collection_service = CollectionService(config_holder, kanji_data_service)
    deepl_service = DeeplService(config_holder)
    jisho_service = JishoService(config_holder)
    hypertts_service = HyperTTSService(config_holder)

    # --- data loading in background (must run after collection is ready) ---
    def on_collection_loaded(col):
        config_holder.reload()
        jisho_service.initialize()

        def load():
            try:
                updated = ensure_reference_files(mw.col.media.dir())
            except FileNotFoundError as e:
                mw.taskman.run_on_main(
                    lambda e=e: showWarning(
                        str(e),
                        parent=mw,
                        title="JapaneseMining",
                    )
                )
                return

            kanji_data_service.load_learned_kanji()
            try:
                kanji_data_service.load_kanji_meanings()
            except JapaneseMiningError as e:
                global _warned_missing_meanings
                if not _warned_missing_meanings:
                    _warned_missing_meanings = True
                    mw.taskman.run_on_main(
                        lambda e=e: showWarning(
                            e.full_message(),
                            parent=mw,
                            title="JapaneseMining",
                        )
                    )
            kanji_data_service.load_todays_words()
            kanji_data_service.load_todays_kanji()
            kanji_data_service.load_todays_known_cards()
            kanji_data_service.load_flagged_kanji()

            # Clear the update needed flag after loading (Including profile switch) to avoid showing the indicator unnecessarily
            kanji_data_service.clear_update_needed()

        _executor.submit(load)

    # --- update indicator ---
    setup_update_indicator(kanji_data_service)

    # --- HOOKS ---
    gui_hooks.collection_did_load.append(on_collection_loaded)

    # --- editor tracking ---
    gui_hooks.editor_did_init.append(_set_current_editor)

    # --- focused field tracking ---
    gui_hooks.editor_did_focus_field.append(_set_focused_field)

    def on_note_added(note: Note):
        editor = _get_live_add_cards_editor() or _get_current_editor()
        try:
            collection_service.update_single_note_kanji_knowledge(note)
            collection_service.ensure_rtk_kanji_for_note(note)
        except JapaneseMiningError as e:
            parent = editor.widget if editor and getattr(editor, "widget", None) else mw
            showWarning(
                e.full_message(),
                parent=parent,
                title="JapaneseMining",
            )

    def on_will_add_note(problem: str | None, note: Note):
        editor = _get_live_add_cards_editor() or _get_current_editor()
        if editor is None or getattr(editor, "web", None) is None:
            return
        try:
            hypertts_service.add_audio(problem, note, editor)
        except JapaneseMiningError as e:
            parent = editor.widget if editor and getattr(editor, "widget", None) else mw
            showWarning(
                e.full_message(),
                parent=parent,
                title="JapaneseMining",
            )

    gui_hooks.add_cards_did_add_note.append(on_note_added)
    gui_hooks.add_cards_will_add_note.append(on_will_add_note)

    gui_hooks.editor_did_init.append(inject_editor_css)

    set_translate_btn = make_translate_btn_setup(deepl_service, config_holder)
    gui_hooks.editor_did_init_buttons.append(set_translate_btn)

    segment_sentence = make_segment_sentence(config_holder, _get_focused_field_index)
    gui_hooks.editor_did_fire_typing_timer.append(segment_sentence)

    gui_hooks.reviewer_did_answer_card.append(kanji_data_service.handle_card_answered)

    # --- Setup menu actions ---
    show_settings = make_show_settings(
        config_holder, save_config, collection_service, deepl_service
    )

    setup_menu(
        config_holder,
        collection_service,
        kanji_data_service,
        show_settings,
    )
