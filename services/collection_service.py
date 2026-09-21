from aqt import mw
from anki.notes import Note, NoteId
from anki.cards import Card, CardId
from anki.decks import Deck, DeckId
from anki.models import FieldDict
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

    def _media_path(self, filename: str) -> Path | None:
        """Return the full path to a file in the Anki media directory."""
        if not isinstance(filename, str):
            raise TypeError(f"_media_path expects a string, got {type(filename).__name__}")
        return Path(mw.col.media.dir()) / filename

    def get_models(self):
        """Return a list of all models (note types) in the collection."""
        return mw.col.models

    def get_model_by_name(self, model_name: str):
        """Return the model (note type) with the given name, or None if not found."""
        if not isinstance(model_name, str):
            raise TypeError(f"get_model_by_name expects a string, got {type(model_name).__name__}")
        return mw.col.models.by_name(model_name)

    def update_note(self, note: Note):
        """Update a note in the collection."""
        if not isinstance(note, Note):
            raise TypeError(f"update_note expects a Note, got {type(note).__name__}")
        mw.col.update_note(note)
    
    def get_note_by_note_id(self, note_id: NoteId):
        """Return the note with the given ID, or None if not found."""
        if not isinstance(note_id, NoteId):
            raise TypeError(f"get_note_by_note_id expects a NoteId, got {type(note_id).__name__}")
        return mw.col.get_note(note_id)
    
    def get_note_by_card_id(self, card_id: CardId):
        """Return the note associated with the given card ID, or None if not found."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_note_by_card_id expects a CardId, got {type(card_id).__name__}")
        return mw.col.get_card(card_id).note()
    
    def find_notes_by_query(self, query: str):
        """Return a list of notes (note ids) matching the given query."""
        if not isinstance(query, str):
            raise TypeError(f"find_notes_by_query expects a string, got {type(query).__name__}")
        return mw.col.find_notes(query)
    
    def get_card_stats_data_by_card_id(self, card_id: CardId):
        """Return the card stats for the given card id."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_card_stats_data_by_card_id expects a CardId, got {type(card_id).__name__}")
        return mw.col.card_stats_data(card_id)
    
    def find_cards_by_query(self, query: str):
        """Return a list of cards (card ids) matching the given query."""
        if not isinstance(query, str):
            raise TypeError(f"find_cards_by_query expects a string, got {type(query).__name__}")
        return mw.col.find_cards(query)
    
    def get_card_by_card_id(self, card_id: CardId):
        """Return the card with the given ID, or None if not found."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_card_by_card_id expects a CardId, got {type(card_id).__name__}")
        return mw.col.get_card(card_id)

    def get_decks(self):
        """Return a list of all decks in the collection."""
        return mw.col.decks

    def get_deck_name_by_card_id(self, card_id: CardId):
        """Return the deck name for the given card id."""
        if not isinstance(card_id, CardId):
            raise TypeError(f"get_deck_name_by_card_id expects a CardId, got {type(card_id).__name__}")
        card = mw.col.get_card(card_id)
        if not card:
            return None
        return mw.col.decks.name(card.did)
    
    def get_deck_id_by_deck_name(self, deck_name: str):
        """Return the deck id for the given deck name."""
        if not isinstance(deck_name, str):
            raise TypeError(f"get_deck_id_by_deck_name expects a string, got {type(deck_name).__name__}")
        return mw.col.decks.id(deck_name)
    
    def add_note(self, note: Note, deck_id: DeckId):
        """Add a note to the collection in the specified deck."""
        if not isinstance(note, Note):
            raise TypeError(f"add_note expects a Note, got {type(note).__name__}")
        if not isinstance(deck_id, DeckId):
            raise TypeError(f"add_note expects a DeckId (int), got {type(deck_id).__name__}")
        return mw.col.add_note(note, deck_id)

    def add_model(self, model_name: str):
        """Add a new model (note type) to the collection with the given name."""
        if not isinstance(model_name, str):
            raise TypeError(f"add_model expects a string, got {type(model_name).__name__}")
        return mw.col.models.new(model_name)
    
    def create_new_model_field(self, field_name: str):
        """Create a new field in the given model (note type) with the specified name."""
        if not isinstance(field_name, str):
            raise TypeError(f"create_new_model_field expects a string, got {type(field_name).__name__}")
        return mw.col.models.new_field(field_name)
    
    def add_field_to_model(self, model, field: FieldDict):
        """Add a field to the given model (note type)."""
        if not isinstance(field, dict):
            raise TypeError(f"add_field_to_model expects a FieldDict (dict), got {type(field).__name__}")
        return mw.col.models.add_field(model, field)
    
    def create_new_model_card_template(self, name: str):
        """Create a new card template with the specified name."""
        if not isinstance(name, str):
            raise TypeError(f"create_new_model_card_template expects a string, got {type(name).__name__}")
        return mw.col.models.new_template(name)
    
    def add_template_to_model(self, model, template):
        """Add a card template to the given model (note type)."""
        return mw.col.models.add_template(model, template)
    
    def add_css_to_model(self, model, css: str):
        """Add CSS to the given model (note type)."""
        model["css"] = css
    
    def add_question_format_to_template(self, template, question_format: str):
        """Add a question format to the specified card template in the given model (note type)."""
        if not isinstance(question_format, str):
            raise TypeError(f"add_question_format_to_template expects a string, got {type(question_format).__name__}")
        template["qfmt"] = question_format
        return template
    
    def add_answer_format_to_template(self, template, answer_format: str):
        """Add an answer format to the specified card template in the given model (note type)."""
        if not isinstance(answer_format, str):
            raise TypeError(f"add_answer_format_to_template expects a string, got {type(answer_format).__name__}")
        template["afmt"] = answer_format
        return template
    
    def add_model_to_models(self, model):
        """Add a model (note type) to the collection."""
        return mw.col.models.add(model)
    
    def get_fields_from_model(self, model):
        """Return a list of field names for the given model (note type)."""
        if not model:
            return []
        return [field["name"] for field in model["flds"]]
    
    def update_card(self, card: Card):
        """Update a card in the collection."""
        if not isinstance(card, Card):
            raise TypeError(f"update_card expects a Card, got {type(card).__name__}")
        mw.col.update_card(card)
    