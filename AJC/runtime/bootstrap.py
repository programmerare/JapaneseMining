# -*- coding: utf-8 -*-
"""Bootstrap wiring for Anki Jisho Connect."""

from aqt import mw
from aqt.gui_hooks import (
    editor_did_init_buttons,
    editor_did_load_note,
    editor_will_load_note,
    profile_did_open,
    theme_did_change,
    webview_did_receive_js_message,
    webview_will_set_content,
)
from dataclasses import asdict

from .constants import set_language
from .integration.editor_hooks import (
    ROOT_MODULE_NAME,
    add_jisho_editor_button,
    install_editor_bridge_refresh,
    load_editor_header_assets,
    on_editor_did_load_note,
    on_editor_js_message,
    on_editor_will_load_note,
    on_theme_changed,
    show_results_dialog,
)
from .integration.menu_actions import setup_menu_action, show_welcome_if_needed
from .jisho_client import load_config
from .logger import logger


_INITIALIZED = False


def initialize_ajc(cfg) -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    logger.info("Anki Jisho Connect loaded")

    config = asdict(cfg)
    set_language(config.get("language", "en"))
    mw.addonManager.setWebExports(
        ROOT_MODULE_NAME,
        r"(assets/web/.*\.(js|css)|assets/icons/jisho_icon\.(png|svg))",
    )

    def helper_add_jisho_editor_button(buttons, editor):
        return add_jisho_editor_button(config, buttons, editor)

    def helper_on_editor_js_message(handled, message, context):
        return on_editor_js_message(config, handled, message, context)

    def helper_on_editor_will_load_note(js, note, editor):
        return on_editor_will_load_note(config, js, note, editor)

    def helper_on_editor_did_load_note(editor):
        return on_editor_did_load_note(config, editor)

    def helper_show_welcome_if_needed():
        return show_welcome_if_needed(config)

    editor_did_init_buttons.append(helper_add_jisho_editor_button)
    theme_did_change.append(on_theme_changed)
    webview_will_set_content.append(load_editor_header_assets)
    webview_did_receive_js_message.append(helper_on_editor_js_message)
    editor_will_load_note.append(helper_on_editor_will_load_note)
    editor_did_load_note.append(helper_on_editor_did_load_note)
    install_editor_bridge_refresh(config)
    setup_menu_action()
    profile_did_open.append(helper_show_welcome_if_needed)
    _INITIALIZED = True


__all__ = [
    "initialize_ajc",
    "show_results_dialog",
]
