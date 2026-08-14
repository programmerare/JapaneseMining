from aqt import mw
from aqt.qt import (
    QDialog,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)


def make_show_todays_words(kanji_data_service):
    def show_todays_words():
        dialog = QDialog(mw)
        dialog.setWindowTitle("Today's Progress")
        dialog.resize(780, 640)
        dialog.setMinimumSize(700, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # Summary header
        summary = kanji_data_service.get_todays_summary()
        header = QLabel(
            f"<b>{summary['words']}</b> words · "
            f"<b>{summary['kanji']}</b> kanji · "
            f"<b>{summary['known_cards']}</b> cards became known"
        )
        header.setStyleSheet("font-size: 14px; color: #333; margin-bottom: 4px;")
        layout.addWidget(header)

        text = QTextBrowser()
        text.setOpenExternalLinks(False)

        css = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                   font-size: 14px; line-height: 1.45; color: #222; }
            .section { margin-top: 18px; }
            .section:first-child { margin-top: 4px; }
            .section-title {
                font-size: 15px; font-weight: 700; color: #111;
                border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; margin-bottom: 8px;
            }
            .entry { padding: 8px 0; border-bottom: 1px solid #eee; }
            .top { display: flex; gap: 10px; align-items: baseline; font-size: 16px; font-weight: 600; }
            .reading { color: #666; font-weight: 500; font-size: 14px; }
            .meaning { margin-top: 2px; color: #333; }
            .kanji { font-size: 20px; font-weight: 600; margin-right: 8px; }
            .keyword { color: #555; font-size: 14px; }
            .empty { color: #888; font-style: italic; padding: 6px 0; }
        </style>
        """

        parts = [css]

        # --- Words ---
        parts.append(
            '<div class="section"><div class="section-title">Words learned today</div>'
        )
        words = kanji_data_service.get_todays_words()
        if words:
            for word, reading, meaning in words:
                parts.append(
                    f'<div class="entry">'
                    f'<div class="top"><span>{word}</span>'
                    f'<span class="reading">{reading}</span></div>'
                    f'<div class="meaning">{meaning}</div></div>'
                )
        else:
            parts.append('<div class="empty">No words learned today.</div>')
        parts.append("</div>")

        # --- Kanji ---
        parts.append(
            '<div class="section"><div class="section-title">Kanji learned today</div>'
        )
        kanji_list = kanji_data_service.get_todays_kanji()
        if kanji_list:
            for kanji, keyword in kanji_list:
                kw = f'<span class="keyword">{keyword}</span>' if keyword else ""
                parts.append(
                    f'<div class="entry">'
                    f'<span class="kanji">{kanji}</span>{kw}</div>'
                )
        else:
            parts.append('<div class="empty">No kanji learned today.</div>')
        parts.append("</div>")

        # --- Newly known cards ---
        parts.append(
            '<div class="section"><div class="section-title">Cards that became known today</div>'
        )
        known = kanji_data_service.get_todays_known_cards()
        if known:
            for word, reading, meaning in known:
                parts.append(
                    f'<div class="entry">'
                    f'<div class="top"><span>{word}</span>'
                    f'<span class="reading">{reading}</span></div>'
                    f'<div class="meaning">{meaning}</div></div>'
                )
        else:
            parts.append('<div class="empty">No cards became known today.</div>')
        parts.append("</div>")

        text.setHtml("<html><body>" + "".join(parts) + "</body></html>")
        layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    return show_todays_words
