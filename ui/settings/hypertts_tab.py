from aqt.qt import (
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ...config import ConfigHolder
from ..ui_styles import (
    make_section_card,
    make_instruction_label,
    make_link_button,
    make_scrollable_page,
)


def make_hypertts_tab(config_holder: ConfigHolder, save_config_fn=None, on_goto_help=None):
    config = config_holder.config

    root, root_layout = make_scrollable_page()

    root_layout.addWidget(
        make_instruction_label(
            "Automatic audio via HyperTTS. Install and configure HyperTTS itself first, "
            "then enable the integration here."
        )
    )

    if on_goto_help:
        help_row = QHBoxLayout()
        help_btn = make_link_button("Help → HyperTTS →")
        help_btn.clicked.connect(on_goto_help)
        help_row.addWidget(help_btn)
        help_row.addStretch()
        root_layout.addLayout(help_row)

    card, layout = make_section_card("HyperTTS")
    hypertts_use_checkbox = QCheckBox("Enable HyperTTS")
    hypertts_use_checkbox.setChecked(config.use_hypertts)
    layout.addWidget(hypertts_use_checkbox)
    root_layout.addWidget(card)

    root_layout.addStretch()

    def apply_to_config(cfg):
        cfg.use_hypertts = hypertts_use_checkbox.isChecked()

    return root, "HyperTTS", apply_to_config
