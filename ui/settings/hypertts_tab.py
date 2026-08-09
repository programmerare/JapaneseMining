from aqt import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QWidget,
    Qt,
)


def make_hypertts_tab(config):
    hypertts_tab = QWidget()
    hypertts_layout = QFormLayout(hypertts_tab)
    hypertts_layout.setContentsMargins(16, 12, 16, 12)
    hypertts_layout.setSpacing(10)
    hypertts_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    hypertts_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    header = QLabel("HyperTTS")
    header.setStyleSheet("font-weight: 600; color: #555; margin-top: 4px;")
    hypertts_layout.addRow(header)

    hypertts_use_checkbox = QCheckBox("Enable HyperTTS")
    hypertts_use_checkbox.setChecked(config.use_hypertts)
    hypertts_layout.addRow(hypertts_use_checkbox)

    def apply_to_config(cfg):
        cfg.use_hypertts = hypertts_use_checkbox.isChecked()

    return hypertts_tab, "HyperTTS", apply_to_config