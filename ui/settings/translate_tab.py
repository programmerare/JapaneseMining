from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFrame,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ...config import ConfigHolder
from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_separator,
    TEXT_SECONDARY,
)


def make_translate_tab(
    config_holder: ConfigHolder, deepl_service=None, save_config_fn=None
):
    config = config_holder.config

    res = deepl_service.get_character_usage() if deepl_service else None
    characters_count, characters_limit = res or (0, 0)

    root, root_layout = make_scrollable_page()

    root_layout.addWidget(
        make_instruction_label(
            "DeepL integration for translating example sentences. "
            "Requires a valid API key. Character usage is shown below."
        )
    )

    # Usage card
    usage_card, usage_layout = make_section_card("Usage")
    character_usage = QLabel(
        f"Character count: {characters_count}\n"
        f"Characters limit: {characters_limit}"
    )
    character_usage.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
    usage_layout.addWidget(character_usage)
    root_layout.addWidget(usage_card)

    # Settings card
    settings_card, settings_layout = make_section_card("DeepL settings")

    deepl_use_checkbox = QCheckBox("Enable DeepL")
    deepl_use_checkbox.setChecked(config.use_deepl)
    settings_layout.addWidget(deepl_use_checkbox)

    settings_layout.addWidget(make_separator())

    deepl_key_edit = QLineEdit(config.deepl_api_key)
    deepl_key_edit.setMinimumWidth(360)
    deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    settings_layout.addWidget(QLabel("API key"))
    settings_layout.addWidget(deepl_key_edit)

    deepl_url_edit = QLineEdit(config.deepl_url)
    deepl_url_edit.setMinimumWidth(360)
    settings_layout.addWidget(QLabel("URL"))
    settings_layout.addWidget(deepl_url_edit)

    translate_target_lang_combo = QComboBox()
    translate_target_lang_combo.addItems(
        [
            "Ace", "Af", "Sq", "Ar", "An", "Hy", "As", "Ay", "Az", "Ba", "Eu",
            "Be", "Bn", "Bho", "Bs", "Br", "Bg", "My", "Yue", "Ca", "Ceb",
            "Zh-Hans", "Zh-Hant", "Zh", "Hr", "Cs", "Da", "Prs", "Nl", "En",
            "En-Us", "En-Gb", "Eo", "Et", "Fi", "Fr", "Fr-Ca", "Fr-Fr", "Gl",
            "Ka", "De", "De-De", "De-Ch", "El", "Gn", "Gu", "Ht", "Ha", "He",
            "Hi", "Hu", "Is", "Ig", "Id", "Ga", "It", "Ja", "Jv", "Pam", "Kk",
            "Gom", "Ko", "Kmr", "Ckb", "Ky", "La", "Lv", "Ln", "Lt", "Lmo",
            "Lb", "Mk", "Mai", "Mg", "Ms", "Ml", "Mt", "Mi", "Mr", "Mn", "Ne",
            "Nb", "Oc", "Om", "Pag", "Ps", "Fa", "Pl", "Pt-Br", "Pt-Pt", "Pt",
            "Pa", "Qu", "Ro", "Ru", "Sa", "Sr", "St", "Scn", "Sk", "Sl", "Es",
            "Es-419", "Su", "Sw", "Sv", "Tl", "Tg", "Ta", "Tt", "Te", "Th",
            "Ts", "Tn", "Tr", "Tk", "Uk", "Ur", "Uz", "Vi", "Cy", "Wo", "Xh",
            "Yi", "Zu",
        ]
    )
    translate_target_lang_combo.setCurrentText(config.deepl_target_lang)
    settings_layout.addWidget(QLabel("Target language"))
    settings_layout.addWidget(translate_target_lang_combo)

    deepl_shortcut_edit = QKeySequenceEdit()
    deepl_shortcut_edit.setKeySequence(QKeySequence(config.deepl_shortcut))
    settings_layout.addWidget(QLabel("Shortcut"))
    settings_layout.addWidget(deepl_shortcut_edit)

    root_layout.addWidget(settings_card)
    root_layout.addStretch()

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

    return root, "Translate", apply_to_config
