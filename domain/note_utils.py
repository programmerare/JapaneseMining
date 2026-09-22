from anki.notes import Note


def has_field(note: Note, name: str) -> bool:
    """Check if a note has a field with the given name."""
    if not isinstance(note, Note):
        raise TypeError(f"has_field expects a Note, got {type(note).__name__}")
    if not isinstance(name, str):
        raise TypeError(f"has_field expects a string for name, got {type(name).__name__}")
    return name in note


def get_field(note: Note, name: str, default: str = "") -> str:
    """Get the value of a field in a note."""
    if not isinstance(note, Note):
        raise TypeError(f"get_field expects a Note, got {type(note).__name__}")
    if not isinstance(name, str):
        raise TypeError(f"get_field expects a string for name, got {type(name).__name__}")
    if not isinstance(default, str):
        raise TypeError(f"get_field expects a string for default, got {type(default).__name__}")
    return note[name] if name in note else default