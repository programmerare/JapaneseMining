from urllib import response

from aqt.editor import Editor
import requests

from ..config import ConfigHolder
from ..domain.errors import JapaneseMiningError


class DeeplService:
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    def translate(self, editor: Editor) -> str | None:
        """
        Translate the Example Sentence field using DeepL and write the result
        into the Translation field.

        Returns the translated text on success, or None when the feature is
        simply not applicable (disabled in config, no editor, no text to translate etc.).

        Raises JapaneseMiningError for problems the user should fix
        (missing api key, HTTP / API failures).
        """
        if not self._config.use_deepl:
            return None
        if not editor or not editor.note:
            return None

        note = editor.note

        if note.note_type()["name"] != self._config.mining_note_type:
            raise JapaneseMiningError(
                f"This note is not a “{self._config.mining_note_type}” note.",
                details="DeepL translation only runs on the configured JapaneseMining note type.\n"
                "Change the note type or disable DeepL in the add-on settings.",
            )

        text = (note["Example Sentence"] or "").strip()

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
            "text": [f"{text}"],
            "target_lang": self._config.deepl_target_lang,
            "source_lang": "JA",
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
        translation = data.get("translations", [])
        if not translation:
            raise JapaneseMiningError("DeepL returned no translation.")

        translation = translation[0]["text"]
        note["Translation"] = translation
        editor.loadNote()
        return translation

    def get_character_usage(self) -> tuple[int, int] | None:
        """
        Returns the character count and limit for the DeepL API key, or None
        if the feature is disabled in config or any error occurs.
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
        except requests.RequestException as e:
            return None

        data = response.json()
        character_count = data.get("character_count")
        character_limit = data.get("character_limit")

        if character_count is None or character_limit is None:
            return None

        return character_count, character_limit

    def get_target_languages(self) -> list[tuple[str, str]]:
        """
        Return [(code, display_name), ...] for languages usable as DeepL targets.

        Uses v3 /languages. Returns [] on missing key, network, or parse failure
        so the settings UI can keep its fallback list.
        """
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

        result: list[tuple[str, str]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if not item.get("usable_as_target"):
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
