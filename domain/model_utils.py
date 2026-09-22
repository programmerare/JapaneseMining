from anki.models import NotetypeDict


def get_fields_from_model(model: NotetypeDict) -> list[str]:
    """Return a list of field names for the given model (note type)."""
    if not isinstance(model, NotetypeDict):
        raise TypeError(f"get_fields_from_model expects a NotetypeDict (dict), got {type(model).__name__}")
    return [field["name"] for field in model["flds"]]

def add_css_to_model(model: NotetypeDict, css: str) -> NotetypeDict:
    """Add CSS to the given model (note type)."""
    if not isinstance(model, NotetypeDict):
        raise TypeError(f"add_css_to_model expects a NotetypeDict (dict), got {type(model).__name__}")
    if not isinstance(css, str):
        raise TypeError(f"add_css_to_model expects a string, got {type(css).__name__}")
    model["css"] = css
    return model