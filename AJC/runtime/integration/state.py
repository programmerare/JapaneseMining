# -*- coding: utf-8 -*-
"""Shared runtime state for Anki Jisho Connect integrations."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui.config_dialog import ConfigDialog
    from ..ui.results_dialog import ResultsDialog


results_dialog: Optional["ResultsDialog"] = None
config_dialog: Optional["ConfigDialog"] = None
about_dialog_ref: Any = None
welcome_dialog_ref: Any = None
quick_fill_jobs: list[tuple[Any, Any]] = []
