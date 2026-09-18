# heisig_csv.py
"""File lookup and parsing for the Heisig kanji CSV data."""
import csv
import shutil
from pathlib import Path

HEISIG_KANJI_FILE = "heisig_kanji.csv"


def resolve_heisig_csv(media_dir: Path, addon_dir: Path) -> Path | None:
    """Prefer media folder, fall back to vendor/ inside the add-on package."""
    media = media_dir / HEISIG_KANJI_FILE
    if media.exists():
        return media

    vendor = addon_dir / "vendor" / HEISIG_KANJI_FILE
    if vendor.exists():
        shutil.copy(vendor, media)
        return media

    return None


def load_heisig_rows(path: Path) -> dict[str, dict]:
    """Load the Heisig CSV into {kanji: row} — used in ~4 places verbatim today."""
    with path.open("r", newline="", encoding="utf-8") as f:
        return {row["kanji"]: row for row in csv.DictReader(f) if row.get("kanji")}


def parse_kanji_file(path: Path) -> list[tuple[str, str]]:
    """
    Accepts:
    - one kanji per line
    - kanji,keyword  (comma or tab)
    Returns list of (kanji, keyword).
    """
    text = path.read_text(encoding="utf-8")
    entries = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line or "\t" in line:
            parts = line.replace("\t", ",").split(",", 1)
            kanji = parts[0].strip()
            keyword = parts[1].strip() if len(parts) > 1 else ""
        else:
            kanji, keyword = line, ""
        if kanji:
            entries.append((kanji, keyword))
    return entries