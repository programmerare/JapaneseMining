from aqt import mw
from aqt.qt import QAction, QMenu

from .kanji_heatmap import show_kanji_heatmap
from ..config import ConfigHolder


def setup_menu(
    config_holder: ConfigHolder,
    collection_service,
    kanji_data_service,
    show_todays_words,
    show_settings,
):
    """Set up the JapaneseMining menu in Anki's Tools menu."""
    my_menu = QMenu("JapaneseMining", mw)

    action = QAction("Show Today's Words", mw)
    action.triggered.connect(show_todays_words)
    my_menu.addAction(action)

    action = QAction("Show Kanji Heat Map", mw)
    action.triggered.connect(lambda: show_kanji_heatmap(kanji_data_service))
    my_menu.addAction(action)

    my_menu.addSeparator()

    action = QAction("Settings", mw)
    action.setMenuRole(QAction.MenuRole.NoRole)
    action.triggered.connect(show_settings)
    my_menu.addAction(action)

    my_menu.addSeparator()

    action = QAction("Soft Update Everything", mw)
    action.triggered.connect(collection_service.update_japanese_mining_cards)
    my_menu.addAction(action)

    action = QAction("Force Update Keywords", mw)
    action.triggered.connect(collection_service.force_update_keywords)
    my_menu.addAction(action)

    action = QAction("Force Update Meanings", mw)
    action.triggered.connect(collection_service.force_update_meanings)
    my_menu.addAction(action)

    action = QAction("Force Update Everything", mw)
    action.triggered.connect(collection_service.force_update_everything)
    my_menu.addAction(action)

    my_menu.addSeparator()
    action = QAction("Add Unknown Kanji", mw)
    action.triggered.connect(collection_service.add_unknown_kanji)
    my_menu.addAction(action)

    my_menu.addSeparator()
    action = QAction("Export Learned Kanji", mw)
    action.triggered.connect(collection_service.export_learned_kanji)
    my_menu.addAction(action)

    mw.form.menubar.addMenu(my_menu)
