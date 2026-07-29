from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

show_tooltip = True

learned_kanji_file = "learned_kanji.csv"
learned_kanji_file_path = None
learned_kanji = {}

todays_words_file = "todays_words.csv"
todays_words_file_path = None

kanji_dictionary_file = "kanji_dictionary.xml"
kanji_dictionary_file_path = None
kanji_dictionary = {}

vendor_folder_name = "vendor"
vendor_path = Path(__file__).resolve().parent / vendor_folder_name
if str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))

current_day = None
seen_words = set()

note_type = "JapaneseMining"
rtk_deck = "日本語::RTK"

deepl_api_key = ""
deepl_url = "https://api-free.deepl.com/v2/translate"

addon_config = {}

executor = ThreadPoolExecutor(max_workers=3)
collection_future = None
kanji_future = None

focused_field_index = None

shortcut = "Ctrl+T"

current_editor = None

hypertts = None

use_hypertts = True