# ui/kanji_heatmap.py
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton, Qt
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

    learned, remaining, learned_count, total, keywords = kanji_data_service.get_heatmap_data()

    # Header
    header = QLabel(f"<b>{learned_count}</b> / <b>{total}</b> kanji learned")
    header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    header.setStyleSheet("font-size: 16px; margin-bottom: 4px;")
    layout.addWidget(header)

    # Heatmap
    browser = QTextBrowser()
    browser.setOpenLinks(False)
    browser.setStyleSheet("QTextBrowser { background: #fafafa; border: 1px solid #ddd; }")

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
        chunk = all_kanji[i:i + KANJI_PER_ROW]
        html.append('<div class="row">')
        for j, k in enumerate(chunk):
            keyword = keywords.get(k, "").replace('"', "&quot;")

            if k in learned_set:
                row = i // KANJI_PER_ROW
                col = j
                color = RAINBOW[(row + col) % len(RAINBOW)]
                html.append(
                    f'<span class="k learned" style="color:{color}" title="{keyword}">{k}</span>'
                )
            else:
                html.append(
                    f'<span class="k remaining" title="{keyword}">{k}</span>'
                )
        html.append("</div>")

    html.append("</div>")
    browser.setHtml("".join(html))
    layout.addWidget(browser)

    # Close
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)

    dialog.exec()