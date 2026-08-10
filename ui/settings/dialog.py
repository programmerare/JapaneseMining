from aqt import mw
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
)

from .general_tab import make_general_tab
from .rtk_tab import make_rtk_tab
from .translate_tab import make_translate_tab
from .jisho_tab import make_jisho_tab
from .hypertts_tab import make_hypertts_tab


def make_show_settings(config, save_config_fn):
    def show_settings():
        """Show a dialog for configuring the JapaneseMining add-on."""
        dialog = QDialog(mw)
        dialog.setWindowTitle("JapaneseMining Settings")
        dialog.resize(760, 520)
        dialog.setMinimumSize(680, 420)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(10)

        tabs = QTabWidget()

        # Collect the apply functions and add the tabs to the QTabWidget
        apply_fns = []

        for make_tab in [make_general_tab, make_rtk_tab, make_translate_tab, make_jisho_tab, make_hypertts_tab]:
            tab, title, apply_fn = make_tab(config)
            tabs.addTab(tab, title)
            apply_fns.append(apply_fn)
        main_layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        main_layout.addWidget(buttons)

        # Define the save_and_close function to apply changes and close the dialog
        def save_and_close():
            for apply_fn in apply_fns:
                apply_fn(config)    # Each tab writes its own settings to the config object
            save_config_fn(config)

            if config.use_jisho:
                from ...jisho_adapter import to_ajc_runtime_config
                from ...AJC.runtime.config_holder import set_runtime_config
                set_runtime_config(to_ajc_runtime_config(config))

            dialog.accept()

        buttons.accepted.connect(save_and_close)
        buttons.rejected.connect(dialog.reject)

        dialog.exec()
    return show_settings