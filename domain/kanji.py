import unicodedata


def fetch_kanji_meanings(kanji: str) -> list[str]:
    """Fetch English meanings for a kanji from Jamdict's Chars section."""
    if not kanji:
        return []

    meanings = globals.kanji_dictionary.get(kanji)

    if not meanings:
        return []

    return meanings


def is_kanji(char):
    """Return True if char is a kanji."""
    try:
        return unicodedata.name(char).startswith("CJK UNIFIED IDEOGRAPH")
    except ValueError:
        return False
