from logging import config

from aqt import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
    Qt,
)


def make_general_tab(config):
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
    mining_header = QLabel("JapaneseMining")
    mining_header.setStyleSheet("font-weight: 600; color: #555; margin-top: 12px;")
    general_layout.addRow(mining_header)

    mining_note_type_edit = QLineEdit(config.mining_note_type)
    mining_note_type_edit.setMinimumWidth(380)
    general_layout.addRow("Note type", mining_note_type_edit)

    # --- Section: RTK ---
    rtk_header = QLabel("Remembering the Kanji (Heisig)")
    rtk_header.setStyleSheet("font-weight: 600; color: #555; margin-top: 12px;")
    general_layout.addRow(rtk_header)

    rtk_deck_edit = QLineEdit(config.rtk_deck)
    rtk_deck_edit.setMinimumWidth(380)
    general_layout.addRow("Deck", rtk_deck_edit)

    rtk_note_type_edit = QLineEdit(config.rtk_note_type)
    rtk_note_type_edit.setMinimumWidth(380)
    general_layout.addRow("Note type", rtk_note_type_edit)

    rtk_kanji_field_edit = QLineEdit(config.rtk_kanji_field)
    rtk_kanji_field_edit.setMinimumWidth(380)
    general_layout.addRow("Kanji field", rtk_kanji_field_edit)

    rtk_alternative_kanji_field_edit = QLineEdit(config.rtk_alternative_kanji_field)
    rtk_alternative_kanji_field_edit.setMinimumWidth(380)
    general_layout.addRow("Alternative kanji field", rtk_alternative_kanji_field_edit)

    rtk_keyword_field_edit = QLineEdit(config.rtk_keyword_field)
    rtk_keyword_field_edit.setMinimumWidth(380)
    general_layout.addRow("Keyword field", rtk_keyword_field_edit)

    rtk_heisig_number_field_edit = QLineEdit(config.rtk_heisig_number_field)
    rtk_heisig_number_field_edit.setMinimumWidth(380)
    general_layout.addRow("Heisig number field", rtk_heisig_number_field_edit)

    rtk_stroke_count_field_edit = QLineEdit(config.rtk_stroke_count_field)
    rtk_stroke_count_field_edit.setMinimumWidth(380)
    general_layout.addRow("Stroke count field", rtk_stroke_count_field_edit)

    def apply_to_config(cfg):
        cfg.show_tooltip = show_tooltips_checkbox.isChecked()
        cfg.mining_note_type = mining_note_type_edit.text().strip() or cfg.mining_note_type

        cfg.rtk_deck = rtk_deck_edit.text().strip()
        cfg.rtk_note_type = rtk_note_type_edit.text().strip()
        cfg.rtk_kanji_field = rtk_kanji_field_edit.text().strip()
        cfg.rtk_alternative_kanji_field = rtk_alternative_kanji_field_edit.text().strip()
        cfg.rtk_keyword_field = rtk_keyword_field_edit.text().strip()
        cfg.rtk_heisig_number_field = rtk_heisig_number_field_edit.text().strip()
        cfg.rtk_stroke_count_field = rtk_stroke_count_field_edit.text().strip()

    return general_tab, "General", apply_to_config