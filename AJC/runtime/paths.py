# -*- coding: utf-8 -*-
"""Shared filesystem paths for runtime and development helpers."""

from pathlib import Path


RUNTIME_DIR = Path(__file__).resolve().parent
ADDON_ROOT = RUNTIME_DIR.parent
ASSETS_DIR = ADDON_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
WEB_DIR = ASSETS_DIR / "web"
USER_DATA_DIR = ADDON_ROOT / "user_data"
LOGS_DIR = USER_DATA_DIR / "logs"
CONFIG_PATH = USER_DATA_DIR / "config.json"
LEGACY_CONFIG_PATH = ADDON_ROOT / "config.json"


def icon_path(name: str) -> Path:
    return ICONS_DIR / name


def image_path(name: str) -> Path:
    return IMAGES_DIR / name


def web_path(name: str) -> Path:
    return WEB_DIR / name


def root_relative(path: Path) -> str:
    return path.resolve().relative_to(ADDON_ROOT).as_posix()
