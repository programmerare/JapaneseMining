from aqt import mw
from aqt.utils import tooltip, showInfo
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    Qt,
)

from ...config import ConfigHolder
from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    TEXT_SECONDARY,
)


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


def make_general_tab(
    config_holder: ConfigHolder, collection_service=None, save_config_fn=None
):
    config = config_holder.config

    root, root_layout = make_scrollable_page()

    # Brief instructions
    root_layout.addWidget(
        make_instruction_label(
            "Global preferences and the JapaneseMining note type. "
            "Create the note type once; afterwards you can add extra fields but "
            "should not rename or delete the ones the add-on expects."
        )
    )

    # ── Interface card ──────────────────────────────────────────────────
    ui_card, ui_layout = make_section_card("Interface")
    show_tooltips_checkbox = QCheckBox("Show tooltips")
    show_tooltips_checkbox.setChecked(config.show_tooltip)
    ui_layout.addWidget(show_tooltips_checkbox)
    root_layout.addWidget(ui_card)

    # ── Note type card ──────────────────────────────────────────────────
    mining_card, mining_layout = make_section_card("JapaneseMining note type")

    help_text = QLabel(
        "This is the note type used for mined vocabulary cards.\n"
        "• Select an existing note type or type a new name.\n"
        "• Click the button below to create it with all required fields.\n"
        "• Extra fields are fine; do not delete or rename the expected ones."
    )
    help_text.setWordWrap(True)
    help_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    mining_layout.addWidget(help_text)

    mining_note_type_cb = QComboBox()
    mining_note_type_cb.setMinimumWidth(360)
    mining_note_type_cb.setEditable(True)
    mining_note_type_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    _set_combo_value(
        mining_note_type_cb,
        getattr(config, "mining_note_type", "") or "",
        _note_type_names(),
    )

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

    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    row.addWidget(QLabel("Note type"))
    row.addWidget(mining_note_type_cb, 1)
    row.addWidget(mining_info)
    mining_layout.addLayout(row)

    create_btn = make_primary_button("Create JapaneseMining note type")

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
            _set_combo_value(mining_note_type_cb, name, _note_type_names())
            if save_config_fn is not None:
                save_config_fn(config_holder.config)
            tooltip(message)
        else:
            showInfo(message)

    create_btn.clicked.connect(on_create_mining_note_type)
    mining_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    root_layout.addWidget(mining_card)
    root_layout.addStretch()

    def apply_to_config(cfg):
        cfg.show_tooltip = show_tooltips_checkbox.isChecked()
        cfg.mining_note_type = (
            mining_note_type_cb.currentText().strip() or cfg.mining_note_type
        )

    return root, "General", apply_to_config
