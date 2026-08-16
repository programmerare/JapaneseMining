"""
Shared visual language for JapaneseMining UI.

This is the single source of truth for colors, spacing and component styles.
Keep it in sync with todays_words.py.
"""

from aqt.qt import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, Qt, QWidget, QScrollArea, QSizePolicy

# ── Palette ──────────────────────────────────────────────────────────────
BG_CARD = "#fafafa"
BORDER = "#e8e8e8"
SEPARATOR = "#ececec"
TEXT_PRIMARY = "#222"
TEXT_SECONDARY = "#666"
TEXT_BODY = "#444"
TEXT_MUTED = "#999"
ACCENT = "#1a73e8"
ACCENT_HOVER = "#1557b0"
ACCENT_PRESSED = "#0d47a1"
BADGE_BG = "#e8f0fe"
BADGE_TEXT = "#1a73e8"

# Callout palette (info / warning)
INFO_BG = "#e8f0fe"
INFO_BORDER = "#aecbfa"
INFO_TEXT = "#174ea6"
WARNING_BG = "#fef7e0"
WARNING_BORDER = "#fdd663"
WARNING_TEXT = "#7a5c00"

# ── Reusable stylesheets ────────────────────────────────────────────────
SECTION_CARD_SS = f"""
    QFrame#sectionCard {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}
"""

PRIMARY_BUTTON_SS = f"""
    QPushButton {{
        background: {ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: {ACCENT_HOVER};
    }}
    QPushButton:pressed {{
        background: {ACCENT_PRESSED};
    }}
    QPushButton:disabled {{
        background: #c5c5c5;
        color: #888;
    }}
"""

SECONDARY_BUTTON_SS = f"""
    QPushButton {{
        background: white;
        color: {ACCENT};
        border: 1px solid {ACCENT};
        border-radius: 6px;
        padding: 7px 14px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: {BADGE_BG};
    }}
    QPushButton:pressed {{
        background: #d2e3fc;
    }}
    QPushButton:disabled {{
        background: #f0f0f0;
        color: #9aa0a6;
        border: 1px solid #d0d0d0;
    }}
"""

LINK_BUTTON_SS = f"""
    QPushButton {{
        background: transparent;
        color: {ACCENT};
        border: none;
        font-weight: 600;
        font-size: 13px;
        text-align: left;
        padding: 4px 0;
    }}
    QPushButton:hover {{
        color: {ACCENT_HOVER};
        text-decoration: underline;
    }}
"""

INSTRUCTION_SS = f"""
    color: {TEXT_SECONDARY};
    font-size: 13px;
    line-height: 1.4;
    padding: 2px 0 4px 0;
"""

SECTION_TITLE_SS = f"""
    font-size: 14px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    letter-spacing: 0.2px;
"""


def make_section_card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Create a modern section card. Returns (card, content_layout)."""
    card = QFrame()
    card.setObjectName("sectionCard")
    card.setStyleSheet(SECTION_CARD_SS)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)

    if title:
        header = QLabel(title)
        header.setStyleSheet(SECTION_TITLE_SS)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {SEPARATOR};")
        layout.addWidget(sep)

    return card, layout


def make_instruction_label(text: str) -> QLabel:
    """Brief instruction shown at the top of every settings tab."""
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(INSTRUCTION_SS)
    return label


def make_callout(text: str, *, kind: str = "info") -> QFrame:
    """
    Modern inline callout for guidance or warnings.

    kind: "info" | "warning"
    """
    if kind == "warning":
        bg, border, color, prefix = WARNING_BG, WARNING_BORDER, WARNING_TEXT, "⚠ "
    else:
        bg, border, color, prefix = INFO_BG, INFO_BORDER, INFO_TEXT, "ℹ "

    frame = QFrame()
    frame.setObjectName("callout")
    frame.setStyleSheet(
        f"""
        QFrame#callout {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 8px;
        }}
        """
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(0)

    label = QLabel(prefix + text)
    label.setWordWrap(True)
    label.setStyleSheet(
        f"color: {color}; font-size: 12.5px; line-height: 1.45; background: transparent;"
    )
    layout.addWidget(label)
    return frame


def make_primary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(PRIMARY_BUTTON_SS)
    return btn


def make_secondary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(SECONDARY_BUTTON_SS)
    return btn


def make_compact_secondary_button(text: str) -> QPushButton:
    """Smaller secondary button for toolbars / inline actions (less visual weight)."""
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: white;
            color: {ACCENT};
            border: 1px solid {ACCENT};
            border-radius: 5px;
            padding: 4px 10px;
            font-weight: 600;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background: {BADGE_BG};
        }}
        QPushButton:pressed {{
            background: #d2e3fc;
        }}
        QPushButton:disabled {{
            background: #f0f0f0;
            color: #9aa0a6;
            border: 1px solid #d0d0d0;
        }}
    """)
    return btn


def make_link_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(LINK_BUTTON_SS)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def make_separator() -> QFrame:
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {SEPARATOR};")
    return sep


def make_image_placeholder(caption: str, min_height: int = 140) -> QFrame:
    """Skeleton placeholder for future screenshots."""
    frame = QFrame()
    frame.setMinimumHeight(min_height)
    frame.setStyleSheet(f"""
        QFrame {{
            background: #f0f4f8;
            border: 1px dashed #c5d0dc;
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    icon = QLabel("🖼")
    icon.setStyleSheet("font-size: 28px; color: #8aa;")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

    text = QLabel(caption)
    text.setStyleSheet("color: #7a8a9a; font-size: 12px; font-style: italic;")
    text.setAlignment(Qt.AlignmentFlag.AlignCenter)
    text.setWordWrap(True)

    layout.addWidget(icon)
    layout.addWidget(text)
    return frame


def make_scrollable_page() -> tuple[QWidget, QVBoxLayout]:
    """Returns (outer_widget, content_layout). Put all your cards into content_layout."""
    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    content = QWidget()
    content.setMinimumWidth(0)
    content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    content_layout = QVBoxLayout(content)
    # left/top/right = normal padding, bottom + small right gap for the scrollbar
    content_layout.setContentsMargins(16, 12, 10, 16)
    content_layout.setSpacing(14)

    scroll.setWidget(content)
    outer_layout.addWidget(scroll)
    return outer, content_layout