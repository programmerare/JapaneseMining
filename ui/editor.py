from aqt import mw
from aqt.editor import Editor
from aqt.qt import QTextDocument
from sudachipy import tokenizer, dictionary

from ..config import ConfigHolder

tokenizer_obj = dictionary.Dictionary(dict="small").create()


def make_translate_btn_setup(deepl_service, config_holder: ConfigHolder):
    def set_translate_btn(buttons: list[str], editor: Editor) -> None:
        def on_translate(editor):
            deepl_service.translate(editor)

        button = editor.addButton(
            icon=None,
            cmd="deepl_translate",
            func=on_translate,
            tip="Translate Example Sentence",
            label="T",
            id="deepl-translate",
            keys=config_holder.config.deepl_shortcut,
        )
        buttons.append(button)

    return set_translate_btn


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
    editor.web.eval("""
    if (!document.getElementById("token-style")) {
        const style = document.createElement("style");
        style.id = "token-style";
        style.textContent = `
            .my-preview {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin: 0 0 2px 5px;
                align-items: center;
                min-height: 0;
            }

            .token {
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
            }

            .token:hover {
                background: #4f8df7;
                border-color: #4f8df7;
                color: white;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(79,141,247,.35);
            }

            .token:active {
                transform: translateY(0);
                box-shadow: none;
            }
        `;
        document.head.appendChild(style);
    }
    """)


def make_segment_sentence(config_holder: ConfigHolder, get_focused_field_index):
    def segment_sentence(note):
        """Segment the Example Sentence field of a note and display the tokens in a preview area."""
        config = config_holder.config
        if not note or note.note_type()["name"] != config.mining_note_type:
            return

        if "Example Sentence" not in note:
            return

        fmap_entry = note._fmap.get("Example Sentence")
        if not fmap_entry:
            return

        focused = get_focused_field_index()
        example_sentence_index = str(fmap_entry[0])
        if focused != example_sentence_index:
            return

        if not hasattr(mw.app.activeWindow(), "editor"):
            return

        editor = mw.app.activeWindow().editor

        index = fmap_entry[0]
        text = note.fields[index]

        # Convert HTML to plain text to remove any HTML tags before tokenization
        doc = QTextDocument()
        doc.setHtml(text)
        text = doc.toPlainText()

        tokens = tokenizer_obj.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
        tokens = [t for t in tokens if t.surface().strip()]

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
        editor.web.eval("""
        var word_field = [...document.querySelectorAll('div.rich-text-editable')]
            .map(host => host.shadowRoot?.querySelector('anki-editable[field="Word"]'))
            .find(Boolean);
        var tokens = document.querySelectorAll('.token');
        tokens.forEach(token => {
            token.addEventListener('click', () => {
                text = token.getAttribute('data-token');
                word_field.innerText = text;
            });
        });
        """)

    return segment_sentence
