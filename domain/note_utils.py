from anki.notes import Note


def has_field(note: Note, name: str) -> bool:
    """Check if a note has a field with the given name."""
    return name in note


def get_field(note: Note, name: str, default: str = "") -> str:
    """Get the value of a field in a note."""
    return note[name] if name in note else default