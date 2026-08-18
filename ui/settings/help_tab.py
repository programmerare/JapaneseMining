"""
Help / Instructions tab for JapaneseMining.

Uses a left nav list + stacked pages instead of a crowded sub-tab bar.
Quick Start stays short. Screenshots use make_image_placeholder until assets exist.
"""

from aqt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    Qt,
)

from ..ui_styles import (
    make_section_card,
    make_instruction_label,
    make_image_placeholder,
    TEXT_BODY,
    TEXT_PRIMARY,
    ACCENT,
    BORDER,
    BG_CARD,
)


def _body_label(text: str) -> QLabel:
    """Body text; supports simple HTML (links, <b> for action names)."""
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setOpenExternalLinks(True)
    lbl.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px; line-height: 1.45;")
    return lbl


def _bullet(text: str) -> QLabel:
    lbl = QLabel(f"•  {text}")
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setOpenExternalLinks(True)
    lbl.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px; padding-left: 4px;")
    return lbl


def _subheading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY}; margin-top: 6px;"
    )
    return lbl


def _make_scrollable(content_widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    scroll.setWidget(content_widget)
    return scroll


# ── Page builders ────────────────────────────────────────────────────────

def _build_quick_start() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Get productive in a few minutes. Details live in the other Help pages."
        )
    )

    card, cl = make_section_card("1. Create the mining note type")
    cl.addWidget(
        _body_label(
            "Settings → General → <b>Create JapaneseMining note type</b>. "
            "Keep the default name unless it already exists. Do not rename or delete "
            "the fields the add-on creates."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("2. Set up RTK (Heisig)")
    cl2.addWidget(
        _body_label(
            "Settings → RTK → Setup &amp; Import. Beginners: leave “create all notes” "
            "checked and press <b>Create Deck &amp; Note Type</b>. Already know some kanji: "
            "uncheck it, press <b>Create Deck &amp; Note Type</b>, then use Import "
            "(file or Heisig number up to N)."
        )
    )
    cl2.addWidget(
        _body_label(
            "Deck Mapping is the source of truth for keywords and learned status. "
            "After any deck change, run <b>Export Learned Kanji</b> from the Tools menu."
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("3. Optional integrations")
    for item in [
        "Jisho: Settings → Jisho → enable, map fields for your note type, <b>Save</b>, restart Anki.",
        "DeepL: Settings → Translate → API key + profile (source/target fields). Shortcut defaults to Ctrl+T.",
        "HyperTTS: install the add-on, create an <b>Advanced mode</b> preset for your note type "
        "(source <b>Reading</b> → target <b>Audio</b>), then enable it in Settings → HyperTTS.",
    ]:
        cl3.addWidget(_bullet(item))
    layout.addWidget(card3)

    card4, cl4 = make_section_card("4. Recommended mining workflow")
    cl4.addWidget(
        _body_label(
            "In Add Cards, <b>pin Example Sentence</b> and <b>Translation</b> "
            "(small pushpin next to each field) so the sentence survives after you add a card."
        )
    )
    for step in [
        "Write a Japanese sentence into <b>Example Sentence</b>.",
        "Translate it (DeepL button / shortcut) into <b>Translation</b>.",
        "Token chips appear above the example sentence (Sudachi segmentation). "
        "Click a token to load it into the <b>Word</b> field.",
        "Fill remaining fields with Jisho (lookup / quick-fill).",
        "Add the card. Kanji knowledge is updated automatically.",
    ]:
        cl4.addWidget(_bullet(step))
    layout.addWidget(card4)

    layout.addWidget(make_image_placeholder("[Screenshot: Settings → General + RTK]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_overview() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label("How JapaneseMining fits into daily study.")
    )

    card, cl = make_section_card("Recommended mining workflow")
    cl.addWidget(
        _body_label(
            "Encounter → mine → understand → review. A practical sequence in the editor:"
        )
    )
    for step in [
        "Pin <b>Example Sentence</b> and <b>Translation</b> (Anki pushpin) so they stay after adding.",
        "Paste or type a Japanese sentence into <b>Example Sentence</b>.",
        "Run DeepL so <b>Translation</b> is filled.",
        "Word chips appear above the example (Sudachi). Click one to put it in <b>Word</b>.",
        "Run Jisho to fill Reading, Meaning, Part of Speech, and related fields.",
        "Optional: HyperTTS writes audio into <b>Audio</b> on add "
        "(or batch later — see HyperTTS Help).",
        "Add the card. RTK kanji status is checked automatically.",
    ]:
        cl.addWidget(_bullet(step))
    layout.addWidget(card)

    card2, cl2 = make_section_card("What the add-on manages")
    for item in [
        "JapaneseMining note type and required fields",
        "Jisho lookup + per–note-type field mapping",
        "RTK deck creation, known-kanji import, keyword lookup",
        "DeepL translation (optional)",
        "HyperTTS audio (optional)",
        "Today’s Progress (words / kanji / cards that became known)",
        "RTK deck backups (fields + scheduling)",
    ]:
        cl2.addWidget(_bullet(item))
    layout.addWidget(card2)

    layout.addWidget(make_image_placeholder("[Screenshot: Overall workflow / main editor]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_note_type() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Required fields, what each is for, and safe creation."
        )
    )

    card, cl = make_section_card("Creating the note type")
    cl.addWidget(
        _body_label(
            "Settings → General → <b>Create JapaneseMining note type</b>. "
            "You may add extra fields later. Do not delete or rename the fields "
            "the add-on expects — mapping and RTK integration will break."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Required fields (core)")
    fields = [
        ("Word", "The expression / headword"),
        ("Reading", "Furigana / kana reading"),
        ("Meaning", "Definition or English meaning"),
        ("Example Sentence", "Example from Jisho or your own"),
        ("Translation", "Translation of the example"),
        ("Part of Speech", "Noun, Ichidan verb, …"),
        ("Audio", "Generated or manual audio"),
        ("Kanji Keywords", "Heisig keywords for kanji in the word"),
        ("Kanji is known", "Flag used by RTK integration"),
    ]
    for name, desc in fields:
        row = QLabel(f"<b>{name}</b>  —  {desc}")
        row.setTextFormat(Qt.TextFormat.RichText)
        row.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px;")
        row.setWordWrap(True)
        cl2.addWidget(row)
    layout.addWidget(card2)

    layout.addWidget(
        make_image_placeholder("[Screenshot: Note type fields list in Anki]")
    )
    layout.addStretch()
    return _make_scrollable(page)


def _build_jisho() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Profiles, field mapping, and multi-meaning / multi-word formats."
        )
    )

    card, cl = make_section_card("Profiles")
    cl.addWidget(
        _body_label(
            "Each profile is keyed by an existing note type (search field, mappings, "
            "fill mode). In the editor the add-on picks the profile that matches the "
            "current note automatically — the dropdown in Settings only chooses which "
            "profile you edit. Add only lists note types that do not already have a "
            "profile. After enabling Jisho, restart Anki."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Mapping")
    cl2.addWidget(
        _body_label(
            "Map Jisho sources (Word, Reading, Meanings, …) to your note fields. "
            "Only rows with both a source and a target are saved."
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("Formats")
    cl3.addWidget(
        _body_label(
            "Multi-meaning and multi-word formats control how several senses or "
            "headwords are joined. The UI only offers compatible pairs."
        )
    )
    layout.addWidget(card3)

    layout.addWidget(make_image_placeholder("[Screenshot: Jisho mapping tab]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_rtk_help() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Heisig’s method and how this add-on supports it."
        )
    )

    card, cl = make_section_card("The keyword method")
    cl.addWidget(
        _body_label(
            "Each kanji gets a unique English keyword. You learn the character via "
            "a vivid story that links the keyword to its primitives. Goal: make the "
            "shapes memorable so vocabulary sticks later."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Primitives")
    cl2.addWidget(
        _body_label(
            "Kanji are built from simpler pieces (primitives). Once you know them, "
            "a new character is a combination of familiar parts — not random strokes."
        )
    )
    cl2.addWidget(
        make_image_placeholder(
            "[Diagram: example kanji broken into primitives]", min_height=120
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("Stories")
    cl3.addWidget(
        _body_label(
            "Short, visual, emotional. Force the primitives to interact so only "
            "that keyword fits. Bizarre or funny images stick best."
        )
    )
    layout.addWidget(card3)

    card5, cl5 = make_section_card("How JapaneseMining helps")
    for item in [
        "One-click RTK deck + note type (2200 Heisig 6th-ed kanji).",
        "Import known kanji (file or number up to N): full set exists; known subset parked.",
        "Keyword lookup when you mine a word.",
        "Today’s Progress tracks kanji that became known.",
        "Backups snapshot fields, tags, and scheduling (including FSRS when available).",
    ]:
        cl5.addWidget(_bullet(item))
    layout.addWidget(card5)

    card_tags, cl_tags = make_section_card("Tags the add-on uses")
    for tag, meaning in [
        ("JapaneseMining::RTK", "Every RTK note the add-on manages."),
        ("Heisig", "Bulk-created from the 6th-edition list."),
        ("Imported-Known", "Marked known via Import (usually suspended or far-scheduled)."),
        ("Self-Added", "Added when you mine a word with an unknown kanji."),
    ]:
        cl_tags.addWidget(_subheading(tag))
        cl_tags.addWidget(_body_label(meaning))
    layout.addWidget(card_tags)

    card_sot, cl_sot = make_section_card("Source of truth: the RTK deck")
    cl_sot.addWidget(
        _body_label(
            "The mapped RTK deck is the source of truth for which kanji are learned. "
            "Studied (not new) → learned; suspended after Import → treated as known "
            "until you review; pure new → not learned. After studying an imported card, "
            "run <b>Export Learned Kanji</b> so progress reflects real reviews."
        )
    )
    cl_sot.addWidget(
        _body_label(
            "If you switch decks and run Export, learned status is rebuilt from that deck only."
        )
    )
    layout.addWidget(card_sot)

    card6, cl6 = make_section_card("What should I click?")
    cl6.addWidget(_subheading("Beginner — no RTK deck"))
    cl6.addWidget(
        _body_label(
            "RTK → Setup &amp; Import. Keep “create all notes” checked → "
            "<b>Create Deck &amp; Note Type</b>."
        )
    )
    cl6.addWidget(_subheading("Some kanji already known — no deck yet"))
    cl6.addWidget(
        _body_label(
            "Create (optionally without all notes), then Import (file or Heisig up to N)."
        )
    )
    cl6.addWidget(_subheading("I already have an RTK deck"))
    cl6.addWidget(
        _body_label(
            "Deck Mapping: point at your deck and note type. Kanji + Keyword required. "
            "Create only adds missing notes / fills empty fields. "
            "Avoid Import if you must keep existing scheduling for those kanji."
        )
    )
    layout.addWidget(card6)

    layout.addWidget(make_image_placeholder("[Screenshot: RTK Setup & Import tab]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_translate() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label("DeepL account, URLs, and per–note-type profiles.")
    )

    card, cl = make_section_card("Account")
    cl.addWidget(
        _body_label(
            "Create or manage a DeepL account at "
            '<a href="https://www.deepl.com/en">https://www.deepl.com/en</a>. '
            "Enable DeepL in Settings → Translate, paste your API key, and set the URL."
        )
    )
    cl.addWidget(_subheading("API URLs"))
    cl.addWidget(
        _body_label(
            "• Free: <code>https://api-free.deepl.com</code><br>"
            "• Pro: <code>https://api.deepl.com</code>"
        )
    )
    cl.addWidget(
        _body_label(
            "Match the URL to your key type. The shortcut is global (default Ctrl+T)."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Profiles")
    cl2.addWidget(
        _body_label(
            "Each note type can have its own source field, target field, and languages. "
            "In the editor the add-on picks the profile that matches the current note "
            "automatically — the dropdown in Settings only chooses which profile you edit."
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("Usage")
    cl3.addWidget(
        _body_label(
            "Character count and limit appear in the Translate tab when the key is valid. "
            "Free tier has a monthly character cap."
        )
    )
    layout.addWidget(card3)

    layout.addWidget(make_image_placeholder("[Screenshot: Translate settings]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_hypertts() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Automatic audio via the HyperTTS add-on."
        )
    )

    card, cl = make_section_card("Install &amp; setup")
    cl.addWidget(
        _body_label(
            "1. Install HyperTTS from AnkiWeb: "
            '<a href="https://ankiweb.net/shared/info/111623432">'
            "https://ankiweb.net/shared/info/111623432</a>"
        )
    )
    cl.addWidget(
        _body_label(
            "2. Configure Advanced mode and presets (guide): "
            '<a href="https://www.vocab.ai/tips/hypertts-advanced-mode">'
            "https://www.vocab.ai/tips/hypertts-advanced-mode</a>"
        )
    )
    cl.addWidget(
        _body_label(
            "3. Create a preset for each note type you use with <b>Advanced mode</b> enabled. "
            "This preset is required — without it, JapaneseMining cannot generate audio."
        )
    )
    cl.addWidget(
        _body_label(
            "4. In that preset, map the source field HyperTTS reads from to "
            "<b>Reading</b>, and the target field where audio is written to <b>Audio</b>."
        )
    )
    cl.addWidget(
        _body_label(
            "5. In JapaneseMining → HyperTTS, enable the integration, then <b>Save</b>."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("On Add Card vs batch")
    cl2.addWidget(
        _body_label(
            "Generating audio when you press <b>Add</b> can take a couple of seconds "
            "and feel slow if you mine many cards in a row. If that bothers you, "
            "turn HyperTTS <b>off</b> in JapaneseMining Settings and add audio later in batch."
        )
    )
    cl2.addWidget(
        _body_label(
            "Batch guide (select notes in the browser, then run your preset from the menu): "
            '<a href="https://www.vocab.ai/tutorials/hypertts-collection-audio">'
            "https://www.vocab.ai/tutorials/hypertts-collection-audio</a>"
        )
    )
    layout.addWidget(card2)

    layout.addWidget(make_image_placeholder("[Screenshot: HyperTTS settings]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_backup_help() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "RTK backups: what they store and how restore works."
        )
    )

    card, cl = make_section_card("What a backup is")
    cl.addWidget(
        _body_label(
            "Snapshot of the mapped RTK deck: field values, tags, and per-card "
            "scheduling (type, queue, due, interval, ease, reps, lapses, flags, "
            "and FSRS state when Anki exposes it). Taken from the live deck only."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Where files live")
    cl2.addWidget(
        _body_label(
            "Stored under the add-on profile folder "
            "(user_files/profiles/&lt;profile_id&gt;/backups/). Up to 50 backups; "
            "older ones are pruned. A daily backup is attempted when the collection "
            "loads if none exists for the current UTC day."
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("Restore")
    cl3.addWidget(
        _body_label(
            "Always creates a <b>new</b> deck (Backup_YYYY-MM-DD_HHMM). Your current RTK "
            "deck and Deck Mapping are never modified. Rename the new deck and "
            "update RTK → Deck Mapping if you want to switch, then run "
            "<b>Export Learned Kanji</b>."
        )
    )
    cl3.addWidget(
        _body_label(
            "If the original note type still has the same fields, it is reused; "
            "otherwise a new note type is created with the exact backup fields."
        )
    )
    layout.addWidget(card3)

    card4, cl4 = make_section_card("Limitations")
    cl4.addWidget(
        _body_label(
            "FSRS is restored as precisely as the Anki API allows. After a major "
            "Anki upgrade, spot-check a few cards before relying on a large restore."
        )
    )
    layout.addWidget(card4)

    layout.addStretch()
    return _make_scrollable(page)


def _build_troubleshooting() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(make_instruction_label("Quick fixes for common issues."))

    card, cl = make_section_card("Jisho does nothing")
    cl.addWidget(_bullet("Enable Jisho is checked and Anki was restarted."))
    cl.addWidget(
        _bullet(
            "A Jisho profile exists for this note’s note type "
            "(Settings → Jisho → Profile)."
        )
    )
    cl.addWidget(
        _bullet("That profile’s Search field matches a field that has the word.")
    )
    cl.addWidget(_bullet("Mappings are not empty."))
    layout.addWidget(card)

    card2, cl2 = make_section_card("RTK keywords missing")
    cl2.addWidget(_bullet("Deck Mapping points at the correct deck and note type."))
    cl2.addWidget(_bullet("Kanji field and Keyword field are set."))
    cl2.addWidget(
        _bullet("Run <b>Export Learned Kanji</b> after mapping or import changes.")
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("DeepL / character limit")
    cl3.addWidget(
        _bullet(
            "API key and URL match (free: api-free.deepl.com, pro: api.deepl.com)."
        )
    )
    cl3.addWidget(_bullet("Check character usage on the Translate tab."))
    cl3.addWidget(
        _bullet("Profile has source and target fields for this note type.")
    )
    layout.addWidget(card3)

    card4, cl4 = make_section_card("HyperTTS audio missing")
    cl4.addWidget(
        _bullet("HyperTTS add-on installed and a preset exists for the note type.")
    )
    cl4.addWidget(
        _bullet(
            "Preset maps source → <b>Reading</b>, target → <b>Audio</b> (Advanced mode)."
        )
    )
    cl4.addWidget(_bullet("JapaneseMining → HyperTTS is enabled."))
    cl4.addWidget(
        _bullet(
            "If Add is slow, disable HyperTTS here and batch audio later "
            '(see <a href="https://www.vocab.ai/tutorials/hypertts-collection-audio">'
            "collection audio tutorial</a>)."
        )
    )
    layout.addWidget(card4)

    card5, cl5 = make_section_card("Backup / restore")
    cl5.addWidget(_bullet("RTK deck must be mapped before <b>Create backup now</b>."))
    cl5.addWidget(
        _bullet(
            "Restore never overwrites the live deck — remap if you want to switch."
        )
    )
    layout.addWidget(card5)

    layout.addStretch()
    return _make_scrollable(page)


# ── Public factory ───────────────────────────────────────────────────────

HELP_SECTIONS = (
    "quick_start",
    "overview",
    "note_type",
    "jisho",
    "rtk",
    "translate",
    "hypertts",
    "backup",
    "troubleshooting",
)

_NAV_STYLE = f"""
QListWidget {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QListWidget::item:selected {{
    background: #e8f0fe;
    color: {ACCENT};
    font-weight: 600;
}}
QListWidget::item:hover:!selected {{
    background: #f1f3f4;
}}
"""


def make_help_tab(config_holder=None, save_config_fn=None):
    """
    Returns (tab_widget, title, apply_to_config_fn).

    Left nav list + stacked content (no sub-tab bar).
    Exposes:
      .goto(section: str)
      .goto_rtk()
      .section_index
    """
    outer = QWidget()
    outer_layout = QHBoxLayout(outer)
    outer_layout.setContentsMargins(8, 8, 8, 8)
    outer_layout.setSpacing(10)

    nav = QListWidget()
    nav.setFixedWidth(200)
    nav.setStyleSheet(_NAV_STYLE)
    nav.setSpacing(2)
    nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    outer_layout.addWidget(nav)

    stack = QStackedWidget()
    outer_layout.addWidget(stack, 1)

    builders = [
        ("quick_start", "Quick Start", _build_quick_start),
        ("overview", "Overview", _build_overview),
        ("note_type", "Note Type", _build_note_type),
        ("jisho", "Jisho", _build_jisho),
        ("rtk", "Remembering the Kanji", _build_rtk_help),
        ("translate", "Translate", _build_translate),
        ("hypertts", "HyperTTS", _build_hypertts),
        ("backup", "Backup", _build_backup_help),
        ("troubleshooting", "Troubleshooting", _build_troubleshooting),
    ]

    section_index: dict[str, int] = {}
    for key, title, builder in builders:
        section_index[key] = stack.count()
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, key)
        nav.addItem(item)
        stack.addWidget(builder())

    def on_nav_changed(row: int) -> None:
        if row >= 0:
            stack.setCurrentIndex(row)

    nav.currentRowChanged.connect(on_nav_changed)
    nav.setCurrentRow(0)

    def goto(section: str) -> None:
        idx = section_index.get(section)
        if idx is not None:
            nav.setCurrentRow(idx)

    outer.goto = goto
    outer.goto_rtk = lambda: goto("rtk")
    outer.section_index = section_index
    outer.nav = nav
    outer.stack = stack

    def apply_to_config(_cfg):
        pass  # read-only

    return outer, "Help", apply_to_config
