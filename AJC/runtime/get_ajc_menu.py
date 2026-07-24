# -*- coding: utf-8 -*-
"""AJC menu helper."""

from aqt.qt import QMenu


def get_ajc_menu(mw):
    """Get or create AJC menu."""
    for attr in ["menuBar", "menubar"]:
        menubar = getattr(mw.form, attr, None)
        if menubar:
            for action in menubar.actions():
                menu = action.menu()
                if menu and menu.title().replace("&", "") == "AJC":
                    return menu
            ajc_menu = QMenu("&AJC", mw)
            menubar.addMenu(ajc_menu)
            return ajc_menu
    return None