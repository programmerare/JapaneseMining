import math
from dataclasses import dataclass

from anki.notes import Note

from ..cards.mining_card_template import (
    MINING_FORWARD_FRONT_HTML,
    MINING_FORWARD_BACK_HTML,
    MINING_BACKWARD_FRONT_HTML,
    MINING_BACKWARD_BACK_HTML,
    MINING_CARD_CSS,
)
from .collection_service import CollectionService
from ..config import ConfigHolder, is_valid_mining_note_type
from ..domain.errors import JapaneseMiningError
from ..domain.kanji import is_kanji
from ..domain.model_utils import set_model_field_size, set_model_field_font, set_model_sort_field, set_model_css, get_fields_from_model
from ..domain.note_utils import get_note_type_name, get_field
from ..domain.notetype_utils import set_template_question_format, set_template_answer_format
from ..domain.results import UpdateResult


@dataclass
class _KanjiFieldPlan:
    no_kanji: bool = False
    usually_kana: bool = False
    kanji_is_known: str | None = None   # None = leave unchanged
    keywords: str | None = None
    meanings: str | None = None
    newly_known: bool = False

    @property
    def should_update(self) -> bool:
        return any([
            self.no_kanji, self.usually_kana,
            self.kanji_is_known is not None,
            self.keywords is not None,
            self.meanings is not None,
        ])

class MiningService:
    def __init__(self, config_holder: ConfigHolder, collection_service: CollectionService):
        self._config_holder = config_holder
        self._collection_service = collection_service

    @property
    def _config(self):
        return self._config_holder.config

    def soft_update_everything(self) -> UpdateResult:
        return self.update_japanese_mining_cards()

    def force_update_keywords(self) -> UpdateResult:
        return self.update_japanese_mining_cards(force_update_keywords=True)

    def force_update_meanings(self) -> UpdateResult:
        return self.update_japanese_mining_cards(force_update_meanings=True)

    def force_update_everything(self) -> UpdateResult:
        return self.update_japanese_mining_cards(
            force_update_meanings=True, force_update_keywords=True
        )

    def update_single_note_kanji_knowledge(
        self,
        note: Note,
        force_update_meanings: bool = False,
        force_update_keywords: bool = False,
    ) -> tuple[int, int]:
        """
        Update kanji fields for a single note added from the editor.
        Does not raise an exception on note type missmatch, in order to not interrupt the user with errors from JapaneseMining while adding a note of a different type.
        Returns (newly_known_count, updated_count).
        """
        if not isinstance(note, Note):
            raise TypeError(f"update_single_note_kanji_knowledge expects a Note, got {type(note).__name__}")
        if not is_valid_mining_note_type(get_note_type_name(note), self._config):
            return 0, 0

        return self._update_kanji_knowledge(
            note=note,
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )

    def update_japanese_mining_cards(
        self, force_update_meanings: bool = False, force_update_keywords: bool = False
    ) -> UpdateResult:
        """
        Update all JapaneseMining cards in a single pass over each word.
        Intended to be called from a CollectionOp.
        """
        export_result = self.export_learned_kanji()
        cards_newly_known, cards_updated = self._update_kanji_knowledge(
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        kanji_added_to_rtk = self.add_unknown_kanji()

        return UpdateResult(
            learned_kanji=export_result.learned_kanji,
            not_learned_kanji=export_result.not_learned_kanji,
            cards_newly_known=cards_newly_known,
            cards_updated=cards_updated,
            kanji_added_to_rtk=kanji_added_to_rtk if kanji_added_to_rtk else 0,
        )

    # get_or_create_mining_note_type
    def create_mining_note_type(
        self,
        note_type_name: str = "JapaneseMining",
        *,
        set_as_default: bool = True,
    ) -> tuple[bool, str]:
        """Create (or reuse) the canonical JapaneseMining note type."""
        note_type_name = (note_type_name or "").strip() or "JapaneseMining"

        model = self._collection_service.get_model_by_name(note_type_name)
        model_missing = model is None

        if model_missing:
            model = self._build_mining_model(note_type_name)
        else:
            missing = [
                f for f in self._REQUIRED_MINING_FIELDS
                if f not in get_fields_from_model(model)
            ]
            if missing:
                return False, (
                    
                    f"Note type “{note_type_name}” already exists but is missing "
                    f'required fields: {", ".join(missing)}. '
                    "Choose a different name or add the missing fields manually."
                )

        self._apply_mining_config(note_type_name, set_as_default=set_as_default)

        if model_missing:
            return True, f"Created note type “{note_type_name}”."
        return True, f"Re-used existing note type “{note_type_name}”."

    def _build_mining_model(self, note_type_name: str):
        """Impure: builds a brand-new mining note type via CollectionService."""
        model = self._collection_service.create_new_model(note_type_name)

        # Add required fields
        for name in self._REQUIRED_MINING_FIELDS:
            field = self._collection_service.create_new_model_field(name)
            field = set_model_field_size(field, 12)
            field = set_model_field_font(field, "Arial")
            self._collection_service.add_field_to_model(model, field)

        model = set_model_sort_field(model, 0) # Sort by Word

        # Add Forward and Backward card templates
        fwd = self._collection_service.create_new_model_card_template("Forward")
        fwd = set_template_question_format(fwd, MINING_FORWARD_FRONT_HTML)
        fwd = set_template_answer_format(fwd, MINING_FORWARD_BACK_HTML)
        self._collection_service.add_template_to_model(model, fwd)

        bwd = self._collection_service.create_new_model_card_template("Backward")
        bwd = set_template_question_format(bwd, MINING_BACKWARD_FRONT_HTML)
        bwd = set_template_answer_format(bwd, MINING_BACKWARD_BACK_HTML)
        self._collection_service.add_template_to_model(model, bwd)

        # Set the model CSS
        model = set_model_css(model, MINING_CARD_CSS)
        self._collection_service.add_model(model)
        return model

    def _apply_mining_config(self, note_type_name: str, *, set_as_default: bool = True):
        """Pure-ish: mutates config state only, no Anki calls."""
        if note_type_name not in self._config.mining_note_types:
            self._config.mining_note_types.append(note_type_name)
        if set_as_default:
            self._config.mining_note_type = note_type_name

    def _update_note_kanji_knowledge(
        self,
        note: Note,
        learned_kanji: dict,
        force_update_meanings: bool = False,
        force_update_keywords: bool = False,
    ) -> tuple[int, int]:
        """Update kanji knowledge fields for one note."""
        if not self._mining_fields_ok(note):
            raise JapaneseMiningError(
                f"Note {note.id} is missing required fields. Please check your note and your notetype {self._config.mining_note_type}.",
                details=f"Missing fields: {', '.join(f for f in self._REQUIRED_MINING_FIELDS if f not in note)}",
            )

        plan = self._plan_kanji_field_updates(
            note, learned_kanji,
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords
        )
        self._apply_kanji_plan(note, plan)

        if plan.should_update:
            self._collection_service.update_note(note)

        return int(plan.newly_known), int(plan.should_update)

    def _plan_kanji_field_updates(
        self,
        note: Note,
        learned_kanji: dict,
        *,
        force_update_meanings: bool,
        force_update_keywords: bool
    ) -> _KanjiFieldPlan:
        """
        Decide WHAT should change — doesn't touch the note or the collection.
        Only impure edge: self._kanji_data.get_kanji_meanings (an injected lookup).
        """
        word = get_field(note, "Word")
        keywords_present = bool(get_field(note, "Kanji Keywords"))
        meanings_present = bool(get_field(note, "Kanji Meanings"))

        keywords: list[str] = []
        meanings: list[str] = []
        all_known = True
        no_kanji = True

        for ch in word:
            if not is_kanji(ch):
                continue
            no_kanji = False
            entry = learned_kanji.get(ch)
            if not entry or not entry.get("Learned"):
                all_known = False

            if not keywords_present or force_update_keywords:
                kw = (entry.get("Keyword") if entry else None) or "not known"
                line = f"{ch}: {kw}"
                if line not in keywords:
                    keywords.append(line)

            if not meanings_present or force_update_meanings:
                joined = " · ".join(self._kanji_data.get_kanji_meanings(ch))
                line = f"{ch}: {joined}"
                if line not in meanings:
                    meanings.append(line)

        plan = _KanjiFieldPlan()

        if no_kanji and get_field(note, "No Kanji") != "1":
            plan.no_kanji = True

        if (
            "Usually written using kana alone" in get_field(note, "Tags")
            and get_field(note, "Usually Kana") != "1"
        ):
            plan.usually_kana = True

        previous_known = get_field(note, "Kanji is known")
        new_known = "1" if all_known else ""
        if previous_known != new_known:
            plan.kanji_is_known = new_known
            plan.newly_known = previous_known != "1" and new_known == "1"

        if keywords:
            plan.keywords = " · ".join(keywords)
        if meanings:
            plan.meanings = " | ".join(meanings)

        return plan

    def _apply_kanji_plan(self, note: Note, plan: _KanjiFieldPlan):
        """Write the plan onto the note object. Impure (mutates note), but no I/O yet."""
        if plan.no_kanji:
            note["No Kanji"] = "1"
            note["Usually Kana"] = "1"
        if plan.usually_kana:
            note["Usually Kana"] = "1"
        if plan.kanji_is_known is not None:
            note["Kanji is known"] = plan.kanji_is_known
            if plan.newly_known:
                # Genuine I/O side effect — writing to today's-known-card log.
                self._kanji_data_save_todays_known_card(
                    get_field(note, "Word"),
                    get_field(note, "Reading"),
                    get_field(note, "Meaning"),
                )
        if plan.keywords is not None:
            note["Kanji Keywords"] = plan.keywords
        if plan.meanings is not None:
            note["Kanji Meanings"] = plan.meanings

    def _update_kanji_knowledge(
        self,
        note: Note = None,
        force_update_meanings: bool = False,
        force_update_keywords: bool = False,
    ) -> tuple[int, int]:
        """Update JapaneseMining cards in a single pass over each word."""
        learned_kanji = self._kanji_data.get_learned_kanji()
        if note is not None:
            notes = [note]
        else:
            notes = (
                self.self._collection_service.get_note_by_note_id(note_id)
                for note_id in self._collection_service.find_notes_by_query(
                    f"note:{self._config.mining_note_type}"
                )
            )

        newly_known_count = 0
        updated_count = 0
        for current_note in notes:
            note_newly_known, note_updated = self._update_note_kanji_knowledge(
                current_note, learned_kanji,
                force_update_meanings=force_update_meanings,
                force_update_keywords=force_update_keywords,
            )
            newly_known_count += note_newly_known
            updated_count += note_updated

        return newly_known_count, updated_count

    def _mining_fields_ok(self, note: Note) -> bool:
        """Check if a JapaneseMining note has all required fields."""
        return all(name in note for name in self._REQUIRED_MINING_FIELDS)

    @staticmethod
    def _score_knowledge(stability: float | None, retrievability: float | None) -> float:
        """Pure: turn raw FSRS numbers into a 0..1 score. No Anki objects — fully unit-testable."""
        if stability is None or stability <= 0:
            return 0.0
        S_MAX = 365.0
        stab_norm = min(1.0, math.log1p(stability) / math.log1p(S_MAX))
        r = 0.9 if retrievability is None else max(0.0, min(1.0, retrievability))
        return max(0.0, min(1.0, 0.75 * stab_norm + 0.25 * r))

    def _get_card_knowledge(self, card) -> float:
        """
        Impure: extracts stability/retrievability from Anki's card stats,
        then hands off to the pure scorer above.

        NOTE: near-duplicate of a method in rtk_service.py — both Mining and
        RTK need this. Good candidate for domain/card_knowledge.py once we're
        touching that file; leaving the duplication in place for now since
        we're scoped to mining_service.py this round.
        """
        if card.type == 0:
            return 0.0

        stability = retrievability = None
        try:
            stats = self._collection_service.get_card_stats_data_by_card_id(card.id)
            for attr in ("stability", "fsrs_stability", "s"):
                if hasattr(stats, attr) and getattr(stats, attr) is not None:
                    stability = float(getattr(stats, attr))
                    break
            for attr in ("retrievability", "fsrs_retrievability", "r"):
                if hasattr(stats, attr) and getattr(stats, attr) is not None:
                    retrievability = float(getattr(stats, attr))
                    break
        except Exception:
            pass

        if stability is None:
            try:
                ms = getattr(card, "memory_state", None)
                if ms is not None and getattr(ms, "stability", None) is not None:
                    stability = float(ms.stability)
            except Exception:
                pass

        return self._score_knowledge(stability, retrievability)