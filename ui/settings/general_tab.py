
from aqt import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)


def make_general_tab(config):
    show_tooltips_checkbox = QCheckBox("Show ToolTips")
    show_tooltips_checkbox.setChecked(config.show_tooltip)

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

    general_layout.addRow("", show_tooltips_checkbox)
    general_layout.addRow("JapaneseMining note type", mining_note_type_edit)
    general_layout.addRow("RTK deck", rtk_deck_edit)
    general_layout.addRow("RTK note type", rtk_note_type_edit)
    general_layout.addRow("RTK kanji field", rtk_kanji_field_edit)
    general_layout.addRow("RTK alternative kanji field", rtk_alternative_kanji_field_edit)
    general_layout.addRow("RTK keyword field", rtk_keyword_field_edit)
    general_layout.addRow("RTK Heisig number field", rtk_heisig_number_field_edit)
    general_layout.addRow("RTK stroke count field", rtk_stroke_count_field_edit)

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