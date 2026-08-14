"""Domain-level exceptions for JapaneseMining.

These carry a short user-facing message and optional longer details.
They are raised by service code and turned into UI by the CollectionOp boundary.
"""


class JapaneseMiningError(Exception):
    """Expected, user-visible failure (missing config, missing file, bad note type, …)."""

    def __init__(self, message: str, *, details: str = "") -> None:
        super().__init__(message)
        self.details = details

    def full_message(self) -> str:
        if self.details:
            return f"{self}\n\n{self.details}"
        return str(self)
