from ..domain.errors import JapaneseMiningError


def require_rtk_configured(config) -> None:
    if not rtk_configured(config):
        raise JapaneseMiningError(
            "RTK deck is not configured. Please check your settings.",
            details="Open Settings -> RTK and set the deck + fields",
        )

def rtk_configured(config) -> bool:
    return bool(
        config.rtk_deck
        and config.rtk_note_type
        and config.rtk_kanji_field
        and config.rtk_keyword_field
    )