from aqt import mw
from aqt.utils import tooltip
from anki.notes import Note
import csv
import math
from pathlib import Path

from ..config import Config
from .kanji_data_service import KanjiDataService
from ..domain.kanji import is_kanji


class CollectionService:
    _HEISIG_KANJIS_FILE = "heisig-kanjis.csv"
    _REQUIRED_MINING_FIELDS = [
        "Word",
        "Kanji is known",
        "No Kanji",
        "Usually Kana",
        "Kanji Keywords",
        "Kanji Meanings",
    ]

    def __init__(self, config: Config, kanji_data: KanjiDataService):
        self._config = config
        self._kanji_data = kanji_data

    # --- PUBLIC METHODS --- #
    def force_update_keywords(self) -> None:
        self.update_japanese_mining_cards(force_update_keywords=True)

    def force_update_meanings(self) -> None:
        self.update_japanese_mining_cards(force_update_meanings=True)

    def force_update_everything(self) -> None:
        self.update_japanese_mining_cards(force_update_meanings=True, force_update_keywords=True)

    def fetch_kanji_keyword(self, kanji: str) -> str:
        """Returns one learned keyword associated with kanji from RTK deck"""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return ""

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
        return f"{kanji} {self._get_field(note, keyword_field)}"

    def add_unknown_kanji(self) -> int:
        """Add missing Kanji to the RTK deck"""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return 0

        col = mw.col
        deck = self._config.rtk_deck

        unknown_kanji = self._find_unknown_kanji()
        deck_id = col.decks.id(deck)

        path = self._media_path(self._HEISIG_KANJIS_FILE)
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            kanji_rows = {row["kanji"]: row for row in reader}

        for kanji in unknown_kanji:
            note = self._create_rtk_note(kanji=kanji, tags=["Self-Added"], heisig_kanjis=kanji_rows)
            if note:
                col.add_note(note, deck_id)

        if self._config.show_tooltip:
            tooltip(f"Added {len(unknown_kanji)} unknown kanji to the RTK deck.")

        return len(unknown_kanji)

    def export_learned_kanji(self) -> tuple[int, int]:
        """Save all Kanji, keywords, and learned status in a csv file."""
        if not self._rtk_configured():
            if self._config.show_tooltip:
                tooltip("RTK deck is not configured. Please check your settings.")
            return 0, 0

        col = mw.col
        deck = self._config.rtk_deck
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        all_card_ids = col.find_cards(f'deck:"{deck}"')
        learned_card_ids = set(col.find_cards(f'deck:"{deck}" -is:new'))

        kanji_list = []
        count_unknown_kanji = 0
        count_learned_kanji = 0
        count_learned_alternative_kanji = 0

        for cid in all_card_ids:
            card = col.get_card(cid)
            note = card.note()
            is_learned = cid in learned_card_ids

            if kanji_field in note:
                kanji = self._get_field(note, kanji_field)
                if kanji:
                    kanji_list.append((kanji, is_learned))
                    if is_learned:
                        count_learned_kanji += 1
                    else:
                        count_unknown_kanji += 1

            if alt_kanji_field in note:
                kanji = self._get_field(note, alt_kanji_field).strip()
                if kanji:
                    kanji_list.append((kanji, is_learned))
                    if is_learned:
                        count_learned_alternative_kanji += 1
                    else:
                        count_unknown_kanji += 1

        kanji_rows = {}
        for kanji, is_learned in kanji_list:
            kanji_rows[kanji] = kanji_rows.get(kanji, False) or is_learned

        learned_kanji_rows = []
        learned_kanji_cache = {}

        for kanji in sorted(kanji_rows, key=lambda item: (not kanji_rows[item], item)):
            keyword = self.fetch_kanji_keyword(kanji)
            learned = kanji_rows[kanji]

            knowledge = 0.0
            if learned:
                card_ids = col.find_cards(
                    f'deck:"{deck}" ({kanji_field}:{kanji} OR "{alt_kanji_field}:{kanji}")'
                )
                for cid in card_ids:
                    card = col.get_card(cid)
                    r = self._get_card_knowledge(card)
                    if r > knowledge:
                        knowledge = r

            learned_kanji_rows.append({
                "Kanji": kanji,
                "Keyword": keyword,
                "Learned": "1" if learned else "",
                "Knowledge": f"{knowledge:.4f}" if learned else "",
            })
            learned_kanji_cache[kanji] = {
                "Keyword": keyword,
                "Learned": learned,
                "Knowledge": knowledge if learned else 0.0,
            }

        if self._kanji_data:
            self._kanji_data.save_learned_kanji(learned_kanji_rows, learned_kanji_cache)

        if self._config.show_tooltip:
            tooltip(f"Exported {count_learned_kanji + count_learned_alternative_kanji} learned kanji and {count_unknown_kanji} unknown kanji.")

        return count_learned_kanji + count_learned_alternative_kanji, count_unknown_kanji

    def update_single_note_kanji_knowledge(self, note: Note, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update kanji fields for a single note added from the editor."""
        if note is None:
            return 0, 0

        if note.note_type()["name"] != self._config.mining_note_type:
            if self._config.show_tooltip:
                tooltip(f"The note is not a {self._config.mining_note_type} note. Please check your settings.")
            return 0, 0

        newly_known_count, updated_count = self._update_kanji_knowledge(
            note=note,
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        return newly_known_count, updated_count

    def update_japanese_mining_cards(self, force_update_meanings: bool = False, force_update_keywords: bool = False) -> None:
        """Update all JapaneseMining cards in a single pass over each word."""
        number_learned_kanji, count_unknown_kanji = self.export_learned_kanji()
        newly_known_count, number_updated_cards = self._update_kanji_knowledge(
            force_update_meanings=force_update_meanings,
            force_update_keywords=force_update_keywords,
        )
        number_unknown_kanji = self.add_unknown_kanji()

        if self._config.show_tooltip:
            tooltip(
                f"Exported {number_learned_kanji} learned and {count_unknown_kanji} not learned kanji. "
                f"{newly_known_count} card(s) became known. "
                f"{number_updated_cards} card(s) were updated. {number_unknown_kanji} unknown kanji were added."
            )

    def create_rtk_deck_and_note_type(
        self,
        deck_name: str,
        note_type_name: str,
        create_all_notes: bool = True,
    ) -> tuple[bool, str]:
        """
        Create (or reuse) the RTK note type + deck.
        Optionally bulk-create notes from heisig-kanjis.csv.
        Updates self._config with the standard field mapping.
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

        if model is None:
            model = mm.new(note_type_name)

            for field_name in (
                "Kanji",
                "Alternative Kanji",
                "Keyword",
                "Story",
                "Heisig Number",
                "Stroke Count",
            ):
                mm.add_field(model, mm.new_field(field_name))

            model["sortf"] = 4  # Heisig Number becomes the sort field

            t = mm.new_template("Recognition")
            t["qfmt"] = FRONT_HTML
            t["afmt"] = BACK_HTML
            mm.add_template(model, t)

            model["css"] = CARD_CSS
            mm.add(model)
            created_model = True
        else:
            existing = {f["name"] for f in model["flds"]}
            required = {"Kanji", "Alternative Kanji", "Keyword"}
            missing = required - existing
            if missing:
                return False, (
                    f"Note type “{note_type_name}” already exists but is missing "
                    f"required fields: {', '.join(sorted(missing))}. "
                    "Choose a different name or fix the note type."
                )

        # ----- 2. Deck (creates if missing) -----
        deck_id = col.decks.id(deck_name)

        # ----- 3. Update config so the rest of the addon is consistent -----
        self._config.rtk_deck = deck_name
        self._config.rtk_note_type = note_type_name
        self._config.rtk_kanji_field = "Kanji"
        self._config.rtk_alternative_kanji_field = "Alternative Kanji"
        self._config.rtk_keyword_field = "Keyword"
        self._config.rtk_heisig_number_field = "Heisig Number"
        self._config.rtk_stroke_count_field = "Stroke Count"

        # ----- 4. Optionally create all Heisig notes -----
        notes_created = 0
        if create_all_notes:
            path = self._resolve_heisig_csv()
            if path is None:
                return False, (
                    f"Could not find {self._HEISIG_KANJIS_FILE}. "
                    "Put it in the Anki media folder or in the add-on’s vendor/ directory."
                )

            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                kanji_rows = {row["kanji"]: row for row in reader if row.get("kanji")}

            # sort by Heisig number (id_6th_ed) so that the cards are added in order (id_5th_ed is fallback)
            sorted_rows = sorted(kanji_rows.values(), key=lambda row: self._heisig_number_and_edition(row)[0])

            for row in sorted_rows:
                kanji = row["kanji"]
                note = self._create_rtk_note(
                    kanji=kanji,
                    tags=["Heisig"],
                    heisig_kanjis=kanji_rows,
                )
                if note is None:
                    continue

                col.add_note(note, deck_id)

                heisig_num = self._heisig_number_and_edition(row)[0]
                for card in note.cards():
                    card.due = heisig_num
                    col.update_card(card)

                notes_created += 1

        col.save()

        parts = []
        if created_model:
            parts.append(f"Created note type “{note_type_name}”")
        else:
            parts.append(f"Re-used existing note type “{note_type_name}”")
        parts.append(f"Deck “{deck_name}” is ready")
        if create_all_notes:
            parts.append(f"Added {notes_created} new notes")

        self._ensure_rtk_fonts()

        return True, ". ".join(parts) + "."

    def import_known_kanji_from_file(
        self,
        file_path: str | Path,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ) -> tuple[bool, str]:
        """
        Parse a file of known kanji (one per line, or kanji,keyword).
        Updates learned_kanji.csv. Optionally creates/updates RTK cards.
        """
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {path}"

        try:
            entries = self._parse_kanji_file(path)
        except Exception as e:
            return False, f"Coudl not read file: {e}"

        if not entries:
            return False, "No kanji found in the file."

        # Make sure we start from whatever is already on disk
        self._kanji_data.load_learned_kanji()

        marked, touched = self._apply_known_kanji(
            entries,
            fill_keywords=fill_keywords,
            suspend = suspend,
            schedule_min_days=schedule_min_days,
            schedule_max_days=schedule_max_days,
        )
        return True, f"Marked {marked} kanji as known. Touched {touched} card(s)."

    def import_known_kanji_up_to_heisig(
        self,
        heisig_number: int,
        *,
        fill_keywords: bool = True,
        suspend: bool = True,
        schedule_min_days: int = 30,
        schedule_max_days: int = 700,
    ):
        """
        Mark every Heisig kanji with id_6th_ed ≤ heisig_number as learned.
        """
        if heisig_number < 1:
            return False, "Heisig number must be ≥ 1."

        path = self._resolve_heisig_csv()
        if path is None:
            return False, "Heisig CSV not found."

        with path.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        entries: list[tuple[str, str]] = []
        for row in rows:
            n, edition = self._heisig_number_and_edition(row)
            if n == 99999:  # Missing
                continue
            if n > heisig_number:
                continue
            keyword = self._heisig_keyword(row) if fill_keywords else ""
            entries.append((row["kanji"], keyword))

        if not entries:
            return False, f"No kanji found with Heisig number ≤ {heisig_number}."

        # Make sure we start from whatever is already on disk
        self._kanji_data.load_learned_kanji()

        marked, touched = self._apply_known_kanji(
            entries,
            fill_keywords=fill_keywords,
            suspend=suspend,
            schedule_min_days=schedule_min_days,
            schedule_max_days=schedule_max_days,
        )
        return True, f"Marked {marked} kanji as known. Touched {touched} card(s)."

    # --- PRIVATE METHODS --- #
    def _find_unknown_kanji(self) -> list[str]:
        """Find all unknown Kanji in JapaneseMining cards"""
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        rtk_note_ids = mw.col.find_notes(f'note:"{self._config.rtk_note_type}"')
        mining_note_ids = mw.col.find_notes(f'note:{self._config.mining_note_type} -is:suspended')

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

    def _create_rtk_note(self, kanji: str, alt_kanji: str = "", tags=None, heisig_kanjis=None) -> Note | None:
        """Create a new Remembering the Kanji note"""
        col = mw.col
        kanji_field = self._config.rtk_kanji_field
        alt_kanji_field = self._config.rtk_alternative_kanji_field

        tags = tags or []
        model = col.models.by_name(self._config.rtk_note_type)
        if model is None:
            raise RuntimeError(f"Note type '{self._config.rtk_note_type}' not found")

        note = Note(col, model)
        note[kanji_field] = kanji
        note[alt_kanji_field] = alt_kanji
        note.tags.extend(tags)

        if heisig_kanjis is not None:
            row = heisig_kanjis.get(kanji)
            if row:
                note[self._config.rtk_keyword_field] = row["keyword_6th_ed"]
            if row and self._has_field(note, self._config.rtk_heisig_number_field):
                note[self._config.rtk_heisig_number_field] = row["id_6th_ed"]    # Optional
            if row and self._has_field(note, self._config.rtk_stroke_count_field):
                note[self._config.rtk_stroke_count_field] = row["stroke_count"]  # Optional

        if note.dupeOrEmpty():
            return None
        return note

    def _update_note_kanji_knowledge(self, note: Note, learned_kanji: dict, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update kanji knowledge fields for one note."""
        if not self._mining_fields_ok(note):
            if self._config.show_tooltip:
                tooltip(f"Note {note.id} is missing required fields. Please check your note and you notetype {self._config.mining_note_type}.")
            return 0, 0

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
                kanji_keyword = kanji_entry.get("Keyword", "") if kanji_entry else ""
                if kanji_keyword and kanji_keyword not in keywords:
                    keywords.append(kanji_keyword)

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
            note["Kanji is known"] = new_value
            should_update = True

        if keywords:
            note["Kanji Keywords"] = " · ".join(keywords)
            should_update = True

        if meanings:
            note["Kanji Meanings"] = " | ".join(meanings)
            should_update = True

        tags = self._get_field(note, "Tags")
        if self._get_field(note, "Usually Kana") != "1" and "Usually written using kana alone" in tags:
            note["Usually Kana"] = "1"
            should_update = True

        if should_update:
            col.update_note(note)

        return newly_known, int(should_update)


    def _update_kanji_knowledge(self, note: Note = None, force_update_meanings: bool = False, force_update_keywords: bool = False) -> tuple[int, int]:
        """Update JapaneseMining cards in a single pass over each word."""
        col = mw.col

        learned_kanji = self._kanji_data.get_learned_kanji()
        if note is not None:
            notes = [note]
        else:
            notes = (col.get_note(note_id) for note_id in col.find_notes(f"note:{self._config.mining_note_type}"))

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

        if note is None and self._config.show_tooltip:
            tooltip(
                f"Rechecked kanji knowledge. {newly_known_count} card(s) became known. "
                f"Updated kanji details for {updated_count} card(s)."
            )

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
        if card.type == 0:          # new
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
            retrievability = 0.9          # neutral default when missing

        retrievability = max(0.0, min(1.0, retrievability))

        # Final blend: stability is the dominant signal
        knowledge = 0.75 * stab_norm + 0.25 * retrievability
        return max(0.0, min(1.0, knowledge))

    def _resolve_heisig_csv(self) -> Path | None:
        """Prefer media folder, fall back to vendor/ inside the add-on package."""
        media = self._media_path(self._HEISIG_KANJIS_FILE)
        if media.exists():
            return media

        vendor = Path(__file__).resolve().parent.parent / "vendor" / self._HEISIG_KANJIS_FILE
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
        from datetime import date, timedelta
        import random

        # 1. Load Heisig data once (for keywords + later card creation)
        heisig_rows: dict[str, dict] = {}
        path = self._resolve_heisig_csv()
        if path is not None:
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                heisig_rows = {row["kanji"]: row for row in reader if row.get("kanji")}

        # 2. Build the new learned cache entries
        cache = dict(self._kanji_data.get_learned_kanji())  # start from current
        rows_for_csv = []

        for kanji, keyword in entries:
            kanji = (kanji or "").strip()
            if not kanji or not is_kanji(kanji[0]):   # simple guard
                continue
            kanji = kanji[0]  # take first character if someone pasted a compound

            if not keyword and fill_keywords and kanji in heisig_rows:
                keyword = self._heisig_keyword(heisig_rows[kanji])

            cache[kanji] = {
                "Keyword": keyword or cache.get(kanji, {}).get("Keyword", ""),
                "Learned": True,
                "Knowledge": 1.0,
            }

        # Rebuild full CSV rows (keep previously known + newly imported)
        for k, v in sorted(cache.items(), key=lambda kv: (not kv[1]["Learned"], kv[0])):
            rows_for_csv.append({
                "Kanji": k,
                "Keyword": v.get("Keyword", ""),
                "Learned": "1" if v.get("Learned") else "",
                "Knowledge": f"{v.get('Knowledge', 0.0):.4f}" if v.get("Learned") else "",
            })

        self._kanji_data.save_learned_kanji(rows_for_csv, cache)

        # 3. Optionally touch RTK cards
        cards_touched = 0
        if self._rtk_configured():
            col = mw.col
            deck_id = col.decks.id(self._config.rtk_deck)

            for kanji, _ in entries:
                kanji = (kanji or "").strip()
                if not kanji:
                    continue
                kanji = kanji[0]

                # Re-use existing note-creation helper
                note = self._create_rtk_note(
                    kanji=kanji,
                    tags=["Imported-Known"],
                    heisig_kanjis=heisig_rows,
                )
                if note is None:
                    # already exists – find it and update scheduling if needed
                    note_ids = col.find_notes(
                        f'note:"{self._config.rtk_note_type}" '
                        f'{self._config.rtk_kanji_field}:{kanji}'
                    )
                    if not note_ids:
                        continue
                    note = col.get_note(note_ids[0])
                else:
                    col.add_note(note, deck_id)

                for card in note.cards():
                    if suspend:
                        card.queue = -1          # suspended
                    else:
                        # Turn into a review card with a far-future due date
                        days = random.randint(schedule_min_days, schedule_max_days)
                        card.type = 2            # review
                        card.queue = 2
                        card.ivl = days
                        card.factor = 2500        # 250 %
                        card.due = col.sched.today + days
                    col.update_card(card)
                    cards_touched += 1

        return len({e[0][0] for e in entries if e[0]}), cards_touched

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

    def _ensure_rtk_fonts(self) -> None:
        import shutil
        media_dir = Path(mw.col.media.dir())
        vendor_fonts = Path(__file__).resolve().parent.parent / "vendor" / "fonts"
        for name in ("_YUMIN.ttf", "_YUGOTHB.ttc", "_HGRKK.ttc", "_StrokeOrder.ttf"):
            src = vendor_fonts / name
            dst = media_dir / name
            if src.exists() and not dst.exists():
                shutil.copy(src, dst)


FRONT_HTML = r"""
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

BACK_HTML = r"""
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

CARD_CSS = r"""
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