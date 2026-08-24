from aqt.utils import tooltip, showInfo, showWarning
from aqt import mw
from anki.collection import OpChanges
from aqt.operations import CollectionOp
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
from ...domain.results import CreateAndImportResult
from ..ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    make_secondary_button,
    make_link_button,
    make_separator,
    make_callout,
    TEXT_BODY,
    TEXT_PRIMARY,
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
            "Map the deck and note type for Heisig (RTK) cards. Changes apply "
            "immediately to Setup &amp; Import (no <b>Save</b> needed). "
            "Kanji and Keyword required."
        )
    )
    mapping_root.addWidget(
        make_callout(
            "Mapped deck is the source of truth for learned kanji status. "
            "After switching decks, run <b>Export Learned Kanji</b>.",
            kind="info",
        )
    )

    if on_goto_rtk_help:
        learn_row = QHBoxLayout()
        learn_btn = make_link_button("Help → Remembering the Kanji →")
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
    rtk_deck_cb.setMaximumWidth(340)
    _set_combo_value(rtk_deck_cb, getattr(config, "rtk_deck", "") or "", _deck_names())
    form.addRow("Deck *", rtk_deck_cb)

    rtk_note_type_cb = QComboBox()
    rtk_note_type_cb.setMinimumWidth(340)
    rtk_note_type_cb.setMaximumWidth(340)
    _set_combo_value(
        rtk_note_type_cb,
        getattr(config, "rtk_note_type", "") or "",
        _note_type_names(),
    )
    form.addRow("Note type *", rtk_note_type_cb)

    rtk_kanji_field_cb = QComboBox()
    rtk_kanji_field_cb.setMinimumWidth(340)
    rtk_kanji_field_cb.setMaximumWidth(340)
    form.addRow("Kanji field *", rtk_kanji_field_cb)

    rtk_keyword_field_cb = QComboBox()
    rtk_keyword_field_cb.setMinimumWidth(340)
    rtk_keyword_field_cb.setMaximumWidth(340)
    form.addRow("Keyword field *", rtk_keyword_field_cb)

    rtk_alternative_kanji_field_cb = QComboBox()
    rtk_alternative_kanji_field_cb.setMinimumWidth(340)
    rtk_alternative_kanji_field_cb.setMaximumWidth(340)
    form.addRow("Alternative kanji field", rtk_alternative_kanji_field_cb)

    rtk_meanings_field_cb = QComboBox()
    rtk_meanings_field_cb.setMinimumWidth(340)
    rtk_meanings_field_cb.setMaximumWidth(340)
    form.addRow("Meanings field", rtk_meanings_field_cb)

    rtk_note_field_cb = QComboBox()
    rtk_note_field_cb.setMinimumWidth(340)
    rtk_note_field_cb.setMaximumWidth(340)
    form.addRow("Note field", rtk_note_field_cb)

    rtk_heisig_number_field_cb = QComboBox()
    rtk_heisig_number_field_cb.setMinimumWidth(340)
    rtk_heisig_number_field_cb.setMaximumWidth(340)
    form.addRow("Heisig number field", rtk_heisig_number_field_cb)

    rtk_stroke_count_field_cb = QComboBox()
    rtk_stroke_count_field_cb.setMinimumWidth(340)
    rtk_stroke_count_field_cb.setMaximumWidth(340)
    form.addRow("Stroke count field", rtk_stroke_count_field_cb)

    req_hint = QLabel("* Required for RTK features (keyword lookup, heatmap, imports).")
    req_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
    form.addRow("", req_hint)

    map_layout.addLayout(form)

    field_combos = [
        (rtk_kanji_field_cb, getattr(config, "rtk_kanji_field", "") or ""),
        (rtk_keyword_field_cb, getattr(config, "rtk_keyword_field", "") or ""),
        (
            rtk_alternative_kanji_field_cb,
            getattr(config, "rtk_alternative_kanji_field", "") or "",
        ),
        (
            rtk_heisig_number_field_cb,
            getattr(config, "rtk_heisig_number_field", "") or "",
        ),
        (
            rtk_stroke_count_field_cb,
            getattr(config, "rtk_stroke_count_field", "") or "",
        ),
        (
            rtk_meanings_field_cb,
            getattr(config, "rtk_meanings_field", "") or "",
        ),
        (
            rtk_note_field_cb,
            getattr(config, "rtk_note_field", "") or "",
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

    def load_mapping_from_config() -> None:
        """
        Re-read mapping from config_holder.config into the UI.
        Used after Backup restore with “set as active RTK deck”.
        """
        cfg = config_holder.config
        # Block signals so we don't push stale intermediate states
        widgets = (
            rtk_deck_cb,
            rtk_note_type_cb,
            rtk_kanji_field_cb,
            rtk_keyword_field_cb,
            rtk_alternative_kanji_field_cb,
            rtk_meanings_field_cb,
            rtk_note_field_cb,
            rtk_heisig_number_field_cb,
            rtk_stroke_count_field_cb,
        )
        for w in widgets:
            w.blockSignals(True)
        try:
            _set_combo_value(
                rtk_deck_cb, getattr(cfg, "rtk_deck", "") or "", _deck_names()
            )
            _set_combo_value(
                rtk_note_type_cb,
                getattr(cfg, "rtk_note_type", "") or "",
                _note_type_names(),
            )
            # Field lists depend on note type — rebuild from config values
            fields = _field_names(rtk_note_type_cb.currentText())
            for combo, attr in (
                (rtk_kanji_field_cb, "rtk_kanji_field"),
                (rtk_keyword_field_cb, "rtk_keyword_field"),
                (rtk_alternative_kanji_field_cb, "rtk_alternative_kanji_field"),
                (rtk_meanings_field_cb, "rtk_meanings_field"),
                (rtk_heisig_number_field_cb, "rtk_heisig_number_field"),
                (rtk_stroke_count_field_cb, "rtk_stroke_count_field"),
                (rtk_note_field_cb, "rtk_note_field"),
            ):
                _set_combo_value(
                    combo,
                    getattr(cfg, attr, "") or "",
                    fields,
                    preserve_missing=True,
                )
            # Keep Setup & Import fields in sync
            deck = rtk_deck_cb.currentText().strip()
            note_type = rtk_note_type_cb.currentText().strip()
            if deck:
                create_deck_edit.setText(deck)
            if note_type:
                create_note_type_edit.setText(note_type)
        finally:
            for w in widgets:
                w.blockSignals(False)

    mapping_root.addWidget(map_card)
    mapping_root.addStretch()
    tabs.addTab(mapping_page, "Deck Mapping")

    # Live push of mapping → in-memory config (no Save required for Setup/Import)
    def push_mapping_to_config() -> None:
        cfg = config_holder.config
        cfg.rtk_deck = rtk_deck_cb.currentText().strip()
        cfg.rtk_note_type = rtk_note_type_cb.currentText().strip()
        cfg.rtk_kanji_field = rtk_kanji_field_cb.currentText().strip()
        cfg.rtk_keyword_field = rtk_keyword_field_cb.currentText().strip()
        cfg.rtk_alternative_kanji_field = (
            rtk_alternative_kanji_field_cb.currentText().strip()
        )
        cfg.rtk_meanings_field = rtk_meanings_field_cb.currentText().strip()
        cfg.rtk_heisig_number_field = rtk_heisig_number_field_cb.currentText().strip()
        cfg.rtk_stroke_count_field = rtk_stroke_count_field_cb.currentText().strip()
        cfg.rtk_note_field = rtk_note_field_cb.currentText().strip()
    # ==================================================================
    # Tab 2 – Setup & Import
    # ==================================================================
    setup_page, setup_root = make_scrollable_page()

    setup_root.addWidget(
        make_instruction_label(
            "<b>Create</b> sets up deck + note type (never deletes notes or overwrites "
            "non-empty fields). <b>Import</b> fills the Heisig set and parks known kanji. "
            "Deck Mapping is the live source for both. "
            "Beginner: leave “create all notes” on. Already know some: uncheck, then Import."
        )
    )

    # ----- Create section -----
    create_card, create_layout = make_section_card("Create RTK Deck & Note Type")

    create_form = QFormLayout()
    create_form.setSpacing(8)
    create_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    create_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    _initial_deck = (
        getattr(config, "rtk_deck", "") or ""
    ).strip() or f"RTK_{random_suffix}"
    _initial_nt = (
        getattr(config, "rtk_note_type", "") or ""
    ).strip() or f"Remembering the Kanji_{random_suffix}"
    create_deck_edit = QLineEdit(_initial_deck)
    create_deck_edit.setMinimumWidth(300)
    create_form.addRow("Deck name", create_deck_edit)

    create_note_type_edit = QLineEdit(_initial_nt)
    create_note_type_edit.setMinimumWidth(300)
    create_form.addRow("Note type name", create_note_type_edit)

    create_layout.addLayout(create_form)

    create_all_notes_cb = QCheckBox(
        "Also create notes for all Heisig kanji (2200, 6th ed). Skips duplicates; fills empty fields."
    )
    create_all_notes_cb.setChecked(True)
    create_layout.addWidget(create_all_notes_cb)

    create_btn = make_primary_button("Create Deck & Note Type")
    create_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    # Keep Setup deck/note fields in sync with Deck Mapping (live, no Save)
    def sync_setup_from_mapping() -> None:
        deck = rtk_deck_cb.currentText().strip()
        note_type = rtk_note_type_cb.currentText().strip()
        if deck:
            create_deck_edit.setText(deck)
        if note_type:
            create_note_type_edit.setText(note_type)
        push_mapping_to_config()

    rtk_deck_cb.currentTextChanged.connect(lambda _t: sync_setup_from_mapping())
    rtk_note_type_cb.currentTextChanged.connect(lambda _t: sync_setup_from_mapping())
    for _cb in (
        rtk_kanji_field_cb,
        rtk_keyword_field_cb,
        rtk_alternative_kanji_field_cb,
        rtk_meanings_field_cb,
        rtk_note_field_cb,
        rtk_heisig_number_field_cb,
        rtk_stroke_count_field_cb,
    ):
        _cb.currentTextChanged.connect(lambda _t: push_mapping_to_config())

    def on_create_clicked() -> None:
        # Prefer explicit Setup fields; still push mapping fields (kanji/keyword/…)
        push_mapping_to_config()
        deck_name = create_deck_edit.text().strip()
        note_type_name = create_note_type_edit.text().strip()
        create_all = create_all_notes_cb.isChecked()

        if not deck_name or not note_type_name:
            raise JapaneseMiningError(
                "Please enter both a deck name and a note type name."
            )

        success, message = collection_service.create_rtk_deck_and_note_type(
            deck_name=deck_name,
            note_type_name=note_type_name,
            create_all_notes=create_all,
        )

        if not success:
            raise JapaneseMiningError(message)

        if save_config_fn:
            save_config_fn(collection_service._config)

        cfg = collection_service._config
        _set_combo_value(rtk_deck_cb, cfg.rtk_deck, _deck_names())
        _set_combo_value(rtk_note_type_cb, cfg.rtk_note_type, _note_type_names())
        refresh_rtk_fields(cfg.rtk_note_type, preserve_missing=True)
        # Reflect whatever mappings create_rtk_deck_and_note_type decided
        fields = _field_names(cfg.rtk_note_type)
        for combo, value in (
            (rtk_kanji_field_cb, cfg.rtk_kanji_field),
            (rtk_keyword_field_cb, cfg.rtk_keyword_field),
            (rtk_alternative_kanji_field_cb, cfg.rtk_alternative_kanji_field),
            (rtk_meanings_field_cb, cfg.rtk_meanings_field),
            (rtk_heisig_number_field_cb, cfg.rtk_heisig_number_field),
            (rtk_stroke_count_field_cb, cfg.rtk_stroke_count_field),
            (rtk_note_field_cb, cfg.rtk_note_field),
        ):
            if value:
                _set_combo_value(combo, value, fields, preserve_missing=True)

        tabs.setCurrentIndex(0)
        return CreateAndImportResult(kanji_imported=0, notes_created=0, message=message)

    create_btn.clicked.connect(lambda: _run_import_op(on_create_clicked, show_tooltip=True))
    setup_root.addWidget(create_card)

    # ----- Import section -----
    # Flow: short note → how to park cards → how to run import.
    # Everything left-aligned to match Deck Mapping and Create.
    import_card, import_layout = make_section_card("Import Known Kanji")

    import_layout.addWidget(
        make_callout(
            "Builds the full Heisig 6th-ed set if needed, marks the imported subset known, "
            "and fills empty Keyword / number / stroke fields. "
            "Existing cards are suspended or re-scheduled — field values are never overwritten. "
            "Skip Import if you must keep current scheduling for those cards.",
            kind="warning",
        )
    )

    # How known cards are parked (shared by both import actions)
    park_label = QLabel("How known cards are parked")
    park_label.setStyleSheet(
        f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY}; margin-top: 2px;"
    )
    import_layout.addWidget(park_label)

    fill_keywords_cb = QCheckBox("Fill missing keywords from Heisig data")
    fill_keywords_cb.setChecked(True)
    import_layout.addWidget(fill_keywords_cb)

    suspend_radio = QRadioButton("Suspend the cards")
    suspend_radio.setChecked(True)
    import_layout.addWidget(suspend_radio)

    schedule_radio = QRadioButton("Schedule as review cards with due dates between")
    import_layout.addWidget(schedule_radio)

    min_days_spin = QSpinBox()
    min_days_spin.setRange(1, 2200)
    min_days_spin.setValue(30)
    max_days_spin = QSpinBox()
    max_days_spin.setRange(1, 2200)
    max_days_spin.setValue(700)

    range_row = QHBoxLayout()
    range_row.setContentsMargins(22, 0, 0, 0)  # indent under the radio
    range_row.setSpacing(6)
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

    import_layout.addWidget(make_separator())

    # Import actions — form-style rows, left-aligned
    run_label = QLabel("Run import")
    run_label.setStyleSheet(
        f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};"
    )
    import_layout.addWidget(run_label)

    run_hint = QLabel("Both actions use the parking options above.")
    run_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    run_hint.setWordWrap(True)
    import_layout.addWidget(run_hint)

    # File import row
    file_row = QHBoxLayout()
    file_row.setSpacing(10)
    file_row_label = QLabel("From file")
    file_row_label.setMinimumWidth(100)
    file_row_label.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px;")
    file_btn = make_secondary_button("Choose file…")
    file_row.addWidget(file_row_label)
    file_row.addWidget(file_btn)
    file_row.addStretch()
    import_layout.addLayout(file_row)

    file_format_hint = QLabel(
        "Accepted formats: <b>.txt</b> — one kanji per line;<br>"
        "<b>.csv</b> — one kanji and keyword per row (kanji,keyword)."
    )
    file_format_hint.setWordWrap(True)
    file_format_hint.setTextFormat(Qt.TextFormat.RichText)
    file_format_hint.setStyleSheet(
        f"color: {TEXT_SECONDARY}; font-size: 12px; padding-left: 100px;"
    )
    import_layout.addWidget(file_format_hint)

    # Heisig number row

    # Heisig number row
    heisig_row = QHBoxLayout()
    heisig_row.setSpacing(10)
    heisig_row_label = QLabel("Heisig up to")
    heisig_row_label.setMinimumWidth(100)
    heisig_row_label.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px;")
    heisig_spin = QSpinBox()
    heisig_spin.setRange(1, 2200)
    heisig_spin.setValue(2200)
    heisig_spin.setMinimumWidth(90)
    heisig_apply_btn = make_secondary_button("Apply")
    heisig_row.addWidget(heisig_row_label)
    heisig_row.addWidget(heisig_spin)
    heisig_row.addWidget(heisig_apply_btn)
    heisig_row.addStretch()
    import_layout.addLayout(heisig_row)

    def _schedule_opts() -> dict:
        return {
            "fill_keywords": fill_keywords_cb.isChecked(),
            "suspend": suspend_radio.isChecked(),
            "schedule_min_days": min_days_spin.value(),
            "schedule_max_days": max_days_spin.value(),
        }

    def _run_import_op(op_callable, *, show_tooltip: bool = True) -> None:
        """op_callable() must not touch Qt widgets or dialogs."""
        def op(col):
            return op_callable()

        CollectionOp(parent=mw, op=op).success(
            lambda result: _on_success(result, show_tooltip)
        ).failure(lambda exc: _on_failure(exc)).run_in_background()

    def _on_success(result: CreateAndImportResult, show_tooltip: bool) -> None:
        if not show_tooltip or not result.message:
            return
        message = result.message
        tooltip(message, period=6000, parent=mw)

    def _on_failure(exc: Exception) -> None:
        if isinstance(exc, JapaneseMiningError):
            showWarning(exc.full_message(), parent=mw, title="JapaneseMining")
        else:
            showWarning(
                f"Unexpected error:\n\n{exc}", parent=mw, title="JapaneseMining"
            )

    def on_file_import_clicked() -> CreateAndImportResult:
        from aqt.qt import QFileDialog

        # Apply mapping live so Import uses the deck chosen on the Mapping tab
        push_mapping_to_config()
        path, _ = QFileDialog.getOpenFileName(
            outer,
            "Select kanji list",
            "",
            "Text / CSV (*.txt *.csv);;All files (*)",
        )
        if not path:
            return CreateAndImportResult()

        def op(col):
            marked, created = collection_service.import_known_kanji_from_file(
                path, **_schedule_opts()
            )
            return CreateAndImportResult(kanji_imported=marked, notes_created=created)

        CollectionOp(parent=mw, op=op).success(
            lambda result: _on_success(result, show_tooltip=True)
        ).failure(_on_failure).run_in_background()

    def on_heisig_import() -> CreateAndImportResult:
        push_mapping_to_config()
        marked, created = collection_service.import_known_kanji_up_to_heisig(
            heisig_spin.value(), **_schedule_opts()
        )
        return CreateAndImportResult(kanji_imported=marked, notes_created=created)

    file_btn.clicked.connect(on_file_import_clicked)
    heisig_apply_btn.clicked.connect(
        lambda: _run_import_op(on_heisig_import, show_tooltip=True)
    )

    setup_root.addWidget(import_card)
    setup_root.addStretch()
    tabs.addTab(setup_page, "Setup & Import")

    # When the user opens Setup & Import, re-sync from Mapping
    def on_tab_changed(index: int) -> None:
        if index == 1:  # Setup & Import
            sync_setup_from_mapping()

    tabs.currentChanged.connect(on_tab_changed)

    # ==================================================================
    # apply_to_config (persisted on Save)
    # ==================================================================
    def apply_to_config(cfg):
        cfg.rtk_deck = rtk_deck_cb.currentText().strip()
        cfg.rtk_note_type = rtk_note_type_cb.currentText().strip()
        cfg.rtk_kanji_field = rtk_kanji_field_cb.currentText().strip()
        cfg.rtk_alternative_kanji_field = (
            rtk_alternative_kanji_field_cb.currentText().strip()
        )
        cfg.rtk_keyword_field = rtk_keyword_field_cb.currentText().strip()
        cfg.rtk_meanings_field = rtk_meanings_field_cb.currentText().strip()
        cfg.rtk_note_field = rtk_note_field_cb.currentText().strip()
        cfg.rtk_heisig_number_field = rtk_heisig_number_field_cb.currentText().strip()
        cfg.rtk_stroke_count_field = rtk_stroke_count_field_cb.currentText().strip()

    outer.refresh_mapping_combos = refresh_mapping_combos
    outer.load_mapping_from_config = load_mapping_from_config
    outer.rtk_deck_cb = rtk_deck_cb
    outer.rtk_note_type_cb = rtk_note_type_cb
    outer.rtk_meanings_field_cb = rtk_meanings_field_cb
    outer.rtk_heisig_number_field_cb = rtk_heisig_number_field_cb
    outer.rtk_stroke_count_field_cb = rtk_stroke_count_field_cb
    outer.rtk_note_field_cb = rtk_note_field_cb
    return outer, "RTK", apply_to_config
