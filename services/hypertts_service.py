import aqt
from aqt.editor import Editor
from anki.notes import Note

from .audio_service import AudioService
from ..config import ConfigHolder, is_valid_mining_note_type


class HyperTTSService(AudioService):
    def __init__(self, config_holder: ConfigHolder):
        super().__init__(config_holder)
        self._hypertts_instance = None

    def add_audio_to_note(self, problem: str | None, note: Note, editor: Editor = None) -> None:
        """
        Add audio to the note using HyperTTS.
        Returns None when the feature is simply not applicable (disabled in config, no editor, etc.).
        Returns also None when HyperTTS fails, in order to not interrupt the user with errors from HyperTTS.
        """
        if not self._config.use_hypertts:
            return None
        if problem is not None or note is None:
            return None
        if not is_valid_mining_note_type(note.note_type()["name"], self._config):
            return None
        if editor is None or getattr(editor, "web", None) is None:
            return None

        instance = self._get_hypertts_instance()
        if instance is None:
            return None

        try:
            editor_context = instance.get_editor_context(editor)
            instance.apply_all_mapping_rules(editor_context)
        except Exception as e:
            return None

    def _get_hypertts_instance(self):
        """
        This method checks the Anki sound players for an instance of HyperTTS.
        Return the running HyperTTS instance, or None if not available.
        """
        if self._hypertts_instance is not None:
            return self._hypertts_instance

        try:
            for player in aqt.sound.av_player.players:
                # HyperTTS registers AnkiHyperTTSPlayer with a .hypertts attribute
                hypertts = getattr(player, "hypertts", None)
                if hypertts is not None:
                    self._instance = hypertts
                    return self._instance
        except Exception as e:
            pass

        return None
