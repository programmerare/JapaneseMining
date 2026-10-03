"""Generic extraction of a numeric FSRS stat from an Anki stats/memory-state object."""


def extract_stat(obj, attr_names: tuple[str, ...]) -> float | None:
    """Return the first present, non-None attribute in attr_names as a float."""
    for attr in attr_names:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if value is not None:
                return float(value)
    return None
