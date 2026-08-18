from aqt import mw
from aqt.utils import tooltip, showInfo
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    Qt,
)

from ...config import ConfigHolder, REQUIRED_MINING_FIELDS
from ..ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_primary_button,
    TEXT_SECONDARY,
    TEXT_PRIMARY,
    ACCENT,
    BADGE_BG,
    BORDER,
)


def _note_type_names() -> list[str]:
    try:
        if not mw.col:
            return []
        return sorted(m.name for m in mw.col.models.all_names_and_ids())
    except Exception:
        return []


def _fields_of(note_type: str) -> set[str]:
    try:
        model = mw.col.models.by_name(note_type) if mw.col and note_type else None
        if model:
            return {f["name"] for f in model["flds"]}
    except Exception:
        pass
    return set()


def _mining_note_types() -> list[str]:
    """Note types that currently contain every required mining field."""
    result = []
    for name in _note_type_names():
        fields = _fields_of(name)
        if fields and all(f in fields for f in REQUIRED_MINING_FIELDS):
            result.append(name)
    return result


def _set_combo_value(combo: QComboBox, value: str, items: list[str]) -> None:
    """Populate combo with items and select value. Inserts value if missing."""
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


def _make_status_card() -> tuple[QFrame, QLabel, QLabel, QLabel]:
    """
    Modern status card under the note-type combo.
    Returns (frame, title_label, detail_label, missing_label).
    """
    frame = QFrame()
    frame.setObjectName("statusCard")
    frame.setStyleSheet(f"""
        QFrame#statusCard {{
            background: #f8fafc;
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(6)

    header = QHBoxLayout()
    header.setSpacing(8)

    icon = QLabel("●")
    icon.setStyleSheet("font-size: 12px;")
    title = QLabel("Checking fields…")
    title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")
    header.addWidget(icon)
    header.addWidget(title, 1)
    layout.addLayout(header)

    detail = QLabel("")
    detail.setWordWrap(True)
    detail.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    layout.addWidget(detail)

    missing = QLabel("")
    missing.setWordWrap(True)
    missing.setStyleSheet(
        "color: #b45309; font-size: 12px; font-family: monospace;"
    )
    missing.setVisible(False)
    layout.addWidget(missing)

    # Keep refs on the frame for the refresh helper
    frame._status_icon = icon
    frame._status_title = title
    frame._status_detail = detail
    frame._status_missing = missing
    return frame, title, detail, missing


def _refresh_status(frame: QFrame, note_type: str) -> None:
    icon: QLabel = frame._status_icon
    title: QLabel = frame._status_title
    detail: QLabel = frame._status_detail
    missing_lbl: QLabel = frame._status_missing

    name = (note_type or "").strip()
    if not name:
        icon.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        title.setText("No note type selected")
        detail.setText("Choose or create a note type above.")
        missing_lbl.setVisible(False)
        return

    fields = _fields_of(name)
    if not fields and mw.col:
        # Note type does not exist yet — user may create it
        icon.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        title.setText("Note type does not exist yet")
        detail.setText(
            "Click “Create JapaneseMining note type” to create it with all required fields."
        )
        missing_lbl.setVisible(False)
        return

    missing = [f for f in REQUIRED_MINING_FIELDS if f not in fields]
    present = len(REQUIRED_MINING_FIELDS) - len(missing)

    if not missing:
        icon.setStyleSheet("font-size: 12px; color: #1e8e3e;")
        title.setText("All required fields present")
        detail.setText(
            f"{present}/{len(REQUIRED_MINING_FIELDS)} fields · ready to use as a mining note type."
        )
        missing_lbl.setVisible(False)
        frame.setStyleSheet(f"""
            QFrame#statusCard {{
                background: #e6f4ea;
                border: 1px solid #ceead6;
                border-radius: 8px;
            }}
        """)
    else:
        icon.setStyleSheet("font-size: 12px; color: #e37400;")
        title.setText(f"Missing {len(missing)} required field(s)")
        detail.setText(
            f"{present}/{len(REQUIRED_MINING_FIELDS)} fields present. "
            "Add the fields below (or create a fresh note type) before using this as a mining note type."
        )
        missing_lbl.setText("Missing: " + ", ".join(missing))
        missing_lbl.setVisible(True)
        frame.setStyleSheet(f"""
            QFrame#statusCard {{
                background: #fef7e0;
                border: 1px solid #fde293;
                border-radius: 8px;
            }}
        """)


def _make_mining_list_card() -> tuple[QFrame, QVBoxLayout]:
    card, layout = make_section_card("Your mining note types")
    return card, layout


def make_general_tab(
    config_holder: ConfigHolder, collection_service=None, save_config_fn=None
):
    config = config_holder.config

    root, root_layout = make_scrollable_page()

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

    show_update_needed_checkbox = QCheckBox("Show update needed indicator")
    show_update_needed_checkbox.setChecked(
        getattr(config, "show_update_needed", True)
    )
    ui_layout.addWidget(show_update_needed_checkbox)

    root_layout.addWidget(ui_card)

    # ── Note type card ──────────────────────────────────────────────────
    mining_card, mining_layout = make_section_card("JapaneseMining note type")

    help_text = QLabel(
        "This is the primary note type used for mined vocabulary cards.\n"
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
        "Required fields:\n" + "\n".join(f"• {f}" for f in REQUIRED_MINING_FIELDS)
        + "\n\nExtra fields are fine."
    )
    mining_info.setCursor(Qt.CursorShape.WhatsThisCursor)

    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    row.addWidget(QLabel("Note type"))
    row.addWidget(mining_note_type_cb, 1)
    row.addWidget(mining_info)
    mining_layout.addLayout(row)

    # Field completeness status
    status_frame, _, _, _ = _make_status_card()
    mining_layout.addWidget(status_frame)

    def on_note_type_changed(_text=None):
        _refresh_status(status_frame, mining_note_type_cb.currentText())

    mining_note_type_cb.currentTextChanged.connect(on_note_type_changed)
    on_note_type_changed()

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
            _refresh_status(status_frame, name)
            refresh_mining_list()
            tooltip(message)
        else:
            showInfo(message)

    create_btn.clicked.connect(on_create_mining_note_type)
    mining_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    root_layout.addWidget(mining_card)

    # ── Mining note types you own ───────────────────────────────────────
    list_card, list_layout = _make_mining_list_card()
    list_hint = QLabel(
        "Note types that already contain every required mining field."
    )
    list_hint.setWordWrap(True)
    list_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    list_layout.addWidget(list_hint)

    chips_container = QWidget()
    chips_layout = QVBoxLayout(chips_container)
    chips_layout.setContentsMargins(0, 0, 0, 0)
    chips_layout.setSpacing(6)
    list_layout.addWidget(chips_container)

    def refresh_mining_list():
        while chips_layout.count():
            item = chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        names = _mining_note_types()
        if not names:
            empty = QLabel("No complete mining note types found yet.")
            empty.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 12px; font-style: italic;"
            )
            chips_layout.addWidget(empty)
            return

        for name in names:
            chip = QLabel(name)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {BADGE_BG};
                    color: {ACCENT};
                    border: 1px solid #d2e3fc;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 12px;
                }}
            """)
            chips_layout.addWidget(chip)

    refresh_mining_list()
    root_layout.addWidget(list_card)
    root_layout.addStretch()

    def apply_to_config(cfg):
        cfg.show_tooltip = show_tooltips_checkbox.isChecked()
        cfg.show_update_needed = show_update_needed_checkbox.isChecked()
        cfg.mining_note_type = (
            mining_note_type_cb.currentText().strip() or cfg.mining_note_type
        )

    return root, "General", apply_to_config
