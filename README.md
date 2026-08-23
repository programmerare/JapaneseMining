# JapaneseMining

Anki add-on for Japanese sentence mining.

Mine words from real sentences, keep track of which kanji you already know (via Remembering the Kanji / Heisig), fill dictionary data from Jisho, translate example sentences with DeepL, and optionally generate audio with HyperTTS — all from inside Anki.

---

## Features

- **Sentence mining workflow**
  - Type or paste a Japanese example sentence.
  - Token chips appear above the field (Sudachi). Click a token → it goes into the Word field.
  - One-click DeepL translation into the Translation field.
  - Jisho lookup / quick-fill for reading, meaning, POS, tags, etc.

- **Kanji knowledge tracking (RTK / Heisig)**
  - Works with a Remembering the Kanji deck.
  - Automatically marks whether every kanji in a mined word is already known.
  - Fills Kanji Keywords and Kanji Meanings.
  - “Add Unknown Kanji” and export of learned kanji.
  - Heatmap + difficult-kanji views.

- **Profiles by note type**
  - Jisho and Translate settings are keyed by note type.
  - You can use different field mappings for different mining note types.

- **Backup**
  - Snapshot of the live RTK deck.
  - Restore creates a new deck (safe).

- **HyperTTS integration** (optional)
  - Configure once; use from the mining workflow.

- **Help inside the add-on**
  - Quick Start + detailed pages for every major feature.

---

## Requirements

- **Anki**: Tested on **25.09.4**. Should work on recent Anki versions (25.x / 26.x). Older versions are untested.
- Internet connection for Jisho, DeepL, and HyperTTS (if used).
- A DeepL API key if you want automatic translation (the free tier works).

Optional but recommended:

- A Remembering the Kanji (Heisig) deck for kanji tracking
- HyperTTS if you want automatic audio

---

## Quick Start

1. Install the add-on and restart Anki.
2. **JapaneseMining → Settings → General**  
   Create the JapaneseMining note type (keep the default field names).
3. **Settings → RTK**  
   - New to RTK → create the deck + note type.  
   - Already have an RTK deck → map it in Deck Mapping, then run **Export Learned Kanji**.
4. (Optional) **Settings → Jisho** and **Settings → Translate**  
   Enable and map fields for your note type. Save.
5. Open the Add window, choose the mining note type, and start mining:
   - Write an example sentence → tokens appear → click a token into Word.
   - Translate, look up on Jisho, add the card.
   - Kanji knowledge is updated automatically.

Full walkthrough lives in **Settings → Help → Quick Start**.

---

## Configuration

All settings live under **JapaneseMining → Settings**.

| Tab        | Purpose                                              |
|------------|------------------------------------------------------|
| General    | Note type, field completeness, basic options         |
| RTK        | Deck mapping, import, learned-kanji cache            |
| Jisho      | Per-note-type profiles and field mappings            |
| Translate  | DeepL key/URL + per-note-type source/target fields   |
| HyperTTS   | Optional automatic audio                             |
| Backup     | Snapshot / restore of the RTK deck                   |
| Help       | Documentation inside Anki                            |

Config is stored per Anki profile. The add-on is careful about surviving note-type renames where possible.

---

## Menu actions (JapaneseMining)

- Show Today’s Progress
- Show Kanji (heatmap + difficult kanji)
- Settings
- Soft / Force Update (keywords, meanings, everything)

---

## Privacy & data

- DeepL and Jisho calls go over the network (your API key for DeepL).
- Learned-kanji cache and today’s-progress files live within the add-on.
- No analytics, no telemetry, no “buy me a coffee” prompts.

---

## Known limitations / first release

This is the first public version. Expect rough edges.

- Some edge cases around note-type changes, suspended cards, and multi-profile setups may still surface.
- HyperTTS and certain Jisho fill modes benefit from a bit of manual tuning per note type.

**Always back up your Anki collection** before installing or updating any add-on.

---

## Bug reports & contact

Found a bug or have feedback? Please get in touch.

When reporting a problem, include:

- Anki version (Help → About)
- JapaneseMining version
- Steps to reproduce
- What you expected vs what actually happened
- Any error message or screenshot if available

**Contact options**:

- GitHub Issues: `https://github.com/programmerare/JapaneseMining/issues`
- AnkiWeb support URL (set when you upload the add-on)

I read every report. Even short ones help.

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

- **MAJOR** – breaking changes  
- **MINOR** – new features (backward-compatible)  
- **PATCH** – bug fixes only  

First public release is **1.0.0**.

---

## Credits

Built for people who actually mine sentences and use Heisig.

Special thanks to the Anki, Sudachi, Jisho, DeepL, and HyperTTS ecosystems.
