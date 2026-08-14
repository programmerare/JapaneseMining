# -*- coding: utf-8 -*-
"""Auxiliary informational dialogs for Anki Jisho Connect."""

from __future__ import annotations

from aqt import mw
from aqt.qt import QDialog, QGridLayout, QLabel, QPushButton, Qt, QVBoxLayout, QWidget
from aqt.utils import openLink

from ..integration import state
from ..paths import image_path
from ..ui_common import apply_base_stylesheet


def ajc_copy() -> dict:
    return {
        "about_title": "About AJC",
        "about_header": "THANK YOU FOR USING AJC ADD-ONS",
        "about_body": (
            "AJC add-ons were built to support language learning workflows in Anki.\n\n"
            "Each tool started from real day-to-day study and review needs, then evolved "
            "into focused utilities for speed, clarity, and practical use."
        ),
        "support_title": "SUPPORT THIS PROJECT",
        "support_body": "If these add-ons help your routine, consider supporting the project.",
        "welcome_title": "WELCOME TO AJC ADD-ONS",
        "welcome_intro": "Thanks for installing {addon_name}.",
        "welcome_addon_prefix": "Add-on summary:",
        "welcome_support_title": "SUPPORT THIS PROJECT",
        "welcome_support_body": "If this add-on helps your study flow, your support keeps it going.",
        "welcome_report_title": "REPORT ISSUES & QUESTIONS",
        "welcome_report_body": "Use the project link to report bugs, ask questions, and suggest improvements.",
        "btn_kofi": "Ko-fi",
        "btn_github": "GitHub",
        "btn_no_link": "NO LINK",
        "btn_close": "Close",
    }


def apply_kofi_icon(button: QPushButton) -> None:
    try:
        from aqt.qt import QIcon, QPixmap

        path = image_path("kofi.png")
        if not path.exists():
            return
        pix = QPixmap(str(path))
        if pix.isNull():
            return
        pix = pix.scaled(
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        button.setIcon(QIcon(pix))
        button.setIconSize(pix.size())
    except Exception:
        pass


def build_ajc_dialog(title: str, min_width: int = 560) -> tuple[QDialog, QVBoxLayout]:
    dialog = QDialog(mw)
    dialog.setWindowTitle(title)
    dialog.setModal(False)
    dialog.setWindowModality(Qt.WindowModality.NonModal)
    dialog.setMinimumWidth(min_width)
    apply_base_stylesheet(dialog)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(0)

    card = QWidget(dialog)
    card.setObjectName("ToolkitCard")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(14, 14, 14, 12)
    card_layout.setSpacing(8)
    layout.addWidget(card)
    return dialog, card_layout


def show_about_ajc_dialog() -> None:
    if not mw:
        return
    copy = ajc_copy()
    dialog, card_layout = build_ajc_dialog(copy["about_title"], min_width=560)

    title_label = QLabel(f"<b>{copy['about_header']}</b>")
    title_label.setTextFormat(Qt.TextFormat.RichText)
    title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    body_label = QLabel(copy["about_body"])
    body_label.setWordWrap(True)
    body_label.setTextFormat(Qt.TextFormat.PlainText)
    body_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

    support_title = QLabel(f"<b>{copy['support_title']}</b>")
    support_title.setTextFormat(Qt.TextFormat.RichText)
    support_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    support_body = QLabel(copy["support_body"])
    support_body.setWordWrap(True)
    support_body.setTextFormat(Qt.TextFormat.PlainText)
    support_body.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    kofi_button = QPushButton(copy["btn_kofi"])
    kofi_button.setCursor(Qt.CursorShape.PointingHandCursor)
    kofi_button.setObjectName("ToolkitPrimaryButton")
    apply_kofi_icon(kofi_button)
    kofi_button.clicked.connect(lambda: openLink("https://ko-fi.com/"))

    close_button = QPushButton(copy["btn_close"])
    close_button.setObjectName("ToolkitPrimaryButton")
    close_button.clicked.connect(dialog.accept)

    row = QGridLayout()
    row.setColumnStretch(0, 1)
    row.setColumnStretch(1, 1)
    row.addWidget(kofi_button, 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
    row.addWidget(close_button, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)

    card_layout.addWidget(title_label)
    card_layout.addWidget(body_label)
    card_layout.addSpacing(6)
    card_layout.addWidget(support_title)
    card_layout.addWidget(support_body)
    card_layout.addSpacing(6)
    card_layout.addLayout(row)

    state.about_dialog_ref = dialog
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def show_welcome_dialog() -> None:
    if not mw:
        return

    copy = ajc_copy()
    addon_name = "Anki Jisho Connect"
    addon_details = (
        "Anki Jisho Connect is built to move dictionary lookup directly into your editing workflow.\n\n"
        "It reads the term from your configured Search Field, fetches entries from Jisho, and lets you map "
        "meaning, part of speech, readings, tags, and other forms into your target Anki fields.\n\n"
        "You can use either quick-fill behavior for speed or open full results to choose specific senses before writing data."
    )

    dialog, card_layout = build_ajc_dialog(copy["welcome_title"], min_width=620)

    title_label = QLabel(f"<b>{copy['welcome_title']}</b>")
    title_label.setTextFormat(Qt.TextFormat.RichText)
    title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    intro_label = QLabel(
        f"{copy['welcome_intro'].format(addon_name=addon_name)}\n\n"
        f"{addon_details}"
    )
    intro_label.setWordWrap(True)
    intro_label.setTextFormat(Qt.TextFormat.PlainText)

    support_title = QLabel(f"<b>{copy['welcome_support_title']}</b>")
    support_title.setTextFormat(Qt.TextFormat.RichText)
    support_body = QLabel(copy["welcome_support_body"])
    support_body.setWordWrap(True)
    support_body.setTextFormat(Qt.TextFormat.PlainText)

    report_title = QLabel(f"<b>{copy['welcome_report_title']}</b>")
    report_title.setTextFormat(Qt.TextFormat.RichText)
    report_body = QLabel(copy["welcome_report_body"])
    report_body.setWordWrap(True)
    report_body.setTextFormat(Qt.TextFormat.PlainText)

    kofi_button = QPushButton(copy["btn_kofi"])
    kofi_button.setCursor(Qt.CursorShape.PointingHandCursor)
    kofi_button.setObjectName("ToolkitPrimaryButton")
    apply_kofi_icon(kofi_button)
    kofi_button.clicked.connect(lambda: openLink("https://ko-fi.com/"))

    github_button = QPushButton(copy["btn_github"])
    github_button.setCursor(Qt.CursorShape.PointingHandCursor)
    github_button.setObjectName("ToolkitPrimaryButton")
    github_button.clicked.connect(lambda: openLink("https://github.com/Grakinn/Anki-Jisho-Connect"))

    columns_grid = QGridLayout()
    columns_grid.setHorizontalSpacing(16)
    columns_grid.setColumnStretch(0, 1)
    columns_grid.setColumnStretch(1, 1)
    columns_grid.addWidget(support_title, 0, 0)
    columns_grid.addWidget(report_title, 0, 1)
    columns_grid.addWidget(support_body, 1, 0)
    columns_grid.addWidget(report_body, 1, 1)
    columns_grid.addWidget(kofi_button, 2, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
    columns_grid.addWidget(github_button, 2, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

    close_button = QPushButton(copy["btn_close"])
    close_button.setObjectName("ToolkitPrimaryButton")
    close_button.clicked.connect(dialog.accept)

    card_layout.addWidget(title_label)
    card_layout.addWidget(intro_label)
    card_layout.addSpacing(6)
    card_layout.addLayout(columns_grid)
    card_layout.addSpacing(6)
    card_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignHCenter)

    state.welcome_dialog_ref = dialog
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
