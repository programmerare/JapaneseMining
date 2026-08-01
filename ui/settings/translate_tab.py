from aqt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QKeySequence,
    QKeySequenceEdit,
    QLineEdit,
    QWidget,
)


def make_translate_tab(config):
    translate_tab = QWidget()
    translate_layout = QFormLayout(translate_tab)

    deepl_use_checkbox = QCheckBox("Enable DeepL")
    deepl_use_checkbox.setChecked(config.use_deepl)

    deepl_key_edit = QLineEdit(config.deepl_api_key)
    deepl_key_edit.setMinimumWidth(420)
    deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    deepl_url_edit = QLineEdit(config.deepl_url)
    deepl_url_edit.setMinimumWidth(420)

    translate_target_lang_combo = QComboBox()
    translate_target_lang_combo.addItems(["Ace","Af","Sq","Ar","An","Hy","As","Ay","Az","Ba","Eu","Be","Bn","Bho","Bs","Br","Bg","My","Yue","Ca","Ceb","Zh-Hans","Zh-Hant","Zh","Hr","Cs","Da","Prs","Nl","En","En-Us","En-Gb","Eo","Et","Fi","Fr","Fr-Ca","Fr-Fr","Gl","Ka","De","De-De","De-Ch","El","Gn","Gu","Ht","Ha","He","Hi","Hu","Is","Ig","Id","Ga","It","Ja","Jv","Pam","Kk","Gom","Ko","Kmr","Ckb","Ky","La","Lv","Ln","Lt","Lmo","Lb","Mk","Mai","Mg","Ms","Ml","Mt","Mi","Mr","Mn","Ne","Nb","Oc","Om","Pag","Ps","Fa","Pl","Pt-Br","Pt-Pt","Pt","Pa","Qu","Ro","Ru","Sa","Sr","St","Scn","Sk","Sl","Es","Es-419","Su","Sw","Sv","Tl","Tg","Ta","Tt","Te","Th","Ts","Tn","Tr","Tk","Uk","Ur","Uz","Vi","Cy","Wo","Xh","Yi","Zu"])
    translate_target_lang_combo.setCurrentText(config.deepl_target_lang)

    deepl_shortcut_edit = QKeySequenceEdit()
    deepl_shortcut_edit.setKeySequence(QKeySequence(config.deepl_shortcut))

    translate_layout.addRow("", deepl_use_checkbox)
    translate_layout.addRow("DeepL API key", deepl_key_edit)
    translate_layout.addRow("DeepL URL", deepl_url_edit)
    translate_layout.addRow("DeepL target language", translate_target_lang_combo)
    translate_layout.addRow("Translate shortcut", deepl_shortcut_edit)

    def apply_to_config(cfg):
        seq = deepl_shortcut_edit.keySequence()
        cfg.use_deepl = deepl_use_checkbox.isChecked()
        cfg.deepl_api_key = deepl_key_edit.text().strip()
        cfg.deepl_url = deepl_url_edit.text().strip() or cfg.deepl_url
        cfg.deepl_target_lang = translate_target_lang_combo.currentText()
        cfg.deepl_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText) if not seq.isEmpty() else cfg.deepl_shortcut

    return translate_tab, "Translate", apply_to_config