from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    Qt,
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

    mining_note_type_cb = QComboBox()
    mining_note_type_cb.setMinimumWidth(380)
    _set_combo_value(
        mining_note_type_cb,
        getattr(config, "mining_note_type", "") or "",
        _note_type_names(),
    )

    # Info icon with recommendation
    mining_info = QLabel("ⓘ")
    mining_info.setStyleSheet("color: #666; font-size: 13px;")
    mining_info.setToolTip(
        "Recommended note type: JapaneseMining (shipped with this add-on).\n\n"
        "You may add fields freely, but do not delete existing fields — "
        "the add-on expects them.\n\n"
        "If you create a new note type (e.g. only to rename it), copy the "
        "fields from the JapaneseMining note type first."
    )
    mining_info.setCursor(Qt.CursorShape.WhatsThisCursor)

    mining_row = QHBoxLayout()
    mining_row.setContentsMargins(0, 0, 0, 0)
    mining_row.setSpacing(6)
    mining_row.addWidget(mining_note_type_cb, 1)
    mining_row.addWidget(mining_info)
    general_layout.addRow("Note type", mining_row)

    def apply_to_config(cfg):
        cfg.show_tooltip = show_tooltips_checkbox.isChecked()
        cfg.mining_note_type = mining_note_type_cb.currentText().strip() or cfg.mining_note_type

    return general_tab, "General", apply_to_config