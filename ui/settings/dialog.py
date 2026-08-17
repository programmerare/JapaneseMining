from aqt import mw
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
)
from aqt.utils import showWarning

from .general_tab import make_general_tab
from .rtk_tab import make_rtk_tab
from .translate_tab import make_translate_tab
from .jisho_tab import make_jisho_tab
from .hypertts_tab import make_hypertts_tab
from .backup_tab import make_backup_tab
from .help_tab import make_help_tab
from ...config import ConfigHolder
from ...domain.errors import JapaneseMiningError


def make_show_settings(
    config_holder: ConfigHolder,
    save_config_fn,
    collection_service,
    deepl_service,
    backup_service=None,
):
    def show_settings():
        """Show a dialog for configuring the JapaneseMining add-on."""
        config = config_holder.config
        dialog = QDialog(mw)
        dialog.setWindowTitle("JapaneseMining Settings")
        dialog.resize(780, 640)
        dialog.setMinimumSize(700, 480)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(10)

        tabs = QTabWidget()
        apply_fns = []

        # Forward reference so RTK can jump to Help → RTK
        help_tab_widget = None
        help_tab_index = -1
        rtk_tab_widget = None

        def goto_rtk_help():
            if help_tab_widget is not None and help_tab_index >= 0:
                tabs.setCurrentIndex(help_tab_index)
                help_tab_widget.goto_rtk()

        def refresh_rtk_mapping_ui():
            """Pull current config_holder mapping into the RTK tab widgets."""
            if rtk_tab_widget is not None and hasattr(
                rtk_tab_widget, "load_mapping_from_config"
            ):
                rtk_tab_widget.load_mapping_from_config()

        # --- build tabs ---
        # General
        tab, title, apply_fn = make_general_tab(
            config_holder, collection_service, save_config_fn
        )
        tabs.addTab(tab, title)
        apply_fns.append(apply_fn)

        # RTK
        rtk_tab_widget, title, apply_fn = make_rtk_tab(
            config_holder,
            collection_service,
            save_config_fn,
            on_goto_rtk_help=goto_rtk_help,
        )
        tabs.addTab(rtk_tab_widget, title)
        apply_fns.append(apply_fn)

        # Translate
        tab, title, apply_fn = make_translate_tab(
            config_holder, deepl_service, save_config_fn
        )
        tabs.addTab(tab, title)
        apply_fns.append(apply_fn)

        # Jisho
        tab, title, apply_fn = make_jisho_tab(config_holder, save_config_fn)
        tabs.addTab(tab, title)
        apply_fns.append(apply_fn)

        # HyperTTS
        tab, title, apply_fn = make_hypertts_tab(config_holder, save_config_fn)
        tabs.addTab(tab, title)
        apply_fns.append(apply_fn)

        # Backup (optional until service is wired)
        if backup_service is not None:
            tab, title, apply_fn = make_backup_tab(
                config_holder,
                backup_service,
                save_config_fn,
                on_rtk_mapping_updated=refresh_rtk_mapping_ui,
            )
            tabs.addTab(tab, title)
            apply_fns.append(apply_fn)

        # Help (last)
        help_tab_widget, title, apply_fn = make_help_tab(config_holder, save_config_fn)
        help_tab_index = tabs.addTab(help_tab_widget, title)
        apply_fns.append(apply_fn)

        main_layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        main_layout.addWidget(buttons)

        def save_and_close():
            try:
                for apply_fn in apply_fns:
                    apply_fn(config)
                save_config_fn(config)
                config_holder.config = config
            except JapaneseMiningError as e:
                showWarning(e.full_message(), parent=dialog, title="JapaneseMining")
                return

            if config.use_jisho:
                from ...jisho_adapter import to_ajc_runtime_config
                from ...AJC.runtime.config_holder import set_runtime_config

                set_runtime_config(to_ajc_runtime_config(config))

            dialog.accept()

        buttons.accepted.connect(save_and_close)
        buttons.rejected.connect(dialog.reject)

        dialog.exec()

    return show_settings
