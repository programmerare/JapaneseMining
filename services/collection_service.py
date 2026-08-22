from aqt import mw
from anki.notes import Note
import csv
import math
from pathlib import Path

from ..config import ConfigHolder, REQUIRED_MINING_FIELDS
from .kanji_data_service import KanjiDataService
from ..domain.kanji import is_kanji
from ..domain.errors import JapaneseMiningError
from ..domain.results import UpdateResult


class CollectionService:
    _HEISIG_KANJI_FILE = "heisig_kanji.csv"
    _REQUIRED_MINING_FIELDS = REQUIRED_MINING_FIELDS

    def __init__(self, config_holder: ConfigHolder, kanji_data: KanjiDataService):
        self._config_holder = config_holder
        self._kanji_data = kanji_data

    @property
    def _config(self):
        return self._config_holder.config

    # --- PUBLIC METHODS --- #
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

    def fetch_kanji_keyword(self, kanji: str) -> str:
        """Returns one learned keyword associated with kanji from RTK deck"""
        if not self._rtk_configured():
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings -> RTK and set the deck + fields",
            )

        col = mw.col
        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field
        keyword_field = self._config.rtk_keyword_field

        card_ids = col.find_cards(f'deck:"{deck}" {kanji_field}:{kanji}')
        if not card_ids:
            card_ids = col.find_cards(f'deck:"{deck}" "{alt_kanji_field}:{kanji}"')

        if not card_ids:
            return ""

        card = col.get_card(card_ids[0])
        note = card.note()
        return self._get_field(note, keyword_field)

    def add_kanji_to_rtk_deck(
        self,
        kanji: str,
        *,
        tags: list[str] | None = None,
        heisig_kanjis: dict[str, dict] | None = None,
    ) -> bool:
        """
        Ensure a single kanji exists as an RTK note.
        Returns True if a new note was added, False if skipped (missing config,
        not a kanji, already present, or no Heisig row and you choose to skip).
        """
        if not self._rtk_configured():
            return False

        kanji = (kanji or "").strip()
        if not kanji or not is_kanji(kanji[0]):
            return False
        kanji = kanji[0]

        # Load Heisig data only if the caller did not pass it in
        if heisig_kanjis is None:
            path = self._resolve_heisig_csv()
            if path is None:
                return False
            with path.open("r", newline="", encoding="utf-8") as f:
                heisig_kanjis = {
                    row["kanji"]: row for row in csv.DictReader(f) if row.get("kanji")
                }

        col = mw.col
        deck_id = col.decks.id(self._config.rtk_deck)

        note = self._create_rtk_note(
            kanji=kanji,
            tags=tags or ["Self-Added"],
            heisig_kanjis=heisig_kanjis,
        )
        if note is None:
            return False  # duplicate / empty

        col.add_note(note, deck_id)
        return True

    def add_unknown_kanji(self) -> UpdateResult:
        """Find every unknown kanji in mining notes and add them to the RTK deck."""
        if not self._rtk_configured():
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings -> RTK and set the deck + fields",
            )

        path = self._resolve_heisig_csv()
        if path is None:
            raise JapaneseMiningError(
                f"Could not find {self._HEISIG_KANJI_FILE}.",
                details=f"Put {self._HEISIG_KANJI_FILE} in the Anki media folder or in the add-on’s vendor/ directory.",
            )

        with path.open("r", newline="", encoding="utf-8") as f:
            heisig_kanjis = {
                row["kanji"]: row for row in csv.DictReader(f) if row.get("kanji")
            }

        added = 0
        for kanji in self._find_unknown_kanji():
            if self.add_kanji_to_rtk_deck(kanji, heisig_kanjis=heisig_kanjis):
                added += 1

        return UpdateResult(kanji_added_to_rtk=added)

    def ensure_rtk_kanji_for_note(self, note: Note) -> int:
        if note is None:
            return 0
        if note.note_type()["name"] != self._config.mining_note_type:
            raise JapaneseMiningError(
                f"The note is not a {self._config.mining_note_type} note. Please check your settings.",
                details="Open Settings -> JapaneseMining and set the correct note type.",
            )

        word = note["Word"] if "Word" in note else ""
        added = 0
        seen: set[str] = set()
        for ch in word:
            if ch in seen or not is_kanji(ch):
                continue
            seen.add(ch)
            if self.add_kanji_to_rtk_deck(ch):
                added += 1
        return added

    def export_learned_kanji(self) -> UpdateResult:
        """
        Rebuild learned_kanji.csv from the configured RTK deck only.

        Source of truth = the RTK deck in config (not the previous CSV).

        Per kanji in that deck:
        - Any card with type != 0 (learning / review / relearning)
          → Learned, Knowledge from Anki scheduling/FSRS (reflects real study)
        - Else any card suspended (queue == -1)
          → Learned, Knowledge = 1.0 (intentionally parked as known, e.g. import)
        - Else (pure new, not suspended)
          → not learned

        Switching the mapped RTK deck and exporting therefore fully refreshes
        the CSV from that deck. This method never modifies notes or cards.
        """
        if not self._rtk_configured():
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings -> RTK and set the deck + fields",
            )

        col = mw.col
        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        all_card_ids = col.find_cards(f'deck:"{deck}"')

        # kanji -> {reviewed, suspended, knowledge, keyword}
        from_anki: dict[str, dict] = {}

        def _touch(
            kanji: str,
            *,
            reviewed: bool,
            suspended: bool,
            knowledge: float,
            keyword: str,
        ) -> None:
            if not kanji:
                return
            entry = from_anki.get(kanji)
            if entry is None:
                from_anki[kanji] = {
                    "reviewed": reviewed,
                    "suspended": suspended and not reviewed,
                    "knowledge": knowledge if reviewed else 0.0,
                    "keyword": keyword or "",
                }
            else:
                entry["reviewed"] = entry["reviewed"] or reviewed
                if reviewed:
                    entry["suspended"] = False
                    if knowledge > entry["knowledge"]:
                        entry["knowledge"] = knowledge
                elif suspended and not entry["reviewed"]:
                    entry["suspended"] = True
                if keyword and not entry["keyword"]:
                    entry["keyword"] = keyword

        for cid in all_card_ids:
            card = col.get_card(cid)
            note = card.note()
            reviewed = card.type != 0  # 0 = new (incl. suspended-new)
            suspended = card.queue == -1
            knowledge = self._get_card_knowledge(card) if reviewed else 0.0
            keyword = ""
            if (
                self._config.rtk_keyword_field
                and self._config.rtk_keyword_field in note
            ):
                keyword = self._get_field(note, self._config.rtk_keyword_field)

            if kanji_field and kanji_field in note:
                _touch(
                    self._get_field(note, kanji_field).strip(),
                    reviewed=reviewed,
                    suspended=suspended,
                    knowledge=knowledge,
                    keyword=keyword,
                )
            if alt_kanji_field and alt_kanji_field in note:
                _touch(
                    self._get_field(note, alt_kanji_field).strip(),
                    reviewed=reviewed,
                    suspended=suspended,
                    knowledge=knowledge,
                    keyword=keyword,
                )

        learned_kanji_rows = []
        learned_kanji_cache = {}
        count_learned = 0
        count_not_learned = 0

        def _sort_key(k: str) -> tuple:
            e = from_anki[k]
            is_learned = e["reviewed"] or e["suspended"]
            return (not is_learned, k)

        for kanji in sorted(from_anki.keys(), key=_sort_key):
            anki = from_anki[kanji]
            reviewed = bool(anki["reviewed"])
            suspended = bool(anki["suspended"])
            learned = reviewed or suspended

            keyword = (anki.get("keyword") or "").strip()
            if not keyword:
                try:
                    keyword = self.fetch_kanji_keyword(kanji) or ""
                except JapaneseMiningError:
                    keyword = ""

            if reviewed:
                # Real study wins — reflect current Anki/FSRS state
                knowledge = float(anki.get("knowledge") or 0.0)
            elif suspended:
                # Parked as known (import / manual suspend) until first review
                knowledge = 1.0
            else:
                knowledge = 0.0

            learned_kanji_rows.append(
                {
                    "Kanji": kanji,
                    "Keyword": keyword,
                    "Learned": "1" if learned else "",
                    "Knowledge": f"{knowledge:.4f}" if learned else "",
                }
            )
            learned_kanji_cache[kanji] = {
                "Keyword": keyword,
                "Learned": learned,
                "Knowledge": knowledge if learned else 0.0,
            }
            if learned:
                count_learned += 1
            else:
                count_not_learned += 1

        if self._kanji_data:
            self._kanji_data.save_learned_kanji(learned_kanji_rows, learned_kanji_cache)
            self._kanji_data.clear_update_needed()


        return UpdateResult(
            learned_kanji=count_learned,
            not_learned_kanji=count_not_learned,
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
        if note is None:
            return 0, 0

        if note.note_type()["name"] != self._config.mining_note_type:
            return 0, 0

        newly_known_count, updated_count = self._update_kanji_knowledge(
            note=note,
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        return newly_known_count, updated_count

    def update_japanese_mining_cards(
        self, force_update_meanings: bool = False, force_update_keywords: bool = False
    ) -> UpdateResult:
        """
        Update all JapaneseMining cards in a single pass over each word.
        Intended to be called from a CollectionOp.
        """
        res = self.export_learned_kanji()
        learned_kanji, not_learned_kanji = res.learned_kanji, res.not_learned_kanji
        cards_newly_known, cards_updated = self._update_kanji_knowledge(
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        kanji_added_to_rtk = (
            (res := self.add_unknown_kanji()).kanji_added_to_rtk if res else 0
        )

        return UpdateResult(
            learned_kanji=learned_kanji,
            not_learned_kanji=not_learned_kanji,
            cards_newly_known=cards_newly_known,
            cards_updated=cards_updated,
            kanji_added_to_rtk=kanji_added_to_rtk,
        )

    def create_mining_note_type(
        self,
        note_type_name: str = "JapaneseMining",
        *,
        set_as_default: bool = True,
    ) -> tuple[bool, str]:
        """
        Create (or reuse) the canonical JapaneseMining note type
        with all fields the add-on expects.
        Optionally updates config.mining_note_type.
        Returns (success, human-readable message).
        """
        col = mw.col
        if not col:
            return False, "No collection open."

        note_type_name = (note_type_name or "").strip() or "JapaneseMining"

        mm = col.models
        model = mm.by_name(note_type_name)
        created = False

        if model is None:
            model = mm.new(note_type_name)

            for name in self._REQUIRED_MINING_FIELDS:
                field = mm.new_field(name)
                field["size"] = 12
                field["font"] = "Arial"
                mm.add_field(model, field)

            # Sort by Word
            model["sortf"] = 0

            fwd = mm.new_template("Forward")
            fwd["qfmt"] = MINING_FORWARD_FRONT_HTML
            fwd["afmt"] = MINING_FORWARD_BACK_HTML
            mm.add_template(model, fwd)

            bwd = mm.new_template("Backward")
            bwd["qfmt"] = MINING_BACKWARD_FRONT_HTML
            bwd["afmt"] = MINING_BACKWARD_BACK_HTML
            mm.add_template(model, bwd)

            model["css"] = MINING_CARD_CSS

            mm.add(model)
            created = True
        else:
            existing = {f["name"] for f in model["flds"]}
            missing = [f for f in self._REQUIRED_MINING_FIELDS if f not in existing]
            if missing:
                return False, (
                    f"Note type “{note_type_name}” already exists but is missing "
                    f'required fields: {", ".join(missing)}. '
                    "Choose a different name or add the missing fields manually."
                )

        if set_as_default:
            self._config.mining_note_type = note_type_name
            # Caller is responsible for persisting config if needed

        col.save()

        if created:
            return True, f"Created note type “{note_type_name}”."
        return True, f"Re-used existing note type “{note_type_name}”."

    def create_rtk_deck_and_note_type(
        self,
        deck_name: str,
        note_type_name: str,
        create_all_notes: bool = True,
    ) -> tuple[bool, str]:
        """
        Create (or reuse) the RTK note type + deck.

        Behaviour:
        - New note type  → create with standard fields and wire config mappings.
        - Existing note type → require only Kanji + Keyword; do NOT overwrite
          the user's field mappings (they configure those in Deck Mapping).
        - create_all_notes → add missing Heisig notes only (never duplicates).

        Returns (success, human-readable message).
        """
        col = mw.col
        if not col:
            return False, "No collection open."

        deck_name = (deck_name or "").strip()
        note_type_name = (note_type_name or "").strip()
        if not deck_name or not note_type_name:
            return False, "Deck name and note type name are required."

        # ----- 1. Note type -----
        mm = col.models
        model = mm.by_name(note_type_name)
        created_model = False

        STANDARD_FIELDS = (
            "Kanji",
            "Alternative Kanji",
            "Keyword",
            "Story",
            "Heisig Number",
            "Stroke Count",
        )

        if model is None:
            model = mm.new(note_type_name)

            for field_name in STANDARD_FIELDS:
                field = mm.new_field(field_name)
                field["size"] = 12
                field["font"] = "Arial"
                mm.add_field(model, field)

            model["sortf"] = 4  # Heisig Number

            t = mm.new_template("KeywordToKanji")
            t["qfmt"] = RTK_FRONT_HTML
            t["afmt"] = RTK_BACK_HTML
            mm.add_template(model, t)

            model["css"] = RTK_CARD_CSS
            mm.add(model)
            created_model = True
        else:
            # Existing note type: do not require literal "Kanji"/"Keyword" names.
            # Accept already-mapped fields that exist on the model, or standard names.
            existing_fields = {f["name"] for f in model["flds"]}
            kanji_f = (self._config.rtk_kanji_field or "").strip()
            keyword_f = (self._config.rtk_keyword_field or "").strip()
            if kanji_f not in existing_fields:
                kanji_f = "Kanji" if "Kanji" in existing_fields else ""
            if keyword_f not in existing_fields:
                keyword_f = "Keyword" if "Keyword" in existing_fields else ""
            if not kanji_f or not keyword_f:
                return False, (
                    f"Note type “{note_type_name}” has no usable Kanji/Keyword fields. "
                    "Either map them in the Deck Mapping tab first, or choose a note type "
                    "that contains fields named Kanji and Keyword. "
                    "Recommended: create a fresh note type name so the add-on can build "
                    "the full standard RTK note type for you."
                )

        # ----- 2. Deck (creates if missing) -----
        deck_id = col.decks.id(deck_name)

        # ----- 3. Config -----
        # Always point at the chosen deck + note type.
        # Field mappings: only force standard names when WE created the model.
        # If the user reuses an existing note type, keep their mappings; only
        # auto-detect blanks from standard names that exist on the model.
        # We never delete or rewrite non-empty fields on existing user notes.
        self._config.rtk_deck = deck_name
        self._config.rtk_note_type = note_type_name

        if created_model:
            self._config.rtk_kanji_field = "Kanji"
            self._config.rtk_alternative_kanji_field = "Alternative Kanji"
            self._config.rtk_keyword_field = "Keyword"
            self._config.rtk_heisig_number_field = "Heisig Number"
            self._config.rtk_stroke_count_field = "Stroke Count"
        else:
            existing_fields = {f["name"] for f in model["flds"]}
            if not (self._config.rtk_kanji_field or "").strip() or (
                self._config.rtk_kanji_field not in existing_fields
            ):
                if "Kanji" in existing_fields:
                    self._config.rtk_kanji_field = "Kanji"
            if not (self._config.rtk_keyword_field or "").strip() or (
                self._config.rtk_keyword_field not in existing_fields
            ):
                if "Keyword" in existing_fields:
                    self._config.rtk_keyword_field = "Keyword"
            if (
                not (self._config.rtk_alternative_kanji_field or "").strip()
                and "Alternative Kanji" in existing_fields
            ):
                self._config.rtk_alternative_kanji_field = "Alternative Kanji"
            if (
                not (self._config.rtk_heisig_number_field or "").strip()
                and "Heisig Number" in existing_fields
            ):
                self._config.rtk_heisig_number_field = "Heisig Number"
            if (
                not (self._config.rtk_stroke_count_field or "").strip()
                and "Stroke Count" in existing_fields
            ):
                self._config.rtk_stroke_count_field = "Stroke Count"

        # Guard: without kanji + keyword we cannot create notes reliably
        if not self._config.rtk_kanji_field or not self._config.rtk_keyword_field:
            return False, (
                f"Deck “{deck_name}” and note type “{note_type_name}” are set, "
                "but Kanji / Keyword field mappings are empty. "
                "Open the Deck Mapping tab and select the fields, then try again."
            )

        # ----- 4. Optionally create all Heisig notes (skip duplicates) -----
        notes_created = 0
        notes_filled = 0
        if create_all_notes:
            path = self._resolve_heisig_csv()
            if path is None:
                raise JapaneseMiningError(
                    f"Could not find {self._HEISIG_KANJI_FILE}.",
                    details=(
                        f"Put {self._HEISIG_KANJI_FILE} in the Anki media folder "
                        "or in the add-on’s vendor/ directory."
                    ),
                )

            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                kanji_rows: dict[str, dict] = {}
                for row in reader:
                    if not row.get("kanji"):
                        continue
                    # Bulk create: 6th edition only (no 5th-ed fallback)
                    raw_6 = (row.get("id_6th_ed") or "").strip()
                    if not raw_6:
                        continue
                    try:
                        num_6 = int(raw_6)
                    except ValueError:
                        continue
                    if num_6 <= 2200:
                        kanji_rows[row["kanji"]] = row

            sorted_rows = sorted(
                kanji_rows.values(),
                key=lambda row: int(
                    (row.get("id_6th_ed") or "99999").strip() or "99999"
                ),
            )

            for row in sorted_rows:
                kanji = row["kanji"]
                note = self._create_rtk_note(
                    kanji=kanji,
                    tags=["Heisig"],
                    heisig_kanjis=kanji_rows,
                )
                if note is not None:
                    col.add_note(note, deck_id)
                    try:
                        heisig_num = int((row.get("id_6th_ed") or "0").strip() or "0")
                    except ValueError:
                        heisig_num = 0
                    if heisig_num:
                        for card in note.cards():
                            card.due = heisig_num
                            col.update_card(card)
                    notes_created += 1
                else:
                    # Already exists — fill any empty Heisig fields
                    note_ids = col.find_notes(
                        f'note:"{note_type_name}" '
                        f"{self._config.rtk_kanji_field}:{kanji}"
                    )
                    if note_ids:
                        existing_note = col.get_note(note_ids[0])
                        if self._fill_note_from_heisig_row(existing_note, row):
                            col.update_note(existing_note)
                            notes_filled += 1

        col.save()

        parts = []
        if created_model:
            parts.append(f"Created note type “{note_type_name}”")
        else:
            parts.append(f"Re-used existing note type “{note_type_name}”")
            parts.append(
                "Recommended: the add-on’s own RTK note type for full field support"
            )
        parts.append(f"Deck “{deck_name}” is ready")
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
                    "(Anki blocks duplicates across decks)"
                )

        self.export_learned_kanji()

        return True, ". ".join(parts) + "."

    def import_known_kanji_from_file(
        self,
        file_path: str | Path,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ) -> tuple[int, int]:
        """
        Parse a file of known kanji (one per line, or kanji,keyword).
        Updates learned_kanji.csv. Optionally creates/updates RTK cards.
        """
        path = Path(file_path)
        if not path.exists():
            raise JapaneseMiningError(
                "Kanji file not found.",
                details=f"Could not find the file at {path}.",
            )

        try:
            entries = self._parse_kanji_file(path)
        except Exception as e:
            raise JapaneseMiningError(
                "Failed to read kanji file.",
                details=f"Could not read file {path}:\n{e}",
            ) from e

        if not entries:
            return 0, 0

        # Make sure we start from whatever is already on disk
        self._kanji_data.load_learned_kanji()

        marked, touched = self._apply_known_kanji(
            entries,
            fill_keywords=fill_keywords,
            suspend=suspend,
            schedule_min_days=schedule_min_days,
            schedule_max_days=schedule_max_days,
        )
        return marked, touched

    def import_known_kanji_up_to_heisig(
        self,
        heisig_number: int,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ) -> tuple[int, int]:
        """
        Mark every Heisig kanji with id_6th_ed ≤ heisig_number as learned.
        """
        if heisig_number < 1:
            raise JapaneseMiningError(
                "Heisig number must be ≥ 1.",
                details=f"Invalid Heisig number: {heisig_number}.",
            )

        path = self._resolve_heisig_csv()
        if path is None:
            return 0, 0

        with path.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Import-by-number: 6th edition only (matches RTK 6th ordering)
        entries: list[tuple[str, str]] = []
        for row in rows:
            if not row.get("kanji"):
                continue
            raw_6 = (row.get("id_6th_ed") or "").strip()
            if not raw_6:
                continue
            try:
                n = int(raw_6)
            except ValueError:
                continue
            if n > heisig_number:
                continue
            keyword = self._heisig_keyword(row) if fill_keywords else ""
            entries.append((row["kanji"], keyword))

        if not entries:
            return 0, 0

        # Make sure we start from whatever is already on disk
        self._kanji_data.load_learned_kanji()

        marked, touched = self._apply_known_kanji(
            entries,
            fill_keywords=fill_keywords,
            suspend=suspend,
            schedule_min_days=schedule_min_days,
            schedule_max_days=schedule_max_days,
        )
        return marked, touched

    # --- PRIVATE METHODS --- #
    def _find_unknown_kanji(self) -> list[str]:
        """Find all unknown Kanji in JapaneseMining cards"""
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        rtk_note_ids = mw.col.find_notes(f'note:"{self._config.rtk_note_type}"')
        mining_note_ids = mw.col.find_notes(
            f"note:{self._config.mining_note_type} -is:suspended"
        )

        known = set()
        for note_id in rtk_note_ids:
            note = col.get_note(note_id)
            known.add(self._get_field(note, kanji_field))
            known.add(self._get_field(note, alt_kanji_field))

        unknown = []
        for note_id in mining_note_ids:
            note = col.get_note(note_id)
            for ch in self._get_field(note, "Word"):
                if is_kanji(ch) and ch not in known and ch not in unknown:
                    unknown.append(ch)

        return unknown

    def _create_rtk_note(
        self, kanji: str, alt_kanji: str = "", tags=None, heisig_kanjis=None
    ) -> Note | None:
        """
        Create a new RTK note filled from Heisig data where possible.

        Returns None if the note would be a duplicate or empty (caller should
        then look up the existing note if it needs to update scheduling/fields).
        Only writes into fields that exist on the note type.
        """
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        tags = tags or []
        model = col.models.by_name(self._config.rtk_note_type)
        if model is None:
            raise JapaneseMiningError(
                f"RTK note type '{self._config.rtk_note_type}' not found. Please check your settings.",
                details="Open Settings -> RTK and set the note type.",
            )

        note = Note(col, model)
        if kanji_field and kanji_field in note:
            note[kanji_field] = kanji
        if alt_kanji and alt_kanji_field and alt_kanji_field in note:
            note[alt_kanji_field] = alt_kanji

        # Standard tag namespace so users can search reliably
        base_tags = ["JapaneseMining::RTK"]
        for t in base_tags + list(tags):
            if t and t not in note.tags:
                note.tags.append(t)

        if heisig_kanjis is not None:
            row = heisig_kanjis.get(kanji)
            if row:
                self._fill_note_from_heisig_row(note, row)

        return note

    def _fill_note_from_heisig_row(self, note: Note, row: dict) -> bool:
        """
        Best-effort fill of Keyword / Heisig Number / Stroke Count from a
        Heisig CSV row. Only writes into fields that exist AND are currently
        empty (never overwrites user data). Returns True if anything changed.
        """
        changed = False
        keyword_field = self._config.rtk_keyword_field
        heisig_field = self._config.rtk_heisig_number_field
        stroke_field = self._config.rtk_stroke_count_field

        if (
            keyword_field
            and keyword_field in note
            and not (note[keyword_field] or "").strip()
        ):
            kw = self._heisig_keyword(row)
            if kw:
                note[keyword_field] = kw
                changed = True

        if (
            heisig_field
            and heisig_field in note
            and not (note[heisig_field] or "").strip()
        ):
            num, _edition = self._heisig_number_and_edition(row)
            if num != 99999:
                note[heisig_field] = str(num)
                changed = True

        if (
            stroke_field
            and stroke_field in note
            and not (note[stroke_field] or "").strip()
        ):
            strokes = (row.get("stroke_count") or "").strip()
            if strokes:
                note[stroke_field] = strokes
                changed = True

        return changed

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

        col = mw.col
        should_update = False
        all_known = True
        no_kanji = True

        keywords = []
        meanings = []
        keywords_present = bool(self._get_field(note, "Kanji Keywords"))
        meanings_present = bool(self._get_field(note, "Kanji Meanings"))

        for ch in self._get_field(note, "Word"):
            if not is_kanji(ch):
                continue

            no_kanji = False
            kanji_entry = learned_kanji.get(ch)
            if not kanji_entry or not kanji_entry.get("Learned"):
                all_known = False

            if not keywords_present or force_update_keywords:
                kanji_keyword = kanji_entry.get("Keyword") or "not known" if kanji_entry else "not known"
                if kanji_keyword not in keywords:
                    keywords.append(f"{ch}: {kanji_keyword}")

            if not meanings_present or force_update_meanings:
                tmp = self._kanji_data.get_kanji_meanings(ch)
                tmp = " · ".join(tmp)
                tmp = ch + ": " + tmp
                if tmp not in meanings:
                    meanings.append(tmp)

        if no_kanji and self._get_field(note, "No Kanji") != "1":
            note["No Kanji"] = "1"
            note["Usually Kana"] = "1"
            should_update = True

        previous_value = self._get_field(note, "Kanji is known")
        new_value = "1" if all_known else ""
        newly_known = 0

        if previous_value != new_value:
            if previous_value != "1" and new_value == "1":
                newly_known = 1
                self._kanji_data.save_todays_known_card(
                    self._get_field(note, "Word"),
                    self._get_field(note, "Reading"),
                    self._get_field(note, "Meaning"),
                )
            note["Kanji is known"] = new_value
            should_update = True

        if keywords:
            note["Kanji Keywords"] = " · ".join(keywords)
            should_update = True

        if meanings:
            note["Kanji Meanings"] = " | ".join(meanings)
            should_update = True

        tags = self._get_field(note, "Tags")
        if (
            self._get_field(note, "Usually Kana") != "1"
            and "Usually written using kana alone" in tags
        ):
            note["Usually Kana"] = "1"
            should_update = True

        if should_update:
            col.update_note(note)

        return newly_known, int(should_update)

    def _update_kanji_knowledge(
        self,
        note: Note = None,
        force_update_meanings: bool = False,
        force_update_keywords: bool = False,
    ) -> tuple[int, int]:
        """Update JapaneseMining cards in a single pass over each word."""
        col = mw.col

        learned_kanji = self._kanji_data.get_learned_kanji()
        if note is not None:
            notes = [note]
        else:
            notes = (
                col.get_note(note_id)
                for note_id in col.find_notes(f"note:{self._config.mining_note_type}")
            )

        newly_known_count = 0
        updated_count = 0

        for current_note in notes:
            note_newly_known, note_updated = self._update_note_kanji_knowledge(
                current_note,
                learned_kanji,
                force_update_meanings=force_update_meanings,
                force_update_keywords=force_update_keywords,
            )
            newly_known_count += note_newly_known
            updated_count += note_updated

        return newly_known_count, updated_count

    def _has_field(self, note: Note, name: str) -> bool:
        """Check if a note has a field with the given name."""
        return name in note

    def _get_field(self, note: Note, name: str, default: str = "") -> str:
        """Get the value of a field in a note."""
        return note[name] if name in note else default

    def _mining_fields_ok(self, note: Note) -> bool:
        """Check if a JapaneseMining note has all required fields."""
        return all(name in note for name in self._REQUIRED_MINING_FIELDS)

    def _rtk_configured(self) -> bool:
        return bool(
            self._config.rtk_deck
            and self._config.rtk_note_type
            and self._config.rtk_kanji_field
            and self._config.rtk_keyword_field
        )

    def _media_path(self, filename: str) -> Path:
        """Return the full path to a file in the Anki media directory."""
        return Path(mw.col.media.dir()) / filename

    def _get_card_knowledge(self, card) -> float:
        """
        Return a knowledge score in [0.0, 1.0] suitable for the heatmap.

        - New cards → 0.0
        - Main signal: log-scaled Stability (long-term strength)
        - Small contribution from current Retrievability
        """
        if card.type == 0:  # new
            return 0.0

        stability = None
        retrievability = None

        # 1. Prefer the official stats object
        try:
            stats = mw.col.card_stats_data(card.id)

            for attr in ("stability", "fsrs_stability", "s"):
                if hasattr(stats, attr):
                    val = getattr(stats, attr)
                    if val is not None:
                        stability = float(val)
                        break

            for attr in ("retrievability", "fsrs_retrievability", "r"):
                if hasattr(stats, attr):
                    val = getattr(stats, attr)
                    if val is not None:
                        retrievability = float(val)
                        break
        except Exception:
            pass

        # 2. Fallback to memory_state (FSRS)
        if stability is None:
            try:
                if getattr(card, "memory_state", None) is not None:
                    ms = card.memory_state
                    if hasattr(ms, "stability") and ms.stability is not None:
                        stability = float(ms.stability)
                    if hasattr(ms, "difficulty") and retrievability is None:
                        # we don't have R here, leave it None
                        pass
            except Exception:
                pass

        # 3. Build the score
        if stability is None or stability <= 0:
            return 0.0

        # Log-scale stability so that the difference between
        # 3 days and 30 days is still visible, while very high
        # values (years) don't dominate everything.
        # S_max = 365 → a one-year stability maps to ~1.0
        S_MAX = 365.0
        stab_norm = min(1.0, math.log1p(stability) / math.log1p(S_MAX))

        if retrievability is None:
            retrievability = 0.9  # neutral default when missing

        retrievability = max(0.0, min(1.0, retrievability))

        # Final blend: stability is the dominant signal
        knowledge = 0.75 * stab_norm + 0.25 * retrievability
        return max(0.0, min(1.0, knowledge))

    def _resolve_heisig_csv(self) -> Path | None:
        """Prefer media folder, fall back to vendor/ inside the add-on package."""
        media = self._media_path(self._HEISIG_KANJI_FILE)
        if media.exists():
            return media

        vendor = (
            Path(__file__).resolve().parent.parent / "vendor" / self._HEISIG_KANJI_FILE
        )
        if vendor.exists():
            # Copy once into media so later runs (and the user) can find it easily
            import shutil

            shutil.copy(vendor, media)
            return media

        return None

    def _heisig_number_and_edition(self, row: dict) -> tuple[int, str]:
        """
        Return (number, edition).
        Prefer 6th edition; fall back to 5th. Missing → (99999, "").
        """
        for key, edition in (("id_6th_ed", "6th"), ("id_5th_ed", "5th")):
            raw = (row.get(key) or "").strip()
            if raw:
                try:
                    return int(raw), edition
                except ValueError:
                    pass
        return 99999, ""

    def _heisig_keyword(self, row: dict, prefer_6th: bool = True) -> str:
        if prefer_6th:
            order = ("keyword_6th_ed", "keyword_5th_ed")
        else:
            order = ("keyword_5th_ed", "keyword_6th_ed")
        for key in order:
            val = (row.get(key) or "").strip()
            if val:
                return val
        return ""

    def _apply_known_kanji(
        self,
        entries: list[tuple[str, str]],
        *,
        fill_keywords: bool,
        suspend: bool,
        schedule_min_days: int,
        schedule_max_days: int,
    ) -> tuple[int, int]:
        """
        Import known kanji into the configured RTK deck.

        Behaviour:
        1. Ensure all Heisig 6th-ed kanji (≤2200) exist as notes in the RTK deck.
        2. For the imported subset: mark cards suspended or scheduled, tag
           Imported-Known.
        3. Remaining notes stay as new cards (not learned).
        4. Rebuild learned_kanji.csv from the deck (source of truth).

        Never deletes notes. Only fills empty fields on existing notes.
        """
        import random

        if not self._rtk_configured():
            # Still update an in-memory/disk cache of known kanji for mining,
            # but without a deck we cannot create cards.
            self._kanji_data.load_learned_kanji()
            cache = dict(self._kanji_data.get_learned_kanji())
            marked = 0
            for kanji, keyword in entries:
                kanji = (kanji or "").strip()
                if not kanji or not is_kanji(kanji[0]):
                    continue
                kanji = kanji[0]
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
                    "Knowledge": (
                        f"{v.get('Knowledge', 0.0):.4f}" if v.get("Learned") else ""
                    ),
                }
                for k, v in sorted(
                    cache.items(), key=lambda kv: (not kv[1].get("Learned"), kv[0])
                )
            ]
            self._kanji_data.save_learned_kanji(rows, cache)
            return marked, 0

        # 1. Load Heisig 6th-ed rows (≤2200) — full set for note creation
        path = self._resolve_heisig_csv()
        if path is None:
            raise JapaneseMiningError(
                f"Could not find {self._HEISIG_KANJI_FILE}.",
                details=(
                    f"Put {self._HEISIG_KANJI_FILE} in the Anki media folder "
                    "or in the add-on’s vendor/ directory."
                ),
            )

        heisig_rows: dict[str, dict] = {}
        with path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("kanji"):
                    continue
                raw_6 = (row.get("id_6th_ed") or "").strip()
                if not raw_6:
                    continue
                try:
                    if int(raw_6) <= 2200:
                        heisig_rows[row["kanji"]] = row
                except ValueError:
                    continue

        # Known set from the import list
        known_set: set[str] = set()
        known_keywords: dict[str, str] = {}
        for kanji, keyword in entries:
            kanji = (kanji or "").strip()
            if not kanji or not is_kanji(kanji[0]):
                continue
            kanji = kanji[0]
            known_set.add(kanji)
            if keyword:
                known_keywords[kanji] = keyword
            elif fill_keywords and kanji in heisig_rows:
                known_keywords[kanji] = self._heisig_keyword(heisig_rows[kanji])

        col = mw.col
        deck_id = col.decks.id(self._config.rtk_deck)
        kanji_field = self._config.rtk_kanji_field
        note_type = self._config.rtk_note_type
        cards_touched = 0
        notes_created = 0

        def _find_existing_note(kanji: str):
            note_ids = col.find_notes(f'note:"{note_type}" {kanji_field}:{kanji}')
            if not note_ids:
                alt = self._config.rtk_alternative_kanji_field
                if alt:
                    note_ids = col.find_notes(f'note:"{note_type}" "{alt}:{kanji}"')
            if not note_ids:
                return None
            return col.get_note(note_ids[0])

        # 2. Ensure every 6th-ed kanji has a note; mark known subset
        sorted_kanji = sorted(
            heisig_rows.keys(),
            key=lambda k: int(
                (heisig_rows[k].get("id_6th_ed") or "99999").strip() or "99999"
            ),
        )

        for kanji in sorted_kanji:
            row = heisig_rows[kanji]
            is_known = kanji in known_set
            tags = ["Heisig"]
            if is_known:
                tags.append("Imported-Known")

            note = self._create_rtk_note(
                kanji=kanji,
                tags=tags,
                heisig_kanjis=heisig_rows,
            )
            if note is not None:
                # Prefer explicit keyword from the import file when provided
                if is_known and known_keywords.get(kanji):
                    kw_field = self._config.rtk_keyword_field
                    if (
                        kw_field
                        and kw_field in note
                        and not (note[kw_field] or "").strip()
                    ):
                        note[kw_field] = known_keywords[kanji]
                col.add_note(note, deck_id)
                notes_created += 1
            else:
                note = _find_existing_note(kanji)
                if note is None:
                    continue
                if self._fill_note_from_heisig_row(note, row):
                    col.update_note(note)
                # Tags: add without removing user tags
                changed_tags = False
                for t in ["JapaneseMining::RTK", "Heisig"] + (
                    ["Imported-Known"] if is_known else []
                ):
                    if t not in note.tags:
                        note.tags.append(t)
                        changed_tags = True
                if changed_tags:
                    col.update_note(note)

            if is_known and note is not None:
                for card in note.cards():
                    if suspend:
                        card.queue = -1
                    else:
                        days = random.randint(schedule_min_days, schedule_max_days)
                        card.type = 2
                        card.queue = 2
                        card.ivl = days
                        card.factor = 2500
                        card.due = col.sched.today + days
                    col.update_card(card)
                    cards_touched += 1

        col.save()

        # 3. Deck is source of truth — rebuild CSV from card state
        self.export_learned_kanji()

        return len(known_set), cards_touched

    def _parse_kanji_file(self, path: Path) -> list[tuple[str, str]]:
        """
        Accepts:
        - one kanji per line
        - kanji,keyword  (comma or tab)
        Returns list of (kanji, keyword).
        """
        text = path.read_text(encoding="utf-8")
        entries = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line or "\t" in line:
                parts = line.replace("\t", ",").split(",", 1)
                kanji = parts[0].strip()
                keyword = parts[1].strip() if len(parts) > 1 else ""
            else:
                kanji, keyword = line, ""
            if kanji:
                entries.append((kanji, keyword))
        return entries

    def _ensure_heisig_kanjis_csv(self) -> None:
        import shutil

        media_dir = Path(mw.col.media.dir())
        src = Path(__file__).resolve().parent.parent / "vendor" / "heisig_kanji.csv"
        dst = media_dir / "heisig_kanji.csv"
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)


MINING_FORWARD_FRONT_HTML = r"""
<div class="kanji" style="margin-top:0.3em;">
  <ruby class="{{^No Kanji}}{{#Usually Kana}}is-always-visible{{/Usually Kana}}{{/No Kanji}}">
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>
</div>

<div id="hint" style="display:none; margin-top:0.3em;">
  <div class="example">{{Example Sentence}}</div>
</div>

{{#Example Sentence}}
<button onclick="document.getElementById('hint').style.display='block'; this.style.display='none';">
  Show Sentence
</button>
{{/Example Sentence}}
"""

MINING_FORWARD_BACK_HTML = r"""
<style>
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Badges */
.badges {
  display: flex;
  flex-direction: column;
  gap: 0.2em;
}

.badge {
  font-size: 0.5em;
  font-weight: 600;
  padding: 0.1em 0.35em;
  border-radius: 10px;
  color: #fff;
  text-align: center;
  white-space: nowrap;
}

.badge.jlpt { background-color: #4d8dff; }
.badge.wk { background-color: #c04dff; }
.badge.common { background-color: #4fbf6a; }

/* Section labels */
h1 {
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 1em 0 0.3em;
  color: #777;
}

/* Dividers */
hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 0.8em 0;
}

/* Note section */
.note {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Mnemonic section */
.mnemonic {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Meta info */
.meta {
  font-size: 0.82em;
  color: #666;
  margin-top: 0.6em;
}

/* Kanji Meanings Tooltip */
#kanji-tooltip {
  position: fixed;
  display: none;
  background: #222;
  color: #fff;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 0.85em;
  pointer-events: none;
  max-width: 220px;
  z-index: 9999;
}

/* Audio Play Button */
.audio-button {
  display: flex;
  justify-content: flex-end;
}
</style>

<div class="kanji" style="margin-top:0.3em;">
  <ruby>
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<!-- Top-right info area -->
<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>

	<!-- Badges in top-right corner -->
  <div class="badges">
    <div class="badge jlpt">JLPT {{JLPT Level}}</div>
    <div class="badge wk">WK {{Wanikani Level}}</div>
    <div class="badge common">{{#Is Common}}Common{{/Is Common}}{{^Is Common}}Rare{{/Is Common}}</div>
  </div>

	<!-- Audio Play Button -->
  <div class="audio-button">
    {{Audio}}
  </div>
</div>

<h1>Reading</h1>
<div class="reading">
  {{Reading}}
</div>

<h1>Meaning</h1>
<div class="meaning">{{Meaning}}</div>

<h1>Example Sentence</h1>
<div class="example">{{Example Sentence}}</div>
<div class="example">{{Translation}}</div>

{{#Note}}
<h1>Note</h1>
<div class="note">{{Note}}</div>
{{/Note}}

{{#Mnemonic}}
<h1>Mnemonic</h1>
<div class="mnemonic">{{Mnemonic}}</div>
{{/Mnemonic}}

<hr>

<div class="meta">
  <strong>Part of speech:</strong> {{Part of speech}} ·<br>
  <strong>Info:</strong> {{Info}} ·<br>
  <strong>Tags:</strong> {{Tags}} ·<br>
  <strong>Other forms:</strong> {{Other forms}} ·
</div>

<!-- Kanji Keywords -->
{{#Kanji Keywords}}
<h1>Kanji Keywords</h1>
<div class="kanji-keywords">
  <div class="kanji-list">
    {{Kanji Keywords}}
  </div>
</div>
{{/Kanji Keywords}}

<!-- Kanji Meanings Tooltip-->
<div id="kanji-tooltip"></div>

<!-- Java Script -->
<script>
(() => {
    <!-- Format Kanji Meanings -->
    const rawMeanings = `{{Kanji Meanings}}`;

    const kanjiMeanings = Object.fromEntries(
        rawMeanings.split("|").map(part => {
            const [kanji, meanings] = part.split(":").map(s => s.trim());
            return [kanji, meanings];
        }).filter(x => x[0] && x[1])
    );

    <!-- Wrap Kanji in spans -->
    function wrapKanji(root) {
        if (!root) return;
        if (root.dataset.wrapped) return;
        root.dataset.wrapped = "1";

        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        const kanjiRegex = /[\u4e00-\u9faf]/g;

        const nodes = [];
        let node;

        while (node = walker.nextNode()) {
            if (kanjiRegex.test(node.nodeValue)) {
                nodes.push(node);
            }
        }

        for (const textNode of nodes) {
            const span = document.createElement("span");
            span.innerHTML = textNode.nodeValue.replace(
                kanjiRegex,
                c => `<span class="kanji-hover" data-kanji="${c}">${c}</span>`
            );
            textNode.replaceWith(span);
        }
    }

    function initializeCard() {
        const targets = [
            document.querySelector(".kanji"),
            document.querySelector(".kanji-list")
        ];

        targets.forEach(wrapKanji);
    }

    initializeCard();

    <!-- Hover logic to show Kanji Meaning Tooltip -->
    const tooltip = document.getElementById("kanji-tooltip");

    document.addEventListener("mouseover", (e) => {
        const el = e.target.closest(".kanji-hover");
        if (!el) return;

        const kanji = el.dataset.kanji;
        const meaning = kanjiMeanings[kanji];

        if (!meaning) return;

        tooltip.textContent = `${kanji}: ${meaning}`;
        tooltip.style.display = "block";
    });

    document.addEventListener("mousemove", (e) => {
        const margin = 12;

        let cursorX = e.clientX;
        let cursorY = e.clientY;

        let windowWidth = window.innerWidth;
        let windowHeight = window.innerHeight;

        let tooltipWidth = tooltip.offsetWidth;
        let tooltipHeight = tooltip.offsetHeight;

        let tooltipX = cursorX + margin;
        let tooltipY = cursorY + margin;

        tooltip.style.left = (tooltipX) + "px";
        tooltip.style.top = (tooltipY) + "px";

        if (tooltipX + tooltipWidth > windowWidth) {
            tooltipX = cursorX - tooltipWidth - margin;
        }

        if (tooltipY + tooltipHeight > windowHeight) {
            tooltipY = cursorY - tooltipHeight - margin;
        }

        tooltip.style.left = `${tooltipX}px`;
        tooltip.style.top = `${tooltipY}px`;
    });

    document.addEventListener("mouseout", (e) => {
        if (e.target.closest(".kanji-hover")) {
            tooltip.style.display = "none";
        }
    });
})();
</script>
"""

MINING_CARD_CSS = r"""
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Text sizing */
.reading {
  font-size: 1.5em;
  margin-bottom: 0.4em;
}

.meaning {
  font-size: 1em;
  margin-bottom: 0.5em;
}

.example {
  font-size: 0.95em;
  margin-top: 0.5em;
  padding-left: 0.5em;
  border-left: 3px solid #ddd;
  color: #444;
  font-style: italic;
}

/* Smaller, top-right container */
.top-right {
  position: absolute;
  top: 0.8em;
  right: 1em;

  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4em;
}

/* Kanji display */
.kanji {
  font-size: 1.5em;
  font-weight: 500;
  cursor: help;
}

/* Indicators within top-right container */
.indicators {
	display: flex;
	gap: 0.4em;
	align-items: center;
}

/* Kanji is known indicator */
.kanji-indicator {
  position: relative;
  top: 0px;
  right: 0px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.kanji-indicator.known {
  background-color: #4caf50;
}

.kanji-indicator.unknown {
  background-color: #ffa500;
}

.kanji-indicator.no-kanji {
	background-color: #ccc;
}

/* Usually Kana indicator */
.usually-kana-indicator {
  position: relative;
  top: 0px;
  right: 0px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
	background-color: #ccc;
}

.usually-kana-indicator.true {
	background-color: #9c27b0
}

.usually-kana-indicator.false {
	background-color: #2196f3;
}

/* Tooltip */
.tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  top: 140%;
  right: 0;
  background: #333;
  color: #fff;
  font-size: 0.75em;
  padding: 4px 6px;
  border-radius: 4px;
  white-space: nowrap;
  transition: opacity 0.2s;
}

.kanji-indicator:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.usually-kana-indicator:hover .tooltip {
	visibility: visible;
	opacity: 1;
}

/* Hide furigana by default */
ruby rt {
  visibility: hidden;
  font-size: 0.5em;
  color: #555;
}

/* Show furigana always */
ruby.is-always-visible rt {
  visibility: visible;
}

/* Show furigana on hover */
ruby:not(.is-always-visible):hover rt {
  visibility: visible;
}

/* Kanji Keywords */
.kanji-keywords {
  margin-top: 0em;
}

.kanji-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4em;
  margin-top: 0.4em;
}

.kanji-chip {
  display: inline-block;
  padding: 0.25em 0.55em;
  background: #f6f6f6;
  border: 1px solid #e3e3e3;
  border-radius: 999px;
  font-size: 0.82em;
  color: #555;
  line-height: 1.3;
}

.kanji-chip .char {
  font-size: 1.15em;
  font-weight: 600;
  color: #222;
  margin-right: 0.25em;
}
"""

MINING_BACKWARD_FRONT_HTML = r"""
<div class="meaning" id="readingFront">
  {{Meaning}}
</div>

<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>
</div>

<div id="hint" style="display:none; margin-top:0.3em;">
  <div class="example">{{Translation}}</div>
</div>

{{#Example Sentence}}
<button onclick="document.getElementById('hint').style.display='block'; this.style.display='none';">
  Show Sentence
</button>
{{/Example Sentence}}
"""

MINING_BACKWARD_BACK_HTML = r"""
<style>
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Badges */
.badges {
  display: flex;
  flex-direction: column;
  gap: 0.2em;
}

.badge {
  font-size: 0.5em;
  font-weight: 600;
  padding: 0.1em 0.35em;
  border-radius: 10px;
  color: #fff;
  text-align: center;
  white-space: nowrap;
}

.badge.jlpt { background-color: #4d8dff; }
.badge.wk { background-color: #c04dff; }
.badge.common { background-color: #4fbf6a; }

/* Section labels */
h1 {
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 1em 0 0.3em;
  color: #777;
}

/* Dividers */
hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 0.8em 0;
}

/* Note section */
.note {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Mnemonic section */
.mnemonic {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Meta info */
.meta {
  font-size: 0.82em;
  color: #666;
  margin-top: 0.6em;
}

/* Kanji Meanings Tooltip */
#kanji-tooltip {
  position: fixed;
  display: none;
  background: #222;
  color: #fff;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 0.85em;
  pointer-events: none;
  max-width: 220px;
  z-index: 9999;
}

/* Audio Play Button */
.audio-button {
  display: flex;
  justify-content: flex-end;
}
</style>

<div class="kanji" style="margin-top:0.3em;">
  <ruby>
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<!-- Top-right info area -->
<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>

	<!-- Badges in top-right corner -->
  <div class="badges">
    <div class="badge jlpt">JLPT {{JLPT Level}}</div>
    <div class="badge wk">WK {{Wanikani Level}}</div>
    <div class="badge common">{{#Is Common}}Common{{/Is Common}}{{^Is Common}}Rare{{/Is Common}}</div>
  </div>

	<!-- Audio Play Button -->
  <div class="audio-button">
    {{Audio}}
  </div>
</div>

<h1>Reading</h1>
<div class="reading">
  {{Reading}}
</div>

<h1>Meaning</h1>
<div class="meaning">{{Meaning}}</div>

<h1>Example Sentence</h1>
<div class="example">{{Example Sentence}}</div>
<div class="example">{{Translation}}</div>

{{#Note}}
<h1>Note</h1>
<div class="note">{{Note}}</div>
{{/Note}}

{{#Mnemonic}}
<h1>Mnemonic</h1>
<div class="mnemonic">{{Mnemonic}}</div>
{{/Mnemonic}}

<hr>

<div class="meta">
  <strong>Part of speech:</strong> {{Part of speech}} ·<br>
  <strong>Info:</strong> {{Info}} ·<br>
  <strong>Tags:</strong> {{Tags}} ·<br>
  <strong>Other forms:</strong> {{Other forms}} ·
</div>

<!-- Kanji Keywords -->
{{#Kanji Keywords}}
<h1>Kanji Keywords</h1>
<div class="kanji-keywords">
  <div class="kanji-list">
    {{Kanji Keywords}}
  </div>
</div>
{{/Kanji Keywords}}

<!-- Kanji Meanings Tooltip-->
<div id="kanji-tooltip"></div>

<!-- Java Script -->
<script>
(() => {
    <!-- Format Kanji Meanings -->
    const rawMeanings = `{{Kanji Meanings}}`;

    const kanjiMeanings = Object.fromEntries(
        rawMeanings.split("|").map(part => {
            const [kanji, meanings] = part.split(":").map(s => s.trim());
            return [kanji, meanings];
        }).filter(x => x[0] && x[1])
    );

    <!-- Wrap Kanji in spans -->
    function wrapKanji(root) {
        if (!root) return;
        if (root.dataset.wrapped) return;
        root.dataset.wrapped = "1";

        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        const kanjiRegex = /[\u4e00-\u9faf]/g;

        const nodes = [];
        let node;

        while (node = walker.nextNode()) {
            if (kanjiRegex.test(node.nodeValue)) {
                nodes.push(node);
            }
        }

        for (const textNode of nodes) {
            const span = document.createElement("span");
            span.innerHTML = textNode.nodeValue.replace(
                kanjiRegex,
                c => `<span class="kanji-hover" data-kanji="${c}">${c}</span>`
            );
            textNode.replaceWith(span);
        }
    }

    function initializeCard() {
        const targets = [
            document.querySelector(".kanji"),
            document.querySelector(".kanji-list")
        ];

        targets.forEach(wrapKanji);
    }

    initializeCard();

    <!-- Hover logic to show Kanji Meaning Tooltip -->
    const tooltip = document.getElementById("kanji-tooltip");

    document.addEventListener("mouseover", (e) => {
        const el = e.target.closest(".kanji-hover");
        if (!el) return;

        const kanji = el.dataset.kanji;
        const meaning = kanjiMeanings[kanji];

        if (!meaning) return;

        tooltip.textContent = `${kanji}: ${meaning}`;
        tooltip.style.display = "block";
    });

    document.addEventListener("mousemove", (e) => {
        const margin = 12;

        let cursorX = e.clientX;
        let cursorY = e.clientY;

        let windowWidth = window.innerWidth;
        let windowHeight = window.innerHeight;

        let tooltipWidth = tooltip.offsetWidth;
        let tooltipHeight = tooltip.offsetHeight;

        let tooltipX = cursorX + margin;
        let tooltipY = cursorY + margin;

        tooltip.style.left = (tooltipX) + "px";
        tooltip.style.top = (tooltipY) + "px";

        if (tooltipX + tooltipWidth > windowWidth) {
            tooltipX = cursorX - tooltipWidth - margin;
        }

        if (tooltipY + tooltipHeight > windowHeight) {
            tooltipY = cursorY - tooltipHeight - margin;
        }

        tooltip.style.left = `${tooltipX}px`;
        tooltip.style.top = `${tooltipY}px`;
    });

    document.addEventListener("mouseout", (e) => {
        if (e.target.closest(".kanji-hover")) {
            tooltip.style.display = "none";
        }
    });
})();
</script>
"""

RTK_FRONT_HTML = r"""
<div class="card-content">

  <div class="keyword">
    {{#Heisig Number}}
      <a href="https://hochanh.github.io/rtk/{{Kanji}}/index.html">
        {{Keyword}}
      </a>
    {{/Heisig Number}}

    {{^Heisig Number}}
      <div class="not-found">
        <span>Kanji not found</span>
        <a href="https://jisho.org/search/{{Kanji}}%20%23kanji">
          Jisho: {{Kanji}}
        </a>
      </div>
    {{/Heisig Number}}
  </div>

</div>
"""

RTK_BACK_HTML = r"""
<div class="card-content">

  <!-- Header -->
  <div class="keyword">
    {{#Heisig Number}}
      <a href="https://hochanh.github.io/rtk/{{Kanji}}/index.html">
        {{Keyword}}
      </a>
    {{/Heisig Number}}

    {{^Heisig Number}}
      <span class="keyword-unknown">Kanji not found</span>
    {{/Heisig Number}}
  </div>

  <hr id="answer">

  <!-- Main Kanji -->
  <section class="kanji-section">

    <div class="section-label">Kanji</div>

    <div class="kanji-main">
      <span class="kanji-font yumin">{{Kanji}}</span>
      <span class="kanji-font yugothb">{{Kanji}}</span>
      <span class="kanji-font hgrkk">{{Kanji}}</span>
      <span class="kanji-font stroke-order">{{Kanji}}</span>
    </div>

  </section>

  <!-- Alternative Kanji -->
  {{#Alternative Kanji}}
  <section class="alternative-section">

    <div class="section-label">
      Alternative Kanji
    </div>

    <div class="kanji-alternative">
      <span class="kanji-font yumin">{{Alternative Kanji}}</span>
      <span class="kanji-font yugothb">{{Alternative Kanji}}</span>
      <span class="kanji-font hgrkk">{{Alternative Kanji}}</span>
      <span class="kanji-font stroke-order">{{Alternative Kanji}}</span>
    </div>

  </section>
  {{/Alternative Kanji}}

  <!-- Story -->
  {{#Story}}
  <section class="story-section">

    <div class="section-label">Story</div>

    <div class="story">
      {{Story}}
    </div>

  </section>
  {{/Story}}

  <!-- Meta -->
  <section class="meta">

    {{#Stroke Count}}
    <div class="meta-item">
      <span class="meta-label">Strokes</span>
      <span class="meta-value">{{Stroke Count}}</span>
    </div>
    {{/Stroke Count}}

    {{#Heisig Number}}
    <div class="meta-item">
      <span class="meta-label">RTK</span>
      <span class="meta-value">#{{Heisig Number}}</span>
    </div>
    {{/Heisig Number}}

  </section>

</div>
"""

RTK_CARD_CSS = r"""
.card {
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Arial,
    sans-serif;

  font-size: 20px;
  line-height: 1.5;

  color: #2f2f2f;
  background: #fcfcfc;

  margin: 0;
  padding: 1.2em 1.1em;

  text-align: center;

  -webkit-text-size-adjust: none;
}

.card-content {
  max-width: 850px;
  margin: 0 auto;
}


/* Keyword */

.keyword {
  font-size: 1.7em;
  font-weight: 500;
  line-height: 1.2;
  margin: 0.15em 0 0.35em;
}

.keyword a {
  color: #222;
  text-decoration: none;
}

.keyword a:hover {
  color: #555;
  text-decoration: underline;
}

.keyword-unknown {
  color: #777;
}

.not-found {
  display: flex;
  flex-direction: column;
  gap: 0.25em;
  font-size: 1em;
  color: #777;
}

.not-found a {
  color: #555;
  font-size: 0.75em;
}


/* Divider */

hr#answer {
  border: none;
  border-top: 1px solid #dedede;
  margin: 1em 0 1.2em;
}


/* Section labels */

.section-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;

  margin: 0 0 0.55em;

  color: #777;

  font-size: 0.62em;
  font-weight: 700;

  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-label::before,
.section-label::after {
  content: "";
  width: 2em;
  height: 1px;
  background: #ddd;
}


/* Main Kanji */

.kanji-section {
  margin-bottom: 1.3em;
}

.kanji-main {
  display: flex;
  justify-content: center;
  align-items: baseline;
  flex-wrap: wrap;

  gap: 0.05em;

  color: #181818;
  line-height: 1;
}

.kanji-font {
  display: inline-block;

  font-size: 5.8em;
  line-height: 1;

  margin: 0 0.015em;
}

.yumin {
  font-family: YUMIN;
}

.yugothb {
  font-family: YUGOTHB;
}

.hgrkk {
  font-family: HGRKK;
}

.stroke-order {
  font-family: StrokeOrder;
}


/* Alternative Kanji */

.alternative-section {
  margin-top: 1.3em;
  padding-top: 1em;

  border-top: 1px solid #eee;
}

.kanji-alternative {
  display: flex;
  justify-content: center;
  align-items: baseline;
  flex-wrap: wrap;

  gap: 0.05em;

  color: #444;
  line-height: 1;
}

.kanji-alternative .kanji-font {
  font-size: 3.8em;
}


/* Story */

.story-section {
  margin-top: 1.5em;
}

.story {
  max-width: 700px;
  margin: 0 auto;

  padding: 0.75em 0.9em;

  background: #f5f5f5;

  border: 1px solid #e8e8e8;
  border-radius: 7px;

  color: #555;

  font-family: Arial, sans-serif;
  font-size: 0.95em;

  text-align: center;
}


/* Metadata */

.meta {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;

  gap: 0.45em;

  margin-top: 1.2em;
  padding-top: 0.9em;

  border-top: 1px solid #e5e5e5;
}

.meta-item {
  display: inline-flex;
  align-items: center;

  gap: 0.35em;

  padding: 0.25em 0.65em;

  background: #f3f3f3;

  border: 1px solid #e3e3e3;
  border-radius: 999px;

  font-size: 0.65em;
}

.meta-label {
  color: #888;
  font-weight: 600;
}

.meta-value {
  color: #444;
}


/* Fonts */

@font-face {
  font-family: YUMIN;
  src: url('_YUMIN.ttf');
}

@font-face {
  font-family: StrokeOrder;
  src: url('_StrokeOrder.ttf');
}

@font-face {
  font-family: HGRKK;
  src: url('_HGRKK.ttc');
}

@font-face {
  font-family: YUGOTHB;
  src: url('_YUGOTHB.ttc');
}


/* Mobile */

@media (max-width: 600px) {
  .card {
    font-size: 18px;
    padding: 1em 0.7em;
  }

  .keyword {
    font-size: 1.45em;
  }

  .kanji-font {
    font-size: 4.4em;
  }

  .kanji-alternative .kanji-font {
    font-size: 3em;
  }

  .font-labels {
    font-size: 0.42em;
  }
}


/* Dark mode */

.nightMode .card {
  color: #ddd;
  background: #202020;
}

.nightMode .keyword a {
  color: #f0f0f0;
}

.nightMode .keyword a:hover {
  color: #fff;
}

.nightMode .keyword-unknown {
  color: #aaa;
}

.nightMode .not-found {
  color: #aaa;
}

.nightMode .not-found a {
  color: #bbb;
}

.nightMode hr#answer,
.nightMode .alternative-section,
.nightMode .meta {
  border-color: #383838;
}

.nightMode .section-label {
  color: #999;
}

.nightMode .section-label::before,
.nightMode .section-label::after {
  background: #444;
}

.nightMode .kanji-main {
  color: #f2f2f2;
}

.nightMode .kanji-alternative {
  color: #ccc;
}

.nightMode .font-labels {
  color: #777;
}

.nightMode .story {
  background: #292929;
  border-color: #3a3a3a;
  color: #ccc;
}

.nightMode .meta-item {
  background: #292929;
  border-color: #3a3a3a;
}

.nightMode .meta-label {
  color: #999;
}

.nightMode .meta-value {
  color: #ccc;
}
"""
