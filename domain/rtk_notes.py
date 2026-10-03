"""Pure helpers for Heisig-CSV-driven RTK note data. No Anki/collection access."""


def heisig_number_and_edition(row: dict) -> tuple[int, str]:
    """
    Return (number, edition). Prefers 6th edition, falls back to 5th.
    Missing on both -> (99999, "").
    """
    for key, edition in (("id_6th_ed", "6th"), ("id_5th_ed", "5th")):
        raw = (row.get(key) or "").strip()
        if raw:
            try:
                return int(raw), edition
            except ValueError:
                pass
    return 99999, ""


def sixth_edition_number(row: dict) -> int | None:
    """
    Return the 6th-edition Heisig number only (NO 5th-ed fallback), or None
    if absent/invalid.

    Deliberately narrower than heisig_number_and_edition: the "bulk create up
    to kanji #2200" ranges in rtk_service.py are 6th-edition-specific and
    must not silently pick up a 5th-ed-only row.
    """
    raw = (row.get("id_6th_ed") or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def heisig_keyword(row: dict, prefer_6th: bool = True) -> str:
    """Return the Heisig keyword for a row, preferring one edition over the other."""
    order = ("keyword_6th_ed", "keyword_5th_ed") if prefer_6th else ("keyword_5th_ed", "keyword_6th_ed")
    for key in order:
        val = (row.get(key) or "").strip()
        if val:
            return val
    return ""


def heisig_kanji(row: dict) -> str:
    """Return the kanji character for a Heisig CSV row."""
    return (row.get("kanji") or "").strip()


def sort_kanji_by_sixth_edition(rows: dict[str, dict]) -> list[str]:
    """Sort kanji keys by their 6th-ed Heisig number; missing/invalid sort last."""
    def sort_key(kanji: str) -> int:
        num = sixth_edition_number(rows[kanji])
        return num if num is not None else 99999
    return sorted(rows.keys(), key=sort_key)


def build_rtk_field_values(row: dict, kanji_meanings: list[str] | None = None) -> dict[str, str]:
    """
    Given one Heisig CSV row (+ optionally preloaded meanings), compute the
    values that could be filled onto an RTK note.

    Keys are abstract concepts ("keyword", "heisig_number", ...), not config
    field names — the caller maps these onto the user's configured field
    names (rtk_keyword_field, rtk_heisig_number_field, etc.).
    """
    num, _edition = heisig_number_and_edition(row)
    return {
        "keyword": heisig_keyword(row),
        "heisig_number": str(num) if num != 99999 else "",
        "stroke_count": (row.get("stroke_count") or "").strip(),
        "meanings": " · ".join(m for m in (kanji_meanings or []) if m),
        "note": (row.get("note") or "").strip(),
    }
