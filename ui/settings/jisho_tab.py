# jisho_tab.py
from aqt import mw
from aqt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QCheckBox, QComboBox, QPushButton, QKeySequenceEdit,
    QKeySequence, QScrollArea, QFrame, Qt, QSizePolicy
)

# Re-use the same constants we put in config.py
from ...config import (
    JISHO_MAPPING_OPTIONS,
    ALLOWED_MULTI_WORD,
)

# Compatibility matrix (copied from foreign code)
MULTI_WORD_COMPATIBILITY = {
    "numbered": {
        "basic": True, "inline": False, "tagged": True,
        "numbered": True, "tagged_numbered": False,
    },
    "semicolon_merged": {
        "basic": True, "inline": True, "tagged": True,
        "numbered": True, "tagged_numbered": True,
    },
    "pipe_merged": {
        "basic": True, "inline": True, "tagged": True,
        "numbered": True, "tagged_numbered": True,
    },
}


def make_jisho_tab(config):
    """
    Returns (tab_widget, title, apply_to_config_fn)
    The tab itself contains three sub-tabs: General / Mapping / Advanced
    """
    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    tabs = QTabWidget()
    outer_layout.addWidget(tabs)

    # ------------------------------------------------------------------
    # State that the three sub-tabs share
    # ------------------------------------------------------------------
    state = {
        "mapping_rows": [dict(m) for m in (config.mappings or [])],  # deep copy
        "current_fields": [],
    }

    # ==================================================================
    # 1. GENERAL TAB
    # ==================================================================
    general = QWidget()
    g_layout = QFormLayout(general)
    g_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    # Enable
    use_jisho_cb = QCheckBox("Enable Jisho")
    use_jisho_cb.setChecked(config.use_jisho)
    note = QLabel("Restart Anki after changing this.")
    note.setStyleSheet("color: gray; font-size: 11px;")
    enable_row = QHBoxLayout()
    enable_row.addWidget(use_jisho_cb)
    enable_row.addWidget(note)
    enable_row.addStretch()
    g_layout.addRow(enable_row)

    # Note type
    card_type_cb = QComboBox()
    card_type_cb.setEditable(False)
    try:
        models = mw.col.models.all_names() if mw.col else []
        card_type_cb.addItems(sorted(models))
    except Exception:
        pass
    if config.card_type:
        idx = card_type_cb.findText(config.card_type)
        if idx >= 0:
            card_type_cb.setCurrentIndex(idx)
        else:
            card_type_cb.addItem(config.card_type)
            card_type_cb.setCurrentText(config.card_type)
    g_layout.addRow("Note type:", card_type_cb)

    # Target deck (optional)
    target_deck_cb = QComboBox()
    target_deck_cb.setEditable(True)          # allow empty / free text
    target_deck_cb.addItem("")                # empty = no restriction
    try:
        decks = mw.col.decks.all_names() if mw.col else []
        target_deck_cb.addItems(sorted(decks))
    except Exception:
        pass
    target_deck_cb.setCurrentText(config.target_deck or "")
    g_layout.addRow("Target deck:", target_deck_cb)

    # Search field (will be refreshed when note type changes)
    search_field_cb = QComboBox()
    g_layout.addRow("Search field:", search_field_cb)

    # Fill mode
    fill_mode_cb = QComboBox()
    fill_mode_cb.addItem("Replace content", "replace")
    fill_mode_cb.addItem("Append to content", "append")
    fill_mode_cb.setCurrentIndex(0 if config.fill_mode == "replace" else 1)
    g_layout.addRow("Fill mode:", fill_mode_cb)

    # Multi-meaning format
    multi_meaning_cb = QComboBox()
    multi_meaning_cb.addItem("Pipe Merged", "pipe_merged")
    multi_meaning_cb.addItem("Numbered", "numbered")
    multi_meaning_cb.addItem("Semicolon Merged", "semicolon_merged")
    mm_map = {"pipe_merged": 0, "numbered": 1, "semicolon_merged": 2}
    multi_meaning_cb.setCurrentIndex(mm_map.get(config.multi_meaning_format, 2))
    g_layout.addRow("Multi-meaning format:", multi_meaning_cb)

    # Multi-word format (filtered by compatibility)
    multi_word_cb = QComboBox()
    g_layout.addRow("Multi-word format:", multi_word_cb)

    def refresh_multi_word_options():
        meaning_key = multi_meaning_cb.currentData()
        compatible = MULTI_WORD_COMPATIBILITY.get(meaning_key, {})
        current = multi_word_cb.currentData()
        multi_word_cb.blockSignals(True)
        multi_word_cb.clear()
        options = [
            ("basic", "Basic"),
            ("inline", "Inline (merged)"),
            ("tagged", "Tagged (with word)"),
            ("numbered", "Numbered (word #)"),
            ("tagged_numbered", "Tagged + Numbered"),
        ]
        for key, label in options:
            if compatible.get(key, False):
                multi_word_cb.addItem(label, key)
                if key == current:
                    multi_word_cb.setCurrentIndex(multi_word_cb.count() - 1)
        # fallback if nothing selected
        if multi_word_cb.currentIndex() < 0 and multi_word_cb.count():
            multi_word_cb.setCurrentIndex(0)
        multi_word_cb.blockSignals(False)

    multi_meaning_cb.currentIndexChanged.connect(refresh_multi_word_options)
    refresh_multi_word_options()
    # restore saved value if still valid
    for i in range(multi_word_cb.count()):
        if multi_word_cb.itemData(i) == config.multi_word_format:
            multi_word_cb.setCurrentIndex(i)
            break

    # Shortcuts
    open_shortcut_edit = QKeySequenceEdit()
    open_shortcut_edit.setKeySequence(QKeySequence(config.jisho_shortcut))
    g_layout.addRow("Jisho shortcut:", open_shortcut_edit)

    quick_shortcut_edit = QKeySequenceEdit()
    quick_shortcut_edit.setKeySequence(QKeySequence(config.jisho_fastfill_shortcut))
    g_layout.addRow("Quick-fill shortcut:", quick_shortcut_edit)

    # Quick-fill mode
    quick_fill_mode_cb = QComboBox()
    quick_fill_mode_cb.addItem("All meanings", "all")
    quick_fill_mode_cb.addItem("First meaning", "first")
    quick_fill_mode_cb.setCurrentIndex(0 if config.quick_fill_mode == "all" else 1)
    g_layout.addRow("Quick-fill mode:", quick_fill_mode_cb)

    tabs.addTab(general, "General")

    # ==================================================================
    # 2. MAPPING TAB
    # ==================================================================
    mapping_tab = QWidget()
    m_layout = QVBoxLayout(mapping_tab)

    mapping_scroll = QScrollArea()
    mapping_scroll.setWidgetResizable(True)
    mapping_scroll.setFrameShape(QFrame.Shape.NoFrame)
    mapping_container = QWidget()
    mapping_rows_layout = QVBoxLayout(mapping_container)
    mapping_rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    mapping_scroll.setWidget(mapping_container)
    m_layout.addWidget(mapping_scroll)

    add_mapping_btn = QPushButton("+ Add Mapping")
    m_layout.addWidget(add_mapping_btn)

    def rebuild_mapping_rows():
        # clear
        while mapping_rows_layout.count():
            item = mapping_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, row_data in enumerate(state["mapping_rows"]):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 2, 0, 2)

            left = QComboBox()
            left.addItems(sorted(JISHO_MAPPING_OPTIONS))
            left.setCurrentText(row_data.get("jisho", ""))
            left.currentTextChanged.connect(
                lambda text, i=idx: state["mapping_rows"][i].__setitem__("jisho", text)
            )

            arrow = QLabel("→")
            arrow.setFixedWidth(20)
            arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

            right = QComboBox()
            right.addItem("")  # empty allowed
            right.addItems(state["current_fields"])
            right.setCurrentText(row_data.get("field", ""))
            right.currentTextChanged.connect(
                lambda text, i=idx: state["mapping_rows"][i].__setitem__("field", text)
            )

            remove_btn = QPushButton("✕")
            remove_btn.setFixedWidth(28)
            remove_btn.clicked.connect(lambda _, i=idx: remove_mapping_row(i))

            row.addWidget(left, 1)
            row.addWidget(arrow)
            row.addWidget(right, 1)
            row.addWidget(remove_btn)

            mapping_rows_layout.addWidget(row_widget)

        mapping_rows_layout.addStretch()

    def remove_mapping_row(index: int):
        if 0 <= index < len(state["mapping_rows"]):
            del state["mapping_rows"][index]
            rebuild_mapping_rows()

    def add_mapping_row():
        state["mapping_rows"].append({"jisho": "", "field": ""})
        rebuild_mapping_rows()

    add_mapping_btn.clicked.connect(add_mapping_row)

    tabs.addTab(mapping_tab, "Mapping")

    # ==================================================================
    # 3. ADVANCED TAB
    # ==================================================================
    advanced = QWidget()
    a_layout = QFormLayout(advanced)

    # Button position
    button_pos_cb = QComboBox()
    button_pos_cb.addItem("Toolbar", "toolbar")
    button_pos_cb.addItem("Field Label", "field_label")
    button_pos_cb.addItem("Toolbar + Field Label", "both")
    bp_map = {"toolbar": 0, "field_label": 1, "both": 2}
    button_pos_cb.setCurrentIndex(bp_map.get(config.editor_button_position, 0))
    a_layout.addRow("Button position:", button_pos_cb)

    # Checkboxes
    remove_pos_cb = QCheckBox("Remove 'with x ending' from Part of speech")
    remove_pos_cb.setChecked(config.remove_pos_ending)
    a_layout.addRow(remove_pos_cb)

    remove_furigana_cb = QCheckBox("Remove furigana from search term")
    remove_furigana_cb.setChecked(config.remove_furigana_search)
    a_layout.addRow(remove_furigana_cb)

    disable_multi_word_cb = QCheckBox("Disable multi-word selection warning")
    disable_multi_word_cb.setChecked(config.disable_multi_word_warning)
    a_layout.addRow(disable_multi_word_cb)

    show_quick_success_cb = QCheckBox("Show quick-fill success message")
    show_quick_success_cb.setChecked(config.show_quick_fill_success)
    a_layout.addRow(show_quick_success_cb)

    # Language (kept for future / foreign compatibility)
    lang_cb = QComboBox()
    lang_cb.addItem("English", "en")
    lang_cb.addItem("Português", "pt")
    lang_cb.setCurrentIndex(0 if config.language == "en" else 1)
    a_layout.addRow("UI Language:", lang_cb)

    tabs.addTab(advanced, "Advanced")

    # ==================================================================
    # Shared helpers – note type → fields
    # ==================================================================
    def refresh_fields_from_note_type():
        model_name = card_type_cb.currentText()
        fields = []
        try:
            model = mw.col.models.by_name(model_name) if mw.col and model_name else None
            if model:
                fields = [f["name"] for f in model["flds"]]
        except Exception:
            pass

        state["current_fields"] = fields

        # Search field
        current_search = search_field_cb.currentText()
        search_field_cb.blockSignals(True)
        search_field_cb.clear()
        search_field_cb.addItems(fields)
        if current_search in fields:
            search_field_cb.setCurrentText(current_search)
        elif config.search_field in fields:
            search_field_cb.setCurrentText(config.search_field)
        search_field_cb.blockSignals(False)

        # Rebuild mapping rows so right-side combos have the new fields
        rebuild_mapping_rows()

    card_type_cb.currentIndexChanged.connect(refresh_fields_from_note_type)
    refresh_fields_from_note_type()   # initial fill

    # ==================================================================
    # apply_to_config – called when user clicks Save
    # ==================================================================
    def apply_to_config(cfg):
        cfg.use_jisho = use_jisho_cb.isChecked()

        cfg.card_type = card_type_cb.currentText()
        cfg.target_deck = target_deck_cb.currentText().strip()
        cfg.search_field = search_field_cb.currentText()

        cfg.fill_mode = fill_mode_cb.currentData()
        cfg.multi_meaning_format = multi_meaning_cb.currentData()
        cfg.multi_word_format = multi_word_cb.currentData() or "inline"
        cfg.quick_fill_mode = quick_fill_mode_cb.currentData()

        # Shortcuts
        seq = open_shortcut_edit.keySequence()
        if not seq.isEmpty():
            cfg.jisho_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText)
        seq = quick_shortcut_edit.keySequence()
        if not seq.isEmpty():
            cfg.jisho_fastfill_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText)

        # Mapping
        cfg.mappings = [dict(r) for r in state["mapping_rows"] if r.get("jisho") or r.get("field")]

        # Advanced
        cfg.editor_button_position = button_pos_cb.currentData()
        cfg.remove_pos_ending = remove_pos_cb.isChecked()
        cfg.remove_furigana_search = remove_furigana_cb.isChecked()
        cfg.disable_multi_word_warning = disable_multi_word_cb.isChecked()
        cfg.show_quick_fill_success = show_quick_success_cb.isChecked()
        cfg.language = lang_cb.currentData()

    return outer, "Jisho", apply_to_config