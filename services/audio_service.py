from abc import ABC, abstractmethod

from ..config import ConfigHolder

class AudioService(ABC):
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    @abstractmethod
    def add_audio_to_note(self, problem: str | None, note, editor=None) -> None:
        pass