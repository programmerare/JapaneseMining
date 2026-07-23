import csv
import os
from datetime import date

import requests
from aqt import mw
from aqt.editor import Editor
from aqt.utils import tooltip
from aqt.qt import QLabel
from sudachipy import tokenizer, dictionary
from . import globals, helpers


tokenizer_obj = dictionary.Dictionary().create()

def export_learned_kanji():
    """Save all RTK Kanji, keywords, and learned status in a csv file."""
    col = mw.col
    deck_name = globals.rtk_deck

    all_card_ids = col.find_cards(f'deck:"{deck_name}"')
    learned_card_ids = set(col.find_cards(f'deck:"{deck_name}" -is:new'))

    kanji_list = []
    count_unknown_kanji = 0
    count_learned_kanji = 0
    count_learned_alternative_kanji = 0

    for cid in all_card_ids:
        card = col.get_card(cid)
        note = card.note()
        is_learned = cid in learned_card_ids

        if "Kanji" in note:
            kanji = note["Kanji"].strip()
            if kanji:
                kanji_list.append((kanji, is_learned))
                if is_learned:
                    count_learned_kanji += 1
                else:
                    count_unknown_kanji += 1

        if "Alternative Kanji" in note:
            kanji = note["Alternative Kanji"].strip()
            if kanji:
                kanji_list.append((kanji, is_learned))
                if is_learned:
                    count_learned_alternative_kanji += 1
                else:
                    count_unknown_kanji += 1

    kanji_rows = {}
    for kanji, is_learned in kanji_list:
        kanji_rows[kanji] = kanji_rows.get(kanji, False) or is_learned

    learned_kanji_rows = []
    learned_kanji_cache = {}

    for kanji in sorted(kanji_rows, key=lambda item: (not kanji_rows[item], item)):
        keyword = helpers.fetch_kanji_keyword(kanji)
        learned = kanji_rows[kanji]
        learned_kanji_rows.append({"Kanji": kanji, "Keyword": keyword, "Learned": "1" if learned else ""})
        learned_kanji_cache[kanji] = {"Keyword": keyword, "Learned": learned}

    globals.learned_kanji = learned_kanji_cache

    file_path = globals.learned_kanji_file_path or os.path.join(mw.col.media.dir(), globals.learned_kanji_file)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Kanji", "Keyword", "Learned"])
        writer.writeheader()
        writer.writerows(learned_kanji_rows)

    if globals.show_tooltip:
        tooltip(f"Exported {count_learned_kanji} kanji, {count_learned_alternative_kanji} alternative kanji and {count_unknown_kanji} unknown kanji.")
    return len(kanji_rows)


def _update_note_kanji_knowledge(note, learned_kanji, force_update_meanings=False, force_update_keywords=False):
    """Update kanji knowledge fields for one note."""
    should_update = False
    all_known = True
    no_kanji = True

    keywords = []
    meanings = []
    keywords_present = bool(note["Kanji Keywords"])
    meanings_present = bool(note["Kanji Meanings"])

    for ch in note["Word"]:
        if not helpers.is_kanji(ch):
            continue

        no_kanji = False
        kanji_entry = learned_kanji.get(ch)
        if not kanji_entry or not kanji_entry.get("Learned"):
            all_known = False

        if not keywords_present or force_update_keywords:
            kanji_keyword = kanji_entry.get("Keyword", "") if kanji_entry else ""
            if kanji_keyword and kanji_keyword not in keywords:
                keywords.append(kanji_keyword)

        if not meanings_present or force_update_meanings:
            tmp = helpers.fetch_kanji_meanings(ch)
            tmp = " · ".join(tmp)
            tmp = ch + ": " + tmp
            if tmp not in meanings:
                meanings.append(tmp)

    if no_kanji and note["No Kanji"] != "1":
        note["No Kanji"] = "1"
        note["Usually Kana"] = "1"
        should_update = True

    previous_value = note["Kanji is known"]
    new_value = "1" if all_known else ""
    newly_known = 0

    if previous_value != new_value:
        if previous_value != "1" and new_value == "1":
            newly_known = 1
        note["Kanji is known"] = new_value
        should_update = True

    if keywords:
        note["Kanji Keywords"] = " · ".join(keywords)
        should_update = True

    if meanings:
        note["Kanji Meanings"] = " | ".join(meanings)
        should_update = True

    tags = note["Tags"]
    if note["Usually Kana"] != "1" and "Usually written using kana alone" in tags:
        note["Usually Kana"] = "1"
        should_update = True

    if should_update:
        mw.col.update_note(note)

    return newly_known, int(should_update)


def update_kanji_knowledge(note=None, force_update_meanings=False, force_update_keywords=False):
    """Update JapaneseMining cards in a single pass over each word."""
    helpers.ensure_collection_loaded()

    try:
        learned_kanji = globals.learned_kanji
        if note is not None:
            notes = [note]
        else:
            notes = (mw.col.get_note(note_id) for note_id in mw.col.find_notes(f"note:{globals.note_type}"))

        newly_known_count = 0
        updated_count = 0

        for current_note in notes:
            note_newly_known, note_updated = _update_note_kanji_knowledge(
                current_note,
                learned_kanji,
                force_update_meanings=force_update_meanings,
                force_update_keywords=force_update_keywords,
            )
            newly_known_count += note_newly_known
            updated_count += note_updated

        if note is None and globals.show_tooltip:
            tooltip(
                f"Rechecked kanji knowledge. {newly_known_count} card(s) became known. "
                f"Updated kanji details for {updated_count} card(s)."
            )

        return newly_known_count, updated_count

    except FileNotFoundError:
        tooltip("Rechecking kanji knowledge failed. learned_kanji.csv not found.")
        return -1, 0


def add_unknown_kanji():
    """Add missing Kanji to the RTK deck"""
    unknown_kanji = helpers.find_unknown_kanji()
    deck_id = mw.col.decks.id("日本語::RTK")

    heisig_kanjis_path = os.path.join(mw.col.media.dir(), "heisig-kanjis.csv")
    with open(heisig_kanjis_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        kanji_rows = {row["kanji"]: row for row in reader}

    for kanji in unknown_kanji:
        note = helpers.create_rtk_note(kanji=kanji, tags=["Self-Added"], heisig_kanjis=kanji_rows)
        if note:
            mw.col.add_note(note, deck_id)

    if globals.show_tooltip:
        tooltip(f"Added {len(unknown_kanji)} unknown kanji to the RTK deck.")

    return len(unknown_kanji)


def update_single_note_kanji_knowledge(note, force_update_meanings=False, force_update_keywords=False):
    """Update kanji fields for a single note added from the editor."""
    if note is None or note.note_type()["name"] != globals.note_type:
        return 0, 0

    newly_known_count, updated_count = update_kanji_knowledge(
        note=note,
        force_update_meanings=force_update_meanings,
        force_update_keywords=force_update_keywords,
    )
    return newly_known_count, updated_count


def update_japanese_mining_cards(force_update_meanings=False, force_update_keywords=False):
    """Update all JapaneseMining cards in a single pass over each word."""
    globals.show_tooltip = False
    number_kanji = export_learned_kanji()
    newly_known_count, number_updated_cards = update_kanji_knowledge(
        force_update_meanings=force_update_meanings,
        force_update_keywords=force_update_keywords,
    )
    number_unknown_kanji = add_unknown_kanji()
    globals.show_tooltip = True

    if globals.show_tooltip:
        tooltip(
            f"Exported {number_kanji} kanji. {newly_known_count} card(s) became known. "
            f"{number_updated_cards} card(s) were updated. {number_unknown_kanji} unknown kanji were added."
        )


def force_update_keywords():
    update_japanese_mining_cards(force_update_keywords=True)


def force_update_meanings():
    update_japanese_mining_cards(force_update_meanings=True)


def force_update_everything():
    update_japanese_mining_cards(force_update_meanings=True, force_update_keywords=True)


def overwrite_file():
    """Overwrite the todays_words.csv file with a new header."""
    file_path = globals.todays_words_file_path or os.path.join(mw.col.media.dir(), globals.todays_words_file)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Word", "Reading", "Meaning"])


def save_word(word, reading, meaning):
    """Save a word to the todays_words.csv file."""
    helpers.ensure_collection_loaded()

    today = str(date.today())

    if globals.current_day != today:
        globals.current_day = today
        overwrite_file()

    append_word(word, reading, meaning)


def append_word(word, reading, meaning):
    """Append a word to the todays_words.csv file if it hasn't been seen today."""
    key = (word, reading)

    if key in globals.seen_words:
        return
    globals.seen_words.add(key)

    file_path = globals.todays_words_file_path or os.path.join(mw.col.media.dir(), globals.todays_words_file)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            date.today(),
            word,
            reading,
            meaning,
        ])


def words_learned_today():
    """Return a list of words learned today from the todays_words.csv file."""
    helpers.ensure_collection_loaded()

    today = str(date.today())
    result = []

    file_path = globals.todays_words_file_path or os.path.join(mw.col.media.dir(), globals.todays_words_file)
    with open(file_path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if row[0] == today:
                result.append(row)

    return result


def load_today_words():
    """Load words learned today from the CSV file."""
    helpers.ensure_collection_loaded()

    today = str(date.today())
    words = []

    file_path = globals.todays_words_file_path or os.path.join(mw.col.media.dir(), globals.todays_words_file)
    with open(file_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[0] == today:
                words.append((row[1], row[2], row[3]))

    return words


def translate(editor: Editor) -> None:
    """Translate the Example Sentence field of a note using DeepL API."""
    if not editor:
        return

    note = editor.note
    text = note["Example Sentence"]

    if not text:
        print("No text to translate.")
        return

    headers = {
        "Authorization": f"DeepL-Auth-Key {globals.deepl_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": [f"{text}"],
        "target_lang": "EN-US",
        "source_lang": "JA",
        "show_billed_characters": True,
        "split_sentences": "nonewlines",
        "preserve_formatting": True,
        "formality": "default",
        "model_type": "quality_optimized",
    }

    response = requests.post(globals.deepl_url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    translations = data.get("translations", [])
    if translations:
        translation = translations[0]["text"]
        note["Translation"] = translation
    else:
        print("No translation returned.")

    editor.loadNote()


def segment_sentence(note):
    """Segment the Example Sentence field of a note and display the tokens in a preview area."""
    if not note or note.note_type()["name"] != globals.note_type or not note._fmap.get("Example Sentence"):
        return

    if not hasattr(mw.app.activeWindow(), "editor"):
        return

    editor = mw.app.activeWindow().editor

    if globals.focused_field_index != str(note._fmap["Example Sentence"][0]):
        return
    
    index = note._fmap["Example Sentence"][0]
    text = note.fields[index]

    tokens = tokenizer_obj.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
    html = "".join(
        f'<span class="token" data-token="{str(token)}">{str(token)}</span>'
        for token in tokens
    )

    editor.web.eval(f"""
    var field = document.querySelector('[data-index="{index}"]');
    if (field) {{
        let preview = field.parentElement.querySelector(".my-preview");
        if (!preview) {{
            preview = document.createElement("div");
            preview.className = "my-preview";
            field.parentElement.insertBefore(preview, field);
        }}
        if ({html!r}) {{
            preview.innerHTML = {html!r};
            preview.style.display = "flex";
        }}
        else {{
            preview.innerHTML = "";
            preview.style.display = "none";
        }}
    }}
    """)

    # Make the tokens clickable to replace the field content with the clicked token
    editor.web.eval(f"""
    var word_field = [...document.querySelectorAll('div.rich-text-editable')]
        .map(host => host.shadowRoot?.querySelector('anki-editable[field="Word"]'))
        .find(Boolean);
    var tokens = document.querySelectorAll('.token');
    tokens.forEach(token => {{
        token.addEventListener('click', () => {{
            text = token.getAttribute('data-token');
            word_field.innerText = text;
        }});
    }});
    """)