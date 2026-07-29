from anki.notes import Note
import aqt
from aqt.editor import Editor

from config import Config


class HyperTTSService:
    def __init__(self, config: Config):
        self._config = config
        self._instane = None

    def _get_instance(self):
        """Return the running HyperTTS instance, or None if not available."""
        if self._instane is None:
            for player in aqt.sound.av_player.players:
                if isinstance(player, aqt.tts.TTSProcessPlayer) and hasattr(player, "hypertts"):
                    self._instane = player.hypertts
                    break
        return self._instane

    def add_audio(self, problem: str | None, note: Note, editor: Editor = None) -> None:
        """Add audio to the note using HyperTTS."""
        if not self._config.use_hypertts:
            return None
        if problem is not None or note is None:
            return None
        if note.note_type()["name"] != self._config.note_type:
            return None

        instance = self._get_instance()
        if instance is None:
            return None

        try:
            editor_context = instance.get_editor_context(editor)
            instance.apply_all_mapping_rules(editor_context)
        except Exception as e:
            print(f"HyperTTS error: {e}")
        return None