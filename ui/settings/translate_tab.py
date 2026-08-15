from aqt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QWidget,
    Qt,
)

from ...config import ConfigHolder


def make_translate_tab(
    config_holder: ConfigHolder, deepl_service=None, save_config_fn=None
):
    config = config_holder.config

    res = deepl_service.get_character_usage() if deepl_service else None
    characters_count, characters_limit = res or (0, 0)

    translate_tab = QWidget()
    translate_layout = QFormLayout(translate_tab)
    translate_layout.setContentsMargins(16, 12, 16, 12)
    translate_layout.setSpacing(10)
    translate_layout.setFieldGrowthPolicy(
        QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
    )
    translate_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    # Section header
    header = QLabel("DeepL")
    header.setStyleSheet("font-weight: 600; color: #555; margin-top: 4px;")
    translate_layout.addRow(header)

    character_usage = QLabel(
        f"Character count: {characters_count}\n"
        f"Characters limit: {characters_limit}"
    )
    translate_layout.addRow(character_usage)

    deepl_use_checkbox = QCheckBox("Enable DeepL")
    deepl_use_checkbox.setChecked(config.use_deepl)
    translate_layout.addRow(deepl_use_checkbox)

    # Thin separator
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("color: #ddd;")
    translate_layout.addRow(sep)

    deepl_key_edit = QLineEdit(config.deepl_api_key)
    deepl_key_edit.setMinimumWidth(380)
    deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    translate_layout.addRow("API key", deepl_key_edit)

    deepl_url_edit = QLineEdit(config.deepl_url)
    deepl_url_edit.setMinimumWidth(380)
    translate_layout.addRow("URL", deepl_url_edit)

    translate_target_lang_combo = QComboBox()
    translate_target_lang_combo.addItems(
        [
            "Ace",
            "Af",
            "Sq",
            "Ar",
            "An",
            "Hy",
            "As",
            "Ay",
            "Az",
            "Ba",
            "Eu",
            "Be",
            "Bn",
            "Bho",
            "Bs",
            "Br",
            "Bg",
            "My",
            "Yue",
            "Ca",
            "Ceb",
            "Zh-Hans",
            "Zh-Hant",
            "Zh",
            "Hr",
            "Cs",
            "Da",
            "Prs",
            "Nl",
            "En",
            "En-Us",
            "En-Gb",
            "Eo",
            "Et",
            "Fi",
            "Fr",
            "Fr-Ca",
            "Fr-Fr",
            "Gl",
            "Ka",
            "De",
            "De-De",
            "De-Ch",
            "El",
            "Gn",
            "Gu",
            "Ht",
            "Ha",
            "He",
            "Hi",
            "Hu",
            "Is",
            "Ig",
            "Id",
            "Ga",
            "It",
            "Ja",
            "Jv",
            "Pam",
            "Kk",
            "Gom",
            "Ko",
            "Kmr",
            "Ckb",
            "Ky",
            "La",
            "Lv",
            "Ln",
            "Lt",
            "Lmo",
            "Lb",
            "Mk",
            "Mai",
            "Mg",
            "Ms",
            "Ml",
            "Mt",
            "Mi",
            "Mr",
            "Mn",
            "Ne",
            "Nb",
            "Oc",
            "Om",
            "Pag",
            "Ps",
            "Fa",
            "Pl",
            "Pt-Br",
            "Pt-Pt",
            "Pt",
            "Pa",
            "Qu",
            "Ro",
            "Ru",
            "Sa",
            "Sr",
            "St",
            "Scn",
            "Sk",
            "Sl",
            "Es",
            "Es-419",
            "Su",
            "Sw",
            "Sv",
            "Tl",
            "Tg",
            "Ta",
            "Tt",
            "Te",
            "Th",
            "Ts",
            "Tn",
            "Tr",
            "Tk",
            "Uk",
            "Ur",
            "Uz",
            "Vi",
            "Cy",
            "Wo",
            "Xh",
            "Yi",
            "Zu",
        ]
    )
    translate_target_lang_combo.setCurrentText(config.deepl_target_lang)
    translate_layout.addRow("Target language", translate_target_lang_combo)

    deepl_shortcut_edit = QKeySequenceEdit()
    deepl_shortcut_edit.setKeySequence(QKeySequence(config.deepl_shortcut))
    translate_layout.addRow("Shortcut", deepl_shortcut_edit)

    def apply_to_config(cfg):
        seq = deepl_shortcut_edit.keySequence()
        cfg.use_deepl = deepl_use_checkbox.isChecked()
        cfg.deepl_api_key = deepl_key_edit.text().strip()
        cfg.deepl_url = deepl_url_edit.text().strip() or cfg.deepl_url
        cfg.deepl_target_lang = translate_target_lang_combo.currentText()
        cfg.deepl_shortcut = (
            seq.toString(QKeySequence.SequenceFormat.NativeText)
            if not seq.isEmpty()
            else cfg.deepl_shortcut
        )

    return translate_tab, "Translate", apply_to_config
