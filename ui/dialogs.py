from aqt import mw
from aqt.qt import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QTabWidget,
    QWidget,
)
import features


def make_show_today_words(kanji_data_service):
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

def make_show_settings(config, save_config_fn):
    def show_settings():
        """Show a dialog for configuring the JapaneseMining add-on."""
        dialog = QDialog(mw)
        dialog.setWindowTitle("JapaneseMining Settings")
        dialog.resize(720, 400)
        dialog.setMinimumWidth(640)

        main_layout = QVBoxLayout(dialog)

        tabs = QTabWidget()

        # -------------------
        # General tab
        # -------------------
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)

        note_type_edit = QLineEdit(config.mining_note_type)
        note_type_edit.setMinimumWidth(420)

        rtk_deck_edit = QLineEdit(config.rtk_deck)
        rtk_deck_edit.setMinimumWidth(420)

        deepl_key_edit = QLineEdit(config.deepl_api_key)
        deepl_key_edit.setMinimumWidth(420)
        deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        deepl_url_edit = QLineEdit(config.deepl_url)
        deepl_url_edit.setMinimumWidth(420)

        general_layout.addRow("JapaneseMining note type", note_type_edit)
        general_layout.addRow("RTK deck", rtk_deck_edit)
        general_layout.addRow("DeepL API key", deepl_key_edit)
        general_layout.addRow("DeepL URL", deepl_url_edit)

        tabs.addTab(general_tab, "General")

        # -------------------
        # Translate tab
        # -------------------
        translate_tab = QWidget()
        translate_layout = QFormLayout(translate_tab)

        # Add translate settings here later
        translate_layout.addRow("Example", QLineEdit())

        tabs.addTab(translate_tab, "Translate")

        # -------------------
        # Jisho tab
        # -------------------
        jisho_tab = QWidget()
        jisho_layout = QFormLayout(jisho_tab)

        # Add Jisho settings here later
        jisho_layout.addRow("Example", QLineEdit())

        tabs.addTab(jisho_tab, "Jisho")

        # -------------------
        # HyperTTS tab
        # -------------------
        hypertts_tab = QWidget()
        hypertts_layout = QFormLayout(hypertts_tab)

        # Add HyperTTS settings here later
        hypertts_layout.addRow("Example", QLineEdit())

        tabs.addTab(hypertts_tab, "HyperTTS")


        main_layout.addWidget(tabs)

        # -------------------
        # Buttons
        # -------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )

        main_layout.addWidget(buttons)

        def save_and_close():
            config = {
                "note_type": note_type_edit.text().strip() or config.mining_note_type,
                "rtk_deck": rtk_deck_edit.text().strip() or config.rtk_deck,
                "deepl_api_key": deepl_key_edit.text().strip(),
                "deepl_url": deepl_url_edit.text().strip() or config.deepl_url,
            }

            save_config_fn(config)
            dialog.accept()


        buttons.accepted.connect(save_and_close)
        buttons.rejected.connect(dialog.reject)

        dialog.exec()
    return show_settings