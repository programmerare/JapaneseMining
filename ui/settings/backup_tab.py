"""
Backup tab for JapaneseMining Settings.

Create / list / restore RTK deck snapshots. Restore always targets a *new*
deck so the live RTK deck is never overwritten by accident.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aqt import mw
from aqt.qt import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    Qt,
)
from aqt.utils import showInfo, showWarning, tooltip

from ...config import ConfigHolder
from ...domain.errors import JapaneseMiningError
from ..ui_styles import (
    make_callout,
    make_instruction_label,
    make_primary_button,
    make_scrollable_page,
    make_secondary_button,
    make_section_card,
    TEXT_MUTED,
    TEXT_SECONDARY,
)


def _format_created_at(iso: str) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso[:16] if len(iso) >= 16 else iso


def _format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def make_backup_tab(
    config_holder: ConfigHolder,
    backup_service,
    save_config_fn=None,
    on_rtk_mapping_updated=None,
):
    """
    Returns (widget, title, apply_to_config_fn).

    Restore always creates a new deck. The user renames / remaps in RTK
    settings if they want the restored deck to become the active RTK deck.
    """
    outer, layout = make_scrollable_page()

    layout.addWidget(
        make_instruction_label(
            "Snapshot the configured RTK deck (fields, tags, and full card "
            "scheduling including FSRS state when available). Restore always "
            "creates a new deck so your current RTK deck is never overwritten."
        )
    )

    layout.addWidget(
        make_callout(
            "Backups are taken directly from the live RTK deck — not from the "
            "learned_kanji cache. Keep the RTK deck mapped correctly in the RTK tab "
            "before creating a backup. After a restore, rename the new deck and "
            "update Deck Mapping if you want to use it as your RTK deck.",
            kind="info",
        )
    )

    # ── Create ────────────────────────────────────────────────────────────
    create_card, create_cl = make_section_card("Create backup")
    create_cl.addWidget(
        QLabel(
            "Captures every note in the configured RTK deck, including field "
            "values, tags, and per-card scheduling state."
        )
    )
    create_row = QHBoxLayout()
    create_btn = make_primary_button("Create backup now")
    create_status = QLabel("")
    create_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    create_row.addWidget(create_btn)
    create_row.addWidget(create_status, 1)
    create_cl.addLayout(create_row)
    layout.addWidget(create_card)

    # ── List ──────────────────────────────────────────────────────────────
    list_card, list_cl = make_section_card("Available backups (newest first)")
    list_hint = QLabel("Select a backup, then restore it into a new deck.")
    list_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
    list_cl.addWidget(list_hint)

    backup_list = QListWidget()
    backup_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    backup_list.setMinimumHeight(220)
    backup_list.setStyleSheet(
        """
        QListWidget {
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 4px;
            font-size: 13px;
        }
        QListWidget::item {
            padding: 8px 10px;
            border-bottom: 1px solid #f0f0f0;
        }
        QListWidget::item:selected {
            background: #e8f0fe;
            color: #174ea6;
        }
        """
    )
    list_cl.addWidget(backup_list)

    empty_label = QLabel("No backups yet. Create one above.")
    empty_label.setStyleSheet(
        f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;"
    )
    empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    list_cl.addWidget(empty_label)

    path_label = QLabel("")
    path_label.setWordWrap(True)
    path_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
    list_cl.addWidget(path_label)

    layout.addWidget(list_card)

    # ── Restore ───────────────────────────────────────────────────────────
    restore_card, restore_cl = make_section_card("Restore")
    restore_cl.addWidget(
        make_callout(
            "Restore creates a new deck (default name Backup_YYYY-MM-DD_HHMM). "
            "Your current RTK deck and Deck Mapping are left untouched. "
            "Rename the deck and point RTK mapping at it if you want to switch.",
            kind="warning",
        )
    )

    restore_row = QHBoxLayout()
    restore_btn = make_secondary_button("Restore selected → new deck")
    restore_btn.setEnabled(False)
    refresh_btn = make_secondary_button("Refresh list")
    restore_row.addWidget(restore_btn)
    restore_row.addWidget(refresh_btn)
    restore_row.addStretch(1)
    restore_cl.addLayout(restore_row)
    layout.addWidget(restore_card)

    layout.addStretch()

    # ── logic ─────────────────────────────────────────────────────────────
    PATH_ROLE = Qt.ItemDataRole.UserRole

    def refresh_list():
        backup_list.clear()
        try:
            items = backup_service.list_backups()
        except Exception as e:
            showWarning(
                f"Could not list backups:\n{e}", parent=mw, title="JapaneseMining"
            )
            items = []

        empty_label.setVisible(not items)
        backup_list.setVisible(bool(items))

        for meta in items:
            created = _format_created_at(meta.get("created_at") or "")
            deck = meta.get("source_deck") or "?"
            entries = meta.get("entry_count") or 0
            learned = meta.get("learned_count") or 0
            size = _format_size(int(meta.get("size_bytes") or 0))
            label = (
                f"{created}   ·   {deck}   ·   "
                f"{entries} notes ({learned} learned)   ·   {size}"
            )
            item = QListWidgetItem(label)
            item.setData(PATH_ROLE, meta.get("path") or "")
            backup_list.addItem(item)

        try:
            path_label.setText(f"Storage: {backup_service.backups_dir()}")
        except Exception:
            path_label.setText("")

        restore_btn.setEnabled(False)

    def on_selection_changed():
        restore_btn.setEnabled(bool(backup_list.selectedItems()))

    def on_create():
        create_btn.setEnabled(False)
        create_status.setText("Creating…")
        try:
            path = backup_service.create_backup()
            create_status.setText(f"Saved: {Path(path).name}")
            tooltip("Backup created.", parent=mw)
            refresh_list()
        except JapaneseMiningError as e:
            create_status.setText("")
            showWarning(e.full_message(), parent=mw, title="JapaneseMining")
        except Exception as e:
            create_status.setText("")
            showWarning(f"Backup failed:\n\n{e}", parent=mw, title="JapaneseMining")
        finally:
            create_btn.setEnabled(True)

    def on_restore():
        selected = backup_list.selectedItems()
        if not selected:
            return
        path = selected[0].data(PATH_ROLE)
        if not path:
            return

        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        default_deck = f"Backup_{stamp}"

        msg = (
            f"Restore this backup into a new deck?\n\n"
            f"Deck name: {default_deck}\n"
            f"Source file: {Path(path).name}\n\n"
            "The current RTK deck and settings will not be modified."
        )

        reply = QMessageBox.question(
            mw,
            "JapaneseMining — Restore backup",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        restore_btn.setEnabled(False)
        try:
            result = backup_service.restore_to_new_deck(
                path,
                deck_name=default_deck,
            )
            n = getattr(result, "kanji_added_to_rtk", 0) or 0
            showInfo(
                f"Restored {n} notes into deck “{default_deck}”.\n\n"
                "Your RTK mapping is unchanged. Rename the deck and update "
                "Settings → RTK → Deck Mapping if you want to use it.",
                parent=mw,
                title="JapaneseMining",
            )
        except JapaneseMiningError as e:
            showWarning(e.full_message(), parent=mw, title="JapaneseMining")
        except Exception as e:
            showWarning(f"Restore failed:\n\n{e}", parent=mw, title="JapaneseMining")
        finally:
            restore_btn.setEnabled(bool(backup_list.selectedItems()))

    create_btn.clicked.connect(on_create)
    restore_btn.clicked.connect(on_restore)
    refresh_btn.clicked.connect(refresh_list)
    backup_list.itemSelectionChanged.connect(on_selection_changed)

    refresh_list()

    def apply_to_config(_cfg):
        pass

    return outer, "Backup", apply_to_config
