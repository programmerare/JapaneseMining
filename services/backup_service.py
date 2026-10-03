"""
Backup / restore of the RTK deck.

- The live RTK deck remains the source of truth; a backup is a snapshot
  taken directly from that deck, never from the learned_kanji cache.
- Restore always creates a new deck, so the operation is non-destructive.
- If the original note type is missing or its fields diverge, restore
  creates a fresh note type with a unique name and the exact field list
  from the snapshot. Field values are always restored from the backup.

Storage: <addon>/user_files/profiles/<profile_id>/backups/rtk_backup_YYYYMMDD_HHMMSS.json
Format version 1 is a single JSON document (see _SCHEMA_VERSION).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from anki.notes import Note

from .collection_service import CollectionService
from ..config import ConfigHolder, profile_user_dir
from ..domain.errors import JapaneseMiningError
from ..domain.fsrs_stats import extract_stat
from ..domain.results import UpdateResult
from ..domain.rtk_config import is_rtk_configured


_SCHEMA_VERSION = 1
_MAX_BACKUPS = 20
_BACKUP_PREFIX = "rtk_backup_"
_BACKUP_SUFFIX = ".json"


# ---------------------------------------------------------------------------
# Data shapes (internal; serialised to JSON)
# ---------------------------------------------------------------------------

@dataclass
class CardSnapshot:
    """Scheduling + FSRS state for one card of a note."""

    ord: int = 0
    type: int = 0          # 0=new, 1=learning, 2=review, 3=relearning
    queue: int = 0         # -1=suspended, …
    due: int = 0
    ivl: int = 0
    factor: int = 0
    reps: int = 0
    lapses: int = 0
    left: int = 0
    odue: int = 0
    odid: int = 0
    flags: int = 0         # Anki coloured flag (0 = none, 1–7)
    stability: float | None = None
    difficulty: float | None = None
    retrievability: float | None = None
    custom_data: str | None = None
    data: str | None = None


@dataclass
class NoteSnapshot:
    kanji: str
    fields: dict[str, str]
    tags: list[str] = field(default_factory=list)
    cards: list[CardSnapshot] = field(default_factory=list)


@dataclass
class NoteTypeSnapshot:
    name: str
    fields: list[str]
    templates: list[dict[str, str]] = field(default_factory=list)
    css: str = ""


@dataclass
class BackupMeta:
    format_version: int
    created_at: str
    source_deck: str
    source_note_type: str
    field_map: dict[str, str]
    anki_version: str = ""
    entry_count: int = 0
    learned_count: int = 0


@dataclass
class BackupDocument:
    meta: BackupMeta
    note_type: NoteTypeSnapshot
    entries: list[NoteSnapshot]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class BackupService:
    """Create, list, prune and restore RTK deck backups."""

    def __init__(self, config_holder: ConfigHolder, collection_service: CollectionService):
        self._config_holder = config_holder
        self._collection_service = collection_service
        self._last_daily_backup_by_profile: dict[str, str] = {}

    @property
    def _config(self):
        return self._config_holder.config

    # ----- paths ----------------------------------------------------------

    def backups_dir(self) -> Path:
        path = profile_user_dir() / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _backup_path(self, stamp: str | None = None) -> Path:
        if stamp is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.backups_dir() / f"{_BACKUP_PREFIX}{stamp}{_BACKUP_SUFFIX}"

    # ----- public API -----------------------------------------------------

    def list_backups(self, limit: int = _MAX_BACKUPS) -> list[dict[str, Any]]:
        """Return newest-first metadata for existing backups."""
        dir_ = self.backups_dir()
        files = sorted(
            dir_.glob(f"{_BACKUP_PREFIX}*{_BACKUP_SUFFIX}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]

        out: list[dict[str, Any]] = []
        for p in files:
            meta = self._read_meta_only(p)
            out.append(
                {
                    "path": str(p),
                    "filename": p.name,
                    "created_at": (meta or {}).get("created_at") or "",
                    "source_deck": (meta or {}).get("source_deck") or "",
                    "entry_count": (meta or {}).get("entry_count") or 0,
                    "learned_count": (meta or {}).get("learned_count") or 0,
                    "size_bytes": p.stat().st_size,
                }
            )
        return out

    def create_backup(self) -> Path:
        """
        Snapshot the configured RTK deck into a new backup file.
        Raises JapaneseMiningError if RTK is not configured or the deck is empty.
        Prunes older backups beyond _MAX_BACKUPS.
        """
        self._require_rtk_configured()

        card_ids = self._collection_service.find_cards_by_query(f'deck:"{self._config.rtk_deck}"')
        if not card_ids:
            raise JapaneseMiningError(f"Deck “{self._config.rtk_deck}” has no cards to back up.")

        model = self._get_rtk_model_or_raise()
        entries, learned_count = self._collect_note_snapshots(card_ids, model)
        note_type_snap = self._build_note_type_snapshot(model, self._config.rtk_note_type)
        meta = self._build_backup_meta(entries, learned_count)

        doc = BackupDocument(meta=meta, note_type=note_type_snap, entries=entries)
        path = self._backup_path()
        self._write_document(path, doc)
        self._prune_old_backups()
        return path

    def restore_to_new_deck(
        self,
        backup_path: str | Path,
        *,
        deck_name: str | None = None,
    ) -> UpdateResult:
        """
        Recreate notes + cards from a backup into a new deck. Never modifies
        the current RTK deck or Deck Mapping.

        Returns an UpdateResult with kanji_added_to_rtk = number of notes created.
        """
        path = Path(backup_path)
        if not path.is_file():
            raise JapaneseMiningError(f"Backup file not found: {path}")

        doc = self._read_document(path)
        if doc.meta.format_version != _SCHEMA_VERSION:
            raise JapaneseMiningError(
                f"Unsupported backup format version {doc.meta.format_version}.",
                details=f"This add-on understands version {_SCHEMA_VERSION}.",
            )

        deck_name = deck_name or self._default_restore_deck_name(doc.meta.created_at)
        deck_id = self._collection_service.get_deck_id_by_deck_name(deck_name)
        model = self._ensure_note_type(doc.note_type)

        created = 0
        for entry in doc.entries:
            note = self._create_note_from_snapshot(entry, model)
            self._collection_service.add_note(note, deck_id)
            created += 1
            self._apply_card_snapshots(note, entry.cards)

        return UpdateResult(kanji_added_to_rtk=created)

    def maybe_create_daily_backup(self) -> Path | None:
        """
        Create a backup at most once per local calendar day. Safe to call often.
        Returns the path if a backup was created, else None.
        """
        today_local = datetime.now().strftime("%Y-%m-%d")
        profile_key = self._profile_key()
        if self._last_daily_backup_by_profile.get(profile_key) == today_local:
            return None

        if self._backup_already_exists_for(today_local):
            self._last_daily_backup_by_profile[profile_key] = today_local
            return None

        if not is_rtk_configured(self._config):
            self._last_daily_backup_by_profile[profile_key] = today_local
            return None

        try:
            path = self.create_backup()
            self._last_daily_backup_by_profile[profile_key] = today_local
            return path
        except JapaneseMiningError:
            return None
        except Exception as e:
            print(f"JapaneseMining: daily backup failed: {e}")
            return None

    def _backup_already_exists_for(self, today_local: str) -> bool:
        today_prefix = today_local.replace("-", "")
        return any(
            f"{_BACKUP_PREFIX}{today_prefix}" in p.name
            for p in self.backups_dir().glob(f"{_BACKUP_PREFIX}*{_BACKUP_SUFFIX}")
        )

    @staticmethod
    def _profile_key() -> str:
        try:
            from aqt import mw
            name = getattr(getattr(mw, "pm", None), "name", None)
            return str(name) if name else "_default"
        except Exception:
            return "_default"

    # ----- create_backup steps ---------------------------------------------

    def _require_rtk_configured(self) -> None:
        if not is_rtk_configured(self._config):
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings → RTK and set the deck + fields before creating a backup.",
            )

    def _get_rtk_model_or_raise(self):
        note_type_name = self._config.rtk_note_type
        model = self._collection_service.get_model_by_name(note_type_name)
        if model is None:
            raise JapaneseMiningError(
                f"RTK note type “{note_type_name}” not found.",
                details="Open Settings → RTK → Deck Mapping and fix the note type.",
            )
        return model

    def _collect_note_snapshots(self, card_ids: list[int], model) -> tuple[list[NoteSnapshot], int]:
        notes_map: dict[int, list] = {}
        for card_id in card_ids:
            card = self._collection_service.get_card_by_card_id(card_id)
            notes_map.setdefault(card.nid, []).append(card)

        kanji_field = (self._config.rtk_kanji_field or "").strip()
        field_names = [f["name"] for f in model["flds"]]

        entries: list[NoteSnapshot] = []
        learned_count = 0
        for note_id, cards in notes_map.items():
            note = self._collection_service.get_note_by_note_id(note_id)
            fields = self._extract_note_fields(note, field_names)
            kanji = self._guess_kanji(fields, kanji_field)

            card_snaps = [self._snapshot_card(c) for c in sorted(cards, key=lambda c: c.ord)]
            if any(s.type != 0 or s.queue == -1 for s in card_snaps):
                learned_count += 1

            entries.append(NoteSnapshot(kanji=kanji, fields=fields, tags=list(note.tags), cards=card_snaps))

        return entries, learned_count

    @staticmethod
    def _extract_note_fields(note: Note, field_names: list[str]) -> dict[str, str]:
        return {name: (note[name] if name in note else "") for name in field_names}

    @staticmethod
    def _guess_kanji(fields: dict[str, str], kanji_field: str) -> str:
        if kanji_field and kanji_field in fields:
            value = (fields[kanji_field] or "").strip()
            if value:
                return value
        for value in fields.values():
            value = (value or "").strip()
            if len(value) == 1:
                return value
        return ""

    @staticmethod
    def _build_note_type_snapshot(model, note_type_name: str) -> NoteTypeSnapshot:
        field_names = [f["name"] for f in model["flds"]]
        templates = [
            {"name": t.get("name") or "Card", "qfmt": t.get("qfmt") or "", "afmt": t.get("afmt") or ""}
            for t in (model.get("tmpls") or [])
        ]
        return NoteTypeSnapshot(
            name=note_type_name,
            fields=field_names,
            templates=templates,
            css=model.get("css") or "",
        )

    def _build_backup_meta(self, entries: list[NoteSnapshot], learned_count: int) -> BackupMeta:
        return BackupMeta(
            format_version=_SCHEMA_VERSION,
            created_at=datetime.now().isoformat(),
            source_deck=self._config.rtk_deck,
            source_note_type=self._config.rtk_note_type,
            field_map={
                "kanji": self._config.rtk_kanji_field or "",
                "alternative_kanji": self._config.rtk_alternative_kanji_field or "",
                "keyword": self._config.rtk_keyword_field or "",
                "meanings": self._config.rtk_meanings_field or "",
                "note": self._config.rtk_note_field or "",
                "heisig_number": self._config.rtk_heisig_number_field or "",
                "stroke_count": self._config.rtk_stroke_count_field or "",
            },
            anki_version=self._detect_anki_version(),
            entry_count=len(entries),
            learned_count=learned_count,
        )

    @staticmethod
    def _detect_anki_version() -> str:
        try:
            from anki.buildinfo import version
            return str(version)
        except Exception:
            try:
                from aqt import mw
                return str(getattr(mw, "pm", None) and getattr(mw.pm, "meta", {}) or {})
            except Exception:
                return ""

    # ----- restore_to_new_deck steps ---------------------------------------

    @staticmethod
    def _default_restore_deck_name(created_at: str) -> str:
        try:
            created = (created_at or "").replace("Z", "+00:00")
            dt = datetime.fromisoformat(created)
            stamp = dt.astimezone().strftime("%Y-%m-%d_%H%M")
        except Exception:
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        return f"Backup_{stamp}"

    def _create_note_from_snapshot(self, entry: NoteSnapshot, model) -> Note:
        note = self._collection_service.new_note(model)
        for field_name, value in entry.fields.items():
            if field_name in note:
                note[field_name] = value or ""
        for tag in entry.tags:
            if tag and tag not in note.tags:
                note.tags.append(tag)
        for tag in ("JapaneseMining::RTK", "JapaneseMining::BackupRestore"):
            if tag not in note.tags:
                note.tags.append(tag)
        return note

    def _apply_card_snapshots(self, note: Note, snapshots: list[CardSnapshot]) -> None:
        cards = note.cards()
        for snap in snapshots:
            card = self._match_card_for_snapshot(cards, snap)
            if card is not None:
                self._apply_card_snapshot(card, snap)

    @staticmethod
    def _match_card_for_snapshot(cards: list, snap: CardSnapshot):
        for card in cards:
            if card.ord == snap.ord:
                return card
        return cards[0] if cards else None

    def _ensure_note_type(self, snap: NoteTypeSnapshot):
        """Reuse the note type if name + field list match exactly, else create a new one."""
        existing = self._collection_service.get_model_by_name(snap.name)
        if existing is not None:
            existing_fields = [f["name"] for f in existing["flds"]]
            if existing_fields == list(snap.fields):
                return existing

        unique_name = f"{snap.name or 'RTK_Backup'}__restore_{uuid.uuid4().hex[:8]}"
        model = self._collection_service.add_model(unique_name)

        for field_name in snap.fields:
            field = self._collection_service.create_new_model_field(field_name)
            field["size"] = 12
            field["font"] = "Arial"
            self._collection_service.add_field_to_model(model, field)

        for template in self._build_restore_templates(snap):
            tmpl = self._collection_service.create_new_model_card_template(template["name"])
            tmpl["qfmt"] = template["qfmt"]
            tmpl["afmt"] = template["afmt"]
            self._collection_service.add_template_to_model(model, tmpl)

        if snap.css:
            model["css"] = snap.css

        self._collection_service.add_model_to_models(model)
        return model

    @staticmethod
    def _build_restore_templates(snap: NoteTypeSnapshot) -> list[dict[str, str]]:
        if snap.templates:
            return [
                {
                    "name": t.get("name") or "Card",
                    "qfmt": t.get("qfmt") or "{{Front}}",
                    "afmt": t.get("afmt") or "{{FrontSide}}<hr>{{Back}}",
                }
                for t in snap.templates
            ]

        if "Keyword" in snap.fields and "Kanji" in snap.fields:
            qfmt, afmt = "{{Keyword}}", "{{FrontSide}}<hr id=answer>{{Kanji}}"
        else:
            first = snap.fields[0] if snap.fields else "Front"
            second = snap.fields[1] if len(snap.fields) > 1 else first
            qfmt, afmt = "{{" + first + "}}", "{{FrontSide}}<hr id=answer>{{" + second + "}}"
        return [{"name": "Card 1", "qfmt": qfmt, "afmt": afmt}]

    # ----- card snapshotting -------------------------------------------------

    def _snapshot_card(self, card) -> CardSnapshot:
        try:
            stats = self._collection_service.get_card_stats_data_by_card_id(card.id)
        except Exception:
            stats = None

        stability = extract_stat(stats, ("stability", "fsrs_stability", "s")) if stats else None
        difficulty = extract_stat(stats, ("difficulty", "fsrs_difficulty", "d")) if stats else None
        retrievability = extract_stat(stats, ("retrievability", "fsrs_retrievability", "r")) if stats else None

        memory_state = getattr(card, "memory_state", None)
        if memory_state is not None:
            if stability is None:
                stability = extract_stat(memory_state, ("stability",))
            if difficulty is None:
                difficulty = extract_stat(memory_state, ("difficulty",))

        custom_data = str(card.custom_data) if getattr(card, "custom_data", None) else None
        data = str(card.data) if getattr(card, "data", None) else None
        flags = int(getattr(card, "flags", 0) or 0)

        return CardSnapshot(
            ord=int(getattr(card, "ord", 0) or 0),
            type=int(card.type),
            queue=int(card.queue),
            due=int(card.due),
            ivl=int(card.ivl),
            factor=int(card.factor),
            reps=int(card.reps),
            lapses=int(card.lapses),
            left=int(getattr(card, "left", 0) or 0),
            odue=int(getattr(card, "odue", 0) or 0),
            odid=int(getattr(card, "odid", 0) or 0),
            flags=flags,
            stability=stability,
            difficulty=difficulty,
            retrievability=retrievability,
            custom_data=custom_data,
            data=data,
        )

    def _apply_card_snapshot(self, card, snap: CardSnapshot) -> None:
        """Write scheduling state back onto a card. Best-effort for FSRS and optional attributes."""
        card.type = int(snap.type)
        card.queue = int(snap.queue)
        card.due = int(snap.due)
        card.ivl = int(snap.ivl)
        card.factor = int(snap.factor)
        card.reps = int(snap.reps)
        card.lapses = int(snap.lapses)
        if hasattr(card, "left"):
            card.left = int(snap.left)
        if hasattr(card, "odue"):
            card.odue = int(snap.odue)
        if hasattr(card, "odid"):
            card.odid = int(snap.odid)
        if hasattr(card, "flags"):
            card.flags = int(snap.flags or 0)

        if snap.stability is not None or snap.difficulty is not None:
            self._apply_fsrs_memory_state(card, snap)

        if snap.custom_data is not None and hasattr(card, "custom_data"):
            card.custom_data = snap.custom_data
        if snap.data is not None and hasattr(card, "data"):
            card.data = snap.data

        try:
            self._collection_service.update_card(card)
        except Exception:
            try:
                card.flush()
            except Exception:
                pass

    @staticmethod
    def _apply_fsrs_memory_state(card, snap: CardSnapshot) -> None:
        try:
            from anki.cards import FSRSMemoryState
            stability = float(snap.stability) if snap.stability is not None else 0.0
            difficulty = float(snap.difficulty) if snap.difficulty is not None else 0.0
            card.memory_state = FSRSMemoryState(stability=stability, difficulty=difficulty)
        except Exception:
            pass

    # ----- serialisation --------------------------------------------------

    def _write_document(self, path: Path, doc: BackupDocument) -> None:
        payload = {
            "meta": asdict(doc.meta),
            "note_type": asdict(doc.note_type),
            "entries": [
                {
                    "kanji": e.kanji,
                    "fields": e.fields,
                    "tags": e.tags,
                    "cards": [asdict(c) for c in e.cards],
                }
                for e in doc.entries
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _read_document(self, path: Path) -> BackupDocument:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise JapaneseMiningError("Backup file is corrupt (not a JSON object).")

        meta_raw = raw.get("meta") or {}
        nt_raw = raw.get("note_type") or {}
        entries_raw = raw.get("entries") or []

        meta = BackupMeta(
            format_version=int(meta_raw.get("format_version") or 0),
            created_at=str(meta_raw.get("created_at") or ""),
            source_deck=str(meta_raw.get("source_deck") or ""),
            source_note_type=str(meta_raw.get("source_note_type") or ""),
            field_map=dict(meta_raw.get("field_map") or {}),
            anki_version=str(meta_raw.get("anki_version") or ""),
            entry_count=int(meta_raw.get("entry_count") or 0),
            learned_count=int(meta_raw.get("learned_count") or 0),
        )
        note_type = NoteTypeSnapshot(
            name=str(nt_raw.get("name") or ""),
            fields=list(nt_raw.get("fields") or []),
            templates=list(nt_raw.get("templates") or []),
            css=str(nt_raw.get("css") or ""),
        )
        entries: list[NoteSnapshot] = []
        for e in entries_raw:
            cards = [
                CardSnapshot(**{k: c.get(k) for k in CardSnapshot.__dataclass_fields__})
                for c in (e.get("cards") or [])
            ]
            entries.append(
                NoteSnapshot(
                    kanji=str(e.get("kanji") or ""),
                    fields=dict(e.get("fields") or {}),
                    tags=list(e.get("tags") or []),
                    cards=cards,
                )
            )
        return BackupDocument(meta=meta, note_type=note_type, entries=entries)

    def _read_meta_only(self, path: Path) -> dict | None:
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            return raw.get("meta") if isinstance(raw, dict) else None
        except Exception:
            return None

    def _prune_old_backups(self) -> None:
        files = sorted(
            self.backups_dir().glob(f"{_BACKUP_PREFIX}*{_BACKUP_SUFFIX}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for p in files[_MAX_BACKUPS:]:
            try:
                p.unlink()
            except OSError:
                pass
