from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QTabWidget,
    QWidget,
)
from . import features, helpers, globals
from .setup import save_config


def on_card_answered(reviewer, card, ease):
    if card.reps != 1:
        return

    note = card.note()

    if note.note_type()["name"] != globals.note_type:
        return

    features.save_word(
        note["Word"],
        note["Reading"],
        note["Meaning"],
    )


def on_note_added(note):
    features.update_single_note_kanji_knowledge(note)


def show_today_words():
    dialog = QDialog(mw)
    dialog.setWindowTitle("Words learned today")
    dialog.resize(760, 560)
    dialog.setMinimumSize(680, 480)

    layout = QVBoxLayout()

    text = QTextBrowser()

    words = features.load_today_words()
    content = [
        "<style>"
        "body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; line-height: 1.5; }"
        ".entry { padding: 12px 0; border-bottom: 1px solid #ddd; }"
        ".top { display: flex; gap: 10px; align-items: baseline; font-size: 17px; font-weight: 600; }"
        ".reading { color: #666; font-weight: 500; }"
        ".meaning { margin-top: 2px; color: #222; }"
        "</style>",
    ]

    if words:
        for word, reading, meaning in words:
            content.append(
                "<div class='entry'>"
                f"<div class='top'><span class='word'>{word}</span><span class='reading'>{reading}</span></div>"
                f"<div class='meaning'>{meaning}</div>"
                "</div>"
            )
    else:
        content.append("<div class='entry'>No words learned today.</div>")

    text.setHtml("<html><body>" + "".join(content) + "</body></html>")

    layout.addWidget(text)

    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.close)
    layout.addWidget(close_button)

    dialog.setLayout(layout)
    dialog.exec()


from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
)


def show_settings():
    dialog = QDialog(mw)
    dialog.setWindowTitle("JapaneseMining Settings")
    dialog.resize(720, 400)
    dialog.setMinimumWidth(640)

    main_layout = QVBoxLayout(dialog)

    tabs = QTabWidget()

    # -------------------
    # General tab
    # -------------------
    general_tab = QWidget()
    general_layout = QFormLayout(general_tab)

    note_type_edit = QLineEdit(globals.note_type)
    note_type_edit.setMinimumWidth(420)

    rtk_deck_edit = QLineEdit(globals.rtk_deck)
    rtk_deck_edit.setMinimumWidth(420)

    deepl_key_edit = QLineEdit(globals.deepl_api_key)
    deepl_key_edit.setMinimumWidth(420)
    deepl_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    deepl_url_edit = QLineEdit(globals.deepl_url)
    deepl_url_edit.setMinimumWidth(420)

    general_layout.addRow("JapaneseMining note type", note_type_edit)
    general_layout.addRow("RTK deck", rtk_deck_edit)
    general_layout.addRow("DeepL API key", deepl_key_edit)
    general_layout.addRow("DeepL URL", deepl_url_edit)

    tabs.addTab(general_tab, "General")


    # -------------------
    # Translate tab
    # -------------------
    translate_tab = QWidget()
    translate_layout = QFormLayout(translate_tab)

    # Add translate settings here later
    translate_layout.addRow("Example", QLineEdit())

    tabs.addTab(translate_tab, "Translate")


    # -------------------
    # AJC tab
    # -------------------
    ajc_tab = QWidget()
    ajc_layout = QFormLayout(ajc_tab)

    # Add AJC settings here later
    ajc_layout.addRow("Example", QLineEdit())

    tabs.addTab(ajc_tab, "AJC")


    # -------------------
    # HyperTTS tab
    # -------------------
    hypertts_tab = QWidget()
    hypertts_layout = QFormLayout(hypertts_tab)

    # Add HyperTTS settings here later
    hypertts_layout.addRow("Example", QLineEdit())

    tabs.addTab(hypertts_tab, "HyperTTS")


    main_layout.addWidget(tabs)


    # -------------------
    # Buttons
    # -------------------
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save |
        QDialogButtonBox.StandardButton.Cancel
    )

    main_layout.addWidget(buttons)


    def save_and_close():
        config = {
            "note_type": note_type_edit.text().strip() or globals.note_type,
            "rtk_deck": rtk_deck_edit.text().strip() or globals.rtk_deck,
            "deepl_api_key": deepl_key_edit.text().strip(),
            "deepl_url": deepl_url_edit.text().strip() or globals.deepl_url,
        }

        save_config(config)
        dialog.accept()


    buttons.accepted.connect(save_and_close)
    buttons.rejected.connect(dialog.reject)

    dialog.exec()


def set_translate_btn(buttons: list[str], editor: Editor) -> None:
    button = editor.addButton(
        icon=None,
        cmd="my_button",
        func=features.translate,
        tip="Translate Example Sentence",
        label="T",
        id="deepl-translate",
        keys=globals.shortcut,
    )
    buttons.append(button)


def inject_editor_css(editor):
    # Inject CSS for the DeepL translate button
    editor.web.eval("""
    if (!document.getElementById("deepl-button-style")) {
        const style = document.createElement("style");
        style.id = "deepl-button-style";
        style.textContent = `
            #deepl-translate {
                margin-left: 4px;
            }

            #deepl-translate:hover {
                color: #0d47a1;
            }
        `;
        document.head.appendChild(style);
    }
    """)

    # Inject CSS for the token elements
    editor.web.eval(f"""
    if (!document.getElementById("token-style")) {{
        const style = document.createElement("style");
        style.id = "token-style";
        style.textContent = `
            .my-preview {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin: 0 0 2px 5px;
                align-items: center;
                min-height: 0;
            }}

            .token {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 999px;
                background: #f3f5f7;
                border: 1px solid #d5dbe3;
                color: #444;
                font-size: 13px;
                line-height: 1.4;
                cursor: pointer;
                user-select: none;

                transition:
                    background-color 120ms ease,
                    border-color 120ms ease,
                    transform 120ms ease,
                    box-shadow 120ms ease;
            }}

            .token:hover {{
                background: #4f8df7;
                border-color: #4f8df7;
                color: white;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(79,141,247,.35);
            }}

            .token:active {{
                transform: translateY(0);
                box-shadow: none;
            }}
        `;
        document.head.appendChild(style);
    }}
    """)


gui_hooks.reviewer_did_answer_card.append(on_card_answered)
gui_hooks.editor_did_init.append(inject_editor_css)
gui_hooks.editor_did_init_buttons.append(set_translate_btn)
gui_hooks.editor_did_focus_field.append(helpers.set_focused_field_index)
gui_hooks.editor_did_fire_typing_timer.append(features.segment_sentence)
gui_hooks.editor_did_init.append(helpers.set_hypertts)
gui_hooks.editor_did_init.append(helpers.safe_current_editor)
gui_hooks.add_cards_will_add_note.append(helpers.on_card_will_add_note)


my_menu = QMenu("JapaneseMining", mw)

action = QAction("Show Today's Words", mw)
action.triggered.connect(show_today_words)
my_menu.addAction(action)

action = QAction("Settings", mw)
action.triggered.connect(show_settings)
my_menu.addAction(action)

my_menu.addSeparator()

action = QAction("Soft Update Everything", mw)
action.triggered.connect(features.update_japanese_mining_cards)
my_menu.addAction(action)

action = QAction("Force Update Keywords", mw)
action.triggered.connect(features.force_update_keywords)
my_menu.addAction(action)

action = QAction("Force Update Meanings", mw)
action.triggered.connect(features.force_update_meanings)
my_menu.addAction(action)

action = QAction("Force Update Everything", mw)
action.triggered.connect(features.force_update_everything)
my_menu.addAction(action)

my_menu.addSeparator()
action = QAction("Add Unknown Kanji", mw)
action.triggered.connect(features.add_unknown_kanji)
my_menu.addAction(action)

my_menu.addSeparator()
action = QAction("Export Learned Kanji", mw)
action.triggered.connect(features.export_learned_kanji)
my_menu.addAction(action)

mw.form.menuTools.addMenu(my_menu)