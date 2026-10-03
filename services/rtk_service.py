import random
from pathlib import Path

from anki.notes import Note

from .collection_service import CollectionService
from .kanji_data_service import KanjiDataService
from ..cards.rtk_card_template import RTK_FRONT_HTML, RTK_BACK_HTML, RTK_CARD_CSS
from ..config import ConfigHolder, is_valid_mining_note_type
from ..domain.card_knowledge import get_card_knowledge
from ..domain.errors import JapaneseMiningError
from ..domain.heisig_csv import HEISIG_KANJI_FILE, resolve_heisig_csv, load_heisig_rows, parse_kanji_file
from ..domain.kanji import is_kanji
from ..domain.kanji_learning import (
    CardObservation,
    KanjiLearningState,
    aggregate_kanji_learning_state,
    sort_kanji_by_learned_then_alpha,
)
from ..domain.model_utils import (
    get_fields_from_model,
    set_model_field_size,
    set_model_field_font,
    set_model_sort_field,
    set_model_css,
)
from ..domain.note_utils import get_note_type_name, has_field, get_field, set_field
from ..domain.notetype_utils import set_template_question_format, set_template_answer_format
from ..domain.results import UpdateResult
from ..domain.rtk_notes import (
    heisig_keyword,
    sixth_edition_number,
    sort_kanji_by_sixth_edition,
    build_rtk_field_values,
)


class RTKService():
    _STANDARD_RTK_FIELDS = (
        "Kanji", "Alternative Kanji", "Keyword", "Story", "Note",
        "Meanings", "Heisig Number", "Stroke Count",
    )

    # config attribute name -> standard field name it maps to
    _RTK_FIELD_CONFIG_MAP = {
        "rtk_kanji_field": "Kanji",
        "rtk_alternative_kanji_field": "Alternative Kanji",
        "rtk_keyword_field": "Keyword",
        "rtk_meanings_field": "Meanings",
        "rtk_note_field": "Note",
        "rtk_heisig_number_field": "Heisig Number",
        "rtk_stroke_count_field": "Stroke Count",
    }

    # abstract value key (from build_rtk_field_values) -> config attribute name
    _HEISIG_FILL_MAP = {
        "keyword": "rtk_keyword_field",
        "heisig_number": "rtk_heisig_number_field",
        "stroke_count": "rtk_stroke_count_field",
        "meanings": "rtk_meanings_field",
        "note": "rtk_note_field",
    }

    def __init__(self, config_holder: ConfigHolder, collection_service: CollectionService, kanji_data_service: KanjiDataService):
        self._config_holder = config_holder
        self._collection_service = collection_service
        self._kanji_data_service = kanji_data_service
        self._addon_dir = Path(__file__).resolve().parent.parent

    @property
    def _config(self):
        return self._config_holder.config

    # =========================================================================
    # Public API
    # =========================================================================

    def fetch_kanji_keyword(self, kanji: str) -> str:
        """Return one learned keyword for `kanji` from the RTK deck, or "" if not found."""
        if not isinstance(kanji, str):
            raise TypeError(f"fetch_kanji_keyword expects a str, got {type(kanji).__name__}")
        self._require_rtk_configured()

        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_field = self._config.rtk_alternative_kanji_field
        keyword_field = self._config.rtk_keyword_field

        card_ids = self._collection_service.find_cards_by_query(f'deck:"{deck}" {kanji_field}:{kanji}')
        if not card_ids:
            card_ids = self._collection_service.find_cards_by_query(f'deck:"{deck}" "{alt_field}:{kanji}"')
        if not card_ids:
            return ""

        note = self._collection_service.get_note_by_card_id(card_ids[0])
        return get_field(note, keyword_field)

    def add_kanji_to_rtk_deck(
        self,
        kanji: str,
        *,
        tags: list[str] | None = None,
        heisig_rows: dict[str, dict] | None = None,
    ) -> bool:
        """
        Ensure a single kanji exists as an RTK note.
        Returns True if a new note was added, False if skipped (RTK not
        configured, not a kanji, already present, or the Heisig CSV is missing).
        """
        if not isinstance(kanji, str):
            raise TypeError(f"add_kanji_to_rtk_deck expects a str, got {type(kanji).__name__}")
        if not self._rtk_configured():
            return False

        kanji_char = self._first_kanji_char(kanji)
        if kanji_char is None:
            return False

        if heisig_rows is None:
            heisig_rows = self._load_heisig_rows_up_to(limit=None)
            if heisig_rows is None:
                return False

        if self._find_rtk_note_in_deck(
            kanji_char, deck_name=self._config.rtk_deck, note_type=self._config.rtk_note_type
        ) is not None:
            return False

        note = self._create_rtk_note(kanji=kanji_char, tags=tags or ["Self-Added"], heisig_rows=heisig_rows)
        deck_id = self._collection_service.get_deck_id_by_deck_name(self._config.rtk_deck)
        self._collection_service.add_note(note, deck_id)
        return True

    def add_unknown_kanji(self) -> UpdateResult:
        """Find every unknown kanji in mining notes and add them to the RTK deck."""
        self._require_rtk_configured()

        heisig_rows = self._load_heisig_rows_up_to(limit=None)
        if heisig_rows is None:
            raise JapaneseMiningError(
                f"Could not find {HEISIG_KANJI_FILE}.",
                details=f"Put {HEISIG_KANJI_FILE} in the Anki media folder or in the add-on's vendor/ directory.",
            )

        added = 0
        for kanji in self._find_unknown_kanji():
            if self.add_kanji_to_rtk_deck(kanji, heisig_rows=heisig_rows):
                added += 1
        return UpdateResult(kanji_added_to_rtk=added)

    def ensure_rtk_kanji_for_note(self, note: Note | None) -> int:
        """Add every not-yet-known kanji in `note`'s Word field to the RTK deck. No-ops on None or non-mining notes."""
        if note is None:
            return 0
        if not isinstance(note, Note):
            raise TypeError(f"ensure_rtk_kanji_for_note expects a Note or None, got {type(note).__name__}")
        if not is_valid_mining_note_type(get_note_type_name(note), self._config):
            return 0

        added = 0
        seen: set[str] = set()
        for ch in get_field(note, "Word"):
            if ch in seen or not is_kanji(ch):
                continue
            seen.add(ch)
            if self.add_kanji_to_rtk_deck(ch):
                added += 1
        return added

    def export_learned_kanji(self) -> UpdateResult:
        """
        Rebuild learned_kanji.csv from the configured RTK deck only
        (source of truth). Never modifies notes or cards.
        """
        self._require_rtk_configured()

        observations = list(self._collect_card_observations(
            deck=self._config.rtk_deck,
            kanji_field=self._config.rtk_kanji_field,
            alt_field=self._config.rtk_alternative_kanji_field,
            keyword_field=self._config.rtk_keyword_field,
        ))
        states = aggregate_kanji_learning_state(observations)
        rows, cache, count_learned, count_not_learned = self._build_learned_kanji_export(states)

        if self._kanji_data:
            self._kanji_data.save_learned_kanji(rows, cache)
            self._kanji_data.clear_update_needed()

        return UpdateResult(learned_kanji=count_learned, not_learned_kanji=count_not_learned)

    def get_or_create_rtk_deck_and_note_type(
        self, deck_name: str, note_type_name: str, create_all_notes: bool = True,
    ) -> tuple[bool, str]:
        """Create (or reuse) the RTK note type + deck, optionally bulk-creating Heisig notes."""
        deck_name = (deck_name or "").strip()
        note_type_name = (note_type_name or "").strip()
        if not deck_name or not note_type_name:
            return False, "Deck name and note type name are required."

        model, created = self._get_or_create_rtk_note_type(note_type_name)
        if model is None:
            return False, (
                f"Note type \u201c{note_type_name}\u201d has no usable Kanji/Keyword fields. "
                "Either map them in the Deck Mapping tab first, or choose a note type "
                "that contains fields named Kanji and Keyword. "
                "Recommended: create a fresh note type name so the add-on can build "
                "the full standard RTK note type for you."
            )

        self._collection_service.get_deck_id_by_deck_name(deck_name)  # creates the deck if missing
        self._config.rtk_deck = deck_name
        self._config.rtk_note_type = note_type_name
        self._sync_rtk_field_mappings(model, created=created)

        if not self._config.rtk_kanji_field or not self._config.rtk_keyword_field:
            return False, (
                f"Deck \u201c{deck_name}\u201d and note type \u201c{note_type_name}\u201d are set, "
                "but Kanji / Keyword field mappings are empty. "
                "Open the Deck Mapping tab and select the fields, then try again."
            )

        notes_created = notes_filled = 0
        if create_all_notes:
            notes_created, notes_filled = self._create_missing_rtk_notes(deck_name, note_type_name)

        self.export_learned_kanji()
        return True, self._describe_rtk_setup_result(
            note_type_name, deck_name, created, create_all_notes, notes_created, notes_filled,
        )

    def import_known_kanji_from_file(
        self,
        file_path: str | Path,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ) -> tuple[int, int]:
        """Parse a file of known kanji (one per line, or `kanji,keyword`) and mark them known."""
        path = Path(file_path)
        if not path.exists():
            raise JapaneseMiningError("Kanji file not found.", details=f"Could not find the file at {path}.")

        try:
            entries = parse_kanji_file(path)
        except Exception as e:
            raise JapaneseMiningError(
                "Failed to read kanji file.", details=f"Could not read file {path}:\n{e}"
            ) from e

        if not entries:
            return 0, 0

        self._kanji_data.load_learned_kanji()
        return self._apply_known_kanji(
            entries, fill_keywords=fill_keywords, suspend=suspend,
            schedule_min_days=schedule_min_days, schedule_max_days=schedule_max_days,
        )

    def import_known_kanji_up_to_heisig(
        self,
        heisig_number: int,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ) -> tuple[int, int]:
        """Mark every Heisig kanji with a 6th-ed id <= heisig_number as learned."""
        if not isinstance(heisig_number, int):
            raise TypeError(f"import_known_kanji_up_to_heisig expects an int, got {type(heisig_number).__name__}")
        if heisig_number < 1:
            raise JapaneseMiningError("Heisig number must be \u2265 1.", details=f"Invalid Heisig number: {heisig_number}.")

        heisig_rows = self._load_heisig_rows_up_to(limit=heisig_number)
        if heisig_rows is None:
            return 0, 0

        entries = [
            (kanji, heisig_keyword(row) if fill_keywords else "")
            for kanji, row in heisig_rows.items()
        ]
        if not entries:
            return 0, 0

        self._kanji_data.load_learned_kanji()
        return self._apply_known_kanji(
            entries, fill_keywords=fill_keywords, suspend=suspend,
            schedule_min_days=schedule_min_days, schedule_max_days=schedule_max_days,
        )

    # =========================================================================
    # Setup helpers (get_or_create_rtk_deck_and_note_type's steps)
    # =========================================================================

    def _get_or_create_rtk_note_type(self, note_type_name: str) -> tuple[dict | None, bool]:
        """Returns (model, created). model is None if an existing note type lacks usable Kanji/Keyword fields."""
        model = self._collection_service.get_model_by_name(note_type_name)
        if model is not None:
            existing = get_fields_from_model(model)
            kanji_f = self._config.rtk_kanji_field if self._config.rtk_kanji_field in existing else ("Kanji" if "Kanji" in existing else "")
            keyword_f = self._config.rtk_keyword_field if self._config.rtk_keyword_field in existing else ("Keyword" if "Keyword" in existing else "")
            if not kanji_f or not keyword_f:
                return None, False
            return model, False

        model = self._collection_service.create_new_model(note_type_name)
        for field_name in self._STANDARD_RTK_FIELDS:
            field = self._collection_service.create_new_model_field(field_name)
            field = set_model_field_size(field, 12)
            field = set_model_field_font(field, "Arial")
            self._collection_service.add_field_to_model(model, field)

        model = set_model_sort_field(model, self._STANDARD_RTK_FIELDS.index("Heisig Number"))

        template = self._collection_service.create_new_model_card_template("KeywordToKanji")
        template = set_template_question_format(template, RTK_FRONT_HTML)
        template = set_template_answer_format(template, RTK_BACK_HTML)
        self._collection_service.add_template_to_model(model, template)

        model = set_model_css(model, RTK_CARD_CSS)
        self._collection_service.add_model(model)
        return model, True

    def _sync_rtk_field_mappings(self, model: dict, *, created: bool) -> None:
        """
        When we just created the note type: force all mappings to standard names.
        When reusing an existing note type: only fill blank/invalid mappings
        from standard names that exist on the model — never touch a mapping
        the user already set.
        """
        existing = set(get_fields_from_model(model))
        for config_attr, standard_name in self._RTK_FIELD_CONFIG_MAP.items():
            if created:
                setattr(self._config, config_attr, standard_name)
                continue
            current = (getattr(self._config, config_attr) or "").strip()
            if (not current or current not in existing) and standard_name in existing:
                setattr(self._config, config_attr, standard_name)

    def _create_missing_rtk_notes(self, deck_name: str, note_type_name: str) -> tuple[int, int]:
        """Bulk-create RTK notes for every 6th-ed Heisig kanji (\u22642200) missing from the deck; fill blanks on the rest."""
        heisig_rows = self._load_heisig_rows_up_to(limit=2200)
        if heisig_rows is None:
            raise JapaneseMiningError(
                f"Could not find {HEISIG_KANJI_FILE}.",
                details=f"Put {HEISIG_KANJI_FILE} in the Anki media folder or in the add-on's vendor/ directory.",
            )

        deck_id = self._collection_service.get_deck_id_by_deck_name(deck_name)
        created = filled = 0
        for kanji in sort_kanji_by_sixth_edition(heisig_rows):
            row = heisig_rows[kanji]
            existing = self._find_rtk_note_in_deck(kanji, deck_name=deck_name, note_type=note_type_name)
            if existing is None:
                note = self._create_rtk_note(kanji=kanji, tags=["Heisig"], heisig_rows=heisig_rows)
                self._collection_service.add_note(note, deck_id)
                self._apply_heisig_due_order(note, row)
                created += 1
            elif self._fill_note_from_heisig_row(existing, row):
                self._collection_service.update_note(existing)
                filled += 1
        return created, filled

    def _apply_heisig_due_order(self, note: Note, row: dict) -> None:
        """New cards get their 'due' position set to the Heisig number, so the deck studies in Heisig order."""
        num = sixth_edition_number(row)
        if not num:
            return
        for card in note.cards():
            card.due = num
            self._collection_service.update_card(card)

    @staticmethod
    def _describe_rtk_setup_result(
        note_type_name: str, deck_name: str, created: bool,
        create_all_notes: bool, notes_created: int, notes_filled: int,
    ) -> str:
        """Pure: assemble the human-readable result message."""
        parts = [
            f"Created note type \u201c{note_type_name}\u201d" if created
            else f"Re-used existing note type \u201c{note_type_name}\u201d"
        ]
        if not created:
            parts.append("Recommended: the add-on's own RTK note type for full field support")
        parts.append(f"Deck \u201c{deck_name}\u201d is ready")
        if create_all_notes:
            parts.append(f"Added {notes_created} new notes")
            if notes_filled:
                parts.append(
                    f"Filled empty fields on {notes_filled} existing notes "
                    "(existing values were left untouched)"
                )
            if notes_created == 0 and notes_filled == 0:
                parts.append(
                    "No new notes added — they may already exist for this note type "
                )
        return ". ".join(parts) + "."

    # =========================================================================
    # export_learned_kanji's steps
    # =========================================================================

    def _collect_card_observations(self, deck: str, kanji_field: str, alt_field: str, keyword_field: str):
        """Impure: scan every card in the RTK deck, yielding one CardObservation per kanji field found."""
        for card_id in self._collection_service.find_cards_by_query(f'deck:"{deck}"'):
            card = self._collection_service.get_card_by_card_id(card_id)
            note = self._collection_service.get_note_by_card_id(card_id)
            reviewed = self._collection_service.get_card_type_by_card_id(card_id) != 0  # 0 = new (incl. suspended-new)
            suspended = self._collection_service.get_card_queue_by_card_id(card_id) == -1
            knowledge = get_card_knowledge(card) if reviewed else 0.0
            keyword = get_field(note, keyword_field) if keyword_field and has_field(note, keyword_field) else ""

            if kanji_field and has_field(note, kanji_field):
                yield CardObservation(get_field(note, kanji_field).strip(), reviewed, suspended, knowledge, keyword)
            if alt_field and has_field(note, alt_field):
                yield CardObservation(get_field(note, alt_field).strip(), reviewed, suspended, knowledge, keyword)

    def _build_learned_kanji_export(self, states: dict[str, KanjiLearningState]):
        """Turn aggregated states into CSV rows + cache dict + counts. Only impure part is the keyword fallback fetch."""
        rows, cache = [], {}
        count_learned = count_not_learned = 0
        for kanji in sort_kanji_by_learned_then_alpha(states):
            state = states[kanji]
            keyword = state.keyword.strip() or self._safe_fetch_keyword(kanji)
            knowledge = state.knowledge if state.reviewed else (1.0 if state.suspended else 0.0)
            learned = state.learned

            rows.append({
                "Kanji": kanji,
                "Keyword": keyword,
                "Learned": "1" if learned else "",
                "Knowledge": f"{knowledge:.4f}" if learned else "",
            })
            cache[kanji] = {"Keyword": keyword, "Learned": learned, "Knowledge": knowledge if learned else 0.0}
            count_learned += int(learned)
            count_not_learned += int(not learned)
        return rows, cache, count_learned, count_not_learned

    def _safe_fetch_keyword(self, kanji: str) -> str:
        """fetch_kanji_keyword, but never raises — used as a fallback during export."""
        try:
            return self.fetch_kanji_keyword(kanji) or ""
        except JapaneseMiningError:
            return ""

    # =========================================================================
    # _apply_known_kanji's steps (import_known_kanji_*)
    # =========================================================================

    def _apply_known_kanji(
        self, entries: list[tuple[str, str]], *, fill_keywords: bool, suspend: bool,
        schedule_min_days: int, schedule_max_days: int,
    ) -> tuple[int, int]:
        """Mark kanji as known. Falls back to a disk-only cache update if no RTK deck is configured."""
        if not self._rtk_configured():
            return self._mark_known_without_deck(entries)
        return self._apply_known_kanji_to_deck(
            entries, fill_keywords=fill_keywords, suspend=suspend,
            schedule_min_days=schedule_min_days, schedule_max_days=schedule_max_days,
        )

    def _mark_known_without_deck(self, entries: list[tuple[str, str]]) -> tuple[int, int]:
        """No RTK deck configured yet: update the on-disk known-kanji cache only, nothing to create cards in."""
        cache = dict(self._kanji_data.get_learned_kanji())
        marked = 0
        for raw_kanji, keyword in entries:
            kanji = self._first_kanji_char(raw_kanji)
            if kanji is None:
                continue
            cache[kanji] = {
                "Keyword": keyword or cache.get(kanji, {}).get("Keyword", ""),
                "Learned": True,
                "Knowledge": 1.0,
            }
            marked += 1

        rows = [
            {
                "Kanji": k,
                "Keyword": v.get("Keyword", ""),
                "Learned": "1" if v.get("Learned") else "",
                "Knowledge": f"{v.get('Knowledge', 0.0):.4f}" if v.get("Learned") else "",
            }
            for k, v in sorted(cache.items(), key=lambda kv: (not kv[1].get("Learned"), kv[0]))
        ]
        self._kanji_data.save_learned_kanji(rows, cache)
        return marked, 0

    def _apply_known_kanji_to_deck(
        self, entries: list[tuple[str, str]], *, fill_keywords: bool, suspend: bool,
        schedule_min_days: int, schedule_max_days: int,
    ) -> tuple[int, int]:
        """
        1. Ensure all Heisig 6th-ed kanji (\u22642200) exist as notes in the RTK deck.
        2. For the imported subset: mark cards suspended or scheduled, tag Imported-Known.
        3. Remaining notes stay as new cards (not learned).
        4. Rebuild learned_kanji.csv from the deck (source of truth).
        Never deletes notes. Only fills empty fields on existing notes.
        """
        heisig_rows = self._load_heisig_rows_up_to(limit=2200)
        if heisig_rows is None:
            raise JapaneseMiningError(
                f"Could not find {HEISIG_KANJI_FILE}.",
                details=f"Put {HEISIG_KANJI_FILE} in the Anki media folder or in the add-on's vendor/ directory.",
            )

        known_set, known_keywords = self._resolve_known_entries(entries, heisig_rows, fill_keywords)
        deck_id = self._collection_service.get_deck_id_by_deck_name(self._config.rtk_deck)

        notes_created = 0
        for kanji in sort_kanji_by_sixth_edition(heisig_rows):
            row = heisig_rows[kanji]
            is_known = kanji in known_set
            note, was_created = self._ensure_rtk_note_exists(kanji, row, is_known, deck_id, known_keywords)
            if was_created:
                notes_created += 1
            if is_known and note is not None:
                self._schedule_or_suspend_note(
                    note, suspend=suspend,
                    schedule_min_days=schedule_min_days, schedule_max_days=schedule_max_days,
                )

        self.export_learned_kanji()
        return len(known_set), notes_created

    @staticmethod
    def _resolve_known_entries(
        entries: list[tuple[str, str]], heisig_rows: dict[str, dict], fill_keywords: bool,
    ) -> tuple[set[str], dict[str, str]]:
        """Pure: normalize the (kanji, keyword) import list into a known-set + keyword map."""
        known_set: set[str] = set()
        known_keywords: dict[str, str] = {}
        for raw_kanji, keyword in entries:
            kanji = RTKService._first_kanji_char(raw_kanji)
            if kanji is None:
                continue
            known_set.add(kanji)
            if keyword:
                known_keywords[kanji] = keyword
            elif fill_keywords and kanji in heisig_rows:
                known_keywords[kanji] = heisig_keyword(heisig_rows[kanji])
        return known_set, known_keywords

    def _ensure_rtk_note_exists(
        self, kanji: str, row: dict, is_known: bool, deck_id, known_keywords: dict[str, str],
    ) -> tuple[Note | None, bool]:
        """Find-or-create the RTK note for `kanji`. Returns (note, was_newly_created)."""
        tags = ["Heisig"] + (["Imported-Known"] if is_known else [])
        existing = self._find_rtk_note_in_deck(
            kanji, deck_name=self._config.rtk_deck, note_type=self._config.rtk_note_type
        )

        if existing is None:
            note = self._create_rtk_note(kanji=kanji, tags=tags, heisig_rows={kanji: row})
            if is_known and known_keywords.get(kanji):
                kw_field = self._config.rtk_keyword_field
                if kw_field and has_field(note, kw_field) and not get_field(note, kw_field).strip():
                    set_field(note, kw_field, known_keywords[kanji])
            self._collection_service.add_note(note, deck_id)
            return note, True

        if self._fill_note_from_heisig_row(existing, row):
            self._collection_service.update_note(existing)
        changed_tags = False
        for tag in ["JapaneseMining::RTK", *tags]:
            if tag not in existing.tags:
                existing.tags.append(tag)
                changed_tags = True
        if changed_tags:
            self._collection_service.update_note(existing)
        return existing, False

    def _schedule_or_suspend_note(
        self, note: Note, *, suspend: bool, schedule_min_days: int, schedule_max_days: int,
    ) -> None:
        """Mark every card of a known note as suspended, or scheduled to simulate prior study."""
        for card in note.cards():
            if suspend:
                card.queue = -1
            else:
                days = random.randint(schedule_min_days, schedule_max_days)
                card.type = 2
                card.queue = 2
                card.ivl = days
                card.factor = 2500
                card.due = self._collection_service.get_scheduler_today() + days
            self._collection_service.update_card(card)

    # =========================================================================
    # Shared low-level helpers
    # =========================================================================

    def _rtk_configured(self) -> bool:
        return bool(
            self._config.rtk_deck
            and self._config.rtk_note_type
            and self._config.rtk_kanji_field
            and self._config.rtk_keyword_field
        )

    def _require_rtk_configured(self) -> None:
        if not self._rtk_configured():
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings -> RTK and set the deck + fields",
            )

    @staticmethod
    def _first_kanji_char(raw: str) -> str | None:
        """Return the first char of `raw` if it's a kanji, else None."""
        text = (raw or "").strip()
        if not text or not is_kanji(text[0]):
            return None
        return text[0]

    def _load_heisig_rows_up_to(self, limit: int | None) -> dict[str, dict] | None:
        """
        Load Heisig CSV rows keyed by kanji. If `limit` is given, keep only
        rows with a 6th-edition id <= limit (used for the bulk-creation range).
        Returns None if the CSV can't be found at all.
        """
        path = resolve_heisig_csv(
            media_dir=Path(self._collection_service.get_media_path()),
            addon_dir=self._addon_dir,
        )
        if path is None:
            return None
        rows = load_heisig_rows(path)
        if limit is None:
            return rows
        return {
            kanji: row for kanji, row in rows.items()
            if (num := sixth_edition_number(row)) is not None and num <= limit
        }

    def _find_unknown_kanji(self) -> list[str]:
        """Find all kanji in active (non-suspended) mining notes that have no RTK note yet."""
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        rtk_note_ids = self._collection_service.find_notes_by_query(f'note:"{self._config.rtk_note_type}"')
        mining_note_ids = self._collection_service.find_notes_by_query(
            f"note:{self._config.mining_note_type} -is:suspended"
        )

        known: set[str] = set()
        for note_id in rtk_note_ids:
            note = self._collection_service.get_note_by_note_id(note_id)
            known.add(get_field(note, kanji_field))
            known.add(get_field(note, alt_kanji_field))

        unknown: list[str] = []
        for note_id in mining_note_ids:
            note = self._collection_service.get_note_by_note_id(note_id)
            for ch in get_field(note, "Word"):
                if is_kanji(ch) and ch not in known and ch not in unknown:
                    unknown.append(ch)
        return unknown

    def _find_rtk_note_in_deck(
        self, kanji: str, *, deck_name: str | None = None, note_type: str | None = None,
    ) -> Note | None:
        """Return the first RTK note for `kanji` in the given deck. Scoped to deck — never treats the same kanji in another deck as a duplicate."""
        deck = (deck_name or self._config.rtk_deck or "").strip()
        nt = (note_type or self._config.rtk_note_type or "").strip()
        kanji_field = (self._config.rtk_kanji_field or "").strip()
        alt_field = (self._config.rtk_alternative_kanji_field or "").strip()

        if not deck or not nt or not kanji_field or not kanji:
            return None

        note_ids = self._collection_service.find_notes_by_query(
            f'deck:"{deck}" note:"{nt}" "{kanji_field}:""{kanji}"'
        )
        if not note_ids and alt_field:
            note_ids = self._collection_service.find_notes_by_query(
                f'deck:"{deck}" note:"{nt}" "{alt_field}:""{kanji}"'
            )
        if not note_ids:
            return None
        return self._collection_service.get_note_by_note_id(note_ids[0])

    def _create_rtk_note(
        self, kanji: str, alt_kanji: str = "", tags: list[str] | None = None,
        heisig_rows: dict[str, dict] | None = None,
    ) -> Note:
        """
        Create a new RTK note filled from Heisig data where possible.
        Only writes into fields that exist on the note type.

        NOTE: the original docstring claimed this returns None for a
        duplicate/empty note — it never actually did that; dup-checking
        happens in the caller (add_kanji_to_rtk_deck). Fixed here.
        """
        model = self._collection_service.get_model_by_name(self._config.rtk_note_type)
        if model is None:
            raise JapaneseMiningError(
                f"RTK note type '{self._config.rtk_note_type}' not found. Please check your settings.",
                details="Open Settings -> RTK and set the note type.",
            )
        note = self._collection_service.new_note(model)

        kanji_field = self._config.rtk_kanji_field
        alt_field = self._config.rtk_alternative_kanji_field
        meanings_field = self._config.rtk_meanings_field

        if kanji_field and has_field(note, kanji_field):
            set_field(note, kanji_field, kanji)
        if alt_kanji and alt_field and has_field(note, alt_field):
            set_field(note, alt_field, alt_kanji)
        if meanings_field and has_field(note, meanings_field):
            meanings = self._kanji_data.get_kanji_meanings(kanji) or []
            set_field(note, meanings_field, " · ".join(m for m in meanings if m))

        for tag in ["JapaneseMining::RTK", *(tags or [])]:
            if tag and tag not in note.tags:
                note.tags.append(tag)

        if heisig_rows is not None:
            row = heisig_rows.get(kanji)
            if row:
                self._fill_note_from_heisig_row(note, row)

        return note

    def _fill_note_from_heisig_row(self, note: Note, row: dict) -> bool:
        """
        Best-effort fill of Keyword / Heisig Number / Stroke Count / Meanings /
        Note from a Heisig CSV row. Only writes into fields that exist AND are
        currently empty (never overwrites user data). Returns True if anything changed.
        """
        kanji = row.get("kanji", "").strip()
        meanings = self._kanji_data.get_kanji_meanings(kanji) if kanji else []
        values = build_rtk_field_values(row, kanji_meanings=meanings)

        changed = False
        for value_key, config_attr in self._HEISIG_FILL_MAP.items():
            field_name = getattr(self._config, config_attr)
            value = values.get(value_key, "")
            if field_name and has_field(note, field_name) and value and not get_field(note, field_name).strip():
                set_field(note, field_name, value)
                changed = True
        return changed
