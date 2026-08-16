"""
Help / Instructions tab for JapaneseMining.

Contains educational content and workflow documentation.
Sub-tabs keep scrolling manageable once screenshots are added.
"""

from aqt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QTabWidget,
    Qt,
)

from ..ui_styles import (
    make_section_card,
    make_instruction_label,
    make_separator,
    make_image_placeholder,
    SECTION_TITLE_SS,
    TEXT_SECONDARY,
    TEXT_BODY,
    TEXT_PRIMARY,
)


def _body_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px; line-height: 1.45;")
    return lbl


def _bullet(text: str) -> QLabel:
    lbl = QLabel(f"•  {text}")
    lbl.setWordWrap(True)
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


# ── Sub-tab builders ─────────────────────────────────────────────────────

def _build_overview() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "High-level picture of how JapaneseMining fits into your daily study."
        )
    )

    card, cl = make_section_card("Recommended daily workflow")
    cl.addWidget(
        _body_label(
            "JapaneseMining is designed around a simple loop: encounter → mine → "
            "understand → review. The add-on removes most of the friction between "
            "seeing a word and having a high-quality Anki card."
        )
    )
    cl.addWidget(_subheading("Typical flow"))
    for step in [
        "You encounter a word (reading, immersion, textbook, etc.).",
        "Open the JapaneseMining editor / Jisho quick-fill and look it up.",
        "The add-on fills Word, Reading, Meaning, Part of Speech, JLPT, etc.",
        "Optionally run DeepL for a natural example-sentence translation.",
        "Optionally generate audio with HyperTTS.",
        "Save the card. RTK kanji status is checked automatically.",
        "Review as usual. Cards that become “known” are tracked for today’s progress.",
    ]:
        cl.addWidget(_bullet(step))
    layout.addWidget(card)

    card2, cl2 = make_section_card("What the add-on manages for you")
    for item in [
        "JapaneseMining note type with all required fields",
        "Jisho lookup + field mapping per note type",
        "RTK (Heisig) deck creation, import of known kanji, keyword lookup",
        "DeepL translation (optional)",
        "HyperTTS audio generation (optional)",
        "Today’s Progress view (words / kanji / cards that became known)",
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
            "Everything about the JapaneseMining note type — required fields, "
            "what each field is used for, and how to create it safely."
        )
    )

    card, cl = make_section_card("Creating the note type")
    cl.addWidget(
        _body_label(
            "Go to Settings → General and click “Create JapaneseMining note type”. "
            "You can keep the default name or choose a unique name if the default "
            "is already taken. The add-on will create every field it needs."
        )
    )
    cl.addWidget(
        _body_label(
            "You may add extra fields later. Do not delete or rename the fields "
            "the add-on expects — that will break mapping and RTK integration."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Required fields (core)")
    fields = [
        ("Word", "The expression / headword"),
        ("Reading", "Furigana / kana reading"),
        ("Meaning", "English (or target-language) gloss"),
        ("Example Sentence", "Example from Jisho or your own"),
        ("Translation", "Translation of the example (DeepL or manual)"),
        ("Part of Speech", "Noun, Ichidan verb, etc."),
        ("Audio", "Generated or manual audio"),
        ("Kanji Keywords", "Heisig keywords for the kanji in the word"),
        ("Kanji is known", "Flag used by the RTK integration"),
    ]
    for name, desc in fields:
        row = QLabel(f"<b>{name}</b>  —  {desc}")
        row.setStyleSheet(f"color: {TEXT_BODY}; font-size: 13px;")
        row.setWordWrap(True)
        cl2.addWidget(row)
    layout.addWidget(card2)

    layout.addWidget(
        make_image_placeholder("[Screenshot: Note type fields list in Anki]")
    )
    layout.addStretch()
    return _make_scrollable(page)


def _build_tags_decks() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Recommended conventions for decks and tags so the add-on and your "
            "reviews stay organised."
        )
    )

    card, cl = make_section_card("Decks")
    cl.addWidget(
        _body_label(
            "A common setup is one main vocabulary deck for mined cards and a "
            "separate RTK deck for Heisig kanji cards. The RTK deck is created "
            "automatically by the Setup & Import tab if you want."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Tags (suggestions)")
    for t in [
        "source::immersion / source::textbook / source::jisho",
        "jlpt::n5 … jlpt::n1 (filled automatically when available)",
        "rtk::known / rtk::learning (managed by the RTK features)",
        "audio::hypertts (optional, for filtering)",
    ]:
        cl2.addWidget(_bullet(t))
    layout.addWidget(card2)

    layout.addWidget(make_image_placeholder("[Screenshot: Example deck & tag structure]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_jisho() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "How to configure Jisho lookup, field mappings, and the multi-meaning / "
            "multi-word formats."
        )
    )

    card, cl = make_section_card("Profiles")
    cl.addWidget(
        _body_label(
            "Each note type can have its own Jisho profile (search field, mappings, "
            "fill mode, etc.). Switch profiles with the Profile dropdown in the "
            "Jisho → General tab."
        )
    )
    layout.addWidget(card)

    card2, cl2 = make_section_card("Mapping")
    cl.addWidget(
        _body_label(
            "Map Jisho data fields (Word, Reading, Meanings, Part of Speech, …) "
            "to the fields of your note type. Only mapped fields are written."
        )
    )
    layout.addWidget(card2)

    card3, cl3 = make_section_card("Multi-meaning & multi-word formats")
    cl3.addWidget(
        _body_label(
            "When a search returns several senses or several headwords you can "
            "choose how they are joined (pipe, semicolon, numbered, tagged, …). "
            "Compatibility between the two format settings is enforced in the UI."
        )
    )
    layout.addWidget(card3)

    layout.addWidget(make_image_placeholder("[Screenshot: Jisho mapping tab]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_rtk_help() -> QWidget:
    """Educational content about Remembering the Kanji."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "How Heisig’s Remembering the Kanji method works and how this add-on "
            "supports it. This is the educational companion to the RTK settings tab."
        )
    )

    # Core method
    card, cl = make_section_card("The keyword method")
    cl.addWidget(
        _body_label(
            "Heisig assigns every kanji a unique English keyword. You learn to write "
            "the kanji from the keyword (and later the keyword from the kanji) by "
            "creating a vivid story that links the keyword to the kanji’s primitives."
        )
    )
    cl.addWidget(
        _body_label(
            "The goal is not to learn readings or vocabulary first — it is to make "
            "the characters themselves memorable so that later vocabulary sticks "
            "far more easily."
        )
    )
    layout.addWidget(card)

    # Primitives
    card2, cl2 = make_section_card("Primitives")
    cl2.addWidget(
        _body_label(
            "Almost every kanji is built from simpler building blocks called "
            "primitives (or radicals in a looser sense). Heisig gives many of these "
            "primitives their own names and stories as well."
        )
    )
    cl2.addWidget(_subheading("Why primitives matter"))
    cl2.addWidget(
        _body_label(
            "Once you know the primitives, a new kanji is no longer a random "
            "collection of strokes — it is a combination of pieces you already "
            "recognise. This is the real power of the method."
        )
    )
    cl2.addWidget(
        make_image_placeholder("[Diagram: example kanji broken into primitives]")
    )
    layout.addWidget(card2)

    # Stories
    card3, cl3 = make_section_card("Stories & memory")
    cl3.addWidget(
        _body_label(
            "A good story is short, visual, and emotionally charged. It should "
            "force the primitives to interact in a way that can only produce "
            "that particular keyword. Bizarre or humorous images stick best."
        )
    )
    layout.addWidget(card3)

    # Confusing pairs – skeleton
    card4, cl4 = make_section_card("Commonly confused kanji & keywords")
    cl4.addWidget(
        _body_label(
            "Some keywords and shapes are easy to mix up. Below is a starter list "
            "you can expand over time. The add-on can later surface these "
            "automatically when relevant."
        )
    )
    confusions = [
        ("快 (exhilarate) vs 決 (decide)", "Both contain the water primitive; stories must clearly separate the feelings."),
        ("未 (not yet) vs 末 (extremity)", "Very similar shapes — pay attention to the longer stroke."),
        ("土 (soil) vs 士 (gentleman)", "Almost identical; the relative length of the horizontal strokes is the difference."),
        ("千 (thousand) vs 干 (dry)", "Again a single-stroke difference that is easy to miss under speed."),
    ]
    for pair, note in confusions:
        cl4.addWidget(_subheading(pair))
        cl4.addWidget(_body_label(note))
    cl4.addWidget(
        _body_label(
            "Tip: when two kanji feel similar, deliberately invent stories that "
            "contrast them instead of treating them in isolation."
        )
    )
    layout.addWidget(card4)

    # How the add-on helps
    card5, cl5 = make_section_card("How JapaneseMining helps")
    for item in [
        "Create a full RTK deck + note type with one click (≈2200 core Heisig kanji, 6th ed).",
        "Import known kanji: creates the full ~2200 set, parks the known subset "
        "(suspend or schedule), leaves the rest as new.",
        "When you mine a word, look up Heisig keywords for its kanji.",
        "Track which kanji became known today in the Today’s Progress window.",
    ]:
        cl5.addWidget(_bullet(item))
    layout.addWidget(card5)

    # Tags
    card_tags, cl_tags = make_section_card("Tags the add-on uses")
    cl_tags.addWidget(
        _body_label(
            "Every RTK note the add-on creates or touches gets a consistent tag "
            "namespace so you can search and filter in the browser."
        )
    )
    for tag, meaning in [
        (
            "JapaneseMining::RTK",
            "Added to every RTK note the add-on manages. Search: tag:JapaneseMining::RTK",
        ),
        (
            "Heisig",
            "Bulk-created from the Heisig 6th-edition list (Create all notes / Import).",
        ),
        (
            "Imported-Known",
            "This kanji was marked known via Import (file or Heisig number). "
            "Usually suspended or far-scheduled so it does not flood reviews.",
        ),
        (
            "Self-Added",
            "Added automatically when you mine a word that contains an unknown kanji "
            "(Add Unknown Kanji flow).",
        ),
    ]:
        cl_tags.addWidget(_subheading(tag))
        cl_tags.addWidget(_body_label(meaning))
    layout.addWidget(card_tags)

    # Source of truth
    card_sot, cl_sot = make_section_card("Source of truth: the RTK deck")
    cl_sot.addWidget(
        _body_label(
            "learned_kanji.csv is a cache derived from the configured RTK deck. "
            "That deck is the source of truth."
        )
    )
    cl_sot.addWidget(_subheading("How export decides Learned / Knowledge"))
    cl_sot.addWidget(
        _body_label(
            "• Card has been studied (not new) → Learned, Knowledge from Anki/FSRS "
            "(real review history).\n"
            "• Card is suspended (e.g. after Import) → Learned, Knowledge = 1.0 "
            "until you study it.\n"
            "• Card is pure new (not suspended) → not learned."
        )
    )
    cl_sot.addWidget(_subheading("After you study an imported card"))
    cl_sot.addWidget(
        _body_label(
            "Unsusspend (if needed) and review it. The next Export Learned Kanji "
            "writes the real Anki knowledge score — the deck always wins over the "
            "previous CSV value."
        )
    )
    cl_sot.addWidget(_subheading("Switching decks"))
    cl_sot.addWidget(
        _body_label(
            "If you map a different RTK deck and run Export, the CSV is rebuilt "
            "entirely from that deck. The previous deck’s data is not kept."
        )
    )
    layout.addWidget(card_sot)

    # What to do depending on your situation
    card6, cl6 = make_section_card("What should I click? (by situation)")
    cl6.addWidget(_subheading("1. Beginner — no RTK deck yet"))
    cl6.addWidget(
        _body_label(
            "Open Settings → RTK → Setup & Import. Keep “create notes for all Heisig "
            "kanji” checked and press Create. You get a deck, a note type with the "
            "standard fields, and ~2200 notes ordered by Heisig 6th-edition number."
        )
    )
    cl6.addWidget(_subheading("2. Not a beginner — no RTK deck yet"))
    cl6.addWidget(
        _body_label(
            "Create the deck + note type (all-notes optional). Then use Import "
            "(file or Heisig number up to N, 6th ed only). Import ensures all "
            "~2200 notes exist, marks the known subset as learned (suspend or "
            "schedule), and leaves the rest as new cards for you to study."
        )
    )
    cl6.addWidget(_subheading("3. I already have an RTK deck"))
    cl6.addWidget(
        _body_label(
            "Go to Deck Mapping. Point the add-on at your deck and note type. "
            "Kanji field and Keyword field are required. Mapping changes apply "
            "immediately to Setup & Import — you do not need to click Save first. "
            "Create only adds missing notes and fills empty fields. "
            "Recommended: the add-on’s own note type for full field support."
        )
    )
    cl6.addWidget(_subheading("Important: Import on a deck that already has notes"))
    cl6.addWidget(
        _body_label(
            "Import will suspend or re-schedule cards for every kanji in the "
            "imported set — including notes that already existed in that deck. "
            "Field content is never overwritten, but review queues for those cards "
            "will change. Do not run Import if you want to keep the current "
            "scheduling of those kanji. Prefer Import when building a deck or when "
            "you intentionally want those cards parked as known."
        )
    )
    cl6.addWidget(_subheading("Minimum fields"))
    cl6.addWidget(
        _body_label(
            "Any note type the add-on can drive must expose a Kanji field and a "
            "Keyword field (via mapping or those exact names). Everything else is "
            "best-effort fill when the field exists and is empty."
        )
    )
    layout.addWidget(card6)

    layout.addWidget(
        make_image_placeholder("[Screenshot: RTK Setup & Import tab]")
    )
    layout.addStretch()
    return _make_scrollable(page)


def _build_hypertts() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "How to enable and use HyperTTS for automatic audio generation."
        )
    )

    card, cl = make_section_card("Setup")
    cl.addWidget(
        _body_label(
            "1. Install the HyperTTS add-on from AnkiWeb if you have not already.\n"
            "2. Configure a voice / preset inside HyperTTS itself.\n"
            "3. In JapaneseMining → HyperTTS, enable the integration.\n"
            "4. When you save a card, audio can be generated according to your "
            "HyperTTS presets."
        )
    )
    layout.addWidget(card)

    layout.addWidget(make_image_placeholder("[Screenshot: HyperTTS settings]"))
    layout.addStretch()
    return _make_scrollable(page)


def _build_troubleshooting() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(14)

    layout.addWidget(
        make_instruction_label(
            "Quick fixes for the most common issues."
        )
    )

    card, cl = make_section_card("Jisho does nothing")
    cl.addWidget(_bullet("Confirm “Enable Jisho” is checked and restart Anki."))
    cl.addWidget(_bullet("Check that the active profile’s Search field matches a field that actually contains the word."))
    cl.addWidget(_bullet("Verify the field mappings are not empty."))
    layout.addWidget(card)

    card2, cl2 = make_section_card("RTK keywords missing")
    cl2.addWidget(_bullet("Make sure the RTK deck & note type are configured in the Deck Mapping tab."))
    cl2.addWidget(_bullet("Run an import (file or Heisig number) so the known-kanji cache is populated."))
    layout.addWidget(card2)

    card3, cl3 = make_section_card("DeepL / character limit")
    cl3.addWidget(_bullet("Check the character usage shown in the Translate tab."))
    cl3.addWidget(_bullet("Confirm the API key and URL are correct."))
    layout.addWidget(card3)

    layout.addStretch()
    return _make_scrollable(page)


# ── Public factory ───────────────────────────────────────────────────────

def make_help_tab(config_holder=None, save_config_fn=None):
    """
    Returns (tab_widget, title, apply_to_config_fn).

    apply_to_config is a no-op because Help is read-only.
    The returned widget exposes .goto_rtk() so the RTK settings tab
    can jump here.
    """
    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    sub_tabs = QTabWidget()
    outer_layout.addWidget(sub_tabs)

    # Order matters for the jump helper
    sub_tabs.addTab(_build_overview(), "Overview")
    sub_tabs.addTab(_build_note_type(), "Note Type")
    sub_tabs.addTab(_build_tags_decks(), "Tags & Decks")
    sub_tabs.addTab(_build_jisho(), "Jisho")
    rtk_index = sub_tabs.count()
    sub_tabs.addTab(_build_rtk_help(), "Remembering the Kanji")
    sub_tabs.addTab(_build_hypertts(), "HyperTTS")
    sub_tabs.addTab(_build_troubleshooting(), "Troubleshooting")

    def goto_rtk():
        sub_tabs.setCurrentIndex(rtk_index)

    outer.goto_rtk = goto_rtk
    # Also expose the sub-tab widget so the parent dialog can switch to Help itself
    outer.sub_tabs = sub_tabs

    def apply_to_config(_cfg):
        pass  # read-only

    return outer, "Help", apply_to_config
