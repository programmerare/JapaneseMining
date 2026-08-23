# domain/results.py
from dataclasses import dataclass, field
from anki.collection import OpChanges


@dataclass
class UpdateResult:
    """Result of a bulk JapaneseMining update (Soft / Force Update Everything)."""

    learned_kanji: int = 0          # kanji that were already marked learned in the RTK deck
    not_learned_kanji: int = 0      # kanji present in RTK but still new / unseen
    cards_newly_known: int = 0      # mining cards whose "Kanji is known" flipped to true
    cards_updated: int = 0          # mining cards that had any kanji fields rewritten
    kanji_added_to_rtk: int = 0     # unknown kanji that were newly inserted into the RTK deck

    changes: OpChanges = field(default_factory=OpChanges)

    @property
    def message(self) -> str:
        return (
            f"Exported {self.learned_kanji} learned / {self.not_learned_kanji} unlearned kanji; "
            f"{self.cards_newly_known} cards became known, {self.cards_updated} cards updated, {self.kanji_added_to_rtk} kanji added to RTK."
        )

@dataclass
class CreateAndImportResult:
    """Result of a bulk JapaneseMining import (RTK / Heisig)."""

    kanji_imported: int = 0         # kanji that were newly inserted into the RTK deck
    notes_created: int = 0          # mining cards that had any kanji fields rewritten or were added to the RTK deck
    message: str | None = None      # optional message to display to the user

    changes: OpChanges = field(default_factory=OpChanges)

    def __post_init__(self):
        if self.message is None:
            self.message = (
                f"Marked {self.kanji_imported} kanji as known; " 
                f"Created {self.notes_created} note(s)."
            )
