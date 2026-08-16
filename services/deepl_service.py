from aqt.editor import Editor
import requests

from ..config import ConfigHolder, default_translate_profile
from ..domain.errors import JapaneseMiningError


class DeeplService:
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
        merged = default_translate_profile()
        merged.update(
            {k: profile[k] for k in default_translate_profile() if k in profile}
        )
        return merged

    def has_profile_for(self, note_type_name: str) -> bool:
        """True if a translate profile exists for this note type."""
        if not note_type_name:
            return False
        return note_type_name in (self._config.translate_profiles or {})

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def translate(self, editor: Editor) -> str | None:
        """
        Translate the configured source field using DeepL and write the
        result into the configured target field.

        Profile is resolved from the *current note's* note type — the
        active profile in settings is irrelevant at runtime.

        Returns the translated text on success, or None when the feature
        is simply not applicable (disabled, no matching profile, empty
        source text, etc.).

        Raises JapaneseMiningError for problems the user should fix
        (missing API key, HTTP / API failures, missing fields).
        """
        if not editor or not editor.note:
            return None

        note = editor.note
        profile = self.resolve_profile(note)
        if profile is None:
            # No profile for this note type → silently skip
            return None

        source_field = (profile.get("source_field") or "").strip()
        target_field = (profile.get("target_field") or "").strip()
        source_lang = (profile.get("source_lang") or "JA").strip()
        target_lang = (profile.get("target_lang") or "EN-US").strip()

        if not source_field or not target_field:
            raise JapaneseMiningError(
                "Translate profile is incomplete.",
                details=(
                    f"Note type “{note.note_type()['name']}” is missing "
                    "source_field or target_field.\n"
                    "Open Settings → Translate and fix the profile."
                ),
            )

        if source_field not in note:
            raise JapaneseMiningError(
                f"Source field “{source_field}” does not exist on this note.",
                details=(
                    f"Note type: {note.note_type()['name']}\n"
                    "Open Settings → Translate and pick a valid source field."
                ),
            )
        if target_field not in note:
            raise JapaneseMiningError(
                f"Target field “{target_field}” does not exist on this note.",
                details=(
                    f"Note type: {note.note_type()['name']}\n"
                    "Open Settings → Translate and pick a valid target field."
                ),
            )

        text = (note[source_field] or "").strip()
        if not text:
            return None

        if not (self._config.deepl_api_key or "").strip():
            raise JapaneseMiningError(
                "DeepL API key is missing.",
                details="Open Settings → Translate and paste your DeepL API key.",
            )

        headers = {
            "Authorization": f"DeepL-Auth-Key {self._config.deepl_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": [text],
            "target_lang": target_lang,
            "source_lang": source_lang,
            "show_billed_characters": True,
            "split_sentences": "nonewlines",
            "preserve_formatting": True,
            "formality": "default",
            "model_type": "quality_optimized",
        }

        try:
            response = requests.post(
                f"{self._api_base()}/v2/translate",
                headers=headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise JapaneseMiningError(
                "DeepL translation failed.",
                details=str(e),
            ) from e

        data = response.json()
        translations = data.get("translations", [])
        if not translations:
            raise JapaneseMiningError("DeepL returned no translation.")

        translation = translations[0]["text"]
        note[target_field] = translation
        editor.loadNote()
        return translation

    # ------------------------------------------------------------------
    # Usage / languages
    # ------------------------------------------------------------------

    def get_character_usage(self) -> tuple[int, int] | None:
        """
        Returns (character_count, character_limit) or None if the feature
        is disabled or any error occurs.
        """
        if not self._config.use_deepl:
            return None
        if not (self._config.deepl_api_key or "").strip():
            return None

        headers = {
            "Authorization": f"DeepL-Auth-Key {self._config.deepl_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{self._api_base()}/v2/usage",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None

        data = response.json()
        character_count = data.get("character_count")
        character_limit = data.get("character_limit")
        if character_count is None or character_limit is None:
            return None
        return character_count, character_limit

    def get_target_languages(self) -> list[tuple[str, str]]:
        """Return [(code, display_name), ...] usable as DeepL targets."""
        return self._fetch_languages(as_source=False)

    def get_source_languages(self) -> list[tuple[str, str]]:
        """Return [(code, display_name), ...] usable as DeepL sources."""
        return self._fetch_languages(as_source=True)

    def _fetch_languages(self, *, as_source: bool) -> list[tuple[str, str]]:
        if not (self._config.deepl_api_key or "").strip():
            return []

        headers = {
            "Authorization": f"DeepL-Auth-Key {self._config.deepl_api_key}",
        }
        try:
            response = requests.get(
                f"{self._api_base()}/v3/languages?resource=translate_text",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            return []

        if not isinstance(data, list):
            return []

        key = "usable_as_source" if as_source else "usable_as_target"
        result: list[tuple[str, str]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if not item.get(key):
                continue
            code = (item.get("lang") or "").strip()
            name = (item.get("name") or code).strip()
            if not code:
                continue
            result.append((code, name))

        result.sort(key=lambda pair: pair[1].lower())
        return result

    def _api_base(self) -> str:
        url = (self._config.deepl_url or "").rstrip("/")
        for suffix in ("/v3", "/v2"):
            if url.endswith(suffix):
                url = url[: -len(suffix)]
                break
        return url or "https://api-free.deepl.com"
