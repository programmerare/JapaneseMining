from anki.notes import Note
import aqt
from aqt.editor import Editor

from ..config import ConfigHolder


class HyperTTSService:
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder
        self._instance = None

    @property
    def _config(self):
        return self._config_holder.config

    # --- PUBLIC METHODS --- #
    def add_audio(self, problem: str | None, note: Note, editor: Editor = None) -> None:
        """Add audio to the note using HyperTTS."""
        if not self._config.use_hypertts:
            return None
        if problem is not None or note is None:
            return None
        if note.note_type()["name"] != self._config.mining_note_type:
            return None
        if editor is None:
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

    def initialize(self):
        """
        Drop any cached HyperTTS handle.
        Call this when the Anki profile changes so the next use
        discovers the instance that belongs to the new profile.
        """
        self._instance = None

    # --- PRIVATE METHODS --- #
    def _get_instance(self):
        """Return the running HyperTTS instance, or None if not available."""
        if self._instance is None:
            for player in aqt.sound.av_player.players:
                if isinstance(player, aqt.tts.TTSProcessPlayer) and hasattr(player, "hypertts"):
                    self._instance = player.hypertts
                    break
        return self._instance