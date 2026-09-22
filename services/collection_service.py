from aqt import mw
from anki.cards import Card, CardId
from anki.collection import OpChangesWithCount, OpChangesWithId, OpChanges
from anki.decks import DeckId, DeckDict
from anki.models import FieldDict, NotetypeDict, TemplateDict
from anki.notes import Note, NoteId
from anki.stats_pb2 import CardStatsResponse
from pathlib import Path

from ..config import ConfigHolder, REQUIRED_MINING_FIELDS, is_valid_mining_note_type
from .kanji_data_service import KanjiDataService
from ..domain.kanji import is_kanji
from ..domain.errors import JapaneseMiningError
from ..domain.results import UpdateResult
from ..cards.mining_card_template import (
    MINING_FORWARD_FRONT_HTML,
    MINING_FORWARD_BACK_HTML,
    MINING_BACKWARD_FRONT_HTML,
    MINING_BACKWARD_BACK_HTML,
    MINING_CARD_CSS,
)
from ..cards.rtk_card_template import RTK_FRONT_HTML, RTK_BACK_HTML, RTK_CARD_CSS
from ..domain.note_utils import get_field

class CollectionService:
    _HEISIG_KANJI_FILE = "heisig_kanji.csv"
    _REQUIRED_MINING_FIELDS = REQUIRED_MINING_FIELDS

    def __init__(self, config_holder: ConfigHolder, kanji_data: KanjiDataService):
        self._config_holder = config_holder
        self._kanji_data = kanji_data

    @property
    def _config(self):
        return self._config_holder.config

    @property
    def _col(self):
        if not mw.col:
            raise JapaneseMiningError("Anki collection is not open.")
        return mw.col

    def _media_path(self, filename: str) -> Path | None:
        """Return the full path to a file in the Anki media directory."""
        if not isinstance(filename, str):
            raise TypeError(f"_media_path expects a string, got {type(filename).__name__}")
        return Path(self._col.media.dir()) / filename

    def get_models(self) -> list[NotetypeDict]:
        """Return a list of all models (note types) in the collection."""
        return self._col.models

    def get_note_by_note_id(self, note_id: NoteId) -> Note | None:
        """Return the note with the given ID, or None if not found."""
        if not isinstance(note_id, NoteId):
            raise TypeError(f"get_note_by_note_id expects a NoteId, got {type(note_id).__name__}")
        return self._col.get_note(note_id)

    def get_note_by_card_id(self, card_id: CardId) -> Note | None:
        """Return the note associated with the given card ID, or None if not found."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_note_by_card_id expects a CardId, got {type(card_id).__name__}")
        return self._col.get_card(card_id).note()

    def update_note(self, note: Note) -> OpChanges:
        """Update a note in the collection."""
        if not isinstance(note, Note):
            raise TypeError(f"update_note expects a Note, got {type(note).__name__}")
        return self._col.update_note(note)

    def find_notes_by_query(self, query: str) -> list[NoteId]:
        """Return a list of notes (note ids) matching the given query."""
        if not isinstance(query, str):
            raise TypeError(f"find_notes_by_query expects a string, got {type(query).__name__}")
        return self._col.find_notes(query)

    def get_card_by_card_id(self, card_id: CardId) -> Card | None:
        """Return the card with the given ID, or None if not found."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_card_by_card_id expects a CardId, got {type(card_id).__name__}")
        return self._col.get_card(card_id)

    def find_cards_by_query(self, query: str) -> list[CardId]:
        """Return a list of cards (card ids) matching the given query."""
        if not isinstance(query, str):
            raise TypeError(f"find_cards_by_query expects a string, got {type(query).__name__}")
        return self._col.find_cards(query)

    def get_card_stats_data_by_card_id(self, card_id: CardId) -> CardStatsResponse:
        """Return the card stats for the given card id."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_card_stats_data_by_card_id expects a CardId, got {type(card_id).__name__}")
        return self._col.card_stats_data(card_id)

    def get_decks(self) -> list[DeckDict]:
        """Return a list of all decks in the collection."""
        return self._col.decks

    def get_deck_name_by_card_id(self, card_id: CardId) -> str | None:
        """Return the deck name for the given card id."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_deck_name_by_card_id expects a CardId, got {type(card_id).__name__}")
        card = self._col.get_card(card_id)
        if not card:
            return None
        return self._col.decks.name(card.did)
    
    def get_deck_id_by_deck_name(self, deck_name: str) -> DeckId | None:
        """Return the deck id for the given deck name."""
        if not isinstance(deck_name, str):
            raise TypeError(f"get_deck_id_by_deck_name expects a string, got {type(deck_name).__name__}")
        return self._col.decks.id(deck_name)

    def add_note(self, note: Note, deck_id: DeckId) -> OpChangesWithCount:
        """Add a note to the collection in the specified deck."""
        if not isinstance(note, Note):
            raise TypeError(f"add_note expects a Note, got {type(note).__name__}")
        if not isinstance(deck_id, DeckId):
            raise TypeError(f"add_note expects a DeckId (int), got {type(deck_id).__name__}")
        return self._col.add_note(note, deck_id)

    def update_card(self, card: Card) -> OpChanges:
        """Update a card in the collection."""
        if not isinstance(card, Card):
            raise TypeError(f"update_card expects a Card, got {type(card).__name__}")
        return self._col.update_card(card)

    def get_model_by_name(self, model_name: str) -> NotetypeDict | None:
        """Return the model (note type) with the given name, or None if not found."""
        if not isinstance(model_name, str):
            raise TypeError(f"get_model_by_name expects a string, got {type(model_name).__name__}")
        return self._col.models.by_name(model_name)

    def add_model(self, model_name: str) -> NotetypeDict:
        """Add a new model (note type) to the collection with the given name."""
        if not isinstance(model_name, str):
            raise TypeError(f"add_model expects a string, got {type(model_name).__name__}")
        return self._col.models.new(model_name)
    
    def create_new_model_field(self, field_name: str) -> FieldDict:
        """Create a new field in the given model (note type) with the specified name."""
        if not isinstance(field_name, str):
            raise TypeError(f"create_new_model_field expects a string, got {type(field_name).__name__}")
        return self._col.models.new_field(field_name)
    
    def add_field_to_model(self, model: NotetypeDict, field: FieldDict) -> None:
        """Add a field to the given model (note type)."""
        if not isinstance(model, NotetypeDict):
            raise TypeError(f"add_field_to_model expects a NotetypeDict (dict), got {type(model).__name__}")
        if not isinstance(field, FieldDict):
            raise TypeError(f"add_field_to_model expects a FieldDict (dict), got {type(field).__name__}")
        return self._col.models.add_field(model, field)
    
    def create_new_model_card_template(self, name: str) -> TemplateDict:
        """Create a new card template with the specified name."""
        if not isinstance(name, str):
            raise TypeError(f"create_new_model_card_template expects a string, got {type(name).__name__}")
        return self._col.models.new_template(name)
    
    def add_template_to_model(self, model: NotetypeDict, template: TemplateDict) -> None:
        """Add a card template to the given model (note type)."""
        if not isinstance(model, NotetypeDict):
            raise TypeError(f"add_template_to_model expects a NotetypeDict (dict), got {type(model).__name__}")
        if not isinstance(template, TemplateDict):
            raise TypeError(f"add_template_to_model expects a TemplateDict (dict), got {type(template).__name__}")
        return self._col.models.add_template(model, template)
    
    def add_model_to_models(self, model: NotetypeDict) -> OpChangesWithId:
        """Add a model (note type) to the collection."""
        if not isinstance(model, NotetypeDict):
            raise TypeError(f"add_model_to_models expects a NotetypeDict (dict), got {type(model).__name__}")
        return self._col.models.add(model)
    