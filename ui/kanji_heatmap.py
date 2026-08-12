from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextBrowser,
    QPushButton,
    QHBoxLayout,
    Qt,
)

KANJI_PER_ROW = 48

# Simple rainbow palette (HSL-ish). Feel free to tune.
RAINBOW = [
    "#e74c3c",  # red
    "#e67e22",  # orange
    "#f1c40f",  # yellow
    "#2ecc71",  # green
    "#1abc9c",  # teal
    "#3498db",  # blue
    "#9b59b6",  # purple
    "#e91e63",  # pink
    "#00bcd4",  # cyan
    "#ff5722",  # deep orange
    "#8bc34a",  # light green
]


def show_kanji_heatmap(kanji_data_service=None):
    """
    Show a simple kanji heat map.
    Prefer passing kanji_data_service; falls back to globals if None.
    """
    if kanji_data_service is None:
        return

    dialog = QDialog(mw)
    dialog.setWindowTitle("Kanji Heat Map")
    dialog.resize(720, 560)
    dialog.setMinimumSize(600, 400)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)

    learned, remaining, learned_count, total, keywords, knowledge = (
        kanji_data_service.get_heatmap_data()
    )

    # Header row with title + info icon
    header_row = QHBoxLayout()
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(6)

    header = QLabel(f"<b>{learned_count}</b> / <b>{total}</b> kanji learned")
    header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    header.setStyleSheet("font-size: 16px; margin-bottom: 4px;")

    info_icon = QLabel("ⓘ")
    info_icon.setStyleSheet("font-size: 14px; color: #888; padding: 0 2px;")
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

    layout.addLayout(header_row)

    # Heatmap
    browser = QTextBrowser()
    browser.setOpenLinks(False)
    browser.setStyleSheet(
        "QTextBrowser { background: #fafafa; border: 1px solid #ddd; }"
    )

    all_kanji = learned + remaining
    learned_set = set(learned)

    html = [
        "<style>",
        "body { font-family: 'Hiragino Sans', 'Noto Sans CJK JP', 'Yu Gothic', sans-serif; }",
        ".row { margin: 0 0 3px 0; line-height: 1.35; }",
        ".k { display: inline-block; width: 1.35em; text-align: center; "
        "     font-size: 15px; margin: 0 1px; cursor: default; }",
        ".learned { font-weight: 600; }",
        ".remaining { color: #b0b0b0; }",
        "</style>",
        "<div>",
    ]

    for i in range(0, len(all_kanji), KANJI_PER_ROW):
        chunk = all_kanji[i : i + KANJI_PER_ROW]
        html.append('<div class="row">')
        for j, k in enumerate(chunk):
            keyword = keywords.get(k, "").replace('"', "&quot;")

            if k in learned_set:
                r = knowledge.get(k, 0.0)
                color = knowledge_to_color(r)
                html.append(
                    f'<span class="k learned" style="color:{color}" title="{keyword}">{k}</span>'
                )
            else:
                html.append(f'<span class="k remaining" title="{keyword}">{k}</span>')
        html.append("</div>")

    html.append("</div>")
    browser.setHtml("".join(html))
    layout.addWidget(browser)

    # Close
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)

    dialog.exec()


def knowledge_to_color(r: float) -> str:
    """
    Map knowledge 0.0 → 1.0 to a smooth red → yellow → green → blue scale.
    """
    r = max(0.0, min(1.0, r))

    # Piecewise hue so the important perceptual points land nicely
    if r < 0.5:
        # red (0°) → yellow (60°)
        hue = r * 120  # 0 → 60
    elif r < 0.8:
        # yellow (60°) → green (120°)
        hue = 60 + (r - 0.5) * 200  # 60 → 120
    else:
        # green (120°) → blue (210°)
        hue = 120 + (r - 0.8) * 450  # 120 → 210

    return f"hsl({hue:.0f}, 78%, 42%)"
