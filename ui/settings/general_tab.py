from aqt import mw
from aqt.utils import tooltip, showInfo
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    Qt,
)

from ...config import ConfigHolder


def _note_type_names() -> list[str]:
    try:
        if not mw.col:
            return []
        return sorted(m.name for m in mw.col.models.all_names_and_ids())
    except Exception:
        return []


def _set_combo_value(combo: QComboBox, value: str, items: list[str]) -> None:
    """Populate combo with items and select value. Inserts value if missing so nothing is lost."""
    combo.blockSignals(True)
    combo.clear()
    combo.addItems(items)
    value = (value or "").strip()
    if value and combo.findText(value) < 0:
        combo.insertItem(0, value)
    idx = combo.findText(value)
    if idx >= 0:
        combo.setCurrentIndex(idx)
    combo.blockSignals(False)


def make_general_tab(config_holder: ConfigHolder, collection_service=None, save_config_fn=None):
    config = config_holder.config

    general_tab = QWidget()
    general_layout = QFormLayout(general_tab)
    general_layout.setContentsMargins(16, 12, 16, 12)
    general_layout.setSpacing(10)
    general_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    general_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    # --- Section: UI ---
    ui_header = QLabel("Interface")
    ui_header.setStyleSheet("font-weight: 600; color: #555; margin-top: 4px;")
    general_layout.addRow(ui_header)

    show_tooltips_checkbox = QCheckBox("Show tooltips")
    show_tooltips_checkbox.setChecked(config.show_tooltip)
    general_layout.addRow(show_tooltips_checkbox)

    # --- Section: JapaneseMining note ---
    mining_header = QLabel("JapaneseMining note type")
    mining_header.setStyleSheet("font-weight: 600; color: #555; margin-top: 12px;")
    general_layout.addRow(mining_header)

    # Short, always-visible guidance
    mining_help = QLabel(
        "This is the note type the add-on uses for mined vocabulary cards.\n"
        "• Select an existing note type from the list, or type a new name.\n"
        "• Click the button below to create it with all required fields.\n"
        "• You may add extra fields later; do not delete the ones the add-on expects."
    )
    mining_help.setWordWrap(True)
    mining_help.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 4px;")
    general_layout.addRow(mining_help)

    mining_note_type_cb = QComboBox()
    mining_note_type_cb.setMinimumWidth(380)
    mining_note_type_cb.setEditable(True)
    mining_note_type_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    _set_combo_value(
        mining_note_type_cb,
        getattr(config, "mining_note_type", "") or "",
        _note_type_names(),
    )

    # Info icon with recommendation
    mining_info = QLabel("ⓘ")
    mining_info.setStyleSheet("color: #666; font-size: 13px;")
    mining_info.setToolTip(
        "Required fields: Word, Reading, Meaning, Example Sentence, Translation, "
        "Note, Mnemonic, Audio, Other Forms, Tags, Part of Speech, Info, See Also, "
        "JLPT Level, Wanikani Level, Is Common, Kanji is known, No Kanji, Usually Kana, "
        "Kanji Keywords, Kanji Meanings.\n"
        "Extra fields are fine."
    )
    mining_info.setCursor(Qt.CursorShape.WhatsThisCursor)

    mining_row = QHBoxLayout()
    mining_row.setContentsMargins(0, 0, 0, 0)
    mining_row.setSpacing(6)
    mining_row.addWidget(mining_note_type_cb, 1)
    mining_row.addWidget(mining_info)
    general_layout.addRow("Note type", mining_row)

    # Create Note Type button
    create_btn = QPushButton("Create JapaneseMining note type")

    def on_create_mining_note_type():
        if collection_service is None:
            tooltip("Collection service not available.")
            return

        name = mining_note_type_cb.currentText().strip() or "JapaneseMining"
        ok, message = collection_service.create_mining_note_type(
            note_type_name=name,
            set_as_default=True,
        )

        if ok:
            # Refresh the combo so the new type appears and is selected
            _set_combo_value(mining_note_type_cb, name, _note_type_names())
            if save_config_fn is not None:
                save_config_fn(config_holder.config)
            tooltip(message)
        else:
            showInfo(message)

    create_btn.clicked.connect(on_create_mining_note_type)

    general_layout.addRow("", create_btn)

    def apply_to_config(cfg):
        cfg.show_tooltip = show_tooltips_checkbox.isChecked()
        cfg.mining_note_type = mining_note_type_cb.currentText().strip() or cfg.mining_note_type

    return general_tab, "General", apply_to_config