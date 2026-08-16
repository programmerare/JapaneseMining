"""
Kanji window — Heat Map + Difficult Kanji in one tabbed dialog.

Uses the shared visual language from ui_styles.py.
"""

from aqt import mw
from aqt.operations import CollectionOp
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QTabWidget,
    QTextBrowser,
    QLineEdit,
    QFrame,
    Qt,
)
from aqt.utils import tooltip, showWarning

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
    ACCENT,
    BORDER,
    BG_CARD,
)

# Domain errors are optional at import time so the UI still loads if the
# package layout is slightly different during development.
try:
    from ..domain.errors import JapaneseMiningError
    from ..domain.results import UpdateResult
except ImportError:  # pragma: no cover
    JapaneseMiningError = None  # type: ignore
    UpdateResult = None  # type: ignore


# ── Shared helpers (Difficult Kanji) ─────────────────────────────────────

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
    """Kanji on top, keyword underneath. Fixed width → even spacing."""
    TILE_WIDTH = 72

    tile = QWidget()
    tile.setFixedWidth(TILE_WIDTH)
    if tooltip_text:
        tile.setToolTip(tooltip_text)

    layout = QVBoxLayout(tile)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)
    layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    glyph = QLabel(kanji)
    glyph.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {TEXT_PRIMARY};")
    glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(glyph)

    kw = QLabel(keyword or "—")
    kw.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
    kw.setAlignment(Qt.AlignmentFlag.AlignCenter)
    kw.setWordWrap(True)
    kw.setMaximumHeight(32)
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


# ── Heat Map tab ─────────────────────────────────────────────────────────

KANJI_PER_ROW = 48


def _knowledge_to_color(r: float) -> str:
    r = max(0.0, min(1.0, r))
    if r < 0.5:
        hue = r * 120
    elif r < 0.8:
        hue = 60 + (r - 0.5) * 200
    else:
        hue = 120 + (r - 0.8) * 450
    return f"hsl({hue:.0f}, 78%, 42%)"


def _run_collection_op(op_callable, *, show_tooltip: bool, parent) -> None:
    """Run a CollectionService method that returns UpdateResult on a background thread."""

    def op(col):
        return op_callable()

    def on_success(result):
        if not show_tooltip:
            return
        message = getattr(result, "message", None)
        if message:
            tooltip(message, period=6000, parent=parent)

    def on_failure(exc: Exception):
        if JapaneseMiningError is not None and isinstance(exc, JapaneseMiningError):
            showWarning(exc.full_message(), parent=parent, title="JapaneseMining")
        else:
            showWarning(
                f"Unexpected error:\n\n{exc}", parent=parent, title="JapaneseMining"
            )

    CollectionOp(parent=parent, op=op).success(on_success).failure(
        on_failure
    ).run_in_background()


def _build_heatmap_tab(
    kanji_data_service, collection_service, show_tooltip: bool
) -> QWidget:
    """Build the Heat Map tab content. Returns the root widget for the tab."""
    page, page_layout = make_scrollable_page()

    learned, remaining, learned_count, total, keywords, knowledge = (
        kanji_data_service.get_heatmap_data()
    )
    all_kanji = learned + remaining
    learned_set = set(learned)

    # Instruction
    page_layout.addWidget(
        make_instruction_label(
            "Colour shows how solid each kanji is in memory. "
            "Red = still weak → yellow/green = strengthening → blue = very solid. "
            "Unknown kanji stay grey. Hover a kanji to see its keyword."
        )
    )

    # Header card
    header_card, header_layout = make_section_card()
    header_row = QHBoxLayout()
    header_row.setSpacing(6)

    header = QLabel(f"<b>{learned_count}</b> / <b>{total}</b> kanji learned")
    header.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY};")

    info_icon = QLabel("ⓘ")
    info_icon.setStyleSheet(f"font-size: 14px; color: {TEXT_MUTED};")
    info_icon.setCursor(Qt.CursorShape.WhatsThisCursor)
    info_icon.setToolTip(
        "<b>How the colours are calculated</b><br><br>"
        "Each kanji gets a knowledge score from 0.0 to 1.0.<br><br>"
        "• <b>Main signal (75%)</b>: Stability (how many days the memory can last)<br>"
        "• <b>Small helper (25%)</b>: Retrievability (chance of recalling it right now)<br><br>"
        "The score is turned into a colour:<br>"
        "Red = still weak → Yellow/Green = getting stronger → Blue = very solid.<br><br>"
        "Unknown kanji stay grey. Strongest memories appear first."
    )

    header_row.addStretch()
    header_row.addWidget(header)
    header_row.addWidget(info_icon)
    header_row.addStretch()
    header_layout.addLayout(header_row)
    page_layout.addWidget(header_card)

    # Search
    search = QLineEdit()
    search.setPlaceholderText("Search by kanji or keyword…")
    search.setClearButtonEnabled(True)
    search.setStyleSheet(f"""
        QLineEdit {{
            padding: 8px 12px;
            border: 1px solid {BORDER};
            border-radius: 8px;
            font-size: 13px;
            background: #fff;
        }}
        QLineEdit:focus {{
            border-color: {ACCENT};
        }}
    """)
    page_layout.addWidget(search)

    # Heatmap browser inside a card-like frame
    browser_frame = QFrame()
    browser_frame.setObjectName("sectionCard")
    browser_frame.setStyleSheet(f"""
        QFrame#sectionCard {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}
    """)
    browser_layout = QVBoxLayout(browser_frame)
    browser_layout.setContentsMargins(8, 8, 8, 8)

    browser = QTextBrowser()
    browser.setOpenLinks(False)
    browser.setStyleSheet("""
        QTextBrowser {
            background: transparent;
            border: none;
        }
    """)
    browser_layout.addWidget(browser)
    page_layout.addWidget(browser_frame, stretch=1)

    # Actions that used to live in the Tools menu
    actions_card, actions_layout = make_section_card("Actions")
    actions_row = QHBoxLayout()
    actions_row.setSpacing(10)

    add_unknown_btn = make_secondary_button("Add Unknown Kanji")
    add_unknown_btn.setToolTip(
        "Find kanji that appear in your vocabulary but are not yet in the RTK deck, "
        "and add them."
    )
    add_unknown_btn.clicked.connect(
        lambda: _run_collection_op(
            collection_service.add_unknown_kanji,
            show_tooltip=show_tooltip,
            parent=mw,
        )
    )
    actions_row.addWidget(add_unknown_btn)

    export_btn = make_secondary_button("Export Learned Kanji")
    export_btn.setToolTip(
        "Export all RTK kanji, keywords and learned status to a CSV file."
    )
    export_btn.clicked.connect(
        lambda: _run_collection_op(
            collection_service.export_learned_kanji,
            show_tooltip=show_tooltip,
            parent=mw,
        )
    )
    actions_row.addWidget(export_btn)
    actions_row.addStretch()
    actions_layout.addLayout(actions_row)
    page_layout.addWidget(actions_card)

    def render(filter_text: str = ""):
        filter_text = filter_text.strip().lower()

        if filter_text:
            filtered = [
                k
                for k in all_kanji
                if filter_text in k or filter_text in keywords.get(k, "").lower()
            ]
        else:
            filtered = all_kanji

        html = [
            "<style>",
            "body { font-family: 'Hiragino Sans', 'Noto Sans CJK JP', 'Yu Gothic', "
            "'Segoe UI', sans-serif; margin: 4px; }",
            ".row { margin: 0 0 3px 0; line-height: 1.4; }",
            ".k { display: inline-block; width: 1.35em; text-align: center; "
            "     font-size: 15px; margin: 0 1px; cursor: default; }",
            ".learned { font-weight: 600; }",
            ".remaining { color: #b0b0b0; }",
            ".empty { color: #999; font-style: italic; padding: 24px 0; text-align: center; }",
            "</style>",
            "<div>",
        ]

        if not filtered:
            html.append('<div class="empty">No matching kanji.</div>')
        else:
            for i in range(0, len(filtered), KANJI_PER_ROW):
                chunk = filtered[i : i + KANJI_PER_ROW]
                html.append('<div class="row">')
                for k in chunk:
                    keyword = keywords.get(k, "").replace('"', "&quot;")
                    if k in learned_set:
                        color = _knowledge_to_color(knowledge.get(k, 0.0))
                        html.append(
                            f'<span class="k learned" style="color:{color}" '
                            f'title="{keyword}">{k}</span>'
                        )
                    else:
                        html.append(
                            f'<span class="k remaining" title="{keyword}">{k}</span>'
                        )
                html.append("</div>")

        html.append("</div>")
        browser.setHtml("".join(html))

    render()
    search.textChanged.connect(render)

    page_layout.addStretch()
    return page


# ── Difficult Kanji tab ──────────────────────────────────────────────────


def _populate_flagged_section(layout: QVBoxLayout, kanji_data_service) -> None:
    """Fill the flagged section. Safe to call repeatedly."""
    _clear_layout(layout)

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


def _build_difficult_tab(kanji_data_service) -> tuple[QWidget, callable]:
    """
    Build the Difficult Kanji tab.
    Returns (root_widget, refresh_callback).
    """
    page, page_layout = make_scrollable_page()

    page_layout.addWidget(
        make_instruction_label(
            "Kanji you mark with a red flag while reviewing RTK cards "
            "appear here automatically. Hover a kanji to see its Heisig number. "
            "Use Refresh after flagging or unflagging cards in the Browser."
        )
    )

    # Flagged by user
    flagged_card, flagged_outer = make_section_card("Your Flagged Kanji")
    flagged_content = QVBoxLayout()
    flagged_content.setContentsMargins(0, 0, 0, 0)
    flagged_content.setSpacing(8)
    flagged_outer.addLayout(flagged_content)

    _populate_flagged_section(flagged_content, kanji_data_service)
    page_layout.addWidget(flagged_card)

    # Commonly confused
    common_card, common_layout = make_section_card("Commonly Confused Kanji")
    for group in COMMON_CONFUSING:
        common_layout.addWidget(_group_label(group["label"]))
        tiles = [_kanji_tile(kanji, keyword) for kanji, keyword in group["items"]]
        for row_layout in _flow_row(tiles, max_per_row=8):
            common_layout.addLayout(row_layout)

    page_layout.addWidget(common_card)
    page_layout.addStretch()

    def on_refresh():
        count = kanji_data_service.sync_flagged_kanji_from_collection()
        _populate_flagged_section(flagged_content, kanji_data_service)
        return count

    return page, on_refresh


# ── Public factory ───────────────────────────────────────────────────────


def make_show_kanji(kanji_data_service, collection_service, show_tooltip: bool = True):
    """Return a callable that opens the combined Kanji dialog."""

    def show_kanji():
        if kanji_data_service is None:
            return

        dialog = QDialog(mw)
        dialog.setWindowTitle("Kanji")
        dialog.resize(760, 640)
        dialog.setMinimumSize(620, 500)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {TEXT_SECONDARY};
                padding: 8px 18px;
                margin-right: 2px;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                color: {ACCENT};
                border-bottom: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                color: {TEXT_PRIMARY};
            }}
        """)

        # Tab 1 — Heat Map
        heatmap_page = _build_heatmap_tab(
            kanji_data_service, collection_service, show_tooltip
        )
        tabs.addTab(heatmap_page, "Heat Map")

        # Tab 2 — Difficult Kanji
        difficult_page, refresh_fn = _build_difficult_tab(kanji_data_service)
        tabs.addTab(difficult_page, "Difficult Kanji")

        outer.addWidget(tabs, stretch=1)

        # Footer
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 12)
        footer_layout.setSpacing(10)

        def on_refresh():
            count = refresh_fn()
            tooltip(f"Synced {count} flagged kanji", parent=dialog)

        refresh_btn = make_secondary_button("Refresh from collection")
        refresh_btn.setToolTip(
            "Scan the RTK deck for red-flagged cards and update the Difficult list. "
            "Only available on the Difficult Kanji tab."
        )
        refresh_btn.clicked.connect(on_refresh)

        def on_tab_changed(index: int):
            # Disabled state is now clearly visible via SECONDARY_BUTTON_SS
            refresh_btn.setEnabled(index == 1)

        tabs.currentChanged.connect(on_tab_changed)
        refresh_btn.setEnabled(False)  # Heat Map is the default tab

        footer_layout.addWidget(refresh_btn)
        footer_layout.addStretch()

        close_btn = make_primary_button("Close")
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        outer.addWidget(footer)
        dialog.exec()

    return show_kanji
