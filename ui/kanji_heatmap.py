from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QPushButton,
    QLineEdit,
    QFrame,
    Qt,
)

KANJI_PER_ROW = 48


def show_kanji_heatmap(kanji_data_service=None):
    if kanji_data_service is None:
        return

    dialog = QDialog(mw)
    dialog.setWindowTitle("Kanji Heat Map")
    dialog.resize(760, 620)
    dialog.setMinimumSize(640, 480)

    root = QVBoxLayout(dialog)
    root.setContentsMargins(20, 18, 20, 16)
    root.setSpacing(12)

    learned, remaining, learned_count, total, keywords, knowledge = (
        kanji_data_service.get_heatmap_data()
    )
    all_kanji = learned + remaining
    learned_set = set(learned)

    # ── Header ──────────────────────────────────────────────────────────
    header_row = QHBoxLayout()
    header_row.setSpacing(6)

    header = QLabel(f"<b>{learned_count}</b> / <b>{total}</b> kanji learned")
    header.setStyleSheet("font-size: 15px; font-weight: 600; color: #1a1a1a;")

    info_icon = QLabel("ⓘ")
    info_icon.setStyleSheet("font-size: 14px; color: #888;")
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
    root.addLayout(header_row)

    # ── Search bar ──────────────────────────────────────────────────────
    search = QLineEdit()
    search.setPlaceholderText("Search by kanji or keyword…")
    search.setClearButtonEnabled(True)
    search.setStyleSheet("""
        QLineEdit {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 13px;
            background: #fff;
        }
        QLineEdit:focus {
            border-color: #1a73e8;
        }
    """)
    root.addWidget(search)

    # ── Heatmap browser ─────────────────────────────────────────────────
    browser = QTextBrowser()
    browser.setOpenLinks(False)
    browser.setStyleSheet("""
        QTextBrowser {
            background: #fafafa;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            padding: 8px;
        }
    """)
    root.addWidget(browser)

    def knowledge_to_color(r: float) -> str:
        r = max(0.0, min(1.0, r))
        if r < 0.5:
            hue = r * 120
        elif r < 0.8:
            hue = 60 + (r - 0.5) * 200
        else:
            hue = 120 + (r - 0.8) * 450
        return f"hsl({hue:.0f}, 78%, 42%)"

    def render(filter_text: str = ""):
        filter_text = filter_text.strip().lower()

        if filter_text:
            filtered = []
            for k in all_kanji:
                kw = keywords.get(k, "").lower()
                if filter_text in k or filter_text in kw:
                    filtered.append(k)
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
                        color = knowledge_to_color(knowledge.get(k, 0.0))
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

    # Initial render + live filter
    render()
    search.textChanged.connect(render)

    # ── Close button (same style as Progress dialog) ────────────────────
    btn_row = QHBoxLayout()
    btn_row.addStretch()

    close_btn = QPushButton("Close")
    close_btn.setFixedWidth(110)
    close_btn.setStyleSheet("""
        QPushButton {
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 0;
            font-weight: 600;
            font-size: 13px;
        }
        QPushButton:hover {
            background: #1557b0;
        }
        QPushButton:pressed {
            background: #0d47a1;
        }
    """)
    close_btn.clicked.connect(dialog.accept)
    btn_row.addWidget(close_btn)
    root.addLayout(btn_row)

    dialog.exec()