# -*- coding: utf-8 -*-
"""
Results Dialog for Anki Jisho Connect
Displays Jisho search results with selection UI
"""

from typing import Callable, Optional, Any, Dict

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea,
    QLineEdit, QCheckBox, QFrame, Qt, QMessageBox, QApplication, QIcon, QSizePolicy
)
from PyQt6.QtCore import QThread

from ..constants import _, LightTheme, DarkTheme
from ..jisho_client import load_config, JishoFetchWorker
from ..text_utils import clean_search_term
from ..icon_utils import get_icon_path
from ..logger import logger
from ..paths import icon_path
from ..ui_common import apply_jisho_connect_results_stylesheet
from aqt.theme import theme_manager
from aqt.utils import showInfo, showWarning

_RUNTIME_STYLE_MODE = "legacy_and_stable"


class ResultsDialog(QDialog):
    """Dialog to display Jisho search results with checkboxes for selection."""
    
    def __init__(self, initial_term: str, on_select: Callable):
        super().__init__()
        self.is_loading = False
        self.on_select = on_select
        self.initial_term = initial_term
        self._search_thread: Optional[QThread] = None
        self._search_worker: Optional[JishoFetchWorker] = None
        self._last_search_term = ""
        self.entry_widgets = []
        self.setObjectName("JishoConnectResultsDialog")
        self.setWindowTitle(_("results_title"))
        self.setMinimumSize(700, 750)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        self.restyle()

        if self.initial_term:
            self.perform_search(self.initial_term)

    def get_theme(self):
        """Get current theme."""
        return DarkTheme if theme_manager.night_mode else LightTheme

    def _current_style_mode(self) -> str:
        # Style mode is locked for current runtime; config changes apply after restart.
        return _RUNTIME_STYLE_MODE

    def restyle(self):
        """Re-applies all styles based on current theme."""
        self._style_mode = self._current_style_mode()
        search_text = self.search_box.text() if hasattr(self, "search_box") else self.initial_term

        while self.layout().count():
            item = self.layout().takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        apply_jisho_connect_results_stylesheet(self)
        
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Search widget
        search_widget = QWidget()
        search_widget.setObjectName("ToolkitSearchWidget")
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(12, 12, 12, 12)
        search_layout.setSpacing(8)
        self.search_box = QLineEdit(search_text)
        self.search_box.setPlaceholderText(_("search_placeholder"))
        self.search_box.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_box)

        self.search_button = QPushButton(_("search_button"))
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        self.layout().addWidget(search_widget)
        
        # Results scroll area
        scroll_area = QScrollArea()
        scroll_area.setObjectName("ToolkitResultsScroll")
        scroll_area.setWidgetResizable(True)
        self.layout().addWidget(scroll_area)
        
        results_container = QWidget()
        results_container.setObjectName("ToolkitResultsContainer")
        self.results_layout = QVBoxLayout(results_container)
        self.results_layout.setContentsMargins(12, 12, 12, 12)
        self.results_layout.setSpacing(12)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(results_container)

        # Confirm button
        self.confirm_btn = QPushButton(_("confirm_entry"))
        self.confirm_btn.setObjectName("ToolkitResultsConfirmButton")
        self.confirm_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.confirm_selection)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        footer_layout.addWidget(self.confirm_btn)
        self.layout().addLayout(footer_layout)

        current_entries = [item["entry_data"] for item in self.entry_widgets]
        self.clear_results(rebuild=False)
        if current_entries:
            for entry in current_entries:
                self.create_entry_widget(entry)
            self.results_layout.addStretch()
        
        self.update_confirm_button_state()
        self._retranslate_ui()

    def _retranslate_ui(self):
        """Update UI text."""
        self.setWindowTitle(_("results_title"))
        if hasattr(self, "search_box"):
            self.search_box.setPlaceholderText(_("search_placeholder"))
        if hasattr(self, "search_button"):
            self.search_button.setText(_("search_button"))
        if hasattr(self, "confirm_btn") and not self.is_loading:
            self.confirm_btn.setText(_("confirm_entry"))

    def show_loading_state(self, message: str = ""):
        """Show loading message."""
        self.is_loading = True
        effective_message = message or _("loading_message")
        self.clear_results()
        loading_label = QLabel(f"<h3 style='white-space: nowrap;'>{effective_message}</h3>")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(loading_label)
        self.results_layout.addStretch()
        self.search_box.setEnabled(False)
        self.confirm_btn.setEnabled(False)
        self.search_button.setEnabled(False)
        self.confirm_btn.setText(_("loading_message"))
        QApplication.processEvents()

    def hide_loading_state(self):
        """Re-enable controls after search."""
        self.is_loading = False
        self.search_box.setEnabled(True)
        self.confirm_btn.setEnabled(True)
        self.search_button.setEnabled(True)
        self.confirm_btn.setText(_("confirm_entry"))

    def perform_search(self, term: Optional[str] = None):
        """Perform Jisho search using worker thread."""
        # Handle Qt signal passing bool when button clicked (convert to None)
        if isinstance(term, bool):
            term = None
        search_term = term if isinstance(term, str) else self.search_box.text()
        if not search_term:
            return

        config = load_config()
        search_term = clean_search_term(search_term, config.get("remove_furigana_search", True))
        
        if not search_term:
            return

        self._last_search_term = search_term
        self.show_loading_state(_("loading_message_term").format(term=search_term))

        self._search_thread = QThread()
        self._search_worker = JishoFetchWorker(search_term)
        self._search_worker.moveToThread(self._search_thread)

        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.error.connect(self._on_search_error)
        self._search_thread.started.connect(self._search_worker.run)
        self._search_thread.start()

    def _on_search_finished(self, entries: list):
        """Handle successful search completion."""
        self.hide_loading_state()
        self.clear_results()

        if not entries:
            no_results_label = QLabel(f"<h3>{_('no_results').format(term=self._last_search_term)}</h3>")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(no_results_label)
        else:
            for entry in entries:
                self.create_entry_widget(entry)
            self.results_layout.addStretch()
        self.update_confirm_button_state()

        self._cleanup_search_thread()

    def _on_search_error(self, err_msg: str):
        """Handle search errors."""
        self.hide_loading_state()
        self.clear_results()
        logger.error("Error in search: %s", err_msg)
        showWarning(f"Error in search: {err_msg}")
        self._cleanup_search_thread()

    def _cleanup_search_thread(self):
        """Cleanup worker and thread resources."""
        if self._search_worker:
            self._search_worker.deleteLater()
            self._search_worker = None
        if self._search_thread:
            self._search_thread.quit()
            self._search_thread.wait()
            self._search_thread.deleteLater()
            self._search_thread = None

    def _create_tag_widget(self, text: str, bg_color: str, fg_color: str) -> QWidget:
        """Create a styled tag widget."""
        tag_widget = QWidget()
        tag_widget.setAutoFillBackground(True)
        qss = f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
                padding: 0 15px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid {bg_color};
            }}
        """
        tag_widget.setStyleSheet(qss)
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(0)
        tag_label = QLabel(text)
        tag_label.setStyleSheet(f"color: {fg_color}; background: transparent;") 
        tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout.addWidget(tag_label)
        tag_widget.setFixedHeight(24)
        return tag_widget

    def create_entry_widget(self, entry: Dict[str, Any]):
        """Create a card widget for a Jisho entry."""
        if not entry.get("japanese"):
            return
        
        entry_card = QFrame()
        entry_card.setObjectName("ToolkitResultCard")
        layout = QVBoxLayout(entry_card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        word = entry["japanese"][0].get("word", "")
        reading = entry["japanese"][0].get("reading", "")
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        word_label = QLabel(word or reading)
        word_label.setObjectName("ToolkitWordLabel")
        header_layout.addWidget(word_label, alignment=Qt.AlignmentFlag.AlignBottom)
        
        if word and reading and word != reading:
            reading_label = QLabel(reading)
            reading_label.setObjectName("ToolkitReadingLabel")
            header_layout.addWidget(reading_label, alignment=Qt.AlignmentFlag.AlignBottom)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(7)
        theme = self.get_theme()
        
        if entry.get("is_common"):
            tags_layout.addWidget(self._create_tag_widget("common word", theme.SUCCESS, theme.SUCCESS_TEXT))
        if entry.get("jlpt"):
            for tag in entry.get("jlpt", []):
                tags_layout.addWidget(self._create_tag_widget(tag, theme.INFO, theme.INFO_TEXT))
        if entry.get("tags"):
            for tag in entry.get("tags", []):
                if "wanikani" in tag:
                    tags_layout.addWidget(self._create_tag_widget(tag, theme.WARNING, theme.WARNING_TEXT))
        
        tags_layout.addStretch()
        layout.addLayout(tags_layout)
        
        # Senses
        sense_checkboxes = []
        select_all_checkbox = None
        senses = entry.get("senses", [])
        if len(senses) > 1:
            select_all_checkbox = QCheckBox(_("select_all_meanings"))
            select_all_checkbox.setObjectName("ToolkitSelectAllCheckbox")
            select_all_checkbox.setTristate(True)
            select_all_checkbox.clicked.connect(
                lambda checked, boxes=sense_checkboxes: self._set_sense_group_checked(boxes, checked)
            )
            layout.addWidget(select_all_checkbox)
        for i, sense in enumerate(senses):
            sense_widget = QWidget()
            sense_hlayout = QHBoxLayout(sense_widget)
            sense_hlayout.setContentsMargins(0, 0, 0, 0)
            sense_hlayout.setSpacing(8)
            sense_hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            cb = QCheckBox()
            cb.stateChanged.connect(
                lambda _state, master=select_all_checkbox, boxes=sense_checkboxes: self._sync_entry_select_all(master, boxes)
            )
            cb.stateChanged.connect(self.update_confirm_button_state)
            sense_checkboxes.append(cb)
            sense_hlayout.addWidget(cb, alignment=Qt.AlignmentFlag.AlignTop)

            vbox = QVBoxLayout()
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(2)

            # Parts of Speech
            pos = ", ".join(sense.get("parts_of_speech", []))
            if pos:
                pos_label = QLabel(pos)
                pos_label.setObjectName("ToolkitPosLabel")
                vbox.addWidget(pos_label)

            # Definitions
            defs = "; ".join(sense.get("english_definitions", []))
            def_label = QLabel(f"<b>{i+1}.</b> {defs}")
            def_label.setObjectName("ToolkitDefLabel")
            def_label.setWordWrap(True)
            vbox.addWidget(def_label)

            # Tags + Info
            all_tags_info = []
            if sense.get("tags"):
                all_tags_info.extend(sense["tags"])
            if sense.get("info"):
                all_tags_info.extend(sense["info"])
            
            if all_tags_info:
                combined_text = ", ".join([item.replace('\n', ' ').replace('\r', '') for item in all_tags_info])
                tag_info_label = QLabel(combined_text)
                tag_info_label.setObjectName("ToolkitMetaLabel")
                tag_info_label.setWordWrap(True)
                tag_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                vbox.addWidget(tag_info_label)

            sense_hlayout.addLayout(vbox, 1)
            layout.addWidget(sense_widget)
        
        # Other forms
        other_forms_checkboxes = []
        if other_forms := [f for f in entry.get("japanese", [])[1:] if f.get("word") or f.get("reading")]:
            other_forms_label = QLabel(_("other_forms"))
            other_forms_label.setObjectName("ToolkitOtherFormsTitle")
            layout.addWidget(other_forms_label)
            for form in other_forms:
                cb = QCheckBox(f"{form.get('word', '')} [{form.get('reading', '')}]")
                cb.stateChanged.connect(self.update_confirm_button_state)
                other_forms_checkboxes.append(cb)
                layout.addWidget(cb)
        
        self.results_layout.addWidget(entry_card)
        self.entry_widgets.append({
            "widget": entry_card,
            "sense_checkboxes": sense_checkboxes,
            "other_forms_checkboxes": other_forms_checkboxes,
            "select_all_checkbox": select_all_checkbox,
            "entry_data": entry
        })
        self._sync_entry_select_all(select_all_checkbox, sense_checkboxes)

    def _set_sense_group_checked(self, sense_checkboxes: list[QCheckBox], checked: bool) -> None:
        if not sense_checkboxes:
            return
        for cb in sense_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(bool(checked))
            cb.blockSignals(False)
        self.update_confirm_button_state()

    def _sync_entry_select_all(
        self, select_all_checkbox: Optional[QCheckBox], sense_checkboxes: list[QCheckBox]
    ) -> None:
        if select_all_checkbox is None or not sense_checkboxes:
            return
        all_checked = all(cb.isChecked() for cb in sense_checkboxes)
        any_checked = any(cb.isChecked() for cb in sense_checkboxes)
        select_all_checkbox.blockSignals(True)
        if all_checked:
            select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        elif any_checked:
            select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        select_all_checkbox.blockSignals(False)

    def update_confirm_button_state(self, *args, **kwargs):
        """Update confirm button state based on selection."""
        for item in self.entry_widgets:
            self._sync_entry_select_all(
                item.get("select_all_checkbox"), item.get("sense_checkboxes", [])
            )
        any_checked = any(cb.isChecked() for item in self.entry_widgets for cb in item.get("sense_checkboxes", []) + item.get("other_forms_checkboxes", []))
        self.confirm_btn.setEnabled(any_checked)
        checked_entry_indices = {
            i
            for i, item in enumerate(self.entry_widgets)
            if any(cb.isChecked() for cb in item.get("sense_checkboxes", []))
        }
        is_multi = len(checked_entry_indices) > 1
        self.confirm_btn.setToolTip(_("multi_word_warning_body") if is_multi else "")
        state = "idle"
        if any_checked:
            state = "multi" if is_multi else "ready"
        self.confirm_btn.setProperty("state", state)
        self.confirm_btn.style().unpolish(self.confirm_btn)
        self.confirm_btn.style().polish(self.confirm_btn)
        self.confirm_btn.update()

    def confirm_selection(self, *args, **kwargs):
        """Handle confirm button click."""
        config = load_config()
        if not config.get("mappings"):
            showWarning(_("warning_no_mappings"))
            return
        
        checked_entries_indices = [i for i, item in enumerate(self.entry_widgets) if any(cb.isChecked() for cb in item.get("sense_checkboxes", []))]
        
        if not config.get("disable_multi_word_warning", False) and len(checked_entries_indices) > 1:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(_("multi_word_warning_title"))
            msg_box.setInformativeText(_("multi_word_warning_body"))

            ok_button = msg_box.addButton(_("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton(_("button_cancel"), QMessageBox.ButtonRole.RejectRole)
            dont_warn_button = msg_box.addButton(_("ok_dont_warn_again"), QMessageBox.ButtonRole.ActionRole)

            msg_box.exec()
            clicked = msg_box.clickedButton()

            if clicked == cancel_button:
                return 
            
            if clicked == dont_warn_button:
                config["disable_multi_word_warning"] = True
                from ..jisho_client import save_config as save_cfg
                save_cfg(config)
        
        # Collect all selected entries
        all_selected_data = []
        for item in self.entry_widgets:
            selected_senses = [item["entry_data"]["senses"][i] for i, cb in enumerate(item.get("sense_checkboxes", [])) if cb.isChecked()]
            selected_other_forms = [cb.text() for cb in item.get("other_forms_checkboxes", []) if cb.isChecked()]
            if selected_senses or selected_other_forms:
                all_selected_data.append({
                    "entry_data": item["entry_data"],
                    "selected_senses": selected_senses,
                    "selected_other_forms": selected_other_forms
                })
        
        if all_selected_data:
            self.on_select(all_selected_data)
            showInfo(_("info_fields_filled"))
            try:
                mw.reset()
            except Exception:
                logger.exception("Error resetting Anki after fill")
                pass
        
        self.close()

    def clear_results(self, rebuild: bool = True):
        """Clear result widgets."""
        if hasattr(self, "results_layout") and self.results_layout:
            while (item := self.results_layout.takeAt(0)):
                if (widget := item.widget()):
                    widget.deleteLater()
        
        if rebuild:
            self.entry_widgets.clear()
            self.update_confirm_button_state()
