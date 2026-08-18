from ..AJC.runtime.bootstrap import initialize_ajc
from ..AJC.runtime.config_holder import set_runtime_config
from ..config import ConfigHolder, default_jisho_profile
from ..jisho_adapter import to_ajc_runtime_config


class JishoService:
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    # ------------------------------------------------------------------
    # Profile resolution
    # ------------------------------------------------------------------

    def resolve_profile(self, note) -> dict | None:
        """
        Return the Jisho profile for this note's note type, or None
        if the feature does not apply (disabled, no note, no matching profile).

        Runtime always resolves from the live note type. The active profile
        in Settings is only for editing and is irrelevant here.
        """
        if not self._config.use_jisho:
            return None
        if note is None:
            return None
        try:
            name = note.note_type()["name"]
        except Exception:
            return None
        profiles = self._config.jisho_profiles or {}
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            return None
        # Ensure required keys exist even if the stored profile is partial
        merged = default_jisho_profile()
        merged.update({k: profile[k] for k in default_jisho_profile() if k in profile})
        return merged

    def has_profile_for(self, note_type_name: str) -> bool:
        """True if a Jisho profile exists for this note type."""
        if not note_type_name:
            return False
        return note_type_name in (self._config.jisho_profiles or {})

    # ------------------------------------------------------------------
    # Bootstrap (AJC still consumes a flat runtime config today)
    # ------------------------------------------------------------------

    def initialize(self):
        """Initialize the JishoService, ensuring that the AJC runtime is set up."""
        if not self._config.use_jisho:
            return

        runtime = to_ajc_runtime_config(self._config)
        set_runtime_config(runtime)
        initialize_ajc(runtime)
