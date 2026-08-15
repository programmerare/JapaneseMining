from aqt.qt import (
    QCheckBox,
    QVBoxLayout,
    QWidget,
)

from ...config import ConfigHolder
from .ui_styles import make_section_card, make_instruction_label


def make_hypertts_tab(config_holder: ConfigHolder, save_config_fn=None):
    config = config_holder.config

    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.setContentsMargins(16, 12, 16, 16)
    root_layout.setSpacing(14)

    root_layout.addWidget(
        make_instruction_label(
            "Enable integration with the HyperTTS add-on for automatic audio "
            "generation. HyperTTS itself must be installed and configured separately."
        )
    )

    card, layout = make_section_card("HyperTTS")
    hypertts_use_checkbox = QCheckBox("Enable HyperTTS")
    hypertts_use_checkbox.setChecked(config.use_hypertts)
    layout.addWidget(hypertts_use_checkbox)
    root_layout.addWidget(card)

    root_layout.addStretch()

    def apply_to_config(cfg):
        cfg.use_hypertts = hypertts_use_checkbox.isChecked()

    return root, "HyperTTS", apply_to_config
