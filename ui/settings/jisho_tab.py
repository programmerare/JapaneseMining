from aqt import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QWidget,
)


def make_jisho_tab(config):
    jisho_tab = QWidget()
    jisho_layout = QFormLayout(jisho_tab)

    jisho_use_checkbox = QCheckBox("Enable Jisho")
    jisho_use_checkbox.setChecked(config.use_jisho)

    note = QLabel("Restart Anki to make this setting effective.")
    note.setStyleSheet("color: gray; font-size: 11px;")

    checkbox_row = QHBoxLayout()
    checkbox_row.addWidget(jisho_use_checkbox)
    checkbox_row.addWidget(note)
    checkbox_row.addStretch()

    jisho_shortcut_edit = QKeySequenceEdit()
    jisho_shortcut_edit.setKeySequence(QKeySequence(config.jisho_shortcut))

    jisho_fastfill_shortcut_edit = QKeySequenceEdit()
    jisho_fastfill_shortcut_edit.setKeySequence(QKeySequence(config.jisho_fastfill_shortcut))

    jisho_layout.addRow("", checkbox_row)
    jisho_layout.addRow("Jisho shortcut", jisho_shortcut_edit)
    jisho_layout.addRow("Jisho fast-fill shortcut", jisho_fastfill_shortcut_edit)

    def apply_to_config(cfg):
        seq = jisho_shortcut_edit.keySequence()
        fastfill_seq = jisho_fastfill_shortcut_edit.keySequence()

        cfg.use_jisho = jisho_use_checkbox.isChecked()
        cfg.jisho_shortcut = seq.toString(QKeySequence.SequenceFormat.NativeText) if not seq.isEmpty() else cfg.jisho_shortcut
        cfg.jisho_fastfill_shortcut = fastfill_seq.toString(QKeySequence.SequenceFormat.NativeText) if not fastfill_seq.isEmpty() else cfg.jisho_fastfill_shortcut

    return jisho_tab, "Jisho", apply_to_config