# -*- coding: utf-8 -*-
"""Config dialog utilities: themed icons."""

import os
from aqt.qt import QIcon, QPixmap
from aqt.theme import theme_manager

from ..constants import LightTheme, DarkTheme


def get_theme():
    """Get current theme based on Anki settings."""
    return DarkTheme if theme_manager.night_mode else LightTheme


def get_themed_icon(icon_name: str, on_gradient: bool = False) -> QIcon:
    """Create themed QIcon from SVG string."""
    theme = get_theme()
    color = "#f7faff" if on_gradient else theme.TEXT_SECONDARY
    icon_svg = ""
    
    if icon_name == "arrow_up":
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/>
        </svg>
        """
    elif icon_name == "arrow_down":
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/>
        </svg>
        """
    elif icon_name == "remove":
        color = "#f7faff" if on_gradient else theme.DANGER_TEXT
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
        """

    if not icon_svg:
        return QIcon()

    pixmap = QPixmap()
    pixmap.loadFromData(icon_svg.encode("utf-8"))
    return QIcon(pixmap)
