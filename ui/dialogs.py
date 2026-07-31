from aqt import mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
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

        mining_note_type_edit = QLineEdit(config.mining_note_type)
        mining_note_type_edit.setMinimumWidth(420)

        rtk_deck_edit = QLineEdit(config.rtk_deck)
        rtk_deck_edit.setMinimumWidth(420)

        rtk_note_type_edit = QLineEdit(config.rtk_note_type)
        rtk_note_type_edit.setMinimumWidth(420)

        rtk_kanji_field_edit = QLineEdit(config.rtk_kanji_field)
        rtk_kanji_field_edit.setMinimumWidth(420)

        rtk_alternative_kanji_field_edit = QLineEdit(config.rtk_alternative_kanji_field)
        rtk_alternative_kanji_field_edit.setMinimumWidth(420)

        rtk_keyword_field_edit = QLineEdit(config.rtk_keyword_field)
        rtk_keyword_field_edit.setMinimumWidth(420)

        rtk_heisig_number_field_edit = QLineEdit(config.rtk_heisig_number_field)
        rtk_heisig_number_field_edit.setMinimumWidth(420)

        rtk_stroke_count_field_edit = QLineEdit(config.rtk_stroke_count_field)
        rtk_stroke_count_field_edit.setMinimumWidth(420)

        general_layout.addRow("JapaneseMining note type", mining_note_type_edit)
        general_layout.addRow("RTK deck", rtk_deck_edit)
        general_layout.addRow("RTK note type", rtk_note_type_edit)
        general_layout.addRow("RTK kanji field", rtk_kanji_field_edit)
        general_layout.addRow("RTK alternative kanji field", rtk_alternative_kanji_field_edit)
        general_layout.addRow("RTK keyword field", rtk_keyword_field_edit)
        general_layout.addRow("RTK Heisig number field", rtk_heisig_number_field_edit)
        general_layout.addRow("RTK stroke count field", rtk_stroke_count_field_edit)

        tabs.addTab(general_tab, "General")

        # -------------------
        # Translate tab
        # -------------------
        translate_tab = QWidget()
        translate_layout = QFormLayout(translate_tab)

        deepl_key_edit = QLineEdit(config.deepl_api_key)
        deepl_key_edit.setMinimumWidth(420)
        deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        deepl_url_edit = QLineEdit(config.deepl_url)
        deepl_url_edit.setMinimumWidth(420)

        translate_target_lang_combo = QComboBox()
        translate_target_lang_combo.addItems(["Ace","Af","Sq","Ar","An","Hy","As","Ay","Az","Ba","Eu","Be","Bn","Bho","Bs","Br","Bg","My","Yue","Ca","Ceb","Zh-Hans","Zh-Hant","Zh","Hr","Cs","Da","Prs","Nl","En","En-Us","En-Gb","Eo","Et","Fi","Fr","Fr-Ca","Fr-Fr","Gl","Ka","De","De-De","De-Ch","El","Gn","Gu","Ht","Ha","He","Hi","Hu","Is","Ig","Id","Ga","It","Ja","Jv","Pam","Kk","Gom","Ko","Kmr","Ckb","Ky","La","Lv","Ln","Lt","Lmo","Lb","Mk","Mai","Mg","Ms","Ml","Mt","Mi","Mr","Mn","Ne","Nb","Oc","Om","Pag","Ps","Fa","Pl","Pt-Br","Pt-Pt","Pt","Pa","Qu","Ro","Ru","Sa","Sr","St","Scn","Sk","Sl","Es","Es-419","Su","Sw","Sv","Tl","Tg","Ta","Tt","Te","Th","Ts","Tn","Tr","Tk","Uk","Ur","Uz","Vi","Cy","Wo","Xh","Yi","Zu"])
        translate_target_lang_combo.setCurrentText(config.deepl_target_lang)

        shortcut_edit = QKeySequenceEdit()
        shortcut_edit.setKeySequence(QKeySequence(config.deepl_shortcut))

        translate_layout.addRow("DeepL API key", deepl_key_edit)
        translate_layout.addRow("DeepL URL", deepl_url_edit)
        translate_layout.addRow("DeepL target language", translate_target_lang_combo)
        translate_layout.addRow("Translate shortcut", shortcut_edit)

        tabs.addTab(translate_tab, "Translate")

        # -------------------
        # Jisho tab
        # -------------------
        jisho_tab = QWidget()
        jisho_layout = QFormLayout(jisho_tab)

        jisho_use_checkbox = QCheckBox("Enable Jisho")
        jisho_use_checkbox.setChecked(config.use_jisho)

        jisho_layout.addRow(jisho_use_checkbox)
        tabs.addTab(jisho_tab, "Jisho")

        note = QLabel("Restart Anki to make this setting effective.")
        note.setStyleSheet("color: gray; font-size: 11px;")
        jisho_layout.addRow("", note)

        tabs.addTab(jisho_tab, "Jisho")

        # -------------------
        # HyperTTS tab
        # -------------------
        hypertts_tab = QWidget()
        hypertts_layout = QFormLayout(hypertts_tab)

        hypertts_use_checkbox = QCheckBox("Enable HyperTTS")
        hypertts_use_checkbox.setChecked(config.use_hypertts)

        hypertts_layout.addRow(hypertts_use_checkbox)
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
            seq = shortcut_edit.keySequence()
            config.mining_note_type = mining_note_type_edit.text().strip() or config.mining_note_type
            config.rtk_deck = rtk_deck_edit.text().strip()
            config.rtk_note_type = rtk_note_type_edit.text().strip()
            config.rtk_kanji_field = rtk_kanji_field_edit.text().strip()
            config.rtk_alternative_kanji_field = rtk_alternative_kanji_field_edit.text().strip()
            config.rtk_keyword_field = rtk_keyword_field_edit.text().strip()
            config.rtk_heisig_number_field = rtk_heisig_number_field_edit.text().strip()
            config.rtk_stroke_count_field = rtk_stroke_count_field_edit.text().strip()
            config.deepl_api_key = deepl_key_edit.text().strip()
            config.deepl_url = deepl_url_edit.text().strip() or config.deepl_url
            config.deepl_target_lang = translate_target_lang_combo.currentText()
            config.deepl_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText) if not seq.isEmpty() else config.deepl_shortcut
            config.use_hypertts = hypertts_use_checkbox.isChecked()
            config.use_jisho = jisho_use_checkbox.isChecked()
            # later: add other fields here

            save_config_fn(config)
            dialog.accept()

        buttons.accepted.connect(save_and_close)
        buttons.rejected.connect(dialog.reject)

        dialog.exec()
    return show_settings