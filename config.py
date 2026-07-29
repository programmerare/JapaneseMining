from dataclasses import dataclass


@dataclass
class Config:
    # --- GENERAL ---
    show_tooltip: bool = True
    note_type: str = "JapaneseMining"
    kanji_deck: str = ""

    # --- TRANSLATE ---
    use_deepL: bool = False
    deepl_api_key: str = ""
    deepl_url: str = "https://api-free.deepl.com/v2/translate"
    translate_shortcut: str = "Ctrl+T"

    # --- JISHO ---
    use_jisho: bool = True
    jisho_shortcut: str = "Ctrl+J"
    jisho_fastfill_shortcut: str = "Ctrl+Shift+J"

    # --- HYPERTTS ---
    use_hypertts: bool = False
