# -*- coding: utf-8 -*-
"""Shared legacy UI helpers for Anki Jisho Connect."""

import os

from .paths import icon_path

STYLE_MODE_LEGACY = "legacy_and_stable"


def _normalize_style_mode(_style_mode=None) -> str:
    return STYLE_MODE_LEGACY


def _style_mode_from_config() -> str:
    return STYLE_MODE_LEGACY


def _resolve_style_mode(_style_mode=None) -> str:
    return STYLE_MODE_LEGACY


def _theme():
    try:
        from aqt.theme import theme_manager
        from .constants import DarkTheme, LightTheme

        return DarkTheme if theme_manager.night_mode else LightTheme
    except Exception:
        class _FallbackTheme:
            PRIMARY = "#007aff"
            PRIMARY_HOVER = "#005ecb"
            PRIMARY_TEXT = "#ffffff"
            BACKGROUND = "#ffffff"
            BACKGROUND_ALT = "#f0f2f5"
            BACKGROUND_SEARCH = "#f7f7f7"
            BORDER = "#e0e0e0"
            BORDER_LIGHT = "#dddddd"
            BORDER_DARK = "#cccccc"
            TEXT_PRIMARY = "#222222"
            TEXT_SECONDARY = "#555555"
            TEXT_TERTIARY = "#666666"
            TEXT_DISABLED = "#999999"
            CONTROL_DISABLED_TEXT = "#999999"
            CONTROL_DISABLED_BORDER = "#dddddd"
            CONFIRM_DISABLED_BG = "#e9e9e9"

        return _FallbackTheme()


def _ui_tokens() -> dict[str, str]:
    try:
        from aqt import colors, props
        from aqt.theme import theme_manager

        return {
            "canvas": theme_manager.var(colors.CANVAS),
            "elevated": theme_manager.var(colors.CANVAS_ELEVATED),
            "input": theme_manager.var(colors.CANVAS_CODE),
            "border": theme_manager.var(colors.BORDER),
            "border_subtle": theme_manager.var(colors.BORDER_SUBTLE),
            "border_focus": theme_manager.var(colors.BORDER_FOCUS),
            "fg": theme_manager.var(colors.FG),
            "fg_subtle": theme_manager.var(colors.FG_SUBTLE),
            "fg_disabled": theme_manager.var(colors.FG_DISABLED),
            "highlight_bg": theme_manager.var(colors.HIGHLIGHT_BG),
            "highlight_fg": theme_manager.var(colors.HIGHLIGHT_FG),
            "radius": theme_manager.var(props.BORDER_RADIUS),
        }
    except Exception:
        theme = _theme()
        return {
            "canvas": theme.BACKGROUND,
            "elevated": theme.BACKGROUND_SEARCH,
            "input": theme.BACKGROUND,
            "border": theme.BORDER_DARK,
            "border_subtle": theme.BORDER,
            "border_focus": theme.PRIMARY,
            "fg": theme.TEXT_PRIMARY,
            "fg_subtle": theme.TEXT_SECONDARY,
            "fg_disabled": theme.TEXT_DISABLED,
            "highlight_bg": theme.PRIMARY,
            "highlight_fg": theme.PRIMARY_TEXT,
            "radius": "5px",
        }


def _official_anki_widget_stylesheet() -> str:
    try:
        from aqt.stylesheets import custom_styles
        from aqt.theme import theme_manager

        return "".join(
            [
                custom_styles.general(theme_manager),
                custom_styles.button(theme_manager),
                custom_styles.checkbox(theme_manager),
                custom_styles.combobox(theme_manager),
                custom_styles.tabwidget(theme_manager),
                custom_styles.spinbox(theme_manager),
                custom_styles.scrollbar(theme_manager),
            ]
        )
    except Exception:
        return ""


def build_jisho_connect_settings_stylesheet() -> str:
    tokens = _ui_tokens()
    official = _official_anki_widget_stylesheet()

    fallback = ""
    if not official:
        theme = _theme()
        fallback = _legacy_stylesheet(theme)

    return (
        fallback
        + official
        + f"""
        QDialog#JishoConnectSettingsDialog {{
            background: {tokens["canvas"]};
        }}

        QDialog#JishoConnectSettingsDialog QWidget#JishoConnectSettingsPage {{
            background: transparent;
        }}

        QDialog#JishoConnectSettingsDialog QTabWidget {{
            background: none;
            border-radius: {tokens["radius"]};
        }}

        QDialog#JishoConnectSettingsDialog QTabWidget::pane {{
            top: -15px;
            padding-top: 1em;
            background: {tokens["elevated"]};
            border: 1px solid {tokens["border_subtle"]};
            border-radius: {tokens["radius"]};
        }}

        QDialog#JishoConnectSettingsDialog QGroupBox {{
            text-align: center;
            font-weight: bold;
            border: 1px solid {tokens["border_subtle"]};
            padding: 0.75em 0 0.75em 0;
            background: {tokens["elevated"]};
            border-radius: {tokens["radius"]};
            margin-top: 10px;
        }}

        QDialog#JishoConnectSettingsDialog QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            margin: 0 2px;
            left: 15px;
            color: {tokens["fg"]};
        }}

        QDialog#JishoConnectSettingsDialog QLineEdit,
        QDialog#JishoConnectSettingsDialog QComboBox,
        QDialog#JishoConnectSettingsDialog QSpinBox,
        QDialog#JishoConnectSettingsDialog QDoubleSpinBox,
        QDialog#JishoConnectSettingsDialog QPushButton#ToolkitShortcutButton {{
            min-height: 0px;
        }}

        QDialog#JishoConnectSettingsDialog QPushButton#ToolkitIconAction {{
            min-width: 0px;
            max-width: 16777215px;
            min-height: 0px;
            max-height: 16777215px;
            padding: 0px;
            border-radius: {tokens["radius"]};
        }}

        QDialog#JishoConnectSettingsDialog QPushButton#ToolkitInlineButton {{
            min-height: 0px;
            padding-left: 12px;
            padding-right: 12px;
        }}

        QDialog#JishoConnectSettingsDialog QPushButton#ToolkitSaveButton {{
            min-width: 148px;
            min-height: 0px;
            padding-left: 18px;
            padding-right: 18px;
        }}

        QDialog#JishoConnectSettingsDialog QScrollArea#ToolkitMappingScroll {{
            background: {tokens["input"]};
            border: 1px solid {tokens["border_subtle"]};
            border-radius: {tokens["radius"]};
        }}

        QDialog#JishoConnectSettingsDialog QScrollArea#ToolkitMappingScroll > QWidget#qt_scrollarea_viewport,
        QDialog#JishoConnectSettingsDialog QScrollArea#ToolkitMappingScroll QAbstractScrollArea::viewport,
        QDialog#JishoConnectSettingsDialog QWidget#ToolkitMappingContent {{
            background: {tokens["input"]};
            color: {tokens["fg"]};
        }}

        QDialog#JishoConnectSettingsDialog QLabel#ToolkitMappingArrow {{
            background: {tokens["input"]};
            border: 1px solid {tokens["border_subtle"]};
            border-radius: {tokens["radius"]};
            color: {tokens["fg_subtle"]};
            min-width: 26px;
            max-width: 26px;
            min-height: 26px;
            max-height: 26px;
        }}
        """
    )


def _legacy_stylesheet(theme) -> str:
    return f"""
        QDialog {{
            background-color: {theme.BACKGROUND};
            color: {theme.TEXT_PRIMARY};
        }}

        QWidget {{
            color: {theme.TEXT_PRIMARY};
        }}

        QLabel#MutedLabel {{
            color: {theme.TEXT_SECONDARY};
        }}

        QToolTip {{
            background-color: {theme.BACKGROUND};
            color: {theme.TEXT_PRIMARY};
            border: 1px solid {theme.BORDER_DARK};
            border-radius: 4px;
            padding: 4px 6px;
        }}

        QWidget#ToolkitCard {{
            background-color: {theme.BACKGROUND};
            border: 1px solid {theme.BORDER};
            border-radius: 10px;
        }}

        QPushButton {{
            background-color: {theme.PRIMARY};
            color: {theme.PRIMARY_TEXT};
            border: 1px solid {theme.PRIMARY_HOVER};
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 700;
        }}

        QPushButton:hover {{
            background-color: {theme.PRIMARY_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {theme.PRIMARY_HOVER};
        }}

        QPushButton:disabled {{
            background-color: {theme.CONFIRM_DISABLED_BG};
            color: {theme.TEXT_DISABLED};
            border: 1px solid {theme.BORDER_LIGHT};
        }}

        QPushButton#ToolkitSecondaryButton {{
            background-color: {theme.BACKGROUND_SEARCH};
            color: {theme.TEXT_PRIMARY};
            border: 1px solid {theme.BORDER_DARK};
        }}

        QPushButton#ToolkitSaveButton,
        QPushButton#ToolkitShortcutButton,
        QPushButton#ToolkitInlineButton {{
            min-height: 32px;
        }}

        QPushButton#ToolkitIconAction {{
            min-width: 30px;
            max-width: 30px;
            min-height: 30px;
            max-height: 30px;
            padding: 0px;
        }}

        QTabWidget::pane {{
            border: 1px solid {theme.BORDER};
            border-radius: 8px;
            background-color: {theme.BACKGROUND};
            top: -1px;
        }}

        QTabWidget::tab-bar {{
            alignment: center;
        }}

        QTabBar {{
            background: transparent;
        }}

        QTabBar::tab {{
            background-color: {theme.BACKGROUND_ALT};
            color: {theme.TEXT_PRIMARY};
            padding: 6px 14px;
            border: 1px solid {theme.BORDER};
            border-radius: 8px;
            margin-right: 6px;
            font-weight: 600;
        }}

        QTabBar::tab:hover {{
            background-color: {theme.BACKGROUND_SEARCH};
            border-color: {theme.BORDER_DARK};
        }}

        QTabBar::tab:selected {{
            background-color: {theme.PRIMARY};
            color: {theme.PRIMARY_TEXT};
            border-color: {theme.PRIMARY_HOVER};
        }}

        QGroupBox {{
            color: {theme.TEXT_PRIMARY};
            border: 1px solid {theme.BORDER_DARK};
            border-radius: 6px;
            margin-top: 9px;
            padding-top: 8px;
            background-color: {theme.BACKGROUND};
            font-weight: 700;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 8px;
            padding: 0 4px;
            color: {theme.TEXT_PRIMARY};
        }}

        QWidget#ToolkitMappingContent {{
            background-color: {theme.BACKGROUND_ALT};
        }}

        QScrollArea#ToolkitMappingScroll {{
            background-color: {theme.BACKGROUND_ALT};
            border: 1px solid {theme.BORDER};
            border-radius: 6px;
        }}

        QScrollArea#ToolkitMappingScroll > QWidget#qt_scrollarea_viewport,
        QScrollArea#ToolkitMappingScroll QAbstractScrollArea::viewport,
        QScrollArea#ToolkitMappingScroll QWidget {{
            background-color: {theme.BACKGROUND_ALT};
            color: {theme.TEXT_PRIMARY};
        }}

        QLabel#ToolkitMappingArrow {{
            color: {theme.TEXT_PRIMARY};
            background-color: {theme.BACKGROUND_SEARCH};
            border: 1px solid {theme.BORDER};
            border-radius: 8px;
            min-width: 26px;
            max-width: 26px;
            min-height: 26px;
            max-height: 26px;
            padding: 0px;
        }}

        QLineEdit,
        QComboBox,
        QPlainTextEdit,
        QSpinBox,
        QDoubleSpinBox {{
            background-color: {theme.BACKGROUND_SEARCH};
            border: 1px solid {theme.BORDER_DARK};
            border-radius: 4px;
            padding: 6px 8px;
            color: {theme.TEXT_PRIMARY};
            selection-background-color: {theme.PRIMARY};
            selection-color: {theme.PRIMARY_TEXT};
        }}

        QLineEdit:focus,
        QComboBox:focus,
        QPlainTextEdit:focus,
        QSpinBox:focus,
        QDoubleSpinBox:focus {{
            border: 1px solid {theme.PRIMARY};
            outline: none;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
            background-color: {theme.BACKGROUND_ALT};
            border-left: 1px solid {theme.BORDER};
        }}

        QAbstractItemView#ToolkitComboPopup {{
            background-color: {theme.BACKGROUND};
            border: 1px solid {theme.BORDER_DARK};
            color: {theme.TEXT_PRIMARY};
            selection-background-color: {theme.PRIMARY};
            selection-color: {theme.PRIMARY_TEXT};
            padding: 2px;
            outline: none;
        }}

        QAbstractItemView#ToolkitComboPopup::item {{
            min-height: 24px;
            padding: 4px 8px;
        }}

        QAbstractItemView#ToolkitComboPopup::item:hover {{
            background-color: {theme.BACKGROUND_ALT};
        }}

        QTableWidget {{
            background-color: {theme.BACKGROUND};
            border: 1px solid {theme.BORDER_DARK};
            color: {theme.TEXT_PRIMARY};
            border-radius: 4px;
            gridline-color: {theme.BORDER};
            alternate-background-color: {theme.BACKGROUND_ALT};
        }}

        QHeaderView::section {{
            background-color: {theme.BACKGROUND_ALT};
            color: {theme.TEXT_PRIMARY};
            border: 1px solid {theme.BORDER};
            padding: 4px 6px;
            font-weight: 600;
        }}

        QTableCornerButton::section {{
            background-color: {theme.BACKGROUND_ALT};
            border: 1px solid {theme.BORDER};
        }}

        QProgressBar {{
            border: 1px solid {theme.BORDER};
            border-radius: 5px;
            text-align: center;
            color: {theme.TEXT_PRIMARY};
            background-color: {theme.BACKGROUND_ALT};
        }}

        QProgressBar::chunk {{
            background-color: {theme.PRIMARY};
            border-radius: 5px;
        }}

        QCheckBox {{
            spacing: 8px;
            color: {theme.TEXT_PRIMARY};
            background: transparent;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {theme.BORDER_DARK};
            border-radius: 4px;
            background-color: {theme.BACKGROUND_SEARCH};
        }}

        QCheckBox::indicator:hover {{
            border: 1px solid {theme.PRIMARY};
        }}

        QCheckBox::indicator:checked {{
            background-color: {theme.BACKGROUND_SEARCH};
            border: 1px solid {theme.PRIMARY};
        }}

        QScrollBar:vertical {{
            background-color: {theme.BACKGROUND_ALT};
            width: 10px;
            margin: 2px;
            border: 1px solid {theme.BORDER};
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {theme.PRIMARY};
            min-height: 24px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar:horizontal {{
            background-color: {theme.BACKGROUND_ALT};
            height: 10px;
            margin: 2px;
            border: 1px solid {theme.BORDER};
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {theme.PRIMARY};
            min-width: 24px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
            height: 0px;
            background: transparent;
            border: none;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
    """


class _NoNativeComboPopupStyle:
    def __init__(self, base_style):
        try:
            from aqt.qt import QProxyStyle, QStyle

            class _Style(QProxyStyle):  # type: ignore[misc]
                def styleHint(self, hint, option=None, widget=None, returnData=None):  # type: ignore[override]
                    try:
                        if hint == QStyle.StyleHint.SH_ComboBox_Popup:
                            return 0
                    except Exception:
                        pass
                    return super().styleHint(hint, option, widget, returnData)

            self.style = _Style(base_style)
        except Exception:
            self.style = None


class _ComboPopupStyler:
    @staticmethod
    def apply(view) -> None:
        try:
            from aqt.qt import QFrame, Qt
        except Exception:
            return

        tokens = _ui_tokens()
        try:
            if isinstance(view, QFrame):
                view.setFrameShape(QFrame.Shape.NoFrame)
                view.setLineWidth(0)
                view.setMidLineWidth(0)
        except Exception:
            pass

        try:
            popup = view.window()
            if popup is None:
                return
            try:
                if (not popup.isWindow()) or not bool(popup.windowFlags() & Qt.WindowType.Popup):
                    return
            except Exception:
                pass
            popup.setObjectName("ToolkitComboPopupWindow")
            popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            popup.setStyleSheet(
                f"""
                QWidget#ToolkitComboPopupWindow {{
                    background-color: {tokens["elevated"]};
                    border: 1px solid {tokens["border_subtle"]};
                    border-radius: 4px;
                }}
                QWidget#ToolkitComboPopupWindow QAbstractScrollArea,
                QWidget#ToolkitComboPopupWindow QListView,
                QWidget#ToolkitComboPopupWindow QAbstractItemView,
                QWidget#ToolkitComboPopupWindow QFrame,
                QWidget#ToolkitComboPopupWindow QWidget {{
                    background-color: {tokens["elevated"]};
                    color: {tokens["fg"]};
                    border: 0px;
                }}
                """
            )
        except Exception:
            pass


def legacy_stable_stylesheet() -> str:
    return _legacy_stylesheet(_theme())


def base_stylesheet(style_mode=None) -> str:
    _ = style_mode
    return legacy_stable_stylesheet()


def apply_toolkit_combobox_style(combobox, style_mode=None) -> None:
    _ = style_mode
    try:
        from aqt.qt import QColor, QComboBox, QFrame, QPalette

        if not isinstance(combobox, QComboBox):
            return
        combobox.setObjectName("ToolkitComboBox")

        if os.name == "nt":
            try:
                if not getattr(combobox, "_toolkit_non_native_popup_forced", False):
                    style_wrapper = _NoNativeComboPopupStyle(combobox.style())
                    proxy_style = getattr(style_wrapper, "style", None)
                    if proxy_style is not None:
                        combobox.setStyle(proxy_style)
                        combobox._toolkit_combo_proxy_style = proxy_style
                    combobox._toolkit_non_native_popup_forced = True
            except Exception:
                pass

        view = combobox.view()
        if view is not None:
            tokens = _ui_tokens()
            view.setObjectName("ToolkitComboPopup")
            view.setStyleSheet(
                f"""
                QAbstractItemView {{
                    background-color: {tokens["elevated"]};
                    border: 0px;
                    color: {tokens["fg"]};
                    selection-background-color: {tokens["highlight_bg"]};
                    selection-color: {tokens["highlight_fg"]};
                    outline: none;
                    padding: 2px;
                }}
                QAbstractItemView::item {{
                    min-height: 24px;
                    padding: 4px 8px;
                }}
                QAbstractItemView::item:hover {{
                    background-color: {tokens["input"]};
                }}
                """
            )
            try:
                pal = view.palette()
                pal.setColor(QPalette.ColorRole.Base, QColor(tokens["elevated"]))
                pal.setColor(QPalette.ColorRole.Text, QColor(tokens["fg"]))
                pal.setColor(QPalette.ColorRole.Highlight, QColor(tokens["highlight_bg"]))
                pal.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens["highlight_fg"]))
                view.setPalette(pal)
            except Exception:
                pass
            _ComboPopupStyler.apply(view)
            try:
                if isinstance(view, QFrame):
                    view.setFrameShape(QFrame.Shape.NoFrame)
            except Exception:
                pass
    except Exception:
        pass


def apply_base_stylesheet(widget, style_mode=None) -> None:
    _ = style_mode
    stylesheet = base_stylesheet()
    theme = _theme()

    icon_check_fs = icon_path("check_blue.svg")
    icon_down_fs = icon_path("chevron_down_blue.svg")
    icon_up_fs = icon_path("chevron_up_blue.svg")

    if icon_check_fs.exists():
        icon_check = icon_check_fs.as_posix()
        stylesheet += f"""
        QCheckBox::indicator:checked {{
            image: url("{icon_check}");
        }}
        """

    if icon_down_fs.exists() and icon_up_fs.exists():
        icon_down = icon_down_fs.as_posix()
        icon_up = icon_up_fs.as_posix()
        stylesheet += f"""
        QComboBox::down-arrow {{
            image: url("{icon_down}");
            width: 14px;
            height: 14px;
        }}
        QAbstractSpinBox::up-arrow {{
            image: url("{icon_up}");
            width: 12px;
            height: 12px;
        }}
        QAbstractSpinBox::down-arrow {{
            image: url("{icon_down}");
            width: 12px;
            height: 12px;
        }}
        QAbstractSpinBox::up-button,
        QAbstractSpinBox::down-button {{
            width: 20px;
            border-left: 1px solid {theme.BORDER};
            background-color: {theme.BACKGROUND_ALT};
        }}
        QAbstractSpinBox::up-button:hover,
        QAbstractSpinBox::down-button:hover {{
            background-color: {theme.BACKGROUND_SEARCH};
        }}
        """

    widget.setStyleSheet(stylesheet)
    try:
        from aqt.qt import QComboBox

        for combo in widget.findChildren(QComboBox):
            apply_toolkit_combobox_style(combo)
    except Exception:
        pass


def build_jisho_connect_results_stylesheet() -> str:
    tokens = _ui_tokens()
    theme = _theme()
    official = _official_anki_widget_stylesheet()

    fallback = ""
    if not official:
        fallback = _legacy_stylesheet(theme)

    return (
        fallback
        + official
        + f"""
        QDialog#JishoConnectResultsDialog {{
            background: {tokens["canvas"]};
        }}

        QWidget#ToolkitSearchWidget {{
            background: {tokens["elevated"]};
            border: 1px solid {tokens["border_subtle"]};
            border-radius: {tokens["radius"]};
        }}

        QScrollArea#ToolkitResultsScroll {{
            border: 0px;
            background: transparent;
        }}

        QWidget#ToolkitResultsContainer {{
            background: transparent;
        }}

        QFrame#ToolkitResultCard {{
            background: {tokens["elevated"]};
            border: 1px solid {tokens["border_subtle"]};
            border-radius: {tokens["radius"]};
        }}

        QLabel#ToolkitWordLabel {{
            font-size: 32px;
            font-weight: 600;
            color: {tokens["fg"]};
        }}

        QLabel#ToolkitReadingLabel {{
            font-size: 18px;
            color: {tokens["fg_subtle"]};
            padding-bottom: 3px;
        }}

        QLabel#ToolkitPosLabel {{
            color: {tokens["fg_subtle"]};
            font-style: italic;
        }}

        QLabel#ToolkitMetaLabel {{
            color: {tokens["fg_subtle"]};
            font-style: italic;
            font-size: 12px;
        }}

        QLabel#ToolkitOtherFormsTitle {{
            font-size: 14px;
            font-weight: 700;
            margin-top: 10px;
        }}

        QCheckBox#ToolkitSelectAllCheckbox {{
            font-weight: 600;
        }}

        QPushButton#ToolkitResultsConfirmButton {{
            min-width: 220px;
            min-height: 34px;
            padding-left: 22px;
            padding-right: 22px;
        }}

        QPushButton#ToolkitResultsConfirmButton[state="idle"] {{
            background-color: {theme.CONFIRM_DISABLED_BG};
            color: {tokens["fg_disabled"]};
            border: 1px solid {tokens["border_subtle"]};
        }}

        QPushButton#ToolkitResultsConfirmButton[state="ready"] {{
            background-color: {theme.PRIMARY};
            color: {theme.PRIMARY_TEXT};
            border: 1px solid {theme.PRIMARY_HOVER};
        }}

        QPushButton#ToolkitResultsConfirmButton[state="ready"]:hover {{
            background-color: {theme.PRIMARY_HOVER};
        }}

        QPushButton#ToolkitResultsConfirmButton[state="multi"] {{
            background-color: {theme.ACCENT_YELLOW};
            color: {theme.ACCENT_YELLOW_TEXT};
            border: 1px solid {theme.ACCENT_YELLOW_HOVER};
        }}

        QPushButton#ToolkitResultsConfirmButton[state="multi"]:hover {{
            background-color: {theme.ACCENT_YELLOW_HOVER};
        }}
        """
    )


def apply_jisho_connect_results_stylesheet(widget) -> None:
    widget.setStyleSheet(build_jisho_connect_results_stylesheet())
    try:
        from aqt.qt import QComboBox

        for combo in widget.findChildren(QComboBox):
            apply_toolkit_combobox_style(combo)
    except Exception:
        pass


def apply_jisho_connect_settings_stylesheet(widget) -> None:
    widget.setStyleSheet(build_jisho_connect_settings_stylesheet())
    try:
        from aqt.qt import QComboBox

        for combo in widget.findChildren(QComboBox):
            apply_toolkit_combobox_style(combo)
    except Exception:
        pass
