from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    Qt,
)
from copy import deepcopy

from ...config import ConfigHolder, default_translate_profile
from ..ui_styles import (
    make_scrollable_page,
    make_section_card,
    make_instruction_label,
    make_secondary_button,
    make_link_button,
    make_separator,
    TEXT_SECONDARY,
)

# Fallback lists used when the API key is missing or the request fails.
# Always stored as clean (code, display_name) pairs — never re-parse itemText.
_FALLBACK_TARGET_LANGS = [
    ("EN-US", "English (American)"),
    ("EN-GB", "English (British)"),
    ("DE", "German"),
    ("FR", "French"),
    ("ES", "Spanish"),
    ("JA", "Japanese"),
    ("ZH", "Chinese (simplified)"),
    ("PT-BR", "Portuguese (Brazilian)"),
    ("PT-PT", "Portuguese (European)"),
    ("IT", "Italian"),
    ("NL", "Dutch"),
    ("PL", "Polish"),
    ("RU", "Russian"),
    ("KO", "Korean"),
]

_FALLBACK_SOURCE_LANGS = [
    ("JA", "Japanese"),
    ("EN", "English"),
    ("DE", "German"),
    ("FR", "French"),
    ("ES", "Spanish"),
    ("ZH", "Chinese"),
    ("KO", "Korean"),
    ("PT", "Portuguese"),
    ("IT", "Italian"),
    ("RU", "Russian"),
]


def _norm_lang(code: str) -> str:
    """Normalize DeepL language codes for comparison (case + separators)."""
    return (code or "").strip().upper().replace("_", "-")


def _fill_lang_combo(
    combo: QComboBox, items: list[tuple[str, str]], selected: str
) -> None:
    """Rebuild combo from clean (code, name) pairs and select by code."""
    combo.blockSignals(True)
    combo.clear()
    for code, name in items:
        combo.addItem(f"{name} ({code})", code)
    _select_lang(combo, selected)
    combo.blockSignals(False)


def _find_lang_index(combo: QComboBox, selected: str) -> int:
    """Find combo index for a language code, case-insensitive. -1 if missing."""
    want = _norm_lang(selected)
    if not want:
        return -1
    for i in range(combo.count()):
        data = combo.itemData(i)
        if isinstance(data, str) and _norm_lang(data) == want:
            return i
    return -1


def _select_lang(combo: QComboBox, selected: str) -> None:
    """Set current index by language code. Prefer existing items over inventing new ones."""
    selected = (selected or "").strip()
    if not selected:
        if combo.count():
            combo.setCurrentIndex(0)
        return

    idx = _find_lang_index(combo, selected)
    if idx < 0:
        # Truly unknown code — keep the user's value visible, but only once
        combo.insertItem(0, f"{selected} ({selected})", selected)
        idx = 0
    combo.setCurrentIndex(idx)


def _note_type_names() -> list[str]:
    try:
        if not mw.col:
            return []
        return sorted(m.name for m in mw.col.models.all_names_and_ids())
    except Exception:
        return []


def _fields_for_note_type(note_type: str) -> list[str]:
    try:
        model = mw.col.models.by_name(note_type) if mw.col and note_type else None
        if model:
            return [f["name"] for f in model["flds"]]
    except Exception:
        pass
    return []


def make_translate_tab(
    config_holder: ConfigHolder,
    deepl_service=None,
    save_config_fn=None,
    on_goto_help=None,
):
    """
    Returns (tab_widget, title, apply_to_config_fn).

    Account-level: enable, API key, URL, shortcut.
    Per note-type profiles: source/target fields + source/target languages.
    At runtime DeeplService resolves the profile from the current note's
    note type — the "active" profile here is only for editing.
    """
    config = config_holder.config

    root, root_layout = make_scrollable_page()

    root_layout.addWidget(
        make_instruction_label(
            "Each profile is tied to one existing note type (source/target fields "
            "and languages). In the editor the matching profile is chosen "
            "automatically from the note’s note type."
        )
    )

    if on_goto_help:
        help_row = QHBoxLayout()
        help_btn = make_link_button("Help → Translate →")
        help_btn.clicked.connect(on_goto_help)
        help_row.addWidget(help_btn)
        help_row.addStretch()
        root_layout.addLayout(help_row)

    state = {
        "profiles": deepcopy(config.translate_profiles or {}),
        "active": config.active_translate_profile
        or next(iter(config.translate_profiles or {}), ""),
        "current_fields": [],
        # Clean language lists — never derived from combo itemText
        "source_langs": list(_FALLBACK_SOURCE_LANGS),
        "target_langs": list(_FALLBACK_TARGET_LANGS),
    }

    # ── Enable + account ────────────────────────────────────────────────
    account_card, account_layout = make_section_card("Account")

    use_cb = QCheckBox("Enable DeepL")
    use_cb.setChecked(config.use_deepl)
    account_layout.addWidget(use_cb)

    account_layout.addWidget(make_separator())

    account_layout.addWidget(QLabel("API key"))
    key_edit = QLineEdit(config.deepl_api_key)
    key_edit.setMinimumWidth(360)
    key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    account_layout.addWidget(key_edit)

    account_layout.addWidget(QLabel("URL"))
    url_edit = QLineEdit(config.deepl_url)
    url_edit.setMinimumWidth(360)
    account_layout.addWidget(url_edit)

    account_layout.addWidget(QLabel("Shortcut (global)"))
    shortcut_edit = QKeySequenceEdit()
    shortcut_edit.setKeySequence(QKeySequence(config.deepl_shortcut))
    account_layout.addWidget(shortcut_edit)

    root_layout.addWidget(account_card)

    # ── Usage ───────────────────────────────────────────────────────────
    usage_card, usage_layout = make_section_card("Usage")
    character_usage = QLabel("Character count: —\nCharacters limit: —")
    character_usage.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
    usage_layout.addWidget(character_usage)
    root_layout.addWidget(usage_card)

    # ── Profile selector ────────────────────────────────────────────────
    profile_card, profile_layout = make_section_card("Profile (Note type)")

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
    profile_row.addWidget(profile_cb, 1)

    add_profile_btn = make_secondary_button("Add")
    delete_profile_btn = make_secondary_button("Delete")
    profile_row.addWidget(add_profile_btn)
    profile_row.addWidget(delete_profile_btn)
    profile_layout.addLayout(profile_row)

    note = QLabel(
        "The profile is selected automatically in the editor from the note’s "
        "note type. Changing the selection here only edits that profile. "
        "Add only picks from existing note types."
    )
    note.setWordWrap(True)
    note.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    profile_layout.addWidget(note)

    root_layout.addWidget(profile_card)

    # ── Fields + languages for the active profile ───────────────────────
    mapping_card, mapping_layout = make_section_card("Fields & languages")

    form = QFormLayout()
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    source_field_cb = QComboBox()
    source_field_cb.setMinimumWidth(320)
    form.addRow("Source field", source_field_cb)

    target_field_cb = QComboBox()
    target_field_cb.setMinimumWidth(320)
    form.addRow("Target field", target_field_cb)

    source_lang_cb = QComboBox()
    source_lang_cb.setMinimumWidth(320)
    form.addRow("Source language", source_lang_cb)

    target_lang_cb = QComboBox()
    target_lang_cb.setMinimumWidth(320)
    form.addRow("Target language", target_lang_cb)

    mapping_layout.addLayout(form)
    root_layout.addWidget(mapping_card)
    root_layout.addStretch()

    # Fill language combos once from fallbacks. Async API upgrade may
    # replace the lists later — profile switches only change selection.
    _fill_lang_combo(source_lang_cb, state["source_langs"], "JA")
    _fill_lang_combo(target_lang_cb, state["target_langs"], "EN-US")

    # ------------------------------------------------------------------
    # Profile load / persist helpers
    # ------------------------------------------------------------------

    def refresh_fields_for_note_type(note_type: str):
        fields = _fields_for_note_type(note_type)
        state["current_fields"] = fields

        for combo in (source_field_cb, target_field_cb):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("")
            combo.addItems(fields)
            combo.blockSignals(False)

    def persist_current_profile():
        name = state["active"]
        if not name:
            return
        p = state["profiles"].setdefault(name, default_translate_profile())
        p["source_field"] = source_field_cb.currentText().strip()
        p["target_field"] = target_field_cb.currentText().strip()
        src = source_lang_cb.currentData()
        p["source_lang"] = (
            src if isinstance(src, str) and src else source_lang_cb.currentText()
        )
        tgt = target_lang_cb.currentData()
        p["target_lang"] = (
            tgt if isinstance(tgt, str) and tgt else target_lang_cb.currentText()
        )
        state["profiles"][name] = p

    def load_profile_into_ui(name: str):
        profile = state["profiles"].get(name) or default_translate_profile()
        state["active"] = name

        # Fields change per note type — rebuild those combos
        refresh_fields_for_note_type(name)

        source_field_cb.blockSignals(True)
        wanted = profile.get("source_field", "")
        if wanted and source_field_cb.findText(wanted) < 0:
            source_field_cb.insertItem(0, wanted)
        source_field_cb.setCurrentText(wanted)
        source_field_cb.blockSignals(False)

        target_field_cb.blockSignals(True)
        wanted = profile.get("target_field", "")
        if wanted and target_field_cb.findText(wanted) < 0:
            target_field_cb.insertItem(0, wanted)
        target_field_cb.setCurrentText(wanted)
        target_field_cb.blockSignals(False)

        # Languages are global — only change the selected index by code
        source_lang_cb.blockSignals(True)
        _select_lang(source_lang_cb, profile.get("source_lang", "JA"))
        source_lang_cb.blockSignals(False)

        target_lang_cb.blockSignals(True)
        _select_lang(target_lang_cb, profile.get("target_lang", "EN-US"))
        target_lang_cb.blockSignals(False)

    def on_profile_changed(_index: int):
        old = state["active"]
        new = profile_cb.currentText()
        if not new or new == old:
            return
        persist_current_profile()
        load_profile_into_ui(new)

    profile_cb.currentIndexChanged.connect(on_profile_changed)

    def add_profile():
        models = _note_type_names()
        available = [m for m in models if m not in state["profiles"]]
        if not available:
            QMessageBox.information(
                root,
                "No note types available",
                "Every existing note type already has a Translate profile, "
                "or no note types exist in this collection.",
            )
            return

        dlg = QInputDialog(root)
        dlg.setWindowTitle("Add Translate Profile")
        dlg.setLabelText("Note type:")
        dlg.setComboBoxItems(available)
        dlg.setComboBoxEditable(False)
        if dlg.exec() != QInputDialog.DialogCode.Accepted:
            return

        note_type = dlg.textValue().strip()
        if not note_type:
            return
        if note_type in state["profiles"]:
            QMessageBox.warning(
                root,
                "Profile exists",
                f"A translate profile for “{note_type}” already exists.",
            )
            return

        persist_current_profile()
        state["profiles"][note_type] = default_translate_profile()
        state["active"] = note_type
        refresh_profile_combo()
        load_profile_into_ui(note_type)

    def delete_profile():
        note_type = profile_cb.currentText()
        if not note_type:
            return
        if len(state["profiles"]) <= 1:
            QMessageBox.warning(
                root,
                "Cannot delete profile",
                "At least one translate profile must remain.",
            )
            return

        answer = QMessageBox.question(
            root,
            "Delete profile",
            f"Delete the translate profile for “{note_type}”?",
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

    # Initial load (fields + language selection for the active profile)
    load_profile_into_ui(state["active"])

    # ------------------------------------------------------------------
    # apply_to_config
    # ------------------------------------------------------------------

    def apply_to_config(cfg):
        persist_current_profile()

        cfg.use_deepl = use_cb.isChecked()
        cfg.deepl_api_key = key_edit.text().strip()
        cfg.deepl_url = url_edit.text().strip() or cfg.deepl_url
        seq = shortcut_edit.keySequence()
        if not seq.isEmpty():
            cfg.deepl_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText)

        cfg.translate_profiles = deepcopy(state["profiles"])
        cfg.active_translate_profile = state["active"]

    # ------------------------------------------------------------------
    # Async language lists + usage (non-blocking dialog open)
    # ------------------------------------------------------------------

    if deepl_service is not None:

        def load_langs():
            return (
                deepl_service.get_source_languages(),
                deepl_service.get_target_languages(),
            )

        def on_langs_done(fut):
            try:
                sources, targets = fut.result()
            except Exception:
                return
            if not sources and not targets:
                return

            def apply():
                # Remember current selections by code before rebuilding
                src_sel = source_lang_cb.currentData() or "JA"
                tgt_sel = target_lang_cb.currentData() or "EN-US"

                if sources:
                    state["source_langs"] = list(sources)
                    _fill_lang_combo(source_lang_cb, state["source_langs"], src_sel)
                if targets:
                    state["target_langs"] = list(targets)
                    _fill_lang_combo(target_lang_cb, state["target_langs"], tgt_sel)

            mw.taskman.run_on_main(apply)

        mw.taskman.run_in_background(load_langs, on_langs_done)

        def load_usage():
            return deepl_service.get_character_usage()

        def on_usage_done(fut):
            try:
                res = fut.result()
            except Exception:
                return
            if not res:
                return
            count, limit = res

            def apply():
                character_usage.setText(
                    f"Character count: {count}\nCharacters limit: {limit}"
                )

            mw.taskman.run_on_main(apply)

        mw.taskman.run_in_background(load_usage, on_usage_done)

    return root, "Translate", apply_to_config
