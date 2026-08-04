# -*- coding: utf-8 -*-
"""Editor/webview integration hooks for Anki Jisho Connect."""

from __future__ import annotations

import json
from anki.hooks import wrap
from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.qt import QAction, QKeySequence, Qt, QThread, QTimer
from aqt.utils import showInfo, showWarning
from aqt.webview import WebContent

from ..constants import _
from ..field_processor import apply_mappings_and_fill
from ..icon_utils import get_icon_path
from ..jisho_client import JishoFetchWorker
from ..logger import logger
from ..text_utils import clean_search_term
from ..ui.results_dialog import ResultsDialog
from . import state


HEADER_BUTTON_STATE_CMD = "ajc_jisho_header:get_state"
HEADER_BUTTON_OPEN_PREFIX = "ajc_jisho_header:open:"
TOOLBAR_BUTTON_CMD = "ajc_jisho_connect"
TOOLBAR_LABEL = "J"
ASSET_REV = "20260314c"
ROOT_MODULE_NAME = __name__
_BRIDGE_REFRESH_INSTALLED = False
TOOLBAR_BUTTON_STYLE = (
    "display:inline-flex;"
    "align-items:center;"
    "justify-content:center;"
    "width:20px;"
    "height:20px;"
    "min-width:20px;"
    "min-height:20px;"
    "margin-inline-start:4px;"
    "padding:0;"
    "border:1px solid #005ecb;"
    "border-radius:999px;"
    "background:#007aff;"
    "color:#ffffff;"
    "font-size:10px;"
    "font-weight:800;"
    "line-height:1;"
    "box-sizing:border-box;"
    "box-shadow:0 1px 2px rgba(0,0,0,.22);"
    "appearance:none;"
    "-webkit-appearance:none;"
    "background-image:none;"
    "text-decoration:none;"
)


def _editor_button_position(config) -> str:
    value = str(config.get("editor_button_position", "") or "").strip().lower()
    if value in {"toolbar", "field_label", "both"}:
        return value
    return "field_label" if config else "toolbar"


def _uses_toolbar_button(config: dict | None = None) -> bool:
    return _editor_button_position(config) in {"toolbar", "both"}


def _uses_header_button(config: dict | None = None) -> bool:
    return _editor_button_position(config) in {"field_label", "both"}


def _style_toolbar_button_html(button_html: str) -> str:
    marker = 'class="anki-addon-button '
    if marker not in button_html:
        return button_html
    return button_html.replace(marker, f'style="{TOOLBAR_BUTTON_STYLE}" {marker}', 1)


def show_results_dialog(config, initial_term: str = "", note=None, editor=None) -> None:
    """Show or reuse results dialog."""
    if state.results_dialog is not None and state.results_dialog.isVisible():
        clean_term = clean_search_term(initial_term, config.get("remove_furigana_search", True))
        state.results_dialog.search_box.setText(clean_term)
        state.results_dialog.perform_search(clean_term)
        state.results_dialog.raise_()
        return

    def on_select(selected_entries_data):
        if note is None:
            showWarning(_("warning_no_active_editor"))
            return
        try:
            apply_mappings_and_fill(note, selected_entries_data, config)
            refresh_editor(editor, note)
        except Exception as exc:
            logger.exception("Error filling fields")
            showWarning(f"Error filling fields: {str(exc)}")

    state.results_dialog = ResultsDialog(
        config,
        clean_search_term(initial_term, config.get("remove_furigana_search", True)),
        on_select,
    )
    state.results_dialog.show()


def addon_web_url(file_name: str) -> str:
    addon_package = mw.addonManager.addonFromModule(ROOT_MODULE_NAME) or ROOT_MODULE_NAME
    return f"/_addons/{addon_package}/assets/web/{file_name}"


def resolve_search_field_ord(config, editor: Editor) -> int:
    if not editor or not getattr(editor, "note", None):
        return -1
    search_field = config.get("search_field", "")
    if not search_field:
        return -1
    try:
        field_names = list(editor.note.keys())
    except Exception:
        logger.exception("Could not read note field names for search field resolution")
        return -1
    try:
        return field_names.index(search_field)
    except ValueError:
        return -1


def build_header_button_state(config, editor: Editor) -> dict:
    state_payload = {
        "search_ord": -1,
        "search_field": "",
        "has_search_term": False,
    }
    if not editor or not getattr(editor, "note", None):
        return state_payload
    if not _uses_header_button(config):
        return state_payload
    search_field = str(config.get("search_field", "") or "").strip()
    state_payload["search_field"] = search_field
    search_ord = resolve_search_field_ord(config, editor)
    state_payload["search_ord"] = search_ord
    if search_ord < 0:
        return state_payload
    try:
        value = editor.note.fields[search_ord] if search_ord < len(editor.note.fields) else ""
        clean_value = clean_search_term(value or "", config.get("remove_furigana_search", True))
        state_payload["has_search_term"] = bool(clean_value.strip())
    except Exception:
        logger.exception("Failed to compute header button state")
    return state_payload


def _header_button_eval_script(state_payload: dict) -> str:
    payload_json = json.dumps(state_payload, ensure_ascii=False)
    return f"""
    (function() {{
        var payload = {payload_json};
        if (window.AjcJishoHeaderButton) {{
            window.AjcJishoHeaderButton.load_state(payload);
            return;
        }}

        function normalizeText(value) {{
            return String(value || "").replace(/\\s+/g, " ").trim().toLowerCase();
        }}

        function findLabelContainers() {{
            var containers = document.querySelectorAll(".label-container > span:last-child");
            if (containers && containers.length) {{
                return containers;
            }}
            containers = document.querySelectorAll(".label-container");
            return containers || [];
        }}

        function createButton(ord) {{
            var btn = document.createElement("span");
            btn.className = "ajc-jisho-header-btn";
            btn.setAttribute("data-ajc-jisho-ord", String(ord));
            btn.setAttribute("role", "button");
            btn.setAttribute("tabindex", "0");
            btn.setAttribute("title", "Search Dictionary");
            btn.textContent = "J";
            btn.style.cssText = "display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;min-width:20px;min-height:20px;margin-inline-start:4px;border:1px solid #005ecb;border-radius:999px;background:#007aff;color:#ffffff;font-size:10px;font-weight:800;line-height:1;cursor:pointer;padding:0;flex:0 0 auto;box-sizing:border-box;box-shadow:0 1px 2px rgba(0,0,0,.22);";
            function trigger(ev) {{
                if (ev) {{
                    ev.preventDefault();
                    ev.stopPropagation();
                }}
                if (typeof pycmd === "function") {{
                    pycmd("{HEADER_BUTTON_OPEN_PREFIX}" + ord);
                }}
            }}
            btn.addEventListener("click", trigger);
            btn.addEventListener("keydown", function (ev) {{
                if (ev.key === "Enter" || ev.key === " ") {{
                    trigger(ev);
                }}
            }});
            return btn;
        }}

        var labelContainers = findLabelContainers();
        if (!labelContainers || !labelContainers.length) {{
            return;
        }}

        var targetIndex = Number(payload.search_ord);
        var wantedField = normalizeText(payload.search_field);
        if (wantedField) {{
            for (var idx = 0; idx < labelContainers.length; idx++) {{
                var txt = normalizeText(labelContainers[idx].textContent);
                if (txt === wantedField || txt.indexOf(wantedField) !== -1) {{
                    targetIndex = idx;
                    break;
                }}
            }}
        }}

        for (var i = 0; i < labelContainers.length; i++) {{
            var container = labelContainers[i];
            var btn = container.querySelector('.ajc-jisho-header-btn[data-ajc-jisho-ord="' + i + '"]');
            if (!btn) {{
                btn = createButton(i);
                container.prepend(btn);
            }}
            btn.hidden = i !== targetIndex;
            btn.style.opacity = payload.has_search_term ? "1" : "0.82";
        }}
    }})();
    """


def load_editor_header_assets(web_content: WebContent, context) -> None:
    if not isinstance(context, Editor):
        return
    js_url = f"{addon_web_url('jisho_header_button.js')}?v={ASSET_REV}"
    css_url = f"{addon_web_url('jisho_header_button.css')}?v={ASSET_REV}"
    if js_url not in web_content.js:
        web_content.js.append(js_url)
    if css_url not in web_content.css:
        web_content.css.append(css_url)


def on_editor_js_message(config, handled, message, context):
    if not isinstance(context, Editor):
        return handled
    if message == HEADER_BUTTON_STATE_CMD:
        return True, build_header_button_state(config, context)
    if isinstance(message, str) and message.startswith(HEADER_BUTTON_OPEN_PREFIX):
        handle_jisho_lookup(config, context)
        return True, None
    return handled


def add_jisho_editor_button(config, buttons, editor):
    """Setup editor integrations and optional toolbar button."""
    register_editor_shortcuts(config, editor)
    if not _uses_toolbar_button(config):
        return buttons
    shortcut = str(config.get("open_shortcut", "Alt+J") or "Alt+J")
    try:
        btn = editor.addButton(
            icon=None,
            cmd=TOOLBAR_BUTTON_CMD,
            tip=f"{_('editor_button_tooltip')} ({shortcut})" if shortcut else _("editor_button_tooltip"),
            func=lambda ed=editor: handle_jisho_lookup(config, ed),
            label=TOOLBAR_LABEL,
            keys="",
        )
        btn = _style_toolbar_button_html(btn)
        buttons.append(btn)
    except Exception:
        logger.exception("Failed to add Anki Jisho Connect toolbar button")
    return buttons


def handle_jisho_lookup(config, editor) -> None:
    if not editor or not getattr(editor, "note", None):
        showWarning(_("warning_no_active_editor"))
        return
    note = editor.note
    search_field = config.get("search_field", "N/A")
    initial_term = note[search_field] if search_field in note else ""
    show_results_dialog(config, initial_term, note, editor)


def register_editor_shortcuts(config, editor) -> None:
    if hasattr(editor, "_ajc_actions"):
        return
    editor._ajc_actions = []
    open_shortcut = config.get("open_shortcut", "Alt+J")
    quick_shortcut = config.get("quick_fill_shortcut", "Ctrl+Alt+J")
    target = get_shortcut_target(editor)

    add_editor_action(target, editor, open_shortcut, lambda: handle_jisho_lookup(config, editor))
    add_editor_action(target, editor, quick_shortcut, lambda: handle_quick_fill(config, editor))


def on_editor_will_load_note(config, js: str, note: Note, editor: Editor) -> str:
    if not isinstance(editor, Editor) or note is None:
        return js
    return js + ";" + _header_button_eval_script(build_header_button_state(config, editor))


def refresh_header_button_state(config, editor: Editor) -> None:
    if not isinstance(editor, Editor) or not getattr(editor, "web", None):
        return
    try:
        editor.web.eval(_header_button_eval_script(build_header_button_state(config, editor)))
    except Exception:
        logger.exception("Failed to refresh Anki Jisho Connect field-label button")


def on_editor_did_load_note(config, editor: Editor) -> None:
    if not isinstance(editor, Editor):
        return
    refresh_header_button_state(config, editor)
    try:
        QTimer.singleShot(60, lambda ed=editor: refresh_header_button_state(config, ed))
    except Exception:
        pass


def install_editor_bridge_refresh(config) -> None:
    global _BRIDGE_REFRESH_INSTALLED
    if not hasattr(Editor, "onBridgeCmd"):
        return
    if _BRIDGE_REFRESH_INSTALLED or getattr(Editor, "_ajc_jisho_bridge_refresh_installed", False):
        return

    def _on_bridge_cmd_wrapper(self: Editor, cmd: str):
        if isinstance(cmd, str) and cmd.startswith("key:"):
            refresh_header_button_state(config, self)

    Editor.onBridgeCmd = wrap(Editor.onBridgeCmd, _on_bridge_cmd_wrapper, "before")
    setattr(Editor, "_ajc_jisho_bridge_refresh_installed", True)
    _BRIDGE_REFRESH_INSTALLED = True


def get_shortcut_target(editor):
    parent = getattr(editor, "parentWindow", None)
    if callable(parent):
        parent = parent()
    return parent or getattr(editor, "widget", None) or mw


def add_editor_action(target, editor, shortcut: str, callback) -> None:
    """Attach a QAction shortcut to the editor widget."""
    if not shortcut or target is None:
        return
    try:
        action = QAction(target)
        action.setShortcut(QKeySequence(shortcut))
        action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        action.triggered.connect(callback)
        target.addAction(action)
        editor._ajc_actions.append(action)
    except Exception:
        logger.exception("Error adding editor action")


def handle_quick_fill(config,editor) -> None:
    if not editor or not getattr(editor, "note", None):
        showWarning(_("warning_no_active_editor"))
        return
    note = editor.note
    if not config.get("mappings"):
        showWarning(_("warning_no_mappings"))
        return
    search_field = config.get("search_field", "N/A")
    initial_term = note[search_field] if search_field in note else ""
    initial_term = clean_search_term(initial_term, config.get("remove_furigana_search", True))
    if not initial_term:
        showWarning(_("warning_no_search_term"))
        return

    thread = QThread()
    worker = JishoFetchWorker(initial_term)
    worker.moveToThread(thread)
    state.quick_fill_jobs.append((thread, worker))

    def cleanup():
        try:
            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()
        finally:
            if (thread, worker) in state.quick_fill_jobs:
                state.quick_fill_jobs.remove((thread, worker))

    def on_finished(entries: list):
        try:
            if not entries:
                showWarning(_("no_results").format(term=initial_term))
                return
            entry = entries[0]
            senses = entry.get("senses", [])
            if not senses:
                showWarning(_("no_results").format(term=initial_term))
                return
            mode = config.get("quick_fill_mode", "all")
            selected_senses = senses[:1] if mode == "first" else senses
            entries_data = [{
                "entry_data": entry,
                "selected_senses": selected_senses,
                "selected_other_forms": [],
            }]
            apply_mappings_and_fill(note, entries_data, config)
            refresh_editor(editor, note)
            if config.get("show_quick_fill_success", True):
                showInfo(_("info_fields_filled"))
        except Exception as exc:
            logger.exception("Error filling fields")
            showWarning(f"Error filling fields: {str(exc)}")
        finally:
            cleanup()

    def on_error(err_msg: str):
        logger.error("Error in search: %s", err_msg)
        showWarning(f"Error in search: {err_msg}")
        cleanup()

    worker.finished.connect(on_finished)
    worker.error.connect(on_error)
    thread.started.connect(worker.run)
    thread.start()


def refresh_editor(editor, note) -> None:
    """Reload the editor view after filling fields."""
    try:
        if editor and getattr(editor, "note", None) == note:
            editor.loadNote()
            return
    except Exception:
        logger.exception("Error refreshing editor")
    try:
        if hasattr(mw, "editor") and mw.editor and mw.editor.note == note:
            mw.editor.loadNote()
    except Exception:
        logger.exception("Error refreshing editor")


def on_theme_changed() -> None:
    if state.results_dialog is not None and state.results_dialog.isVisible():
        state.results_dialog.restyle()
