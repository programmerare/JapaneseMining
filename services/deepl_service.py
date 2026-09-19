import requests
from aqt.editor import Editor

from ..config import ConfigHolder
from ..domain.errors import JapaneseMiningError
from .translation_service import TranslationService


class DeeplService(TranslationService):
    def __init__(self, config_holder: ConfigHolder):
        super().__init__(config_holder)

    def translate_text(self, editor: Editor) -> str | None:
        if not editor or not editor.note:
            return None

        note = editor.note
        profile = self._resolve_profile_or_raise(note)
        source_field, target_field, source_lang, target_lang = self._extract_profile_fields(profile, note)

        text = (note[source_field] or "").strip()
        if not text:
            return None

        translation = self._call_deepl_api(text, source_lang, target_lang, self._deepl_base_url(), self._config.deepl_api_key)

        note[target_field] = translation
        editor.loadNote()
        return translation

    def _resolve_profile_or_raise(self, note) -> dict:
        profile = self.resolve_translate_profile(note)
        if profile is None:
            raise JapaneseMiningError(
                f"No translate profile for note type “{note.note_type()['name']}”.",
                details=(
                    "Open Settings → Translate and create a profile for this note type."
                ),
            )
        return profile

    def _extract_profile_fields(self, profile: dict, note) -> tuple[str, str, str, str]:
        source_field = (profile.get("source_field") or "").strip()
        target_field = (profile.get("target_field") or "").strip()
        source_lang = (profile.get("source_lang") or "JA").strip()
        target_lang = (profile.get("target_lang") or "EN-US").strip()

        if not source_field:
            raise JapaneseMiningError(
                f"Source field “{source_field}” does not exist on this note.",
                details=(
                    f"Note type: {note.note_type()['name']}\n"
                    "Open Settings → Translate and pick a valid source field."
                ),
            )
        if not target_field:
            raise JapaneseMiningError(
                f"Target field “{target_field}” does not exist on this note.",
                details=(
                    f"Note type: {note.note_type()['name']}\n"
                    "Open Settings → Translate and pick a valid target field."
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

        return source_field, target_field, source_lang, target_lang

    def _call_deepl_api(self, text: str, source_lang: str, target_lang: str, base_url: str,  api_key: str) -> str:
        if not api_key.strip():
            raise JapaneseMiningError(
                "DeepL API key is not set.",
                details=(
                    "Open Settings → Translate and enter your DeepL API key."
                ),
            )

        if not base_url.strip():
            raise JapaneseMiningError(
                "DeepL API URL is not set.",
                details=(
                    "Open Settings → Translate and enter your DeepL API URL."
                ),
            )

        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
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
            response = requests.post(f"{base_url}/v2/translate", headers=headers, json=payload, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            raise JapaneseMiningError("DeepL translation failed.", details=str(e)) from e

        data = response.json()
        translations = data.get("translations", [])
        if not translations:
            raise JapaneseMiningError("DeepL returned no translation.")
        return translations[0]["text"]

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
                f"{self._deepl_base_url()}/v2/usage",
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
        data = self._request_languages(self._deepl_base_url(), self._config.deepl_api_key)
        return self._parse_languages(data, as_source=as_source)

    def _request_languages(self, base_url: str, api_key: str) -> list | None:
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        try:
            response = requests.get(f"{base_url}/v3/languages?resource=translate_text", headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            return None

    def _parse_languages(self, data, *, as_source: bool) -> list[tuple[str, str]]:
        if not isinstance(data, list):
            return []
        key = "usable_as_source" if as_source else "usable_as_target"
        result = []
        for item in data:
            if not isinstance(item, dict) or not item.get(key):
                continue
            code = (item.get("lang") or "").strip()
            name = (item.get("name") or code).strip()
            if code:
                result.append((code, name))
        result.sort(key=lambda pair: pair[1].lower())
        return result

    def _deepl_base_url(self) -> str:
        url = (self._config.deepl_url or "").rstrip("/")
        for suffix in ("/v3", "/v2"):
            if url.endswith(suffix):
                url = url[: -len(suffix)]
                break
        return url or ""
