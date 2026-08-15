from aqt import mw
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
from ..ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_separator,
    TEXT_SECONDARY,
)

_FALLBACK_TARGET_LANGS = [
    ("en-US", "English (American)"),
    ("en-GB", "English (British)"),
    ("de", "German"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("ja", "Japanese"),
    ("zh", "Chinese (simplified)"),
]


def _fill_lang_combo(
    combo: QComboBox, items: list[tuple[str, str]], selected: str
) -> None:
    combo.blockSignals(True)
    combo.clear()
    for code, name in items:
        combo.addItem(f"{name} ({code})", code)  # userData = API code
    # Restore selection by code
    idx = combo.findData(selected)
    if idx < 0:
        idx = combo.findData(selected.upper()) if selected else -1
    if idx < 0 and combo.count():
        idx = 0
    if idx >= 0:
        combo.setCurrentIndex(idx)
    combo.blockSignals(False)


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
        f"Character count: {characters_count}\n" f"Characters limit: {characters_limit}"
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
    translate_target_lang_combo.setMinimumWidth(360)
    _fill_lang_combo(
        translate_target_lang_combo, _FALLBACK_TARGET_LANGS, config.deepl_target_lang
    )

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
        data = translate_target_lang_combo.currentData()
        cfg.deepl_target_lang = (
            data
            if isinstance(data, str) and data
            else translate_target_lang_combo.currentText()
        )
        cfg.deepl_shortcut = (
            seq.toString(QKeySequence.SequenceFormat.NativeText)
            if not seq.isEmpty()
            else cfg.deepl_shortcut
        )

    # --- async language load (does not block dialog open) ---
    if deepl_service is not None:
        selected = config.deepl_target_lang

        def work():
            return deepl_service.get_target_languages()

        def on_done(fut):
            try:
                langs = fut.result()
            except Exception:
                return
            if not langs:
                return

            def apply():
                _fill_lang_combo(translate_target_lang_combo, langs, selected)

            mw.taskman.run_on_main(apply)

        mw.taskman.run_in_background(work, on_done)

    return root, "Translate", apply_to_config
