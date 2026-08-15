"""
Difficult Kanji window.

Shows:
  1. Kanji the user marked with a red flag while reviewing RTK cards.
  2. Curated groups of commonly confused kanji.
"""

from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    Qt,
)
from aqt.utils import tooltip

from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    make_secondary_button,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_BODY,
)


COMMON_CONFUSING = [
    {
        "label": "Direction of the short stroke",
        "items": [
            ("未", "not yet"),
            ("末", "end"),
        ],
    },
    {
        "label": "Gentleman vs soil",
        "items": [
            ("士", "gentleman"),
            ("土", "soil"),
        ],
    },
    {
        "label": "Dry vs thousand",
        "items": [
            ("干", "dry"),
            ("千", "thousand"),
        ],
    },
    {
        "label": "Eye vs day",
        "items": [
            ("目", "eye"),
            ("日", "day"),
        ],
    },
    {
        "label": "Person vs enter",
        "items": [
            ("人", "person"),
            ("入", "enter"),
        ],
    },
    {
        "label": "Large vs dog",
        "items": [
            ("大", "large"),
            ("犬", "dog"),
        ],
    },
]


def _kanji_tile(kanji: str, keyword: str, tooltip_text: str = "") -> QWidget:
    """Kanji on top, keyword underneath. No border."""
    tile = QWidget()
    if tooltip_text:
        tile.setToolTip(tooltip_text)

    layout = QVBoxLayout(tile)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(2)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    glyph = QLabel(kanji)
    glyph.setStyleSheet(
        f"font-size: 26px; font-weight: 600; color: {TEXT_PRIMARY};"
    )
    glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(glyph)

    kw = QLabel(keyword or "—")
    kw.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
    kw.setAlignment(Qt.AlignmentFlag.AlignCenter)
    kw.setWordWrap(True)
    layout.addWidget(kw)

    return tile


def _group_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {TEXT_BODY}; font-size: 12px; font-weight: 600; "
        f"padding: 2px 0 0 0;"
    )
    return lbl


def _empty_state(message: str) -> QLabel:
    lbl = QLabel(message)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {TEXT_MUTED}; font-size: 13px; font-style: italic; padding: 8px 0;"
    )
    return lbl


def _flow_row(widgets: list[QWidget], max_per_row: int = 6) -> list[QHBoxLayout]:
    rows = []
    for i in range(0, len(widgets), max_per_row):
        row = QHBoxLayout()
        row.setSpacing(4)
        for w in widgets[i : i + max_per_row]:
            row.addWidget(w)
        row.addStretch()
        rows.append(row)
    return rows


def _clear_layout(layout: QVBoxLayout) -> None:
    """Remove every widget/layout from a layout (keeps the layout itself)."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())
            item.layout().deleteLater()


def _populate_flagged_section(layout: QVBoxLayout, kanji_data_service) -> None:
    """Fill the flagged section. Safe to call repeatedly."""
    _clear_layout(layout)

    # Re-add the section title that make_section_card created? 
    # No – make_section_card already put the title + separator into the layout.
    # We only clear *content* that we added after the title.
    # Simpler approach: keep a dedicated content layout (see below).

    flagged = kanji_data_service.get_flagged_kanji()
    if not flagged:
        layout.addWidget(
            _empty_state(
                "No flagged kanji yet. While reviewing an RTK card, "
                "press Ctrl+1 (red flag), or flag cards in the Browser "
                "and press Refresh."
            )
        )
        return

    def sort_key(item):
        kanji, keyword, heisig = item
        try:
            return (0, int(heisig))
        except (TypeError, ValueError):
            return (1, kanji)

    tiles = [
        _kanji_tile(kanji, keyword, f"RTK #{heisig}" if heisig else "")
        for kanji, keyword, heisig in sorted(flagged, key=sort_key)
    ]
    for row_layout in _flow_row(tiles, max_per_row=8):
        layout.addLayout(row_layout)


def make_show_difficult_kanji(kanji_data_service):
    def show_difficult_kanji():
        dialog = QDialog(mw)
        dialog.setWindowTitle("Difficult Kanji")
        dialog.resize(720, 620)
        dialog.setMinimumSize(560, 480)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        page, page_layout = make_scrollable_page()

        page_layout.insertWidget(
            0,
            make_instruction_label(
                "Kanji you mark with a red flag while reviewing RTK cards "
                "appear here automatically. Hover a kanji to see its Heisig number. "
                "Use Refresh after flagging or unflagging cards in the Browser."
            ),
        )

        # ── Flagged by user ──────────────────────────────────────────────
        flagged_card, flagged_outer = make_section_card("Your Flagged Kanji")

        # Dedicated content layout so we can clear/rebuild without
        # touching the section title / separator that make_section_card added.
        flagged_content = QVBoxLayout()
        flagged_content.setContentsMargins(0, 0, 0, 0)
        flagged_content.setSpacing(8)
        flagged_outer.addLayout(flagged_content)

        _populate_flagged_section(flagged_content, kanji_data_service)
        page_layout.addWidget(flagged_card)

        # ── Commonly confused ────────────────────────────────────────────
        common_card, common_layout = make_section_card("Commonly Confused Kanji")

        for group in COMMON_CONFUSING:
            common_layout.addWidget(_group_label(group["label"]))
            tiles = [
                _kanji_tile(kanji, keyword)
                for kanji, keyword in group["items"]
            ]
            for row_layout in _flow_row(tiles, max_per_row=8):
                common_layout.addLayout(row_layout)

        page_layout.addWidget(common_card)
        page_layout.addStretch()

        outer.addWidget(page, stretch=1)

        # ── Footer ───────────────────────────────────────────────────────
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 12)
        footer_layout.setSpacing(10)

        def on_refresh():
            count = kanji_data_service.sync_flagged_kanji_from_collection()
            _populate_flagged_section(flagged_content, kanji_data_service)
            tooltip(f"Synced {count} flagged kanji", parent=dialog)

        refresh_btn = make_secondary_button("Refresh from collection")
        refresh_btn.setToolTip(
            "Scan the RTK deck for red-flagged cards and update this list"
        )
        refresh_btn.clicked.connect(on_refresh)
        footer_layout.addWidget(refresh_btn)

        footer_layout.addStretch()

        close_btn = make_primary_button("Close")
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        outer.addWidget(footer)
        dialog.exec()

    return show_difficult_kanji