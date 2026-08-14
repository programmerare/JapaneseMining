from anki.notes import Note
import aqt
from aqt.editor import Editor

from ..domain.errors import JapaneseMiningError
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
        """
        Add audio to the note using HyperTTS.

        Returns None when the feature is simply not applicable (disabled in config, no editor, etc.).
        Returns also None when HyperTTS fails, in order to not interrupt the user with errors from HyperTTS.

        Raises JapaneseMiningError for problems the user should fix
        (wrong note type).
        """
        if not self._config.use_hypertts:
            return None
        if problem is not None or note is None:
            return None
        if note.note_type()["name"] != self._config.mining_note_type:
            raise JapaneseMiningError(
                f"This note is not a “{self._config.mining_note_type}” note.",
                details="HyperTTS only runs on the configured JapaneseMining note type.\n"
                "Change the note type or disable HyperTTS in the add-on settings.",
            )
        if editor is None:
            return None

        instance = self._get_instance()
        if instance is None:
            return None

        try:
            editor_context = instance.get_editor_context(editor)
            instance.apply_all_mapping_rules(editor_context)
        except Exception as e:
            pass
        return None

    # --- PRIVATE METHODS --- #
    def _get_instance(self):
        """
        This method checks the Anki sound players for an instance of HyperTTS.

        Return the running HyperTTS instance, or None if not available.
        """
        if self._instance is not None:
            return self._instance

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
