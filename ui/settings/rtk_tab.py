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


def _deck_names() -> list[str]:
    try:
        if not mw.col:
            return []
        return sorted(d.name for d in mw.col.decks.all_names_and_ids())
    except Exception:
        return []


def _field_names(note_type: str) -> list[str]:
    if not note_type or not mw.col:
        return []
    try:
        model = mw.col.models.by_name(note_type)
        if model:
            return [f["name"] for f in model["flds"]]
    except Exception:
        pass
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


def make_rtk_tab(config):
    rtk_tab = QWidget()
    rtk_layout = QFormLayout(rtk_tab)
    rtk_layout.setContentsMargins(16, 12, 16, 12)
    rtk_layout.setSpacing(10)
    rtk_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    rtk_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    # --- Section: RTK ---
    rtk_header = QLabel("Remembering the Kanji (Heisig)")
    rtk_header.setStyleSheet("font-weight: 600; color: #555; margin-top: 12px;")
    rtk_layout.addRow(rtk_header)

    rtk_deck_cb = QComboBox()
    rtk_deck_cb.setMinimumWidth(380)
    _set_combo_value(
        rtk_deck_cb,
        getattr(config, "rtk_deck", "") or "",
        _deck_names(),
    )
    rtk_layout.addRow("Deck", rtk_deck_cb)

    rtk_note_type_cb = QComboBox()
    rtk_note_type_cb.setMinimumWidth(380)
    _set_combo_value(
        rtk_note_type_cb,
        getattr(config, "rtk_note_type", "") or "",
        _note_type_names(),
    )
    rtk_layout.addRow("Note type", rtk_note_type_cb)

    # Field combos — populated from the selected RTK note type
    rtk_kanji_field_cb = QComboBox()
    rtk_kanji_field_cb.setMinimumWidth(380)
    rtk_layout.addRow("Kanji field", rtk_kanji_field_cb)

    rtk_alternative_kanji_field_cb = QComboBox()
    rtk_alternative_kanji_field_cb.setMinimumWidth(380)
    rtk_layout.addRow("Alternative kanji field", rtk_alternative_kanji_field_cb)

    rtk_keyword_field_cb = QComboBox()
    rtk_keyword_field_cb.setMinimumWidth(380)
    rtk_layout.addRow("Keyword field", rtk_keyword_field_cb)

    rtk_heisig_number_field_cb = QComboBox()
    rtk_heisig_number_field_cb.setMinimumWidth(380)
    rtk_layout.addRow("Heisig number field", rtk_heisig_number_field_cb)

    rtk_stroke_count_field_cb = QComboBox()
    rtk_stroke_count_field_cb.setMinimumWidth(380)
    rtk_layout.addRow("Stroke count field", rtk_stroke_count_field_cb)

    field_combos = [
        (rtk_kanji_field_cb, getattr(config, "rtk_kanji_field", "") or ""),
        (rtk_alternative_kanji_field_cb, getattr(config, "rtk_alternative_kanji_field", "") or ""),
        (rtk_keyword_field_cb, getattr(config, "rtk_keyword_field", "") or ""),
        (rtk_heisig_number_field_cb, getattr(config, "rtk_heisig_number_field", "") or ""),
        (rtk_stroke_count_field_cb, getattr(config, "rtk_stroke_count_field", "") or ""),
    ]

    def refresh_rtk_fields(note_type: str | None = None) -> None:
        note_type = note_type if note_type is not None else rtk_note_type_cb.currentText()
        fields = _field_names(note_type)
        for combo, saved in field_combos:
            # Prefer currently selected text if the user already picked something
            current = combo.currentText() if combo.count() else saved
            _set_combo_value(combo, current or saved, fields)

    def on_rtk_note_type_changed(_index: int = -1) -> None:
        refresh_rtk_fields(rtk_note_type_cb.currentText())

    rtk_note_type_cb.currentIndexChanged.connect(on_rtk_note_type_changed)
    refresh_rtk_fields()  # initial population from config

    def apply_to_config(cfg):
        cfg.rtk_deck = rtk_deck_cb.currentText().strip()
        cfg.rtk_note_type = rtk_note_type_cb.currentText().strip()
        cfg.rtk_kanji_field = rtk_kanji_field_cb.currentText().strip()
        cfg.rtk_alternative_kanji_field = rtk_alternative_kanji_field_cb.currentText().strip()
        cfg.rtk_keyword_field = rtk_keyword_field_cb.currentText().strip()
        cfg.rtk_heisig_number_field = rtk_heisig_number_field_cb.currentText().strip()
        cfg.rtk_stroke_count_field = rtk_stroke_count_field_cb.currentText().strip()

    return rtk_tab, "RTK", apply_to_config