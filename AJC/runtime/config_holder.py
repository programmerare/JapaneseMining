# -*- coding: utf-8 -*-
"""
AJC runtime config holder.

Place this file at: AJC/runtime/config_holder.py

Design B
--------
JapaneseMining registers a resolver via set_config_resolver().
load_config() (in jisho_client) calls resolve_runtime_config(), which
asks that resolver for a flat dict based on the current note's note type.

_RUNTIME_CONFIG remains a fallback snapshot (Settings save / initialize).
"""

from __future__ import annotations

from typing import Any, Callable, Optional

_RUNTIME_CONFIG: dict = {}

# Optional: callable(note=None) -> flat dict. Installed by JishoService.initialize().
_CONFIG_RESOLVER: Optional[Callable[..., dict]] = None


def set_runtime_config(cfg_dict: dict) -> None:
    """Replace the fallback snapshot used when no resolver is installed."""
    global _RUNTIME_CONFIG
    _RUNTIME_CONFIG = cfg_dict if isinstance(cfg_dict, dict) else {}


def get_runtime_config() -> dict:
    """Return the fallback snapshot (not note-aware). Prefer resolve_runtime_config."""
    return _RUNTIME_CONFIG


def set_config_resolver(resolver: Callable[..., dict] | None) -> None:
    """
    Install or clear the note-aware resolver.

    resolver(note=None) must return a flat AJC config dict.
    """
    global _CONFIG_RESOLVER
    _CONFIG_RESOLVER = resolver


def resolve_runtime_config(note: Any = None) -> dict:
    """
    Return the config AJC should use right now.

    1. If a resolver is installed, call it with the note (may be None).
    2. Otherwise return the fallback snapshot.
    """
    if _CONFIG_RESOLVER is not None:
        try:
            resolved = _CONFIG_RESOLVER(note)
            if isinstance(resolved, dict) and resolved:
                return resolved
        except Exception:
            # Never let resolver failures break the add-on; fall through.
            pass
    return _RUNTIME_CONFIG if isinstance(_RUNTIME_CONFIG, dict) else {}
