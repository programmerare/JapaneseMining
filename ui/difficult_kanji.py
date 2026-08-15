"""
Difficult Kanji window.

Shows:
  1. Kanji the user marked with a red flag while reviewing RTK cards.
  2. A curated list of commonly confused kanji.
"""

from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QWidget,
    Qt,
)

from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    BORDER,
)


# Curated list – expand over time.
# (kanji, keyword, note)
COMMON_CONFUSING = [
    ("未", "not yet", "Often confused with 末 (end)"),
    ("末", "end", "Often confused with 未 (not yet)"),
    ("土", "soil", "Often confused with 士 (gentleman)"),
    ("士", "gentleman", "Often confused with 土 (soil)"),
    ("干", "dry", "Often confused with 千"),
    ("千", "thousand", "Often confused with 干"),
    ("目", "eye", "Often confused with 日 (day)"),
    ("日", "day", "Often confused with 目 (eye)"),
    ("人", "person", "Often confused with 入 (enter)"),
    ("入", "enter", "Often confused with 人 (person)"),
    ("大", "large", "Often confused with 犬 (dog)"),
    ("犬", "dog", "Often confused with 大 (large)"),
]


def _kanji_row(kanji: str, keyword: str, extra: str = "") -> QFrame:
    """One row: large kanji + keyword (+ optional extra line)."""
    row = QFrame()
    row.setStyleSheet(
        f"""
        QFrame {{
            background: white;
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
        """
    )
    layout = QHBoxLayout(row)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(14)

    glyph = QLabel(kanji)
    glyph.setStyleSheet(
        f"font-size: 28px; font-weight: 600; color: {TEXT_PRIMARY}; min-width: 40px;"
    )
    glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(glyph)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)

    kw = QLabel(keyword or "—")
    kw.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {TEXT_PRIMARY};")
    text_col.addWidget(kw)

    if extra:
        extra_lbl = QLabel(extra)
        extra_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
        extra_lbl.setWordWrap(True)
        text_col.addWidget(extra_lbl)

    layout.addLayout(text_col, stretch=1)
    return row


def _empty_state(message: str) -> QLabel:
    lbl = QLabel(message)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {TEXT_MUTED}; font-size: 13px; font-style: italic; padding: 8px 0;"
    )
    return lbl


def make_show_difficult_kanji(kanji_data_service):
    def show_difficult_kanji():
        dialog = QDialog(mw)
        dialog.setWindowTitle("Difficult Kanji")
        dialog.resize(520, 640)
        dialog.setMinimumSize(420, 480)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable page from ui_styles
        page, page_layout = make_scrollable_page()

        page_layout.insertWidget(
            0,
            make_instruction_label(
                "Kanji you mark with a red flag while reviewing RTK cards "
                "appear here automatically. Below is a small curated list of "
                "pairs that are easy to mix up."
            ),
        )

        # ── Flagged by user ──────────────────────────────────────────────
        flagged_card, flagged_layout = make_section_card("Your Flagged Kanji")

        flagged = kanji_data_service.get_flagged_kanji()
        if flagged:
            def sort_key(item):
                kanji, keyword, heisig = item
                try:
                    return (0, int(heisig))
                except (TypeError, ValueError):
                    return (1, kanji)

            for kanji, keyword, heisig in sorted(flagged, key=sort_key):
                extra = f"RTK #{heisig}" if heisig else ""
                flagged_layout.addWidget(_kanji_row(kanji, keyword, extra))
        else:
            flagged_layout.addWidget(
                _empty_state(
                    "No flagged kanji yet. While reviewing an RTK card, "
                    "press Ctrl+1 (red flag) on kanji you find difficult."
                )
            )

        page_layout.addWidget(flagged_card)

        # ── Curated list ─────────────────────────────────────────────────
        common_card, common_layout = make_section_card("Commonly Confused Kanji")
        for kanji, keyword, note in COMMON_CONFUSING:
            common_layout.addWidget(_kanji_row(kanji, keyword, note))

        page_layout.addWidget(common_card)
        page_layout.addStretch()

        outer.addWidget(page, stretch=1)

        # Footer (outside the scroll area)
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 12)
        footer_layout.addStretch()
        close_btn = make_primary_button("Close")
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        outer.addWidget(footer)

        dialog.exec()

    return show_difficult_kanji