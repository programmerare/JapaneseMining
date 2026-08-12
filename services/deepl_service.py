from aqt.editor import Editor
import requests

from ..config import ConfigHolder

class DeeplService:
    def __init__(self, config_holder: ConfigHolder):
        self._config_holder = config_holder

    @property
    def _config(self):
        return self._config_holder.config

    def translate(self, editor: Editor) -> None:
        """Translate the Example Sentence field of a note using DeepL API."""
        if not self._config.use_deepl:
            return None
        if not editor:
            return None

        note = editor.note
        if not note:
            return None
        if note.note_type()["name"] != self._config.mining_note_type:
            print(f"Note type '{note.note_type()['name']}' does not match the configured note type '{self._config.mining_note_type}'.")
            return None

        text = note["Example Sentence"]

        if not text:
            print("No text to translate.")
            return None

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

        response = requests.post(self._config.deepl_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        translations = data.get("translations", [])
        if translations:
            translation = translations[0]["text"]
            note["Translation"] = translation
        else:
            print("No translation returned.")

        editor.loadNote()
        return None