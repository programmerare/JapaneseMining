from aqt.utils import tooltip, showInfo, showWarning
from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Qt,
    QButtonGroup,
)
import random
import string

from ...config import ConfigHolder
from ...domain.errors import JapaneseMiningError
from .ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    make_secondary_button,
    make_link_button,
    make_separator,
    TEXT_SECONDARY,
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


def _set_combo_value(
    combo: QComboBox,
    value: str,
    items: list[str],
    *,
    preserve_missing: bool = True,
) -> None:
    combo.blockSignals(True)
    combo.clear()
    combo.addItems(items)
    value = (value or "").strip()
    if value and combo.findText(value) < 0:
        if preserve_missing:
            combo.insertItem(0, value)
        else:
            value = ""
    idx = combo.findText(value)
    combo.setCurrentIndex(idx if idx >= 0 else -1)
    combo.blockSignals(False)


def make_rtk_tab(
    config_holder: ConfigHolder,
    collection_service,
    save_config_fn=None,
    on_goto_rtk_help=None,
):
    """Return (widget, title, apply_to_config).

    on_goto_rtk_help: optional callable that switches the main settings dialog
    to the Help → Remembering the Kanji sub-tab.
    """
    config = config_holder.config

    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(8, 8, 8, 8)
    outer_layout.setSpacing(6)

    tabs = QTabWidget()
    outer_layout.addWidget(tabs)

    # ==================================================================
    # Tab 1 – Deck Mapping
    # ==================================================================
    mapping_page, mapping_root = make_scrollable_page()

    mapping_root.addWidget(
        make_instruction_label(
            "Tell the add-on which deck and note type hold your Heisig (RTK) cards, "
            "and which fields contain kanji, keyword, Heisig number, etc."
        )
    )

    # Learn more link
    if on_goto_rtk_help:
        learn_row = QHBoxLayout()
        learn_btn = make_link_button("Learn about Remembering the Kanji →")
        learn_btn.clicked.connect(on_goto_rtk_help)
        learn_row.addWidget(learn_btn)
        learn_row.addStretch()
        mapping_root.addLayout(learn_row)

    map_card, map_layout = make_section_card("Deck & note type mapping")

    form = QFormLayout()
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    rtk_deck_cb = QComboBox()
    rtk_deck_cb.setMinimumWidth(340)
    _set_combo_value(rtk_deck_cb, getattr(config, "rtk_deck", "") or "", _deck_names())
    form.addRow("Deck", rtk_deck_cb)

    rtk_note_type_cb = QComboBox()
    rtk_note_type_cb.setMinimumWidth(340)
    _set_combo_value(
        rtk_note_type_cb,
        getattr(config, "rtk_note_type", "") or "",
        _note_type_names(),
    )
    form.addRow("Note type", rtk_note_type_cb)

    rtk_kanji_field_cb = QComboBox()
    rtk_kanji_field_cb.setMinimumWidth(340)
    form.addRow("Kanji field", rtk_kanji_field_cb)

    rtk_alternative_kanji_field_cb = QComboBox()
    rtk_alternative_kanji_field_cb.setMinimumWidth(340)
    form.addRow("Alternative kanji field", rtk_alternative_kanji_field_cb)

    rtk_keyword_field_cb = QComboBox()
    rtk_keyword_field_cb.setMinimumWidth(340)
    form.addRow("Keyword field", rtk_keyword_field_cb)

    rtk_heisig_number_field_cb = QComboBox()
    rtk_heisig_number_field_cb.setMinimumWidth(340)
    form.addRow("Heisig number field", rtk_heisig_number_field_cb)

    rtk_stroke_count_field_cb = QComboBox()
    rtk_stroke_count_field_cb.setMinimumWidth(340)
    form.addRow("Stroke count field", rtk_stroke_count_field_cb)

    map_layout.addLayout(form)

    field_combos = [
        (rtk_kanji_field_cb, getattr(config, "rtk_kanji_field", "") or ""),
        (
            rtk_alternative_kanji_field_cb,
            getattr(config, "rtk_alternative_kanji_field", "") or "",
        ),
        (rtk_keyword_field_cb, getattr(config, "rtk_keyword_field", "") or ""),
        (
            rtk_heisig_number_field_cb,
            getattr(config, "rtk_heisig_number_field", "") or "",
        ),
        (
            rtk_stroke_count_field_cb,
            getattr(config, "rtk_stroke_count_field", "") or "",
        ),
    ]

    def refresh_rtk_fields(
        note_type: str | None = None, *, preserve_missing: bool = False
    ) -> None:
        note_type = (
            note_type if note_type is not None else rtk_note_type_cb.currentText()
        )
        fields = _field_names(note_type)
        for combo, saved in field_combos:
            if preserve_missing:
                value = combo.currentText() if combo.count() else saved
                _set_combo_value(combo, value or saved, fields, preserve_missing=True)
            else:
                current = combo.currentText()
                value = current if current in fields else ""
                _set_combo_value(combo, value, fields, preserve_missing=False)

    def on_rtk_note_type_changed(_index: int = -1) -> None:
        refresh_rtk_fields(rtk_note_type_cb.currentText(), preserve_missing=False)

    rtk_note_type_cb.currentIndexChanged.connect(on_rtk_note_type_changed)
    refresh_rtk_fields(preserve_missing=True)

    def refresh_mapping_combos() -> None:
        _set_combo_value(rtk_deck_cb, rtk_deck_cb.currentText(), _deck_names())
        _set_combo_value(
            rtk_note_type_cb, rtk_note_type_cb.currentText(), _note_type_names()
        )
        refresh_rtk_fields(preserve_missing=True)

    mapping_root.addWidget(map_card)
    mapping_root.addStretch()
    tabs.addTab(mapping_page, "Deck Mapping")

    # ==================================================================
    # Tab 2 – Setup & Import
    # ==================================================================
    setup_page, setup_root = make_scrollable_page()

    setup_root.addWidget(
        make_instruction_label(
            "Create a ready-to-use RTK deck and note type, or import kanji you "
            "already know so the add-on can mark them and (optionally) schedule cards."
        )
    )

    # ----- Create section -----
    create_card, create_layout = make_section_card("Create RTK Deck & Note Type")

    create_form = QFormLayout()
    create_form.setSpacing(8)
    create_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    create_deck_edit = QLineEdit(
        getattr(config, "rtk_deck", "") or f"RTK_{random_suffix}"
    )
    create_deck_edit.setMinimumWidth(300)
    create_form.addRow("Deck name", create_deck_edit)

    create_note_type_edit = QLineEdit(
        getattr(config, "rtk_note_type", "") or f"Remembering the Kanji_{random_suffix}"
    )
    create_note_type_edit.setMinimumWidth(300)
    create_form.addRow("Note type name", create_note_type_edit)

    create_all_notes_cb = QCheckBox("Also create notes for all Heisig kanji (≈3039)")
    create_all_notes_cb.setChecked(True)
    create_form.addRow("", create_all_notes_cb)

    create_layout.addLayout(create_form)

    create_btn = make_primary_button("Create Deck & Note Type")
    create_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    def on_create_clicked() -> None:
        deck_name = create_deck_edit.text().strip()
        note_type_name = create_note_type_edit.text().strip()
        create_all = create_all_notes_cb.isChecked()

        if not deck_name or not note_type_name:
            tooltip("Please enter both a deck name and a note type name.")
            return

        try:
            success, message = collection_service.create_rtk_deck_and_note_type(
                deck_name=deck_name,
                note_type_name=note_type_name,
                create_all_notes=create_all,
            )

            if not success:
                showInfo(message)
                return

            if save_config_fn:
                save_config_fn(collection_service._config)

            _set_combo_value(rtk_deck_cb, deck_name, _deck_names())
            _set_combo_value(rtk_note_type_cb, note_type_name, _note_type_names())
            refresh_rtk_fields(note_type_name, preserve_missing=False)
            for combo, name in (
                (rtk_kanji_field_cb, "Kanji"),
                (rtk_alternative_kanji_field_cb, "Alternative Kanji"),
                (rtk_keyword_field_cb, "Keyword"),
                (rtk_heisig_number_field_cb, "Heisig Number"),
                (rtk_stroke_count_field_cb, "Stroke Count"),
            ):
                _set_combo_value(combo, name, _field_names(note_type_name))

            tooltip(message)
            tabs.setCurrentIndex(0)
        except JapaneseMiningError as e:
            showWarning(e.full_message(), parent=outer, title="JapaneseMining")

    create_btn.clicked.connect(on_create_clicked)
    setup_root.addWidget(create_card)

    # ----- Import section -----
    import_card, import_layout = make_section_card("Import Known Kanji")

    import_info = QLabel(
        "Import a list of known kanji from a file, or mark everything up to a "
        "given Heisig number. The learned_kanji cache is always updated. "
        "Card creation only happens when an RTK deck is already configured."
    )
    import_info.setWordWrap(True)
    import_info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    import_layout.addWidget(import_info)

    file_btn = make_secondary_button("Choose file…")
    import_layout.addWidget(file_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    heisig_row = QHBoxLayout()
    heisig_row.addWidget(QLabel("Heisig number up to:"))
    heisig_spin = QSpinBox()
    heisig_spin.setRange(1, 3100)
    heisig_spin.setValue(3039)
    heisig_row.addWidget(heisig_spin)
    heisig_apply_btn = make_secondary_button("Apply")
    heisig_row.addWidget(heisig_apply_btn)
    heisig_row.addStretch()
    import_layout.addLayout(heisig_row)

    import_layout.addWidget(make_separator())

    fill_keywords_cb = QCheckBox("Fill missing keywords from Heisig data")
    fill_keywords_cb.setChecked(True)
    import_layout.addWidget(fill_keywords_cb)

    sched_label = QLabel("When creating / updating RTK cards for known kanji:")
    sched_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    import_layout.addWidget(sched_label)

    suspend_radio = QRadioButton("Suspend the cards")
    suspend_radio.setChecked(True)
    import_layout.addWidget(suspend_radio)

    schedule_radio = QRadioButton("Schedule as review cards with due dates between")
    import_layout.addWidget(schedule_radio)

    range_row = QHBoxLayout()
    min_days_spin = QSpinBox()
    min_days_spin.setRange(1, 3650)
    min_days_spin.setValue(30)
    max_days_spin = QSpinBox()
    max_days_spin.setRange(1, 3650)
    max_days_spin.setValue(700)
    range_row.addWidget(min_days_spin)
    range_row.addWidget(QLabel("and"))
    range_row.addWidget(max_days_spin)
    range_row.addWidget(QLabel("days"))
    range_row.addStretch()
    import_layout.addLayout(range_row)

    sched_group = QButtonGroup(setup_page)
    sched_group.addButton(suspend_radio)
    sched_group.addButton(schedule_radio)

    def _update_range_enabled() -> None:
        enabled = schedule_radio.isChecked()
        min_days_spin.setEnabled(enabled)
        max_days_spin.setEnabled(enabled)

    schedule_radio.toggled.connect(_update_range_enabled)
    _update_range_enabled()

    def _schedule_opts() -> dict:
        return {
            "fill_keywords": fill_keywords_cb.isChecked(),
            "suspend": suspend_radio.isChecked(),
            "schedule_min_days": min_days_spin.value(),
            "schedule_max_days": max_days_spin.value(),
        }

    def on_file_import() -> None:
        from aqt.qt import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            outer,
            "Select kanji list",
            "",
            "Text / CSV (*.txt *.csv);;All files (*)",
        )
        if not path:
            return
        try:
            marked, touched = collection_service.import_known_kanji_from_file(
                path, **_schedule_opts()
            )
        except JapaneseMiningError as e:
            showWarning(e.full_message(), parent=outer, title="JapaneseMining")
            return
        tooltip(f"Marked {marked} kanji as known. Touched {touched} card(s).")

    def on_heisig_import() -> None:
        try:
            marked, touched = collection_service.import_known_kanji_up_to_heisig(
                heisig_spin.value(), **_schedule_opts()
            )
        except JapaneseMiningError as e:
            showWarning(e.full_message(), parent=outer, title="JapaneseMining")
            return
        tooltip(f"Marked {marked} kanji as known. Touched {touched} card(s).")

    file_btn.clicked.connect(on_file_import)
    heisig_apply_btn.clicked.connect(on_heisig_import)

    setup_root.addWidget(import_card)
    setup_root.addStretch()
    tabs.addTab(setup_page, "Setup & Import")

    # ==================================================================
    # apply_to_config
    # ==================================================================
    def apply_to_config(cfg):
        cfg.rtk_deck = rtk_deck_cb.currentText().strip()
        cfg.rtk_note_type = rtk_note_type_cb.currentText().strip()
        cfg.rtk_kanji_field = rtk_kanji_field_cb.currentText().strip()
        cfg.rtk_alternative_kanji_field = (
            rtk_alternative_kanji_field_cb.currentText().strip()
        )
        cfg.rtk_keyword_field = rtk_keyword_field_cb.currentText().strip()
        cfg.rtk_heisig_number_field = rtk_heisig_number_field_cb.currentText().strip()
        cfg.rtk_stroke_count_field = rtk_stroke_count_field_cb.currentText().strip()

    outer.refresh_mapping_combos = refresh_mapping_combos
    outer.rtk_deck_cb = rtk_deck_cb
    outer.rtk_note_type_cb = rtk_note_type_cb

    return outer, "RTK", apply_to_config
