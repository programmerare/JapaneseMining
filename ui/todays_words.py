from aqt import mw
from aqt import (
    QDialog,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)


def make_show_todays_words(kanji_data_service):
    def show_todays_words():
        """Show a dialog with the words learned today."""
        dialog = QDialog(mw)
        dialog.setWindowTitle("Words learned today")
        dialog.resize(760, 560)
        dialog.setMinimumSize(680, 480)

        layout = QVBoxLayout()

        text = QTextBrowser()

        words = kanji_data_service.get_todays_words()
        content = [
            "<style>"
            "body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; line-height: 1.5; }"
            ".entry { padding: 12px 0; border-bottom: 1px solid #ddd; }"
            ".top { display: flex; gap: 10px; align-items: baseline; font-size: 17px; font-weight: 600; }"
            ".reading { color: #666; font-weight: 500; }"
            ".meaning { margin-top: 2px; color: #222; }"
            "</style>",
        ]

        if words:
            for word, reading, meaning in words:
                content.append(
                    "<div class='entry'>"
                    f"<div class='top'><span class='word'>{word}</span><span class='reading'>{reading}</span></div>"
                    f"<div class='meaning'>{meaning}</div>"
                    "</div>"
                )
        else:
            content.append("<div class='entry'>No words learned today.</div>")

        text.setHtml("<html><body>" + "".join(content) + "</body></html>")

        layout.addWidget(text)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()

    return show_todays_words
