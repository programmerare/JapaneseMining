from anki.notes import Note


def get_note_type_name(note: Note) -> str:
    """Get the name of the note type for a given note."""
    if not isinstance(note, Note):
        raise TypeError(f"get_note_type_name expects a Note, got {type(note).__name__}")
    return note.note_type()["name"]


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


def set_field(note: Note, name: str, value: str) -> None:
    """Set a field's value if the note has that field. No-op otherwise."""
    if not isinstance(note, Note):
        raise TypeError(f"set_field expects a Note, got {type(note).__name__}")
    if not isinstance(name, str):
        raise TypeError(f"set_field expects a string for name, got {type(name).__name__}")
    if not isinstance(value, str):
        raise TypeError(f"set_field expects a string for value, got {type(value).__name__}")
    if name in note:
        note[name] = value