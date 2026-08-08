# -*- coding: utf-8 -*-
"""Menu and first-run actions for Anki Jisho Connect."""

from __future__ import annotations

from aqt import mw
from aqt.qt import QAction

from ..get_ajc_menu import get_ajc_menu
from ..jisho_client import load_config, save_config
from ..ui.config_dialog import ConfigDialog
from ..ui.info_dialogs import show_about_ajc_dialog, show_welcome_dialog
from . import state


def ensure_about_ajc_action(menu) -> None:
    if not menu:
        return
    existing = None
    for action in list(menu.actions()):
        text = (action.text() or "").strip().lower()
        if action.objectName() == "ajc.menu.about" or text in {"about ajc", "sobre o ajc"}:
            if existing is None:
                existing = action
            else:
                menu.removeAction(action)
    if existing is not None:
        try:
            existing.setText("About AJC")
            existing.setObjectName("ajc.menu.about")
        except Exception:
            pass
        return

    action = QAction("About AJC", mw)
    action.setObjectName("ajc.menu.about")
    action.triggered.connect(show_about_ajc_dialog)
    menu.addAction(action)


def show_welcome_if_needed() -> None:
    if not mw:
        return
    config = load_config()
    if not config.get("show_welcome_dialog", True):
        return
    config["show_welcome_dialog"] = False
    save_config(config)
    mw.progress.single_shot(800, show_welcome_dialog, requires_collection=False)


def setup_menu_action() -> None:
    ajc_menu = get_ajc_menu(mw)
    menu = ajc_menu or mw.form.menuTools

    ensure_about_ajc_action(menu)

    for action in list(menu.actions()):
        try:
            obj = action.objectName()
            if obj == "ajc.anki_jisho.settings":
                action.setText("Anki Jisho Connect Settings")
                action.setObjectName("ajc.anki_jisho.settings")
                return
        except Exception:
            pass

    action = QAction(mw)
    action.setText("Anki Jisho Connect Settings")
    action.setObjectName("ajc.anki_jisho.settings")

    def show_config():
        if state.config_dialog is not None:
            try:
                if not state.config_dialog.isVisible():
                    state.config_dialog.show()
                state.config_dialog.raise_()
                state.config_dialog.activateWindow()
                return
            except Exception:
                state.config_dialog = None
        state.config_dialog = ConfigDialog()
        state.config_dialog.show()
        state.config_dialog.raise_()
        state.config_dialog.activateWindow()

    action.triggered.connect(show_config)
    menu.addAction(action)