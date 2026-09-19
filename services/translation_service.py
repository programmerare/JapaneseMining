from abc import ABC, abstractmethod

from ..config import ConfigHolder, get_default_translate_profile


class TranslationService(ABC):
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    @abstractmethod
    def translate_text(self, text: str, target_language: str) -> str:
        pass

    def resolve_translate_profile(self, note) -> dict | None:
        """
        Return the translate profile for this note's note type, or None
        if the feature does not apply (disabled, no note, no matching profile).
        """
        if not self._config.use_deepl:
            return None
        if note is None:
            return None
        try:
            name = note.note_type()["name"]
        except Exception:
            return None
        profiles = self._config.translate_profiles or {}
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            return None
        # Ensure required keys exist even if the stored profile is partial
        merged = get_default_translate_profile()
        merged.update(
            {k: profile[k] for k in get_default_translate_profile() if k in profile}
        )
        return merged

    def has_translate_profile(self, note_type_name: str) -> bool:
        """True if a translate profile exists for this note type."""
        if not note_type_name:
            return False
        return note_type_name in (self._config.translate_profiles or {})