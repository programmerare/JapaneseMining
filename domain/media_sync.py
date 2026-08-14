"""
Ensure reference data files exist in the collection media folder
and stay in sync with the copies shipped inside the add-on.

Contract
--------
- Only the files listed in REFERENCE_FILES may be overwritten.
- User progress files (learned_kanji.csv, todays_words.csv)
  must never be touched by this module.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

# Files that ship with the add-on and may be updated on every install/upgrade.
DATA_FILES = (
    ("heisig_kanji.csv", "heisig_kanji.csv"),
    ("kanji_meanings.xml", "kanji_meanings.xml"),
)

FONT_FILES = (
    ("fonts/_HGRKK.ttc", "_HGRKK.ttc"),
    ("fonts/_StrokeOrder.ttf", "_StrokeOrder.ttf"),
    ("fonts/_YUGOTHB.ttc", "_YUGOTHB.ttc"),
)

# Keep the source of truth next to the package, not in media.
_ADDON_ROOT = Path(__file__).resolve().parent.parent
_VENDOR_DIR = _ADDON_ROOT / "vendor"


def _file_hash(path: Path, chunk_size: int = 65536) -> str:
    """Return a short content hash. Used to decide whether a copy is needed."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_reference_files(media_dir: str | Path) -> list[str]:
    """
    Copy / refresh reference files into the collection media folder.

    Returns a list of filenames that were actually written (useful for logging).
    Safe to call multiple times; never touches user progress files.
    """
    media = Path(media_dir)
    media.mkdir(parents=True, exist_ok=True)

    updated: list[str] = []

    for src_rel, dst_name in DATA_FILES + FONT_FILES:
        src = _VENDOR_DIR / src_rel
        dst = media / dst_name

        if not src.exists():
            print(f"Reference file missing from add-on package: {src}")
            # Packaging error – surface it early instead of failing later.
            raise FileNotFoundError(
                f"Reference file missing from add-on package: {src}"
            )

        needs_copy = False
        if not dst.exists():
            needs_copy = True
        else:
            # Content comparison is more reliable than mtime across
            # zip extraction, different OSes, and Anki media handling.
            try:
                if _file_hash(src) != _file_hash(dst):
                    needs_copy = True
            except OSError:
                # If we cannot read the destination, force a fresh copy.
                needs_copy = True

        if needs_copy:
            shutil.copy2(src, dst)
            updated.append(dst_name)

    return updated
