from aqt import mw
from aqt.operations import CollectionOp
from aqt.utils import tooltip, showWarning
from aqt.qt import QAction, QMenu

from ..domain.errors import JapaneseMiningError
from ..domain.results import UpdateResult
from .kanji_heatmap import show_kanji_heatmap
from ..config import ConfigHolder


def setup_menu(
    config_holder: ConfigHolder,
    collection_service,
    kanji_data_service,
    show_todays_words,
    show_settings,
    show_difficult_kanji,
):
    """Set up the JapaneseMining menu in Anki's Tools menu."""
    show_tt = config_holder.config.show_tooltip

    my_menu = QMenu("JapaneseMining", mw)

    # Show Today's Progress
    action = QAction("Show Today's Progress", mw)
    action.triggered.connect(show_todays_words)
    my_menu.addAction(action)

    # Show Kanji Heat Map
    action = QAction("Show Kanji Heat Map", mw)
    action.triggered.connect(lambda: show_kanji_heatmap(kanji_data_service))
    my_menu.addAction(action)

    # Show Difficult Kanji
    action = QAction("Show Difficult Kanji", mw)
    action.triggered.connect(show_difficult_kanji)
    my_menu.addAction(action)

    my_menu.addSeparator()

    # Open Settings
    action = QAction("Settings", mw)
    action.setMenuRole(QAction.MenuRole.NoRole)
    action.triggered.connect(show_settings)
    my_menu.addAction(action)

    my_menu.addSeparator()

    # Soft Update Everything
    action = QAction("Soft Update Everything", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.soft_update_everything, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    # Force Update Keywords
    action = QAction("Force Update Keywords", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.force_update_keywords, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    # Force Update Meanings
    action = QAction("Force Update Meanings", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.force_update_meanings, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    # Force Update Everything
    action = QAction("Force Update Everything", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.force_update_everything, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    # Search for  and add unknown Kanji
    my_menu.addSeparator()
    action = QAction("Add Unknown Kanji", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.add_unknown_kanji, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    # Export Learned Kanji
    my_menu.addSeparator()
    action = QAction("Export Learned Kanji", mw)
    action.triggered.connect(
        lambda: _run_update_op(
            collection_service.export_learned_kanji, show_tooltip=show_tt
        )
    )
    my_menu.addAction(action)

    mw.form.menubar.addMenu(my_menu)


def _run_update_op(op_callable, *, show_tooltip: bool) -> None:
    """
    Run any CollectionService method that returns UpdateResult
    safely on a background thread.
    """

    def op(col):
        return op_callable()

    CollectionOp(parent=mw, op=op).success(
        lambda result: _on_success(result, show_tooltip)
    ).failure(lambda exc: _on_failure(exc)).run_in_background()


def _on_success(result: UpdateResult, show_tooltip: bool) -> None:
    if show_tooltip and result.message:
        tooltip(result.message, period=10000)


def _on_failure(exc: Exception) -> None:
    if isinstance(exc, JapaneseMiningError):
        showWarning(exc.full_message(), parent=mw, title="JapaneseMining")
    else:
        showWarning(f"Unexpected error:\n\n{exc}", parent=mw, title="JapaneseMining")
