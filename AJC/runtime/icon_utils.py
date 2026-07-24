# -*- coding: utf-8 -*-
"""Icon helpers for Anki Jisho Connect."""

from aqt.qt import QPainter, QPixmap, QFont, QColor, Qt, QIcon

from .logger import logger
from .paths import icon_path


_SVG_TEMPLATE = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
    "<rect width='24' height='24' rx='5' fill='#3ec97a'/>"
    "<text x='12' y='16' font-family='Segoe UI, Arial, sans-serif' "
    "font-size='13' fill='white' text-anchor='middle' font-weight='bold' "
    "letter-spacing='1'>JI</text>"
    "</svg>"
)


def _ensure_svg(svg_path):
    if svg_path.exists():
        return
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(_SVG_TEMPLATE, encoding="utf-8")


def _render_png(png_path) -> bool:
    try:
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3ec97a"))
        painter.drawRoundedRect(0, 0, size, size, 5, 5)

        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "JI")
        painter.end()

        return pixmap.save(str(png_path), "PNG")
    except Exception:
        logger.exception("Error rendering icon")
        return False


def get_icon_path() -> str:
    """Return PNG icon path if available, otherwise SVG."""
    svg_path = icon_path("jisho_icon.svg")
    png_path = icon_path("jisho_icon.png")

    _ensure_svg(svg_path)
    if not png_path.exists():
        png_path.parent.mkdir(parents=True, exist_ok=True)
        if not _render_png(png_path):
            return str(svg_path)

    return str(png_path if png_path.exists() else svg_path)


def get_profile_rename_icon(color: str) -> QIcon:
    """Return a small themed pencil icon for profile rename actions."""
    icon_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path fill="{color}" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/>
        <path fill="{color}" d="M20.71 7.04a.996.996 0 0 0 0-1.41l-2.34-2.34a.996.996 0 1 0-1.41 1.41l2.34 2.34c.39.39 1.02.39 1.41 0z"/>
    </svg>
    """
    pixmap = QPixmap()
    pixmap.loadFromData(icon_svg.encode("utf-8"))
    return QIcon(pixmap)
