# jisho_tab.py

from aqt import mw
from aqt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QInputDialog,
    QFormLayout,
    QTabWidget,
    QLabel,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QPushButton,
    QKeySequenceEdit,
    QKeySequence,
    QScrollArea,
    QFrame,
    Qt,
)
from copy import deepcopy

# Re-use the same constants we put in config.py
from ...config import (
    JISHO_MAPPING_OPTIONS,
    default_jisho_profile,
    ConfigHolder,
)

# Compatibility matrix (copied from foreign code)
MULTI_WORD_COMPATIBILITY = {
    "numbered": {
        "basic": True,
        "inline": False,
        "tagged": True,
        "numbered": True,
        "tagged_numbered": False,
    },
    "semicolon_merged": {
        "basic": True,
        "inline": True,
        "tagged": True,
        "numbered": True,
        "tagged_numbered": True,
    },
    "pipe_merged": {
        "basic": True,
        "inline": True,
        "tagged": True,
        "numbered": True,
        "tagged_numbered": True,
    },
}


def make_jisho_tab(config_holder: ConfigHolder, save_config_fn=None):
    """
    Returns (tab_widget, title, apply_to_config_fn)
    The tab itself contains three sub-tabs: General / Mapping / Advanced
    """
    config = config_holder.config

    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    tabs = QTabWidget()
    outer_layout.addWidget(tabs)

    # ------------------------------------------------------------------
    # State that the three sub-tabs share
    # ------------------------------------------------------------------
    state = {
        "profiles": deepcopy(config.jisho_profiles or {}),
        "active": config.active_jisho_profile
        or next(iter(config.jisho_profiles or {}), ""),
        "mapping_rows": [],
        "current_fields": [],
    }

    # ==================================================================
    # 1. GENERAL TAB
    # ==================================================================
    general = QWidget()
    g_layout = QFormLayout(general)
    g_layout.setContentsMargins(16, 12, 16, 12)
    g_layout.setSpacing(10)
    g_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    g_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    # Section header
    header = QLabel("Jisho")
    header.setStyleSheet("font-weight: 600; color: #555; margin-top: 4px;")
    g_layout.addRow(header)

    # Enable
    use_jisho_cb = QCheckBox("Enable Jisho")
    use_jisho_cb.setChecked(config.use_jisho)
    note = QLabel("Restart Anki after changing this.")
    note.setStyleSheet("color: gray; font-size: 11px;")
    enable_row = QHBoxLayout()
    enable_row.setContentsMargins(0, 0, 0, 0)
    enable_row.setSpacing(8)
    enable_row.addWidget(use_jisho_cb)
    enable_row.addWidget(note)
    enable_row.addStretch()
    g_layout.addRow(enable_row)

    # Thin separator
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("color: #ddd;")
    g_layout.addRow(sep)

    # Profile
    profile_row = QHBoxLayout()
    profile_row.setSpacing(8)
    profile_cb = QComboBox()
    profile_cb.setEditable(False)

    def refresh_profile_combo():
        profile_cb.blockSignals(True)
        profile_cb.clear()
        for name in sorted(state["profiles"].keys()):
            profile_cb.addItem(name)
        idx = profile_cb.findText(state["active"])
        profile_cb.setCurrentIndex(idx if idx >= 0 else 0)
        state["active"] = profile_cb.currentText()
        profile_cb.blockSignals(False)

    refresh_profile_combo()

    profile_row.addWidget(QLabel("Profile (Note type):"))
    profile_row.addWidget(profile_cb, 1)

    add_profile_btn = QPushButton("Add")
    delete_profile_btn = QPushButton("Delete")

    profile_row.addWidget(add_profile_btn)
    profile_row.addWidget(delete_profile_btn)

    g_layout.addRow(profile_row)

    def add_profile():
        try:
            models = mw.col.models.all_names() if mw.col else []
        except Exception:
            models = []

        dlg = QInputDialog(general)
        dlg.setWindowTitle("Add Jisho Profile")
        dlg.setLabelText("Note type:")
        dlg.setComboBoxItems(sorted(models))
        dlg.setComboBoxEditable(True)
        if dlg.exec() != QInputDialog.DialogCode.Accepted:
            return

        note_type = dlg.textValue().strip()
        if not note_type:
            return
        if note_type in state["profiles"]:
            QMessageBox.warning(
                general,
                "Profile exists",
                f"A profile for '{note_type}' already exists.",
            )
            return

        persist_current_profile()  # save what we were editing
        state["profiles"][note_type] = default_jisho_profile()
        state["active"] = note_type
        refresh_profile_combo()
        load_profile_into_ui(note_type)

    def delete_profile():
        note_type = profile_cb.currentText()
        if not note_type:
            return
        if len(state["profiles"]) <= 1:
            QMessageBox.warning(
                general, "Cannot delete profile", "At least one profile must remain."
            )
            return

        answer = QMessageBox.question(
            general,
            "Delete profile",
            f"Are you sure you want to delete the profile for '{note_type}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        del state["profiles"][note_type]
        state["active"] = next(iter(state["profiles"]))
        refresh_profile_combo()
        load_profile_into_ui(state["active"])

    add_profile_btn.clicked.connect(add_profile)
    delete_profile_btn.clicked.connect(delete_profile)

    def persist_current_profile():
        """Write current widget values into state['profiles'][active]."""
        name = state["active"]
        if not name:
            return
        p = state["profiles"].setdefault(name, default_jisho_profile())

        p["target_deck"] = target_deck_cb.currentText().strip()
        p["search_field"] = search_field_cb.currentText()
        p["fill_mode"] = fill_mode_cb.currentData()
        p["multi_meaning_format"] = multi_meaning_cb.currentData()
        p["multi_word_format"] = multi_word_cb.currentData() or "inline"
        p["quick_fill_mode"] = quick_fill_mode_cb.currentData()
        p["remove_pos_ending"] = remove_pos_cb.isChecked()
        p["remove_furigana_search"] = remove_furigana_cb.isChecked()
        p["disable_multi_word_warning"] = disable_multi_word_cb.isChecked()
        p["show_quick_fill_success"] = show_quick_success_cb.isChecked()
        p["mappings"] = [
            dict(r) for r in state["mapping_rows"] if r.get("jisho") or r.get("field")
        ]

        state["profiles"][name] = p

    def load_profile_into_ui(name: str):
        profile = state["profiles"].get(name) or default_jisho_profile()
        state["active"] = name

        target_deck_cb.setCurrentText(profile.get("target_deck", ""))

        # Fill mode
        fill_mode_cb.setCurrentIndex(0 if profile.get("fill_mode") == "replace" else 1)

        # Multi-meaning
        mm_map = {"pipe_merged": 0, "numbered": 1, "semicolon_merged": 2}
        multi_meaning_cb.setCurrentIndex(
            mm_map.get(profile.get("multi_meaning_format"), 2)
        )
        refresh_multi_word_options()
        for i in range(multi_word_cb.count()):
            if multi_word_cb.itemData(i) == profile.get("multi_word_format"):
                multi_word_cb.setCurrentIndex(i)
                break

        # Quick-fill mode
        quick_fill_mode_cb.setCurrentIndex(
            0 if profile.get("quick_fill_mode") == "all" else 1
        )

        # Checkboxes (Advanced tab)
        remove_pos_cb.setChecked(bool(profile.get("remove_pos_ending", True)))
        remove_furigana_cb.setChecked(bool(profile.get("remove_furigana_search", True)))
        disable_multi_word_cb.setChecked(
            bool(profile.get("disable_multi_word_warning", False))
        )
        show_quick_success_cb.setChecked(
            bool(profile.get("show_quick_fill_success", False))
        )

        state["mapping_rows"] = [dict(m) for m in profile.get("mappings", [])]
        refresh_fields_for_note_type(name)
        rebuild_mapping_rows()

    def refresh_fields_for_note_type(note_type: str):
        fields = []
        try:
            model = mw.col.models.by_name(note_type) if mw.col and note_type else None
            if model:
                fields = [f["name"] for f in model["flds"]]
        except Exception:
            pass
        state["current_fields"] = fields

        search_field_cb.blockSignals(True)
        search_field_cb.clear()
        search_field_cb.addItems(fields)
        wanted = (state["profiles"].get(note_type) or {}).get("search_field", "")
        if wanted in fields:
            search_field_cb.setCurrentText(wanted)
        search_field_cb.blockSignals(False)

    def on_profile_changed(_index: int):
        old = state["active"]
        new = profile_cb.currentText()
        if not new or new == old:
            return
        persist_current_profile()  # save the one we are leaving
        load_profile_into_ui(new)  # load the one we are entering

    profile_cb.currentIndexChanged.connect(on_profile_changed)

    # Target deck (optional)
    target_deck_cb = QComboBox()
    target_deck_cb.setEditable(True)  # allow empty / free text
    target_deck_cb.addItem("")  # empty = no restriction
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
            row.setContentsMargins(4, 4, 4, 4)
            row.setSpacing(8)

            left = QComboBox()
            left.addItems(sorted(JISHO_MAPPING_OPTIONS))
            left.setCurrentText(row_data.get("jisho", ""))
            left.currentTextChanged.connect(
                lambda text, i=idx: state["mapping_rows"][i].__setitem__("jisho", text)
            )

            arrow = QLabel("→")
            arrow.setFixedWidth(24)
            arrow.setFixedWidth(20)
            arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow.setStyleSheet("color: #888;")

            right = QComboBox()
            right.addItem("")  # empty allowed
            right.addItems(state["current_fields"])
            right.setCurrentText(row_data.get("field", ""))
            right.currentTextChanged.connect(
                lambda text, i=idx: state["mapping_rows"][i].__setitem__("field", text)
            )

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setStyleSheet("QPushButton { color: #c44; border: none; }")
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
    a_layout.setContentsMargins(16, 12, 16, 12)
    a_layout.setSpacing(10)
    a_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

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

    # Initial load
    load_profile_into_ui(state["active"])

    # ==================================================================
    # apply_to_config – called when user clicks Save
    # ==================================================================
    def apply_to_config(cfg):
        persist_current_profile()

        # Globals
        cfg.use_jisho = use_jisho_cb.isChecked()
        seq = open_shortcut_edit.keySequence()
        if not seq.isEmpty():
            cfg.jisho_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText)
        seq = quick_shortcut_edit.keySequence()
        if not seq.isEmpty():
            cfg.jisho_fastfill_shortcut = seq.toString(
                QKeySequence.SequenceFormat.NativeText
            )
        cfg.editor_button_position = button_pos_cb.currentData()
        cfg.language = lang_cb.currentData()

        # Profiles (source of truth)
        cfg.jisho_profiles = deepcopy(state["profiles"])
        cfg.active_jisho_profile = state["active"]

        # Mirror active profile onto the flat keys (for runtime adapter)
        active_p = state["profiles"].get(state["active"], default_jisho_profile())
        cfg.card_type = state["active"]
        cfg.target_deck = active_p.get("target_deck", "")
        cfg.search_field = active_p.get("search_field", "")
        cfg.mappings = active_p.get("mappings", [])
        cfg.fill_mode = active_p.get("fill_mode", "replace")
        cfg.multi_meaning_format = active_p.get(
            "multi_meaning_format", "semicolon_merged"
        )
        cfg.multi_word_format = active_p.get("multi_word_format", "inline")
        cfg.remove_pos_ending = active_p.get("remove_pos_ending", True)
        cfg.remove_furigana_search = active_p.get("remove_furigana_search", True)
        cfg.disable_multi_word_warning = active_p.get(
            "disable_multi_word_warning", False
        )
        cfg.quick_fill_mode = active_p.get("quick_fill_mode", "all")
        cfg.show_quick_fill_success = active_p.get("show_quick_fill_success", False)

    return outer, "Jisho", apply_to_config
