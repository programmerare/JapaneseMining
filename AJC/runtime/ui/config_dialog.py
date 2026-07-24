# -*- coding: utf-8 -*-
"""
Configuration Dialog for Anki Jisho Connect
Handles add-on settings and field mappings
"""

import json
from typing import List, Any, Dict

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGridLayout, QCheckBox, QScrollArea, QWidget, QSizePolicy,
    QFrame, QLineEdit, QTabWidget, QInputDialog, QMessageBox, Qt
)
from PyQt6.QtCore import QTimer, QEvent, QSize
from PyQt6.QtGui import QIcon

from ..constants import _, TRANSLATIONS, set_language as const_set_language, DEFAULT_CONFIG, JISHO_MAPPING_OPTIONS
from ..jisho_client import load_full_config, save_full_config
from ..icon_utils import get_icon_path, get_profile_rename_icon
from ..ui_common import (
    apply_base_stylesheet,
    apply_jisho_connect_settings_stylesheet,
    apply_toolkit_combobox_style,
)

class HoverableLabel(QLabel):
    """QLabel with hover effect for tooltips."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.normal_style = ""
        self.hover_style = ""
        self.setCursor(Qt.CursorShape.WhatsThisCursor)

    def set_underline_colors(self, normal_color: str, hover_color: str):
        """Set subtle underline that intensifies on hover."""
        self.normal_style = self._build_style(normal_color)
        self.hover_style = self._build_style(hover_color)
        self.setStyleSheet(self.normal_style)

    def _build_style(self, underline_color: str) -> str:
        return (
            "margin-left: 0px;"
            "padding-left: 0px;"
            f"border-bottom: 1px solid {underline_color};"
            "padding-bottom: 1px;"
        )
    
    def showEvent(self, event):
        """Set normal style when showing."""
        self.setStyleSheet(self.normal_style)
        super().showEvent(event)
    
    def enterEvent(self, event: QEvent):
        """Change style on hover."""
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)
    
    def leaveEvent(self, event: QEvent):
        """Restore style when leaving."""
        self.setStyleSheet(self.normal_style)
        super().leaveEvent(event)


class ShortcutCaptureDialog(QDialog):
    """Dialog to capture keyboard shortcut."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcut = ""
        self.setWindowTitle(_("shortcut_dialog_title"))
        apply_base_stylesheet(self)
        self.setMinimumSize(550, 130)
        self.resize(550, 130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        card = QFrame(self)
        card.setObjectName("ToolkitCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        self.prompt_label = QLabel(_("shortcut_dialog_prompt"))
        self.prompt_label.setWordWrap(True)
        self.pressed_keys_label = QLabel(_("shortcut_dialog_pressed_keys"))
        self.pressed_keys_value = QLineEdit()
        self.pressed_keys_value.setReadOnly(True)
        self.pressed_keys_value.setPlaceholderText(_("shortcut_dialog_pressed_placeholder"))
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b00020; font-weight: 700;")

        card_layout.addWidget(self.prompt_label)
        card_layout.addWidget(self.pressed_keys_label)
        card_layout.addWidget(self.pressed_keys_value)
        card_layout.addWidget(self.error_label)
        layout.addWidget(card)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return

        key = event.key()
        mods = event.modifiers()
        self.error_label.setText("")
        self._update_pressed_keys_field(mods, key)

        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt):
            return

        if mods & Qt.KeyboardModifier.MetaModifier:
            self._invalid()
            return

        modifiers = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("Ctrl")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("Shift")
        if mods & Qt.KeyboardModifier.AltModifier:
            modifiers.append("Alt")

        if not modifiers:
            self._invalid()
            return

        key_text = ""
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            key_text = chr(key)
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            key_text = chr(key)

        if not key_text:
            self._invalid()
            return

        self.shortcut = "+".join(modifiers + [key_text])
        self.accept()

    def _update_pressed_keys_field(self, mods, key):
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")

        key_text = ""
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            key_text = chr(key)
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            key_text = chr(key)

        if key_text:
            parts.append(key_text)

        self.pressed_keys_value.setText("+".join(parts))

    def _invalid(self):
        self.error_label.setText(_("shortcut_dialog_invalid"))


class ConfigDialog(QDialog):
    """Dialog for configuring the add-on."""
    
    def __init__(self):
        super().__init__()
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setObjectName("JishoConnectSettingsDialog")
        self._window_title_base = _("settings_title")
        
        self.config = load_full_config()
        self.resize(500, 650)
        self.setMinimumWidth(500)
        self.setMinimumHeight(650)
        self.setMaximumWidth(600)
        self.setMaximumHeight(700)
        self._refresh_window_dimension_title()
        self.mapping_rows_data = [] 
        self._mapping_rebuild_pending = False
        self._pending_cursor_target = None
        self._is_closing = False
        self._shutdown_prepared = False
        self._profile_loading = False
        self._current_profile_name = str(self.config.get("active_profile", "Default") or "Default")
        self._last_valid_card_type = ""
        self._last_valid_target_deck = ""
        self.open_shortcut_value = "Alt+J"
        self.quick_fill_shortcut_value = "Ctrl+Alt+J"

        self._setup_ui()
        self.restyle()
        self._connect_signals()
        self._load_initial_data()

    def _refresh_window_dimension_title(self) -> None:
        try:
            self.setWindowTitle(
                f"{self._window_title_base} [{self.width()}x{self.height()}]"
            )
        except Exception:
            pass

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._refresh_window_dimension_title()
        return super().resizeEvent(event)

    def showEvent(self, event) -> None:  # type: ignore[override]
        # Settings dialog instance is reused; clear close guards when reopening.
        self._is_closing = False
        self._shutdown_prepared = False
        return super().showEvent(event)

    def _prepare_for_close(self) -> None:
        if self._shutdown_prepared:
            return
        self._shutdown_prepared = True
        self._is_closing = True
        self._mapping_rebuild_pending = False
        self._pending_cursor_target = None
        try:
            for combo in self.findChildren(QComboBox):
                try:
                    combo.hidePopup()
                except Exception:
                    pass
        except Exception:
            pass

    def _profile_defaults(self) -> Dict[str, Any]:
        return {
            "card_type": DEFAULT_CONFIG.get("card_type", ""),
            "target_deck": DEFAULT_CONFIG.get("target_deck", ""),
            "search_field": DEFAULT_CONFIG.get("search_field", ""),
            "mappings": list(DEFAULT_CONFIG.get("mappings", [])),
            "fill_mode": DEFAULT_CONFIG.get("fill_mode", "replace"),
            "multi_meaning_format": DEFAULT_CONFIG.get("multi_meaning_format", "numbered"),
            "multi_word_format": DEFAULT_CONFIG.get("multi_word_format", "basic"),
            "disable_multi_word_warning": DEFAULT_CONFIG.get("disable_multi_word_warning", False),
            "remove_pos_ending": DEFAULT_CONFIG.get("remove_pos_ending", True),
            "remove_furigana_search": DEFAULT_CONFIG.get("remove_furigana_search", True),
            "show_quick_fill_success": DEFAULT_CONFIG.get("show_quick_fill_success", True),
            "open_shortcut": DEFAULT_CONFIG.get("open_shortcut", "Alt+J"),
            "quick_fill_shortcut": DEFAULT_CONFIG.get("quick_fill_shortcut", "Ctrl+Alt+J"),
            "quick_fill_mode": DEFAULT_CONFIG.get("quick_fill_mode", "all"),
        }

    def _profiles(self) -> Dict[str, Dict[str, Any]]:
        profiles = self.config.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            profiles = {"Default": self._profile_defaults()}
            self.config["profiles"] = profiles
            self.config["active_profile"] = "Default"
        return profiles

    def _current_profile(self) -> Dict[str, Any]:
        profiles = self._profiles()
        name = str(self._current_profile_name or self.config.get("active_profile", "Default") or "Default")
        if name not in profiles:
            name = next(iter(profiles.keys()))
            self._current_profile_name = name
            self.config["active_profile"] = name
        payload = profiles.get(name) or {}
        defaults = self._profile_defaults()
        merged = defaults.copy()
        merged.update(payload if isinstance(payload, dict) else {})
        merged["mappings"] = [m for m in (merged.get("mappings") or []) if isinstance(m, dict)]
        return merged

    def _set_current_profile_payload(self, payload: Dict[str, Any]) -> None:
        profiles = self._profiles()
        name = str(self._current_profile_name or self.config.get("active_profile", "Default") or "Default")
        profiles[name] = payload
        self.config["profiles"] = profiles
        self.config["active_profile"] = name

    def _next_profile_name(self, base_name: str) -> str:
        existing = {str(k) for k in self._profiles().keys()}
        if base_name not in existing:
            return base_name
        idx = 2
        while True:
            candidate = f"{base_name} {idx}"
            if candidate not in existing:
                return candidate
            idx += 1

    def _load_deck_names(self) -> list[str]:
        names: list[str] = []
        try:
            items = mw.col.decks.all_names_and_ids() or []
            for item in items:
                if isinstance(item, dict):
                    name = item.get("name")
                else:
                    name = getattr(item, "name", None)
                if name:
                    names.append(str(name))
        except Exception:
            pass
        if not names:
            try:
                names = [str(n) for n in (mw.col.decks.all_names() or []) if n]
            except Exception:
                names = []
        return sorted(set(names), key=lambda x: x.lower())

    def _mapping_options(self) -> list[str]:
        return list(JISHO_MAPPING_OPTIONS)

    def _mapping_allowed_keys(self) -> set[str]:
        return {opt for opt in self._mapping_options() if opt}

    def _mapping_tooltip(self) -> str:
        return _("field_mapping_tooltip")

    def _refresh_mapping_tooltip(self) -> None:
        try:
            # Tooltip should appear only when hovering the Add Mapping button.
            self.mapping_group.setToolTip("")
            self.add_btn.setToolTip(self._mapping_tooltip())
        except Exception:
            pass

    def _find_duplicate_combo_profile(self, card_type: str, target_deck: str) -> str:
        card_type = (card_type or "").strip()
        target_deck = (target_deck or "").strip()
        if not card_type or not target_deck:
            return ""
        current_name = str(self._current_profile_name or "")
        for name, payload in self._profiles().items():
            if name == current_name or not isinstance(payload, dict):
                continue
            if (str(payload.get("card_type") or "").strip() == card_type and
                    str(payload.get("target_deck") or "").strip() == target_deck):
                return name
        return ""

    def _refresh_profile_dropdown(self, select_name: str | None = None) -> None:
        profiles = self._profiles()
        names = list(profiles.keys())
        if not names:
            names = ["Default"]
            profiles["Default"] = self._profile_defaults()
        target = select_name or str(self._current_profile_name or self.config.get("active_profile", names[0]) or names[0])
        self.profile_dropdown.blockSignals(True)
        self.profile_dropdown.clear()
        for name in names:
            self.profile_dropdown.addItem(name, name)
        idx = self.profile_dropdown.findData(target)
        self.profile_dropdown.setCurrentIndex(idx if idx >= 0 else 0)
        self.profile_dropdown.blockSignals(False)
        selected = self.profile_dropdown.currentData()
        self._current_profile_name = str(selected or names[0])
        self.config["active_profile"] = self._current_profile_name

    def _apply_profile_to_ui(self, profile_name: str) -> None:
        profiles = self._profiles()
        payload = profiles.get(profile_name) or self._profile_defaults()
        self._profile_loading = True
        try:
            self.card_type_dropdown.setCurrentText(str(payload.get("card_type", "") or ""))
            self.target_deck_dropdown.setCurrentText(str(payload.get("target_deck", "") or ""))
            self.update_fields()
            saved_search = str(payload.get("search_field", "") or "")
            if saved_search and saved_search in self.current_field_names:
                self.search_field_dropdown.setCurrentText(saved_search)
            else:
                self.search_field_dropdown.setCurrentIndex(0 if self.search_field_dropdown.count() else -1)
            self._refresh_mapping_tooltip()

            self.fill_mode_dropdown.setCurrentIndex(1 if str(payload.get("fill_mode", "replace")) == "append" else 0)
            format_map = {"pipe_merged": 0, "numbered": 1, "semicolon_merged": 2}
            self.multi_meaning_format_dropdown.setCurrentIndex(format_map.get(str(payload.get("multi_meaning_format", "numbered")), 1))
            self._update_multi_word_dropdown()
            wanted_multi_word = str(payload.get("multi_word_format", "basic"))
            for i in range(self.multi_word_format_dropdown.count()):
                if self.multi_word_format_dropdown.itemData(i) == wanted_multi_word:
                    self.multi_word_format_dropdown.setCurrentIndex(i)
                    break

            self.open_shortcut_value = str(payload.get("open_shortcut", "Alt+J") or "Alt+J")
            self.quick_fill_shortcut_value = str(payload.get("quick_fill_shortcut", "Ctrl+Alt+J") or "Ctrl+Alt+J")
            self._refresh_shortcut_buttons()

            quick_fill_mode = str(payload.get("quick_fill_mode", "all") or "all")
            for i in range(self.quick_fill_mode_dropdown.count()):
                if self.quick_fill_mode_dropdown.itemData(i) == quick_fill_mode:
                    self.quick_fill_mode_dropdown.setCurrentIndex(i)
                    break

            self.warn_checkbox.setChecked(bool(payload.get("disable_multi_word_warning", False)))
            self.remove_pos_checkbox.setChecked(bool(payload.get("remove_pos_ending", True)))
            self.remove_furigana_checkbox.setChecked(bool(payload.get("remove_furigana_search", True)))
            self.disable_quick_fill_success_checkbox.setChecked(
                not bool(payload.get("show_quick_fill_success", True))
            )

            mappings = payload.get("mappings", [])
            allowed_keys = self._mapping_allowed_keys()
            self.mapping_rows_data = [
                row
                for row in (mappings if isinstance(mappings, list) else [])
                if isinstance(row, dict) and str(row.get("jisho", "") or "") in allowed_keys
            ]
            self._rebuild_mapping_grid()

            self._last_valid_card_type = self.card_type_dropdown.currentText()
            self._last_valid_target_deck = self.target_deck_dropdown.currentText()
        finally:
            self._profile_loading = False

    def _persist_current_profile_from_ui(self) -> None:
        if self._profile_loading:
            return
        format_values = ["pipe_merged", "numbered", "semicolon_merged"]
        fmt_idx = self.multi_meaning_format_dropdown.currentIndex()
        if fmt_idx < 0 or fmt_idx >= len(format_values):
            fmt_idx = 1
        payload = self._current_profile()
        payload.update(
            {
                "card_type": self.card_type_dropdown.currentText(),
                "target_deck": self.target_deck_dropdown.currentText(),
                "search_field": self.search_field_dropdown.currentText(),
                "mappings": list(self.mapping_rows_data),
                "fill_mode": "append" if self.fill_mode_dropdown.currentIndex() == 1 else "replace",
                "multi_meaning_format": format_values[fmt_idx],
                "multi_word_format": self.multi_word_format_dropdown.currentData() or "basic",
                "disable_multi_word_warning": self.warn_checkbox.isChecked(),
                "remove_pos_ending": self.remove_pos_checkbox.isChecked(),
                "remove_furigana_search": self.remove_furigana_checkbox.isChecked(),
                "show_quick_fill_success": not self.disable_quick_fill_success_checkbox.isChecked(),
                "open_shortcut": self.open_shortcut_value,
                "quick_fill_shortcut": self.quick_fill_shortcut_value,
                "quick_fill_mode": self.quick_fill_mode_dropdown.currentData() or "all",
            }
        )
        self._set_current_profile_payload(payload)

    def _on_profile_changed(self, _index: int = 0) -> None:
        if self._profile_loading:
            return
        try:
            self._persist_current_profile_from_ui()
        except Exception:
            pass
        selected_name = str(self.profile_dropdown.currentData() or "").strip()
        if not selected_name:
            return
        self._current_profile_name = selected_name
        self.config["active_profile"] = selected_name
        self._apply_profile_to_ui(selected_name)

    def _on_profile_add(self) -> None:
        base_name = str(_("profile_add_default_name") or "Profile").strip() or "Profile"
        suggested = self._next_profile_name(base_name)
        name, ok = QInputDialog.getText(self, _("profile_add"), _("profile_name_prompt_add"), text=suggested)
        if not ok:
            return
        name = str(name or "").strip()
        if not name:
            QMessageBox.warning(self, _("profile_add"), _("profile_error_empty"))
            return
        profiles = self._profiles()
        if name in profiles:
            QMessageBox.warning(self, _("profile_add"), _("profile_error_exists"))
            return
        self._persist_current_profile_from_ui()
        profiles[name] = self._profile_defaults()
        self.config["profiles"] = profiles
        self._refresh_profile_dropdown(select_name=name)
        self._apply_profile_to_ui(name)

    def _on_profile_rename(self) -> None:
        old_name = str(self._current_profile_name or "").strip()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, _("profile_rename"), _("profile_name_prompt_rename"), text=old_name)
        if not ok:
            return
        new_name = str(new_name or "").strip()
        if not new_name:
            QMessageBox.warning(self, _("profile_rename"), _("profile_error_empty"))
            return
        if new_name == old_name:
            return
        profiles = self._profiles()
        if new_name in profiles:
            QMessageBox.warning(self, _("profile_rename"), _("profile_error_exists"))
            return
        self._persist_current_profile_from_ui()
        payload = profiles.pop(old_name, self._profile_defaults())
        profiles[new_name] = payload
        self.config["profiles"] = profiles
        self._current_profile_name = new_name
        self.config["active_profile"] = new_name
        self._refresh_profile_dropdown(select_name=new_name)

    def _on_profile_delete(self) -> None:
        profiles = self._profiles()
        if len(profiles) <= 1:
            QMessageBox.warning(self, _("profile_delete"), _("profile_error_last"))
            return
        current_name = str(self._current_profile_name or "").strip()
        if not current_name or current_name not in profiles:
            return
        answer = QMessageBox.question(
            self,
            _("profile_delete"),
            _("profile_delete_confirm").format(name=current_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        profiles.pop(current_name, None)
        self.config["profiles"] = profiles
        next_name = next(iter(profiles.keys()))
        self._current_profile_name = next_name
        self.config["active_profile"] = next_name
        self._refresh_profile_dropdown(select_name=next_name)
        self._apply_profile_to_ui(next_name)

    def _on_card_type_changed(self, _index: int = 0) -> None:
        if self._profile_loading:
            self.update_fields()
            return
        candidate_card = self.card_type_dropdown.currentText()
        candidate_deck = self.target_deck_dropdown.currentText()
        conflict = self._find_duplicate_combo_profile(candidate_card, candidate_deck)
        if conflict:
            from aqt.utils import showWarning
            showWarning(_("warning_profile_duplicate_combo").format(profile=conflict))
            self._profile_loading = True
            try:
                self.card_type_dropdown.setCurrentText(self._last_valid_card_type)
            finally:
                self._profile_loading = False
            self.update_fields()
            return
        self._last_valid_card_type = candidate_card
        self.update_fields()

    def _on_target_deck_changed(self, _index: int = 0) -> None:
        if self._profile_loading:
            return
        candidate_card = self.card_type_dropdown.currentText()
        candidate_deck = self.target_deck_dropdown.currentText()
        conflict = self._find_duplicate_combo_profile(candidate_card, candidate_deck)
        if conflict:
            from aqt.utils import showWarning
            showWarning(_("warning_profile_duplicate_combo").format(profile=conflict))
            self._profile_loading = True
            try:
                self.target_deck_dropdown.setCurrentText(self._last_valid_target_deck)
            finally:
                self._profile_loading = False
            return
        self._last_valid_target_deck = candidate_deck

    def _setup_ui(self):
        """Build the UI once."""
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- Language Selector ---
        lang_layout = QHBoxLayout()
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_layout.setSpacing(8)
        self.lang_label = QLabel(_("ui_language"))
        self.lang_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lang_label.setMinimumWidth(120)
        lang_layout.addWidget(self.lang_label)
        self.lang_dropdown = QComboBox()
        self.lang_dropdown.addItems(["English", "Portuguese"])
        self.lang_map = {0: "en", 1: "pt"}
        lang_layout.addWidget(self.lang_dropdown)
        self.button_position_label = QLabel(_("button_position_label"))
        self.button_position_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.button_position_label.setMinimumWidth(120)
        self.button_position_dropdown = QComboBox()

        # --- Main Settings Group ---
        from aqt.qt import QGroupBox
        self.main_config_group = QGroupBox()
        main_config_layout = QGridLayout(self.main_config_group)
        main_config_layout.setContentsMargins(12, 12, 12, 12)
        main_config_layout.setSpacing(12)
        main_config_layout.setColumnStretch(0, 0)
        main_config_layout.setColumnStretch(1, 1)
        main_config_layout.setColumnMinimumWidth(0, 120)
        
        self.profile_label = QLabel()
        self.profile_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.profile_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.profile_label, 0, 0)
        profile_row = QWidget()
        profile_row_layout = QHBoxLayout(profile_row)
        profile_row_layout.setContentsMargins(0, 0, 0, 0)
        profile_row_layout.setSpacing(8)
        self.profile_dropdown = QComboBox()
        profile_row_layout.addWidget(self.profile_dropdown, 1)
        self.profile_add_btn = QPushButton()
        self.profile_add_btn.setObjectName("ToolkitIconAction")
        self.profile_add_btn.setProperty("toolkit_group", "profile")
        self.profile_add_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        profile_row_layout.addWidget(self.profile_add_btn, 0)
        self.profile_rename_btn = QPushButton()
        self.profile_rename_btn.setObjectName("ToolkitIconAction")
        self.profile_rename_btn.setProperty("toolkit_group", "profile")
        self.profile_rename_btn.setIconSize(QSize(14, 14))
        self.profile_rename_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        profile_row_layout.addWidget(self.profile_rename_btn, 0)
        self.profile_delete_btn = QPushButton()
        self.profile_delete_btn.setObjectName("ToolkitIconAction")
        self.profile_delete_btn.setProperty("toolkit_group", "profile")
        self.profile_delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        profile_row_layout.addWidget(self.profile_delete_btn, 0)
        main_config_layout.addWidget(profile_row, 0, 1)

        self.note_type_label = QLabel()
        self.note_type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.note_type_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.note_type_label, 1, 0)
        self.card_type_dropdown = QComboBox()
        self.card_type_names = sorted(mw.col.models.all_names())
        self.card_type_dropdown.addItems([""] + self.card_type_names)
        main_config_layout.addWidget(self.card_type_dropdown, 1, 1)

        self.target_deck_label = QLabel()
        self.target_deck_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.target_deck_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.target_deck_label, 2, 0)
        self.target_deck_dropdown = QComboBox()
        self.target_deck_dropdown.addItems([""] + self._load_deck_names())
        main_config_layout.addWidget(self.target_deck_dropdown, 2, 1)

        self.search_field_label = QLabel()
        self.search_field_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.search_field_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.search_field_label, 3, 0)
        self.search_field_dropdown = QComboBox()
        main_config_layout.addWidget(self.search_field_dropdown, 3, 1)

        self.fill_mode_label = QLabel()
        self.fill_mode_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.fill_mode_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.fill_mode_label, 4, 0)
        self.fill_mode_dropdown = QComboBox()
        main_config_layout.addWidget(self.fill_mode_dropdown, 4, 1)
        
        self.multi_meaning_format_label = HoverableLabel()
        self.multi_meaning_format_label.setToolTip("Hover to see format examples")
        self.multi_meaning_format_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.multi_meaning_format_label.setContentsMargins(0, 0, 0, 0)
        self.multi_meaning_format_label.setIndent(0)
        main_config_layout.addWidget(self.multi_meaning_format_label, 5, 0)
        self.multi_meaning_format_dropdown = QComboBox()
        main_config_layout.addWidget(self.multi_meaning_format_dropdown, 5, 1)
        
        self.multi_word_format_label = HoverableLabel()
        self.multi_word_format_label.setToolTip(_("multi_word_tooltip"))
        self.multi_word_format_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.multi_word_format_label.setContentsMargins(0, 0, 0, 0)
        self.multi_word_format_label.setIndent(0)
        main_config_layout.addWidget(self.multi_word_format_label, 6, 0)
        self.multi_word_format_dropdown = QComboBox()
        main_config_layout.addWidget(self.multi_word_format_dropdown, 6, 1)

        self.open_shortcut_label = QLabel()
        self.open_shortcut_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.open_shortcut_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.open_shortcut_label, 7, 0)
        self.open_shortcut_button = QPushButton()
        self.open_shortcut_button.setObjectName("ToolkitShortcutButton")
        self.open_shortcut_button.setCursor(Qt.CursorShape.PointingHandCursor)
        main_config_layout.addWidget(self.open_shortcut_button, 7, 1)

        self.quick_fill_shortcut_label = QLabel()
        self.quick_fill_shortcut_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.quick_fill_shortcut_label.setMinimumWidth(120)
        main_config_layout.addWidget(self.quick_fill_shortcut_label, 8, 0)
        self.quick_fill_shortcut_button = QPushButton()
        self.quick_fill_shortcut_button.setObjectName("ToolkitShortcutButton")
        self.quick_fill_shortcut_button.setCursor(Qt.CursorShape.PointingHandCursor)
        main_config_layout.addWidget(self.quick_fill_shortcut_button, 8, 1)

        self.quick_fill_mode_label = QLabel()
        self.quick_fill_mode_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.quick_fill_mode_label.setMinimumWidth(120)
        self.quick_fill_mode_label.setToolTip(_("quick_fill_mode_tooltip"))
        main_config_layout.addWidget(self.quick_fill_mode_label, 9, 0)
        self.quick_fill_mode_dropdown = QComboBox()
        self.quick_fill_mode_dropdown.setToolTip(_("quick_fill_mode_tooltip"))
        main_config_layout.addWidget(self.quick_fill_mode_dropdown, 9, 1)

        self.disable_quick_fill_success_checkbox = QCheckBox()
        main_config_layout.addWidget(self.disable_quick_fill_success_checkbox, 10, 0, 1, 2)
        

        # --- Field Mapping Group ---
        self.mapping_group = QGroupBox()
        self.mapping_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mapping_group_layout = QVBoxLayout(self.mapping_group)
        mapping_group_layout.setContentsMargins(12, 12, 12, 12)
        mapping_group_layout.setSpacing(12)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("ToolkitMappingScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(120)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("ToolkitMappingContent")
        scroll_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.mapping_grid_layout = QGridLayout(scroll_content)
        self.mapping_grid_layout.setContentsMargins(8, 8, 8, 8)
        self.mapping_grid_layout.setHorizontalSpacing(8)
        self.mapping_grid_layout.setVerticalSpacing(8)
        scroll_area.setWidget(scroll_content)
        
        mapping_group_layout.addWidget(scroll_area)

        self.add_btn = QPushButton()
        self.add_btn.setObjectName("ToolkitInlineButton")
        mapping_group_layout.addWidget(self.add_btn)
        

        # --- Additional Options & Save Button ---
        self.warn_checkbox = QCheckBox()
        self.remove_pos_checkbox = QCheckBox()
        self.remove_furigana_checkbox = QCheckBox()
        self.save_button = QPushButton()
        self.save_button.setObjectName("ToolkitSaveButton")
        self.save_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.save_button.setMinimumWidth(148)

        general_tab = QWidget()
        general_tab.setObjectName("JishoConnectSettingsPage")
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(12, 12, 12, 12)
        general_layout.setSpacing(12)
        general_layout.addWidget(self.main_config_group)
        general_layout.addStretch()

        mapping_tab = QWidget()
        mapping_tab.setObjectName("JishoConnectSettingsPage")
        mapping_layout = QVBoxLayout(mapping_tab)
        mapping_layout.setContentsMargins(12, 12, 12, 12)
        mapping_layout.setSpacing(12)
        mapping_layout.addWidget(self.mapping_group, 1)

        advanced_tab = QWidget()
        advanced_tab.setObjectName("JishoConnectSettingsPage")
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setContentsMargins(12, 12, 12, 12)
        advanced_layout.setSpacing(12)

        self.advanced_group = QGroupBox()
        adv_group_layout = QGridLayout(self.advanced_group)
        adv_group_layout.setContentsMargins(12, 12, 12, 12)
        adv_group_layout.setSpacing(12)
        adv_group_layout.setColumnStretch(0, 0)
        adv_group_layout.setColumnStretch(1, 1)
        adv_group_layout.setColumnMinimumWidth(0, 120)
        adv_group_layout.addWidget(self.lang_label, 0, 0)
        adv_group_layout.addWidget(self.lang_dropdown, 0, 1)
        adv_group_layout.addWidget(self.button_position_label, 1, 0)
        adv_group_layout.addWidget(self.button_position_dropdown, 1, 1)
        adv_group_layout.addWidget(self.warn_checkbox, 2, 0, 1, 2)
        adv_group_layout.addWidget(self.remove_pos_checkbox, 3, 0, 1, 2)
        adv_group_layout.addWidget(self.remove_furigana_checkbox, 4, 0, 1, 2)

        advanced_layout.addWidget(self.advanced_group)
        advanced_layout.addStretch()
        self.tabs = QTabWidget()
        self.tabs.addTab(general_tab, _("tab_general"))
        self.tabs.addTab(mapping_tab, _("tab_mapping"))
        self.tabs.addTab(advanced_tab, _("tab_advanced"))
        main_layout.addWidget(self.tabs, 1)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(footer_layout)

        self.scroll_area = scroll_area
        try:
            for combo in self.findChildren(QComboBox):
                apply_toolkit_combobox_style(combo, self._current_style_mode())
        except Exception:
            pass
        self._retranslate_ui()

    def _retranslate_ui(self):
        """Update UI text to current language."""
        self._window_title_base = _("settings_title")
        self._refresh_window_dimension_title()
        self.lang_label.setText(_("ui_language"))
        self.button_position_label.setText(_("button_position_label"))
        self._refresh_button_position_dropdown()
        if self.tabs is not None and self.tabs.count() >= 3:
            self.tabs.setTabText(0, _("tab_general"))
            self.tabs.setTabText(1, _("tab_mapping"))
            self.tabs.setTabText(2, _("tab_advanced"))
        self.advanced_group.setTitle(_("advanced_title"))
        
        self.main_config_group.setTitle(_("main_settings"))
        self.profile_label.setText(_("profile_label"))
        self.profile_add_btn.setToolTip(_("profile_add"))
        self.profile_rename_btn.setToolTip(_("profile_rename"))
        self.profile_delete_btn.setToolTip(_("profile_delete"))
        self.profile_add_btn.setText("+")
        self.profile_rename_btn.setText("")
        self.profile_delete_btn.setText("-")
        self.note_type_label.setText(_("note_type"))
        self.target_deck_label.setText(_("target_deck"))
        self.search_field_label.setText(_("search_field"))
        self.fill_mode_label.setText(_("fill_mode"))
        
        current_fill_mode_index = self.fill_mode_dropdown.currentIndex()
        self.fill_mode_dropdown.clear()
        self.fill_mode_dropdown.addItems([_("fill_mode_replace"), _("fill_mode_append")])
        if current_fill_mode_index != -1:
            self.fill_mode_dropdown.setCurrentIndex(current_fill_mode_index)
        
        self.multi_meaning_format_label.setText(_("multi_meaning_format"))
        current_multi_word_index = self.multi_meaning_format_dropdown.currentIndex()
        self.multi_meaning_format_dropdown.clear()
        self.multi_meaning_format_dropdown.addItem(_("multi_meaning_format_pipe_merged"), "pipe_merged")
        self.multi_meaning_format_dropdown.addItem(_("multi_meaning_format_numbered"), "numbered")
        self.multi_meaning_format_dropdown.addItem(_("multi_meaning_format_semicolon_merged"), "semicolon_merged")
        self._setup_multi_meaning_format_tooltips()
        if current_multi_word_index != -1:
            self.multi_meaning_format_dropdown.setCurrentIndex(current_multi_word_index)
        
        self.multi_word_format_label.setText(_("multi_word_format"))
        self.multi_word_format_label.setToolTip(_("multi_word_tooltip"))
        self._update_multi_word_dropdown()

        self.open_shortcut_label.setText(_("open_shortcut"))
        self.quick_fill_shortcut_label.setText(_("quick_fill_shortcut"))
        self.quick_fill_mode_label.setText(_("quick_fill_mode"))
        self.quick_fill_mode_label.setToolTip(_("quick_fill_mode_tooltip"))
        self.quick_fill_mode_dropdown.setToolTip(_("quick_fill_mode_tooltip"))
        current_quick_fill_mode = self.quick_fill_mode_dropdown.currentIndex()
        self.quick_fill_mode_dropdown.clear()
        self.quick_fill_mode_dropdown.addItem(_("quick_fill_mode_all"), "all")
        self.quick_fill_mode_dropdown.addItem(_("quick_fill_mode_first"), "first")
        if current_quick_fill_mode != -1:
            self.quick_fill_mode_dropdown.setCurrentIndex(current_quick_fill_mode)
        
        self.mapping_group.setTitle(_("field_mapping"))
        self.add_btn.setText(_("add_mapping"))
        self._refresh_mapping_tooltip()
        self.warn_checkbox.setText(_("disable_warning"))
        self.remove_pos_checkbox.setText(_("remove_pos_ending"))
        self.remove_furigana_checkbox.setText(_("remove_furigana_search"))
        self.disable_quick_fill_success_checkbox.setText(_("disable_quick_fill_success"))
        self.save_button.setText(_("save_and_close"))
        self._refresh_shortcut_buttons()

    def _refresh_button_position_dropdown(self) -> None:
        current_value = str(self.button_position_dropdown.currentData() or "")
        self.button_position_dropdown.blockSignals(True)
        self.button_position_dropdown.clear()
        self.button_position_dropdown.addItem(_("button_position_toolbar"), "toolbar")
        self.button_position_dropdown.addItem(_("button_position_field_label"), "field_label")
        self.button_position_dropdown.addItem(_("button_position_both"), "both")
        index = self.button_position_dropdown.findData(current_value)
        self.button_position_dropdown.setCurrentIndex(index if index >= 0 else 0)
        self.button_position_dropdown.blockSignals(False)

    def _current_style_mode(self) -> str:
        return "legacy_and_stable"

    def _language_changed(self, index: int = 0):
        """Called when language is changed."""
        lang_code = self.lang_map.get(self.lang_dropdown.currentIndex(), "en")
        const_set_language(lang_code)
        self._retranslate_ui()

    def restyle(self):
        """Apply/update styles based on theme."""
        from ..constants import LightTheme, DarkTheme
        from aqt.theme import theme_manager
        
        theme = DarkTheme if theme_manager.night_mode else LightTheme
        style_mode = self._current_style_mode()
        try:
            apply_jisho_connect_settings_stylesheet(self)
        except RuntimeError:
            return

        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.profile_rename_btn.setIcon(get_profile_rename_icon(theme.TEXT_PRIMARY))
        self.multi_meaning_format_label.set_underline_colors(theme.TEXT_TERTIARY, theme.TEXT_PRIMARY)
        self.multi_word_format_label.set_underline_colors(theme.TEXT_TERTIARY, theme.TEXT_PRIMARY)
        try:
            for combo in self.findChildren(QComboBox):
                apply_toolkit_combobox_style(combo, style_mode)
        except Exception:
            pass
        self._sync_icon_action_buttons()
        self._rebuild_mapping_grid()

    def _setup_multi_meaning_format_tooltips(self):
        """Setup tooltip for multi-meaning format label."""
        self.multi_meaning_format_label.setToolTip(_("multi_meaning_tooltip"))

    def _update_multi_word_dropdown(self):
        """Update multi-word dropdown based on selected multi-meaning format."""
        from ..constants import MULTI_WORD_COMPATIBILITY
        
        meaning_idx = self.multi_meaning_format_dropdown.currentIndex()
        meaning_keys = ["pipe_merged", "numbered", "semicolon_merged"]
        meaning_key = meaning_keys[meaning_idx] if meaning_idx >= 0 else "numbered"
        
        compatible = MULTI_WORD_COMPATIBILITY.get(meaning_key, {})
        current_fmt = self.multi_word_format_dropdown.currentData()
        
        self.multi_word_format_dropdown.clear()
        format_options = [
            ("basic", _("multi_word_format_basic")),
            ("inline", _("multi_word_format_inline")),
            ("tagged", _("multi_word_format_tagged")),
            ("numbered", _("multi_word_format_numbered")),
            ("tagged_numbered", _("multi_word_format_tagged_numbered")),
        ]
        
        for fmt_key, fmt_label in format_options:
            if compatible.get(fmt_key, False):
                self.multi_word_format_dropdown.addItem(fmt_label, fmt_key)
                if fmt_key == current_fmt:
                    self.multi_word_format_dropdown.setCurrentIndex(
                        self.multi_word_format_dropdown.count() - 1
                    )

    def _connect_signals(self):
        """Connect all signals to slots."""
        self.lang_dropdown.currentIndexChanged.connect(self._language_changed)
        self.profile_dropdown.currentIndexChanged.connect(self._on_profile_changed)
        self.profile_add_btn.clicked.connect(self._on_profile_add)
        self.profile_rename_btn.clicked.connect(self._on_profile_rename)
        self.profile_delete_btn.clicked.connect(self._on_profile_delete)
        self.card_type_dropdown.currentIndexChanged.connect(self._on_card_type_changed)
        self.target_deck_dropdown.currentIndexChanged.connect(self._on_target_deck_changed)
        self.multi_meaning_format_dropdown.currentIndexChanged.connect(self._update_multi_word_dropdown)
        self.add_btn.clicked.connect(self.add_mapping_row)
        self.save_button.clicked.connect(self.save_config_clicked)
        self.open_shortcut_button.clicked.connect(lambda: self._capture_shortcut("open_shortcut"))
        self.quick_fill_shortcut_button.clicked.connect(lambda: self._capture_shortcut("quick_fill_shortcut"))

    def _load_initial_data(self):
        """Load configuration into UI."""
        lang_code = self.config.get("language", "en")
        lang_index = 0
        for index, code in self.lang_map.items():
            if code == lang_code:
                lang_index = index
                break
        self.lang_dropdown.setCurrentIndex(lang_index)
        button_position = str(self.config.get("editor_button_position", "toolbar") or "toolbar")
        index = self.button_position_dropdown.findData(button_position)
        self.button_position_dropdown.setCurrentIndex(index if index >= 0 else 0)
        self._refresh_profile_dropdown(select_name=str(self.config.get("active_profile", "Default") or "Default"))
        self._apply_profile_to_ui(self._current_profile_name)

    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
                continue
            widget = item.widget()
            if widget:
                try:
                    widget.hide()
                    widget.setParent(None)
                    QTimer.singleShot(0, widget.deleteLater)
                except Exception:
                    pass

    def _refresh_shortcut_buttons(self):
        """Update shortcut button text."""
        self.open_shortcut_button.setText(self._format_shortcut_label(self.open_shortcut_value))
        self.quick_fill_shortcut_button.setText(self._format_shortcut_label(self.quick_fill_shortcut_value))

    def _format_shortcut_label(self, shortcut: str) -> str:
        return shortcut if shortcut else _("shortcut_unassigned")

    def _capture_shortcut(self, key_name: str):
        """Capture a shortcut and update button text."""
        dialog = ShortcutCaptureDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if key_name == "open_shortcut":
                self.open_shortcut_value = dialog.shortcut
            else:
                self.quick_fill_shortcut_value = dialog.shortcut
            self._refresh_shortcut_buttons()

    def _rebuild_mapping_grid(self):
        """Rebuild mapping grid from data."""
        from .config_dialog_utils import get_themed_icon
        is_legacy = self._current_style_mode() == "legacy_and_stable"
        
        self._clear_layout(self.mapping_grid_layout)
        
        mapping_options = self._mapping_options()

        for row_index, row_data in enumerate(self.mapping_rows_data):
            left_value, right_value = row_data['jisho'], row_data['field']

            up_btn = QPushButton(icon=get_themed_icon("arrow_up", on_gradient=not is_legacy))
            up_btn.setObjectName("ToolkitIconAction")
            up_btn.setProperty("toolkit_group", "mapping")
            
            down_btn = QPushButton(icon=get_themed_icon("arrow_down", on_gradient=not is_legacy))
            down_btn.setObjectName("ToolkitIconAction")
            down_btn.setProperty("toolkit_group", "mapping")
            
            left_combo = QComboBox()
            left_combo.setObjectName("ToolkitComboBox")
            left_combo.setProperty("toolkit_group", "mapping")
            left_combo.addItems(mapping_options)
            if left_value and left_value not in mapping_options:
                left_combo.addItem(left_value)
            arrow_label = QLabel("→")
            arrow_label.setObjectName("ToolkitMappingArrow")
            arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow_label.setFixedSize(26, 26)
            right_combo = QComboBox()
            right_combo.setObjectName("ToolkitComboBox")
            right_combo.setProperty("toolkit_group", "mapping")
            right_combo.addItems([""] + self.current_field_names)
            
            remove_btn = QPushButton(icon=get_themed_icon("remove", on_gradient=not is_legacy))
            remove_btn.setObjectName("ToolkitIconAction")
            remove_btn.setProperty("toolkit_group", "mapping")

            left_combo.setCurrentText(left_value)
            right_combo.setCurrentText(right_value)

            up_btn.clicked.connect(lambda _, idx=row_index: self._move_row(idx, -1))
            down_btn.clicked.connect(lambda _, idx=row_index: self._move_row(idx, 1))
            remove_btn.clicked.connect(lambda _, idx=row_index: self._remove_row(idx))

            left_combo.currentTextChanged.connect(
                lambda text, idx=row_index: self._update_mapping_cell(idx, "jisho", text)
            )
            right_combo.currentTextChanged.connect(
                lambda text, idx=row_index: self._update_mapping_cell(idx, "field", text)
            )
            
            self.mapping_grid_layout.addWidget(up_btn, row_index, 0)
            self.mapping_grid_layout.addWidget(down_btn, row_index, 1)
            self.mapping_grid_layout.addWidget(left_combo, row_index, 2)
            self.mapping_grid_layout.addWidget(arrow_label, row_index, 3)
            self.mapping_grid_layout.addWidget(right_combo, row_index, 4)
            self.mapping_grid_layout.addWidget(remove_btn, row_index, 5)

        self.mapping_grid_layout.setColumnStretch(2, 1)
        self.mapping_grid_layout.setColumnStretch(4, 1)

        for i in range(len(self.mapping_rows_data)):
            self.mapping_grid_layout.setRowStretch(i, 0)
        self.mapping_grid_layout.setRowStretch(len(self.mapping_rows_data), 1)

        self._sync_icon_action_buttons()
        self._update_button_states()

    def add_mapping_row(self, checked: bool = False):
        """Add a new mapping row."""
        self.mapping_rows_data.append({"jisho": "", "field": ""})
        self._schedule_mapping_rebuild()

    def _update_mapping_cell(self, index: int, key: str, value: str) -> None:
        if 0 <= index < len(self.mapping_rows_data):
            self.mapping_rows_data[index][key] = value

    def _remove_row(self, index):
        """Remove a mapping row."""
        if 0 <= index < len(self.mapping_rows_data):
            del self.mapping_rows_data[index]
            self._schedule_mapping_rebuild()
            
    def _move_row(self, index, direction):
        """Move a row up or down."""
        if not (0 <= index < len(self.mapping_rows_data)):
            return
        
        new_index = index + direction
        if not (0 <= new_index < len(self.mapping_rows_data)):
            return

        self.mapping_rows_data.insert(new_index, self.mapping_rows_data.pop(index))
        self._pending_cursor_target = (new_index, 0 if direction == -1 else 1)
        self._schedule_mapping_rebuild()

    def _schedule_mapping_rebuild(self) -> None:
        if getattr(self, "_is_closing", False):
            return
        if self._mapping_rebuild_pending:
            return
        self._mapping_rebuild_pending = True
        QTimer.singleShot(0, self._apply_scheduled_mapping_rebuild)

    def _settings_control_height(self) -> int:
        refs = (
            getattr(self, "profile_dropdown", None),
            getattr(self, "card_type_dropdown", None),
            getattr(self, "target_deck_dropdown", None),
            getattr(self, "search_field_dropdown", None),
            getattr(self, "lang_dropdown", None),
            getattr(self, "button_position_dropdown", None),
            getattr(self, "open_shortcut_button", None),
        )
        heights = []
        self.ensurePolished()
        for widget in refs:
            if widget is None:
                continue
            try:
                widget.ensurePolished()
                hint = int(widget.sizeHint().height())
            except Exception:
                continue
            if hint > 0:
                heights.append(hint)
        return max(28, max(heights, default=30))

    def _mapping_control_height(self) -> int:
        heights = []
        self.ensurePolished()
        for combo in self.findChildren(QComboBox):
            if str(combo.property("toolkit_group") or "") != "mapping":
                continue
            try:
                combo.ensurePolished()
                hint = int(combo.sizeHint().height())
            except Exception:
                continue
            if hint > 0:
                heights.append(hint)
        return max(28, max(heights, default=0))

    def _sync_icon_action_buttons(self) -> None:
        profile_side = self._settings_control_height()
        mapping_side = self._mapping_control_height() or profile_side
        for button in self.findChildren(QPushButton):
            if str(button.objectName() or "") != "ToolkitIconAction":
                continue
            try:
                group = str(button.property("toolkit_group") or "")
                side = mapping_side if group == "mapping" else profile_side
                icon_side = max(12, side - 14)
                button.setFixedSize(side, side)
                button.setIconSize(QSize(icon_side, icon_side))
            except Exception:
                pass

    def _apply_scheduled_mapping_rebuild(self) -> None:
        if getattr(self, "_is_closing", False):
            self._mapping_rebuild_pending = False
            return
        self._mapping_rebuild_pending = False
        self._rebuild_mapping_grid()
        self._apply_pending_cursor_target()

    def _apply_pending_cursor_target(self) -> None:
        if getattr(self, "_is_closing", False):
            self._pending_cursor_target = None
            return
        target = self._pending_cursor_target
        self._pending_cursor_target = None
        if not target:
            return
        row, col = target

        def _focus_widget() -> None:
            try:
                item = self.mapping_grid_layout.itemAtPosition(row, col)
                if item is None:
                    return
                widget = item.widget()
                if widget is None or not widget.isVisible():
                    return
                widget.setFocus(Qt.FocusReason.OtherFocusReason)
            except Exception:
                return

        QTimer.singleShot(0, _focus_widget)

    def _update_button_states(self):
        """Set visual off state for move buttons based on position."""
        count = self.mapping_grid_layout.rowCount() - 1 
        for i in range(count):
            up_btn_item = self.mapping_grid_layout.itemAtPosition(i, 0)
            down_btn_item = self.mapping_grid_layout.itemAtPosition(i, 1)
            if up_btn_item and down_btn_item:
                up_btn = up_btn_item.widget()
                down_btn = down_btn_item.widget()
                up_enabled = i > 0
                down_enabled = i < count - 1
                up_btn.setEnabled(up_enabled)
                down_btn.setEnabled(down_enabled)
                up_btn.update()
                down_btn.update()

    def update_fields(self, index: int = 0):
        """Update fields list based on selected note type."""
        model_name = self.card_type_dropdown.currentText()
        self.current_field_names = []
        if model_name:
            model = mw.col.models.by_name(model_name)
            if model:
                self.current_field_names = [fld["name"] for fld in model["flds"]]
        
        self.search_field_dropdown.clear()
        self.search_field_dropdown.addItems(self.current_field_names)
        
        saved_search = ""
        try:
            saved_search = str(self._current_profile().get("search_field", "") or "")
        except Exception:
            saved_search = ""
        if saved_search in self.current_field_names:
            self.search_field_dropdown.setCurrentText(saved_search)

        self._rebuild_mapping_grid()

    def load_mapping_rows(self):
        """Load mappings from config into data structure."""
        mappings = self._current_profile().get("mappings", [])
        
        if isinstance(mappings, dict):
            self.mapping_rows_data = [{"jisho": jisho, "field": field} for field, jisho in mappings.items()]
        elif isinstance(mappings, list):
            self.mapping_rows_data = mappings
        else:
            self.mapping_rows_data = []

        self._rebuild_mapping_grid()

    def save_config_clicked(self, checked: bool = False):
        """Validate and save configuration."""
        from aqt.utils import showWarning, showInfo
        
        for mapping in self.mapping_rows_data:
            if not mapping["jisho"] or not mapping["field"]:
                showWarning(_("warning_fill_mappings"))
                return

        conflict = self._find_duplicate_combo_profile(
            self.card_type_dropdown.currentText(),
            self.target_deck_dropdown.currentText(),
        )
        if conflict:
            showWarning(_("warning_profile_duplicate_combo").format(profile=conflict))
            return
        
        self._persist_current_profile_from_ui()

        lang_code = self.lang_map.get(self.lang_dropdown.currentIndex(), "en")
        selected_style_mode = "legacy_and_stable"

        self.config["language"] = lang_code
        self.config["style_mode"] = selected_style_mode
        self.config["active_profile"] = str(self._current_profile_name or "Default")
        self.config["editor_button_position"] = str(
            self.button_position_dropdown.currentData() or "toolbar"
        )

        save_full_config(self.config)
        showInfo(_("info_settings_saved"))
        self._prepare_for_close()
        self.close()

    def accept(self) -> None:
        self._prepare_for_close()
        super().accept()

    def reject(self) -> None:
        self._prepare_for_close()
        super().reject()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._prepare_for_close()
        return super().closeEvent(event)
