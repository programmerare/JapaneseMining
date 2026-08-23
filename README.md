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

- Anki 2.1.50+ (recommended: recent 23.x / 24.x)
- Internet for Jisho and DeepL (and HyperTTS if used)
- A DeepL API key if you want automatic translation (free tier works)

Optional but recommended:

- A Remembering the Kanji (Heisig) deck for kanji tracking
- HyperTTS if you want automatic audio

---

## Quick Start

1. Install the add-on and restart Anki.
2. **Tools → JapaneseMining → Settings → General**  
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

All settings live under **Tools → JapaneseMining → Settings**.

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

## Menu actions (Tools → JapaneseMining)

- Show Today’s Words
- Settings
- Soft / Force Update (keywords, meanings, everything)
- Add Unknown Kanji
- Export Learned Kanji
- Show Kanji (heatmap + difficult kanji)

---

## Privacy & data

- DeepL and Jisho calls go over the network (your API key for DeepL).
- Learned-kanji cache and today’s-words file live in the media folder / profile data.
- No analytics, no telemetry, no “buy me a coffee” prompts.

---

## Known limitations / first release

This is the first public version. Expect rough edges.

- Advertising and discovery for Anki add-ons is hard; feedback will probably be scarce at the beginning.
- Some edge cases around note-type changes, suspended cards, and multi-profile setups may still surface.
- HyperTTS and certain Jisho fill modes benefit from a bit of manual tuning per note type.

Please open an issue (or message) with:

- Anki version
- Steps to reproduce
- What you expected vs what happened

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

See the section below in the repository / release notes for what each number means.

---

## License

(Add your chosen license here — MIT is common and friendly for Anki add-ons.)

---

## Credits

Built for people who actually mine sentences and use Heisig.

Special thanks to the Anki, Sudachi, Jisho, DeepL, and HyperTTS ecosystems.
