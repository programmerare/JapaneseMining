"""
Backup / restore of the RTK deck.

Design principles
-----------------
- The live RTK deck remains the source of truth.
- A backup is a *precise* snapshot taken directly from that deck
  (never from the learned_kanji cache).
- Restore always creates a *new* deck so the operation is non-destructive.
- If the original note type is missing or its fields diverge, we create a
  fresh note type with a unique name and the exact field list from the
  snapshot. Field *values* are always restored from the backup.
- The lean learned_kanji cache (kanji / keyword / learned / knowledge) is
  intentionally left alone. It continues to be rebuilt by
  CollectionService.export_learned_kanji().

Storage
-------
  <addon>/user_files/profiles/<profile_id>/backups/
    rtk_backup_YYYYMMDD_HHMMSS.json

Format version 1 is a single JSON document (see _SCHEMA_VERSION).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aqt import mw
from anki.notes import Note

from ..config import ConfigHolder, profile_user_dir
from ..domain.errors import JapaneseMiningError
from ..domain.results import UpdateResult


_SCHEMA_VERSION = 1
_MAX_BACKUPS = 50
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
    # FSRS (best-effort; may be None on older Anki / non-FSRS decks)
    stability: float | None = None
    difficulty: float | None = None
    retrievability: float | None = None
    # Opaque blobs Anki may store (preserve round-trip when present)
    custom_data: str | None = None
    data: str | None = None


@dataclass
class NoteSnapshot:
    kanji: str
    fields: dict[str, str]          # field_name -> value (exact)
    tags: list[str] = field(default_factory=list)
    cards: list[CardSnapshot] = field(default_factory=list)


@dataclass
class NoteTypeSnapshot:
    name: str
    fields: list[str]               # ordered field names
    # Templates / CSS are optional; restore can fall back to a minimal card
    templates: list[dict[str, str]] = field(default_factory=list)
    css: str = ""


@dataclass
class BackupMeta:
    format_version: int
    created_at: str                 # ISO-8601 UTC
    source_deck: str
    source_note_type: str
    field_map: dict[str, str]       # config field roles at backup time
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

    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder
        # Local calendar date (YYYY-MM-DD) of the last successful daily backup
        # check in this process. Lets overnight Anki sessions get a new backup
        # without relying on collection_did_load alone.
        self._last_daily_backup_date: str | None = None

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
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return self.backups_dir() / f"{_BACKUP_PREFIX}{stamp}{_BACKUP_SUFFIX}"

    # ----- public API -----------------------------------------------------

    def list_backups(self, limit: int = _MAX_BACKUPS) -> list[dict[str, Any]]:
        """
        Return newest-first metadata for existing backups.

        Each item:
          path, filename, created_at, source_deck, entry_count,
          learned_count, size_bytes
        """
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
        if not self._rtk_configured():
            raise JapaneseMiningError(
                "RTK deck is not configured. Please check your settings.",
                details="Open Settings → RTK and set the deck + fields before creating a backup.",
            )

        col = mw.col
        if not col:
            raise JapaneseMiningError("No collection open.")

        deck = self._config.rtk_deck
        note_type_name = self._config.rtk_note_type
        model = col.models.by_name(note_type_name)
        if model is None:
            raise JapaneseMiningError(
                f"RTK note type “{note_type_name}” not found.",
                details="Open Settings → RTK → Deck Mapping and fix the note type.",
            )

        card_ids = col.find_cards(f'deck:"{deck}"')
        if not card_ids:
            raise JapaneseMiningError(
                f"Deck “{deck}” has no cards to back up.",
            )

        # Group cards by note
        notes_map: dict[int, list] = {}
        for cid in card_ids:
            card = col.get_card(cid)
            notes_map.setdefault(card.nid, []).append(card)

        entries: list[NoteSnapshot] = []
        learned_count = 0
        kanji_field = (self._config.rtk_kanji_field or "").strip()

        for nid, cards in notes_map.items():
            note = col.get_note(nid)
            fields = {f["name"]: (note[f["name"]] if f["name"] in note else "") for f in model["flds"]}
            kanji = ""
            if kanji_field and kanji_field in fields:
                kanji = (fields[kanji_field] or "").strip()
            if not kanji:
                # Fall back to first non-empty field that looks like a single kanji
                for v in fields.values():
                    v = (v or "").strip()
                    if len(v) == 1:
                        kanji = v
                        break

            card_snaps: list[CardSnapshot] = []
            any_learned = False
            for card in sorted(cards, key=lambda c: c.ord):
                snap = self._snapshot_card(card)
                card_snaps.append(snap)
                if snap.type != 0 or snap.queue == -1:
                    any_learned = True

            if any_learned:
                learned_count += 1

            entries.append(
                NoteSnapshot(
                    kanji=kanji,
                    fields=fields,
                    tags=list(note.tags),
                    cards=card_snaps,
                )
            )

        # Note-type snapshot (fields order + templates/css for best restore)
        field_names = [f["name"] for f in model["flds"]]
        templates = []
        for t in model.get("tmpls") or []:
            templates.append(
                {
                    "name": t.get("name") or "Card",
                    "qfmt": t.get("qfmt") or "",
                    "afmt": t.get("afmt") or "",
                }
            )

        note_type_snap = NoteTypeSnapshot(
            name=note_type_name,
            fields=field_names,
            templates=templates,
            css=model.get("css") or "",
        )

        try:
            anki_ver = str(getattr(mw, "pm", None) and getattr(mw.pm, "meta", {}) or {})
            # Prefer a clean version string when available
            from anki.buildinfo import version as anki_version  # type: ignore

            anki_ver = str(anki_version)
        except Exception:
            anki_ver = ""

        meta = BackupMeta(
            format_version=_SCHEMA_VERSION,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_deck=deck,
            source_note_type=note_type_name,
            field_map={
                "kanji": self._config.rtk_kanji_field or "",
                "alternative_kanji": self._config.rtk_alternative_kanji_field or "",
                "keyword": self._config.rtk_keyword_field or "",
                "heisig_number": self._config.rtk_heisig_number_field or "",
                "stroke_count": self._config.rtk_stroke_count_field or "",
            },
            anki_version=anki_ver,
            entry_count=len(entries),
            learned_count=learned_count,
        )

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
        Recreate notes + cards from a backup into a *new* deck.

        - Creates (or reuses a compatible) note type with the exact fields
          stored in the backup.
        - Restores field values, tags, and card scheduling state as precisely
          as the Anki API allows (type/queue/due/ivl/factor/reps/lapses +
          FSRS memory_state when present).
        - Never modifies the current RTK deck or Deck Mapping. The user
          renames the deck and updates RTK settings if they want to switch.

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

        col = mw.col
        if not col:
            raise JapaneseMiningError("No collection open.")

        # ----- 1. Deck -----
        if not deck_name:
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            deck_name = f"Backup_{stamp}"
        deck_id = col.decks.id(deck_name)

        # ----- 2. Note type -----
        model = self._ensure_note_type(doc.note_type)

        # ----- 3. Create notes + apply scheduling -----
        mm = col.models
        created = 0
        for entry in doc.entries:
            note = Note(col, model)
            for fname, value in entry.fields.items():
                if fname in note:
                    note[fname] = value or ""

            # Tags
            for t in entry.tags:
                if t and t not in note.tags:
                    note.tags.append(t)
            if "JapaneseMining::RTK" not in note.tags:
                note.tags.append("JapaneseMining::RTK")
            if "JapaneseMining::BackupRestore" not in note.tags:
                note.tags.append("JapaneseMining::BackupRestore")

            col.add_note(note, deck_id)
            created += 1

            # Apply per-card scheduling
            cards = note.cards()
            for snap in entry.cards:
                # Match by ord when possible
                card = None
                for c in cards:
                    if c.ord == snap.ord:
                        card = c
                        break
                if card is None and cards:
                    card = cards[0]
                if card is None:
                    continue
                self._apply_card_snapshot(card, snap)

        col.save()

        return UpdateResult(kanji_added_to_rtk=created)

    def maybe_create_daily_backup(self) -> Path | None:
        """
        Create a backup at most once per local calendar day.

        Safe to call often (main window init, deck browser render, etc.).
        Skips when:
        - we already created/attempted a daily backup today in this process, or
        - a backup file for today already exists on disk, or
        - RTK is not configured / deck is empty.

        Returns the path if a backup was created, else None.
        """
        today_local = datetime.now().strftime("%Y-%m-%d")
        if self._last_daily_backup_date == today_local:
            return None

        # File already present for this local day (prefix uses UTC stamp —
        # also accept any file whose mtime falls on local today).
        today_utc_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        dir_ = self.backups_dir()
        for p in dir_.glob(f"{_BACKUP_PREFIX}*{_BACKUP_SUFFIX}"):
            name = p.name
            if f"{_BACKUP_PREFIX}{today_utc_prefix}" in name:
                self._last_daily_backup_date = today_local
                return None
            try:
                mtime_day = datetime.fromtimestamp(p.stat().st_mtime).strftime(
                    "%Y-%m-%d"
                )
                if mtime_day == today_local:
                    self._last_daily_backup_date = today_local
                    return None
            except OSError:
                pass

        try:
            if not self._rtk_configured():
                self._last_daily_backup_date = today_local
                return None
            path = self.create_backup()
            self._last_daily_backup_date = today_local
            return path
        except JapaneseMiningError:
            # Do not stamp the day on config errors — user may fix RTK mapping
            # and we should retry later the same day.
            return None
        except Exception:
            return None

    # ----- internals ------------------------------------------------------

    def _rtk_configured(self) -> bool:
        return bool(
            self._config.rtk_deck
            and self._config.rtk_note_type
            and self._config.rtk_kanji_field
            and self._config.rtk_keyword_field
        )

    def _snapshot_card(self, card) -> CardSnapshot:
        stability = difficulty = retrievability = None
        custom_data = data = None

        # Prefer official stats when available
        try:
            stats = mw.col.card_stats_data(card.id)
            for attr in ("stability", "fsrs_stability", "s"):
                if hasattr(stats, attr) and getattr(stats, attr) is not None:
                    stability = float(getattr(stats, attr))
                    break
            for attr in ("difficulty", "fsrs_difficulty", "d"):
                if hasattr(stats, attr) and getattr(stats, attr) is not None:
                    difficulty = float(getattr(stats, attr))
                    break
            for attr in ("retrievability", "fsrs_retrievability", "r"):
                if hasattr(stats, attr) and getattr(stats, attr) is not None:
                    retrievability = float(getattr(stats, attr))
                    break
        except Exception:
            pass

        # Fallback: memory_state
        try:
            ms = getattr(card, "memory_state", None)
            if ms is not None:
                if stability is None and getattr(ms, "stability", None) is not None:
                    stability = float(ms.stability)
                if difficulty is None and getattr(ms, "difficulty", None) is not None:
                    difficulty = float(ms.difficulty)
        except Exception:
            pass

        try:
            if getattr(card, "custom_data", None):
                custom_data = str(card.custom_data)
        except Exception:
            pass
        try:
            if getattr(card, "data", None):
                data = str(card.data)
        except Exception:
            pass

        flags = 0
        try:
            flags = int(getattr(card, "flags", 0) or 0)
        except Exception:
            flags = 0

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
        """Write scheduling state back onto a card. Best-effort for FSRS."""
        card.type = int(snap.type)
        card.queue = int(snap.queue)
        card.due = int(snap.due)
        card.ivl = int(snap.ivl)
        card.factor = int(snap.factor)
        card.reps = int(snap.reps)
        card.lapses = int(snap.lapses)
        try:
            card.left = int(snap.left)
        except Exception:
            pass
        try:
            card.odue = int(snap.odue)
            card.odid = int(snap.odid)
        except Exception:
            pass
        try:
            card.flags = int(getattr(snap, "flags", 0) or 0)
        except Exception:
            pass

        # FSRS memory_state
        if snap.stability is not None or snap.difficulty is not None:
            try:
                from anki.cards import FSRSMemoryState  # type: ignore

                st = float(snap.stability) if snap.stability is not None else 0.0
                diff = float(snap.difficulty) if snap.difficulty is not None else 0.0
                card.memory_state = FSRSMemoryState(stability=st, difficulty=diff)
            except Exception:
                # Older Anki or different binding — leave scheduler defaults
                pass

        if snap.custom_data is not None:
            try:
                card.custom_data = snap.custom_data
            except Exception:
                pass
        if snap.data is not None:
            try:
                card.data = snap.data
            except Exception:
                pass

        try:
            mw.col.update_card(card)
        except Exception:
            # Last resort: some Anki builds accept flush via card.flush()
            try:
                card.flush()
            except Exception:
                pass

    def _ensure_note_type(self, snap: NoteTypeSnapshot):
        """
        Reuse the note type if name + field list match exactly.
        Otherwise create a new note type with a unique name and the exact
        fields from the snapshot.
        """
        col = mw.col
        mm = col.models
        existing = mm.by_name(snap.name)

        if existing is not None:
            existing_fields = [f["name"] for f in existing["flds"]]
            if existing_fields == list(snap.fields):
                return existing

        # Need a new note type
        base = snap.name or "RTK_Backup"
        # Keep it readable but unique
        unique = f"{base}__restore_{uuid.uuid4().hex[:8]}"
        model = mm.new(unique)

        for fname in snap.fields:
            f = mm.new_field(fname)
            f["size"] = 12
            f["font"] = "Arial"
            mm.add_field(model, f)

        if snap.templates:
            for t in snap.templates:
                tmpl = mm.new_template(t.get("name") or "Card")
                tmpl["qfmt"] = t.get("qfmt") or "{{Front}}"
                tmpl["afmt"] = t.get("afmt") or "{{FrontSide}}<hr>{{Back}}"
                mm.add_template(model, tmpl)
        else:
            # Minimal fallback template
            tmpl = mm.new_template("Card 1")
            # Prefer Keyword → Kanji if those fields exist
            if "Keyword" in snap.fields and "Kanji" in snap.fields:
                tmpl["qfmt"] = "{{Keyword}}"
                tmpl["afmt"] = "{{FrontSide}}<hr id=answer>{{Kanji}}"
            else:
                first = snap.fields[0] if snap.fields else "Front"
                second = snap.fields[1] if len(snap.fields) > 1 else first
                tmpl["qfmt"] = "{{" + first + "}}"
                tmpl["afmt"] = "{{FrontSide}}<hr id=answer>{{" + second + "}}"
            mm.add_template(model, tmpl)

        if snap.css:
            model["css"] = snap.css

        mm.add(model)
        col.save()
        return model

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
