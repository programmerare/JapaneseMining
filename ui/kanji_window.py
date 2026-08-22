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
    QFontMetrics,
    QSizePolicy,
    Qt,
)
from aqt.utils import tooltip, showWarning

from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    make_compact_secondary_button,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_BODY,
    ACCENT,
    BORDER,
    BG_CARD,
)

try:
    from ..domain.errors import JapaneseMiningError
    from ..domain.results import UpdateResult
except ImportError:  # pragma: no cover
    JapaneseMiningError = None  # type: ignore
    UpdateResult = None  # type: ignore


# ── Shared helpers (Difficult Kanji) ─────────────────────────────────────

COMMON_CONFUSING = [
    {
        "label": "Trees",
        "items": [
            ("桃", "peach tree"),
            ("桂", "Japanese Judas-tree"),
            ("桐", "paulownia tree"),
            ("柿", "persimmon tree"),
            ("松", "pine tree"),
            ("梓", "catalpa tree"),
            ("楠", "camphor tree"),
            ("桜", "cherry tree"),
        ],
    },
    {
        "label": "Threads",
        "items": [
            ("紡", "spinning"),
            ("繰", "winding"),
            ("網", "netting"),
            ("織", "weave"),
            ("絡", "entwine"),
        ],
    },
    {
        "label": "Direction of the short stroke",
        "items": [
            ("未", "not yet"),
            ("末", "end"),
        ],
    },
    {
        "label": "Husband vs lose vs dart",
        "items": [
            ("夫", "husband"),
            ("失", "lose"),
            ("矢", "dart"),
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
    {
        "label": "Chestnut vs horse chestnut",
        "items": [
            ("栗", "chestnut"),
            ("栃", "horse chestnut"),
        ],
    },
    {
        "label": "Drown vs drowning",
        "items": [
            ("溺", "drown"),
            ("没", "drowning"),
        ],
    },
]

# Tile width used by _kanji_tile — keep in sync for card width estimates
_TILE_WIDTH = 72
_TILE_GAP = 4
# Max tiles per row inside a group card (Trees/Threads wrap to a 2nd row)
_GROUP_MAX_PER_ROW = 10
# Available content width inside the Difficult tab scroll area (approx)
_FLOW_AVAILABLE_WIDTH = 680
_CARD_H_PAD = 24  # left+right padding inside a group card
_CARD_GAP = 10    # gap between group cards in a flow row


def _kanji_tile(kanji: str, keyword: str, tooltip_text: str = "") -> QWidget:
    """Kanji on top, keyword underneath (single line + ellipsis).

    Fixed width for even columns. Long keywords are truncated with "…";
    the full keyword (and Heisig number when provided) is always in the tooltip.
    """
    tile = QWidget()
    tile.setFixedWidth(_TILE_WIDTH)

    # Tooltip: keyword + optional Heisig / extra context
    tip_parts = [p for p in (keyword, tooltip_text) if p]
    if tip_parts:
        tile.setToolTip(" — ".join(tip_parts))

    layout = QVBoxLayout(tile)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)
    layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    glyph = QLabel(kanji)
    glyph.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {TEXT_PRIMARY};")
    glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(glyph)

    full_keyword = keyword or "—"
    kw = QLabel()
    kw.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
    kw.setAlignment(Qt.AlignmentFlag.AlignCenter)
    kw.setWordWrap(False)
    # Measure with an explicit font — stylesheet size is not always on
    # QWidget.font() before the widget is polished/shown.
    font = kw.font()
    font.setPixelSize(11)
    kw.setFont(font)
    metrics = QFontMetrics(font)
    kw.setText(
        metrics.elidedText(full_keyword, Qt.TextElideMode.ElideRight, _TILE_WIDTH - 8)
    )
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


def _flow_row(
    widgets: list[QWidget], max_per_row: int = 6, *, trailing_stretch: bool = True
) -> list[QHBoxLayout]:
    rows = []
    for i in range(0, len(widgets), max_per_row):
        row = QHBoxLayout()
        row.setSpacing(_TILE_GAP)
        for w in widgets[i : i + max_per_row]:
            row.addWidget(w)
        if trailing_stretch:
            row.addStretch()
        rows.append(row)
    return rows


def _estimate_group_card_width(n_items: int) -> int:
    """Estimate pixel width of a confusing-group card from its item count."""
    cols = min(n_items, _GROUP_MAX_PER_ROW)
    tiles_w = cols * _TILE_WIDTH + max(0, cols - 1) * _TILE_GAP
    return _CARD_H_PAD + tiles_w


def _confusing_group_card(group: dict) -> QFrame:
    """One compact card for a commonly-confused group (title + 1–2 tile rows)."""
    card = QFrame()
    card.setObjectName("confusingGroupCard")
    card.setStyleSheet(f"""
        QFrame#confusingGroupCard {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
    """)
    # Prefer natural size; flow layout will size-hint from this
    card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(6)

    title = QLabel(group["label"])
    title.setWordWrap(True)
    title.setStyleSheet(
        f"color: {TEXT_BODY}; font-size: 12px; font-weight: 600; padding: 0;"
    )
    layout.addWidget(title)

    tiles = [_kanji_tile(kanji, keyword) for kanji, keyword in group["items"]]
    for row_layout in _flow_row(
        tiles, max_per_row=_GROUP_MAX_PER_ROW, trailing_stretch=False
    ):
        layout.addLayout(row_layout)

    # Lock width so flow packing is stable
    card.setFixedWidth(_estimate_group_card_width(len(group["items"])))
    return card


def _flow_group_cards(cards: list[QWidget], available_width: int = _FLOW_AVAILABLE_WIDTH) -> QVBoxLayout:
    """Pack variable-width cards into horizontal rows that wrap when they no longer fit."""
    outer = QVBoxLayout()
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(_CARD_GAP)

    if not cards:
        return outer

    current_row = QHBoxLayout()
    current_row.setSpacing(_CARD_GAP)
    current_row.setContentsMargins(0, 0, 0, 0)
    used = 0

    for card in cards:
        w = card.width() if card.width() > 0 else card.sizeHint().width()
        # Start a new row if this card does not fit (and the row already has something)
        if used > 0 and used + _CARD_GAP + w > available_width:
            current_row.addStretch()
            outer.addLayout(current_row)
            current_row = QHBoxLayout()
            current_row.setSpacing(_CARD_GAP)
            current_row.setContentsMargins(0, 0, 0, 0)
            used = 0
        current_row.addWidget(card)
        used += w if used == 0 else (_CARD_GAP + w)

    current_row.addStretch()
    outer.addLayout(current_row)
    return outer


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


def _run_collection_op(op_callable, *, show_tooltip: bool, parent, on_success_extra=None) -> None:
    """Run a CollectionService method that returns UpdateResult on a background thread.

    on_success_extra: optional callable(result) run after the tooltip on success.
    Use this to refresh UI without closing the dialog.
    """

    def op(col):
        return op_callable()

    def on_success(result):
        if show_tooltip:
            message = getattr(result, "message", None)
            if message:
                tooltip(message, period=6000, parent=parent)
        if on_success_extra is not None:
            on_success_extra(result)

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


def _build_heatmap_tab(kanji_data_service, collection_service, config_holder) -> QWidget:
    """Build the Heat Map tab content. Returns the root widget for the tab.

    Data is held in a mutable state dict so Export / Add Unknown can refresh
    the heatmap in place without closing the dialog.
    """
    page, page_layout = make_scrollable_page()

    # Mutable snapshot — reloaded after collection ops that change learned status
    state = {
        "all_kanji": [],
        "learned_set": set(),
        "keywords": {},
        "knowledge": {},
        "learned_count": 0,
        "total": 0,
    }

    def load_state():
        learned, remaining, learned_count, total, keywords, knowledge = (
            kanji_data_service.get_heatmap_data()
        )
        state["all_kanji"] = learned + remaining
        state["learned_set"] = set(learned)
        state["keywords"] = keywords
        state["knowledge"] = knowledge
        state["learned_count"] = learned_count
        state["total"] = total

    load_state()

    # Instruction
    page_layout.addWidget(
        make_instruction_label(
            "Colour shows how solid each kanji is in memory. "
            "Red = still weak → yellow/green = strengthening → blue = very solid. "
            "Unknown kanji stay grey. Hover a kanji to see its keyword."
        )
    )

    # Header: count + compact action buttons (no heavy card — keeps heatmap tall)
    header_row = QHBoxLayout()
    header_row.setSpacing(8)
    header_row.setContentsMargins(0, 0, 0, 0)

    header = QLabel()
    header.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY};")

    def update_header():
        header.setText(
            f"<b>{state['learned_count']}</b> / <b>{state['total']}</b> kanji learned"
        )

    update_header()

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

    header_row.addWidget(header)
    header_row.addWidget(info_icon)
    header_row.addStretch()

    def _show_tooltip() -> bool:
        # Read live from config_holder so Settings toggles take effect immediately
        return bool(getattr(config_holder.config, "show_tooltip", True))

    # Search (created before buttons so refresh can keep the current filter)
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

    # Heatmap browser — gets the bulk of the vertical space
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

    def render(filter_text: str = ""):
        filter_text = filter_text.strip().lower()
        all_kanji = state["all_kanji"]
        keywords = state["keywords"]
        learned_set = state["learned_set"]
        knowledge = state["knowledge"]

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

    def refresh_heatmap(_result=None):
        """Re-read heatmap data and redraw. Safe to call from CollectionOp success."""
        load_state()
        update_header()
        render(search.text())

    add_unknown_btn = make_compact_secondary_button("Add Unknown Kanji")
    add_unknown_btn.setToolTip(
        "Find kanji that appear in your vocabulary but are not yet in the RTK deck, "
        "and add them."
    )
    add_unknown_btn.clicked.connect(
        lambda: _run_collection_op(
            collection_service.add_unknown_kanji,
            show_tooltip=_show_tooltip(),
            parent=mw,
            on_success_extra=refresh_heatmap,
        )
    )
    header_row.addWidget(add_unknown_btn)

    export_btn = make_compact_secondary_button("Export Learned Kanji")
    export_btn.setToolTip(
        "Export all RTK kanji, keywords and learned status to a CSV file."
    )
    export_btn.clicked.connect(
        lambda: _run_collection_op(
            collection_service.export_learned_kanji,
            show_tooltip=_show_tooltip(),
            parent=mw,
            on_success_extra=refresh_heatmap,
        )
    )
    header_row.addWidget(export_btn)

    page_layout.addLayout(header_row)
    page_layout.addWidget(search)
    page_layout.addWidget(browser_frame, stretch=1)

    render()
    search.textChanged.connect(render)

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


def _build_difficult_tab(kanji_data_service, *, auto_refresh: bool = True) -> QWidget:
    """Build the Difficult Kanji tab. Refresh lives at the top of this tab.

    When auto_refresh is True (default), sync flagged kanji from the collection
    once as the tab is built so the list is current on every open.
    """
    page, page_layout = make_scrollable_page()

    page_layout.addWidget(
        make_instruction_label(
            "Kanji you mark with a red flag while reviewing RTK cards "
            "appear here automatically. Hover a kanji to see its Heisig number. "
            "Use Refresh after flagging or unflagging cards in the Browser."
        )
    )

    # Compact toolbar with Refresh (only relevant on this tab)
    toolbar = QHBoxLayout()
    toolbar.setSpacing(8)
    toolbar.setContentsMargins(0, 0, 0, 0)
    toolbar.addStretch()

    # Flagged content layout is created early so the refresh callback can close over it
    flagged_card, flagged_outer = make_section_card("Your Flagged Kanji")
    flagged_content = QVBoxLayout()
    flagged_content.setContentsMargins(0, 0, 0, 0)
    flagged_content.setSpacing(8)
    flagged_outer.addLayout(flagged_content)

    def on_refresh(*, show_tooltip_msg: bool = True):
        count = kanji_data_service.sync_flagged_kanji_from_collection()
        _populate_flagged_section(flagged_content, kanji_data_service)
        if show_tooltip_msg:
            tooltip(f"Synced {count} flagged kanji", parent=mw)

    refresh_btn = make_compact_secondary_button("Refresh from collection")
    refresh_btn.setToolTip(
        "Scan the RTK deck for red-flagged cards and update this list"
    )
    refresh_btn.clicked.connect(lambda: on_refresh(show_tooltip_msg=True))
    toolbar.addWidget(refresh_btn)
    page_layout.addLayout(toolbar)

    if auto_refresh:
        # Silent sync on open — no tooltip spam every time the dialog appears
        on_refresh(show_tooltip_msg=False)
    else:
        _populate_flagged_section(flagged_content, kanji_data_service)

    page_layout.addWidget(flagged_card)

    # Commonly confused — each group is its own compact card; cards flow
    # side-by-side when they fit, otherwise wrap to the next row.
    section_header = QLabel("Commonly Confused Kanji")
    section_header.setStyleSheet(
        f"font-size: 14px; font-weight: 700; color: {TEXT_PRIMARY}; "
        f"letter-spacing: 0.2px; padding: 4px 0 0 0;"
    )
    page_layout.addWidget(section_header)

    group_cards = [_confusing_group_card(group) for group in COMMON_CONFUSING]
    page_layout.addLayout(_flow_group_cards(group_cards))

    page_layout.addStretch()
    return page


# ── Public factory ───────────────────────────────────────────────────────


def make_show_kanji(kanji_data_service, collection_service, config_holder):
    """Return a callable that opens the combined Kanji dialog.

    config_holder is required so show_tooltip is read live from Settings.
    """

    def show_kanji():
        if kanji_data_service is None:
            return

        dialog = QDialog(mw)
        dialog.setWindowTitle("Kanji")
        dialog.resize(760, 640)
        dialog.setMinimumSize(620, 500)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(12, 12, 12, 8)
        outer.setSpacing(10)

        # Standard Anki / Qt tabs — same as Settings dialog (no custom grey underline)
        tabs = QTabWidget()

        heatmap_page = _build_heatmap_tab(
            kanji_data_service, collection_service, config_holder
        )
        tabs.addTab(heatmap_page, "Heat Map")

        difficult_page = _build_difficult_tab(kanji_data_service, auto_refresh=True)
        tabs.addTab(difficult_page, "Difficult Kanji")

        outer.addWidget(tabs, stretch=1)

        # Footer: Close only
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = make_primary_button("Close")
        close_btn.clicked.connect(dialog.accept)
        footer.addWidget(close_btn)
        outer.addLayout(footer)

        dialog.exec()

    return show_kanji
