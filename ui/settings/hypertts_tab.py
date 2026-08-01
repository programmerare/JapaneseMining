from aqt import (
    QCheckBox,
    QFormLayout,
    QWidget,
)


def make_hypertts_tab(config):
    hypertts_tab = QWidget()
    hypertts_layout = QFormLayout(hypertts_tab)

    hypertts_use_checkbox = QCheckBox("Enable HyperTTS")
    hypertts_use_checkbox.setChecked(config.use_hypertts)

    hypertts_layout.addRow("", hypertts_use_checkbox)

    def apply_to_config(cfg):
        cfg.use_hypertts = hypertts_use_checkbox.isChecked()

    return hypertts_tab, "HyperTTS", apply_to_config