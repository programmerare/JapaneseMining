from anki.models import NotetypeDict, FieldDict

def get_fields_from_model(model: NotetypeDict) -> list[str]:
    """Return a list of field names for the given model (note type)."""
    if not isinstance(model, NotetypeDict):
        raise TypeError(f"get_fields_from_model expects a NotetypeDict (dict), got {type(model).__name__}")
    return [field["name"] for field in model["flds"]]


def set_model_css(model: NotetypeDict, css: str) -> NotetypeDict:
    """Set the CSS of the given model (note type)."""
    if not isinstance(model, NotetypeDict):
        raise TypeError(f"set_model_css expects a NotetypeDict (dict), got {type(model).__name__}")
    if not isinstance(css, str):
        raise TypeError(f"set_model_css expects a string, got {type(css).__name__}")
    model["css"] = css
    return model


def set_model_field_size(field: FieldDict, size: int) -> FieldDict:
    """Set the size of the given field in the model (note type)."""
    if not isinstance(field, FieldDict):
        raise TypeError(f"set_model_field_size expects a FieldDict (dict), got {type(field).__name__}")
    if not isinstance(size, int):
        raise TypeError(f"set_model_field_size expects an int, got {type(size).__name__}")
    field["size"] = size
    return field


def set_model_field_font(field: FieldDict, font: str) -> FieldDict:
    """Set the font of the given field in the model (note type)."""
    if not isinstance(field, FieldDict):
        raise TypeError(f"set_model_field_font expects a FieldDict (dict), got {type(field).__name__}")
    if not isinstance(font, str):
        raise TypeError(f"set_model_field_font expects a string, got {type(font).__name__}")
    field["font"] = font
    return field


def set_model_sort_field(model: NotetypeDict, field_index: int) -> NotetypeDict:
    """Set the sort field of the given model (note type) by field index."""
    if not isinstance(model, NotetypeDict):
        raise TypeError(f"set_model_sort_field expects a NotetypeDict (dict), got {type(model).__name__}")
    if not isinstance(field_index, int):
        raise TypeError(f"set_model_sort_field expects an int, got {type(field_index).__name__}")
    model["sortf"] = field_index
    return model