from ..AJC.runtime.bootstrap import initialize_ajc
from ..AJC.runtime.config_holder import set_config_resolver, set_runtime_config
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
        merged = default_jisho_profile()
        merged.update({k: profile[k] for k in default_jisho_profile() if k in profile})
        return merged

    def has_profile_for(self, note_type_name: str) -> bool:
        """True if a Jisho profile exists for this note type."""
        if not note_type_name:
            return False
        return note_type_name in (self._config.jisho_profiles or {})

    # ------------------------------------------------------------------
    # Design B: AJC load_config() resolves through this callback
    # ------------------------------------------------------------------

    def resolve_runtime_config(self, note=None) -> dict:
        """
        Build the flat AJC runtime dict for the given note (or best fallback).

        Called by AJC's load_config() on every lookup / quick-fill / header
        refresh so the active note type's profile is used without restart.
        """
        note_type_name = None
        profile = None

        if note is not None:
            try:
                note_type_name = note.note_type()["name"]
            except Exception:
                note_type_name = None
            if note_type_name:
                profile = self.resolve_profile(note)

        return to_ajc_runtime_config(
            self._config,
            profile=profile,
            note_type_name=note_type_name,
        )

    def refresh_fallback_runtime(self) -> dict:
        """
        Push a fallback snapshot into AJC's _RUNTIME_CONFIG.

        Used on Settings save and initialize so code paths that cannot see
        an editor note still get a sensible flat config (active / first profile).
        """
        runtime = to_ajc_runtime_config(self._config)
        set_runtime_config(runtime)
        return runtime

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def initialize(self):
        """Wire the resolver into AJC and register hooks (once)."""
        if not self._config.use_jisho:
            return

        # Design B: every AJC load_config() goes through our resolver.
        set_config_resolver(self.resolve_runtime_config)

        # Fallback snapshot for contexts without a current note.
        runtime = self.refresh_fallback_runtime()
        initialize_ajc(runtime)
