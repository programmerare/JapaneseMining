import unicodedata


def is_kanji(char):
    """Return True if char is a kanji."""
    try:
        return unicodedata.name(char).startswith("CJK UNIFIED IDEOGRAPH")
    except ValueError:
        return False
