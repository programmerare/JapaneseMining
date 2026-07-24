# -*- coding: utf-8 -*-

"""Constants: Translations, themes, and configuration."""



TRANSLATIONS = {

    "en": {

        # Config Dialog

        "settings_title": "Anki Jisho Connect Settings",
        "language": "UI Language:",

        "ui_language": "UI Language:",

        "main_settings": "Main Settings",

        "tab_general": "General",

        "tab_mapping": "Mapping",

        "tab_advanced": "Advanced",

    "advanced_title": "Advanced Options",

        "style_mode": "Style:",

        "style_mode_legacy_stable": "Legacy and Stable (Default)",
        "profile_label": "Profile:",
        "profile_add": "Add",
        "profile_rename": "Rename",
        "profile_delete": "Delete",
        "profile_add_default_name": "Profile",
        "profile_name_prompt_add": "New profile name:",
        "profile_name_prompt_rename": "Rename profile:",
        "profile_delete_confirm": "Delete profile '{name}'?",
        "profile_error_exists": "A profile with this name already exists.",
        "profile_error_empty": "Profile name cannot be empty.",
        "profile_error_last": "At least one profile is required.",
        "note_type": "Note Type:",
        "target_deck": "Target Deck:",
        "search_field": "Search Field:",
        "fill_mode": "Fill Mode:",
        "fill_mode_replace": "Replace content",

        "fill_mode_append": "Append to content",

        "multi_meaning_format": "Multi-Meaning Format:",

        "multi_meaning_format_pipe_merged": "Pipe Merged",

        "multi_meaning_format_numbered": "Numbered",

        "multi_meaning_format_semicolon_merged": "Semicolon Merged",

        "multi_meaning_tooltip": "<html><body style='white-space: pre-wrap;'><b>Simple</b><br/>Separates meanings with pipe (|) symbol.<br/>meaning1 | meaning2 | meaning3<br/><br/><b>Numbered</b><br/>Numbers each meaning with line breaks.<br/>1. meaning1<br/>2. meaning2<br/>3. meaning3<br/><br/><b>Merged</b><br/>All meanings merged with semicolon separator.<br/>meaning1; meaning2; meaning3</body></html>",

        "multi_word_tooltip": "Format for combining meanings when adding multiple words into a card. Options are filtered based on the selected Multi-Meaning Format for compatibility.",

        "multi_word_search": "Multi-Word Search",

        "multi_word_format": "Multi-Word Format:",

        "multi_word_format_basic": "Basic",

        "multi_word_format_inline": "Inline (merged)",

        "multi_word_format_tagged": "Tagged (with word)",

        "multi_word_format_numbered": "Numbered (word #)",

        "multi_word_format_tagged_numbered": "Tagged + Numbered",

        "field_mapping": "Field Mapping (Dictionary → Anki)",
        "field_mapping_tooltip": "<html><body style='white-space: pre-wrap;'><b>Word:</b> 戦う<br/><b>Reading:</b> たたかう<br/><b>Meaning:</b> to fight; to battle; to wage war<br/><b>Part of speech:</b> Verb; Godan verb with 'u' ending<br/><b>Info:</b> also written as 闘う<br/><b>Tags:</b> Usually written using kana alone; Buddhism<br/><b>See also:</b> 戦い; 戦争<br/><b>Other forms:</b> 闘う [たたかう]<br/><b>JLPT Level:</b> jlpt-n3<br/><b>Wanikani Level:</b> wanikani17<br/><b>Is Common:</b> common word (only if entry is common)</body></html>",
        "add_mapping": "+ Add Mapping",
        "disable_warning": "Disable multi-word selection warning",

        "remove_pos_ending": "Remove 'with x ending' from Part of speech",

        "remove_furigana_search": "Remove furigana from search term",
        "button_position_label": "Button Position:",
        "button_position_toolbar": "Toolbar",
        "button_position_field_label": "Field Label",
        "button_position_both": "Toolbar + Field Label",
        "save_and_close": "Save and Close",

        "warning_fill_mappings": "Fill all mapping pairs before saving.",
        "warning_profile_duplicate_combo": "This Note Type + Deck combination is already used by profile '{profile}'. Choose a different pair.",
        "info_settings_saved": "Settings saved!",
        "info_settings_saved_restart": "Settings saved. Restart Anki to apply style changes.",


        # Results Dialog

        "results_title": "Anki Jisho Connect Result",
        "search_placeholder": "Enter any Japanese text or English word...",

        "search_button": "Search",

        "confirm_entry": "Confirm Entry",
        "select_all_meanings": "Select all meanings",
        "loading_message": "Looking for results...",

        "loading_message_term": "Looking for '{term}'...",

        "no_results": "Sorry, nothing was found for '{term}'.",

        "other_forms": "Other forms:",

        "multi_word_warning_title": "You selected definitions from multiple words.",

        "multi_word_warning_body": "Meanings from multiple words will be added to the note.",

        "ok_dont_warn_again": "OK, don't warn me again",

        "info_fields_filled": "Fields filled successfully!",

        "button_ok": "OK",          

        "button_cancel": "Cancel",



        # Main Flow

        "input_dialog_title": "Search Dictionary",
        "input_dialog_label": "Search term:",

        "editor_button_tooltip": "Search Dictionary",
        "warning_no_active_editor": "No active editor found.",

        "warning_no_mappings": "No field mappings are configured. Please configure at least one mapping in the settings.",

        "warning_no_search_term": "No search term found in the selected field.",

        "open_shortcut": "Open Dictionary Shortcut:",
        "quick_fill_shortcut": "Quick Fill Shortcut:",

        "quick_fill_mode": "Quick Fill Mode:",

        "quick_fill_mode_all": "All meanings",

        "quick_fill_mode_first": "First meaning",
        "quick_fill_mode_tooltip": "Quick Fill uses the first result block in the results window. Choose whether it adds only the first meaning or all meanings from that block.",
        "disable_quick_fill_success": "Disable quick fill success message",

        "shortcut_unassigned": "Not set",

        "shortcut_dialog_title": "Assign Shortcut",
        "shortcut_dialog_prompt": "Please press the key combination...",
        "shortcut_dialog_pressed_keys": "Pressed keys:",
        "shortcut_dialog_pressed_placeholder": "Waiting for key input...",
        "shortcut_dialog_help": "Allowed: Ctrl/Shift/Alt + letter or number. Press Esc to cancel.",
        "shortcut_dialog_invalid": "Invalid shortcut. Use Ctrl/Shift/Alt + letter or number.",
        "menu_about_ajc": "About AJC",

        "welcome_title": "WELCOME TO AJC ADDONS",

        "welcome_body": "Hi! Thanks for using AJC add-ons.\n\nThese add-ons are built for language learning and to make your study workflow faster and cleaner inside Anki. Each tool focuses on a specific task and integrates directly into the editor.\n\nOpen the AJC menu to find settings, actions, and help for each add-on.",

        "welcome_support_title": "SUPPORT THIS PROJECT",

        "welcome_support_body": "If these add-ons save you time or help your studies, please consider supporting development. A coffee keeps the code flowing!",

        "welcome_report_title": "REPORT ISSUES & QUESTIONS",

        "welcome_report_body": "Found a bug, have a suggestion, or need help? Please use the project page. Clear reports help fixes land faster: include your Anki version, steps to reproduce, and a screenshot if possible.",

        "welcome_support_kofi_label": "Ko-fi",

        "welcome_support_github_label": "GitHub",

    },

    "pt": {

        # Config Dialog

        "settings_title": "Configurações da Anki Jisho Connect",
        "language": "Idioma da UI:",

        "ui_language": "Idioma da UI:",

        "main_settings": "Configurações Principais",

        "tab_general": "Geral",

        "tab_mapping": "Mapeamento",

        "tab_advanced": "Avancado",

    "advanced_title": "Opcoes Avancadas",

        "style_mode": "Estilo:",

        "style_mode_legacy_stable": "Legado e Estavel (Padrao)",
        "profile_label": "Perfil:",
        "profile_add": "Adicionar",
        "profile_rename": "Renomear",
        "profile_delete": "Excluir",
        "profile_add_default_name": "Perfil",
        "profile_name_prompt_add": "Nome do novo perfil:",
        "profile_name_prompt_rename": "Renomear perfil:",
        "profile_delete_confirm": "Excluir o perfil '{name}'?",
        "profile_error_exists": "Já existe um perfil com esse nome.",
        "profile_error_empty": "O nome do perfil não pode ficar vazio.",
        "profile_error_last": "É necessário manter pelo menos um perfil.",
        "note_type": "Tipo de Nota:",
        "target_deck": "Deck Alvo:",
        "search_field": "Campo de Busca:",
        "fill_mode": "Modo de Preenchimento:",
        "fill_mode_replace": "Substituir conteúdo",

        "fill_mode_append": "Adicionar ao conteúdo",

        "multi_meaning_format": "Formato Multi-Significado:",

        "multi_meaning_format_pipe_merged": "Mesclado por Pipe",

        "multi_meaning_format_numbered": "Numerado",

        "multi_meaning_format_semicolon_merged": "Mesclado por Ponto-e-Vírgula",

        "multi_meaning_tooltip": "<html><body style='white-space: pre-wrap;'><b>Simples</b><br/>Separa significados com símbolo de pipe (|).<br/>significado1 | significado2 | significado3<br/><br/><b>Numerado</b><br/>Numera cada significado com quebras de linha.<br/>1. significado1<br/>2. significado2<br/>3. significado3<br/><br/><b>Mesclado</b><br/>Todos os significados mesclados com separador ponto-e-vírgula.<br/>significado1; significado2; significado3</body></html>",

        "multi_word_tooltip": "<html><body style='white-space: pre-wrap;'>Formato para combinar significados quando adicionando múltiplas palavras em um cartão.<br/>As opções são filtradas com base no Formato Multi-Significado selecionado para compatibilidade.</body></html>",

        "multi_word_search": "Busca Multi-Palavra",

        "multi_word_format": "Formato Multi-Palavra:",

        "multi_word_format_basic": "Básico",

        "multi_word_format_inline": "Em Linha (mesclado)",

        "multi_word_format_tagged": "Etiquetado (com palavra)",

        "multi_word_format_numbered": "Numerado (# palavra)",

        "multi_word_format_tagged_numbered": "Etiquetado + Numerado",

        "field_mapping": "Mapeamento de Campos (Dicionario → Anki)",
        "field_mapping_tooltip": "<html><body style='white-space: pre-wrap;'><b>Palavra:</b> 戦う<br/><b>Leitura:</b> たたかう<br/><b>Significado:</b> to fight; to battle; to wage war<br/><b>Classe gramatical:</b> Verb; Godan verb with 'u' ending<br/><b>Info:</b> also written as 闘う<br/><b>Tags:</b> Usually written using kana alone; Buddhism<br/><b>Veja também:</b> 戦い; 戦争<br/><b>Outras formas:</b> 闘う [たたかう]<br/><b>Nível JLPT:</b> jlpt-n3<br/><b>Nível Wanikani:</b> wanikani17<br/><b>Is Common:</b> common word (only if entry is common)</body></html>",
        "add_mapping": "+ Adicionar Mapeamento",
        "disable_warning": "Desativar aviso de seleção de múltiplas palavras",

        "remove_pos_ending": "Remover 'with x ending' de Classe Gramatical",

        "remove_furigana_search": "Remover furigana do termo de busca",
        "button_position_label": "Posicao do Botao:",
        "button_position_toolbar": "Toolbar",
        "button_position_field_label": "Label do Campo",
        "button_position_both": "Toolbar + Label do Campo",
        "save_and_close": "Salvar e Fechar",

        "warning_fill_mappings": "Preencha todos os pares de mapeamento antes de salvar.",
        "warning_profile_duplicate_combo": "Essa combinação de Tipo de Nota + Deck já está em uso no perfil '{profile}'. Escolha outro par.",
        "info_settings_saved": "Configurações salvas!",
        "info_settings_saved_restart": "Configuracoes salvas. Reinicie o Anki para aplicar a mudanca de estilo.",


        # Results Dialog

        "results_title": "Resultado da Anki Jisho Connect",
        "search_placeholder": "Digite um texto em japonês ou uma palavra em inglês...",

        "search_button": "Buscar",

        "confirm_entry": "Confirmar Entrada",
        "select_all_meanings": "Selecionar todos os significados",
        "loading_message": "Procurando resultados...",

        "loading_message_term": "Procurando por '{term}'...",

        "no_results": "Desculpe, não foi encontrado nada para '{term}'.",

        "other_forms": "Outras formas:",

        "multi_word_warning_title": "Você selecionou definições de múltiplas palavras.",

        "multi_word_warning_body": "Os significados de múltiplas palavras serão adicionados à nota.",

        "ok_dont_warn_again": "OK, não me avise novamente",

        "info_fields_filled": "Campos preenchidos com sucesso!",

        "button_ok": "OK",           

        "button_cancel": "Cancelar", 

        

        # Main Flow

        "input_dialog_title": "Buscar no Dicionario",
        "input_dialog_label": "Termo de busca:",

        "editor_button_tooltip": "Buscar no Dicionario",
        "warning_no_active_editor": "Nenhum editor ativo foi encontrado.",

        "warning_no_mappings": "Nenhum mapeamento de campo está configurado. Por favor, configure ao menos um nas configurações.",

        "warning_no_search_term": "Nenhum termo de busca encontrado no campo selecionado.",

        "open_shortcut": "Atalho para abrir Dicionario:",
        "quick_fill_shortcut": "Atalho para preenchimento rápido:",

        "quick_fill_mode": "Modo de preenchimento rápido:",

        "quick_fill_mode_all": "Todos os significados",

        "quick_fill_mode_first": "Primeiro significado",
        "quick_fill_mode_tooltip": "O Quick Fill usa o primeiro bloco retornado na janela de resultados. Escolha se ele adiciona apenas o primeiro significado ou todos os significados desse bloco.",
        "disable_quick_fill_success": "Desativar aviso de sucesso do preenchimento rápido",

        "shortcut_unassigned": "Não definido",

        "shortcut_dialog_title": "Definir atalho",
        "shortcut_dialog_prompt": "Pressione a combinação de teclas...",
        "shortcut_dialog_pressed_keys": "Teclas pressionadas:",
        "shortcut_dialog_pressed_placeholder": "Aguardando entrada de tecla...",
        "shortcut_dialog_help": "Permitido: Ctrl/Shift/Alt + letra ou número. Esc cancela.",
        "shortcut_dialog_invalid": "Atalho inválido. Use Ctrl/Shift/Alt + letra ou número.",
        "menu_about_ajc": "Sobre o AJC",

        "welcome_title": "BEM-VINDO AO ADDONS",

        "welcome_body": "Oi! Obrigado por usar os add-ons AJC.\n\nEstes add-ons sao feitos com foco em utilidade para estudos de idioma e para deixar o seu fluxo de estudo mais rapido e organizado dentro do Anki. Cada ferramenta foca em uma tarefa e se integra direto no editor.\n\nAbra o menu AJC para encontrar configuracoes, acoes e ajuda para cada add-on.",

        "welcome_support_title": "APOIE ESTE PROJETO",

        "welcome_support_body": "Se estes add-ons ajudam nos seus estudos, considere apoiar o desenvolvimento. Um cafe ajuda muito!",

        "welcome_report_title": "RELATAR PROBLEMAS E DUVIDAS",

        "welcome_report_body": "Encontrou um bug, tem sugestao ou precisa de ajuda? Use a pagina do projeto. Relatos claros ajudam a corrigir mais rapido: inclua a versao do Anki, passos para reproduzir e um print se possivel.",

        "welcome_support_kofi_label": "Ko-fi",

        "welcome_support_github_label": "GitHub",

    }

}



current_language = "en"



def _(key: str) -> str:

    """Get translated string, fallback to English."""

    return TRANSLATIONS.get(current_language, {}).get(key, TRANSLATIONS["en"].get(key, key))



def set_language(lang_code: str):

    """Set global add-on language."""

    global current_language

    current_language = lang_code if lang_code in TRANSLATIONS else "en"





class LightTheme:

    PRIMARY = "#007aff"

    PRIMARY_HOVER = "#005ecb"

    PRIMARY_TEXT = "#ffffff"

    ACCENT_YELLOW = "#ffc107"

    ACCENT_YELLOW_HOVER = "#e0a800"

    ACCENT_YELLOW_TEXT = "#333333"

    BACKGROUND = "#ffffff"

    BACKGROUND_ALT = "#f0f2f5"

    BACKGROUND_SEARCH = "#f7f7f7"

    BORDER = "#e0e0e0"

    BORDER_LIGHT = "#dddddd"

    BORDER_DARK = "#cccccc"

    TEXT_PRIMARY = "#222222"

    TEXT_SECONDARY = "#555555"

    TEXT_TERTIARY = "#666666"

    TEXT_DISABLED = "#999999"

    SUCCESS = "#88cc88"

    SUCCESS_TEXT = "#005000"

    INFO = "#88bbff"

    INFO_TEXT = "#004080"

    WARNING = "#dd77ff"

    WARNING_TEXT = "#500080"

    DANGER = "#ffeaea"

    DANGER_TEXT = "#c00000"

    CONTROL_BG = "transparent"

    CONTROL_BORDER = "#dddddd"

    CONTROL_HOVER_BG = "#e0e0e0"

    CONTROL_HOVER_BORDER = "#cccccc"

    CONTROL_DISABLED_TEXT = "#cccccc"

    CONTROL_DISABLED_BORDER = "#eeeeee"

    CONFIRM_DISABLED_BG = "#e9e9e9"



class DarkTheme:

    PRIMARY = "#008aff"

    PRIMARY_HOVER = "#006cd1"

    PRIMARY_TEXT = "#ffffff"

    ACCENT_YELLOW = "#ffc107"

    ACCENT_YELLOW_HOVER = "#e0a800"

    ACCENT_YELLOW_TEXT = "#333333"

    BACKGROUND = "#2d2d2d"

    BACKGROUND_ALT = "#252525"

    BACKGROUND_SEARCH = "#3a3a3a"

    BORDER = "#4a4a4a"

    BORDER_LIGHT = "#404040"

    BORDER_DARK = "#555555"

    TEXT_PRIMARY = "#f0f0f0"

    TEXT_SECONDARY = "#bbbbbb"

    TEXT_TERTIARY = "#999999"

    TEXT_DISABLED = "#777777"

    SUCCESS = "#77b677"

    SUCCESS_TEXT = "#d9f0d9"

    INFO = "#77aadd"

    INFO_TEXT = "#d9e8f7"

    WARNING = "#cc66ef"

    WARNING_TEXT = "#f4d9ff"

    DANGER = "#5c2e2e"

    DANGER_TEXT = "#ffc0c0"

    CONTROL_BG = "transparent"

    CONTROL_BORDER = "#555555"

    CONTROL_HOVER_BG = "#4f4f4f"

    CONTROL_HOVER_BORDER = "#666666"

    CONTROL_DISABLED_TEXT = "#666666"

    CONTROL_DISABLED_BORDER = "#444444"

    CONFIRM_DISABLED_BG = "#4a4a4a"





DEFAULT_CONFIG = {
    "language": "en",

    "style_mode": "legacy_and_stable",
    "show_welcome_dialog": True,

    "active_profile": "Default",

    "profiles": {},

    "card_type": "",

    "target_deck": "",
    "search_field": "N/A",
    "mappings": [],
    "fill_mode": "replace",
    "multi_meaning_format": "semicolon_merged",

    "disable_multi_word_warning": False,

    "remove_pos_ending": True,

    "remove_furigana_search": True,
    "editor_button_position": "toolbar",
    "multi_word_format": "inline",

    "open_shortcut": "Alt+J",

    "quick_fill_shortcut": "Ctrl+Alt+J",

    "quick_fill_mode": "all",

    "show_quick_fill_success": True,

}


JISHO_MAPPING_OPTIONS = [
    "",
    "Word",
    "Reading",
    "Meaning",
    "Part of speech",
    "Info",
    "Tags",
    "See also",
    "Other forms",
    "JLPT Level",
    "Wanikani Level",
    "Is Common",
]


# Multi-word format compatibility with multi-meaning formats

MULTI_WORD_COMPATIBILITY = {

    "numbered": {

        "basic": True,

        "inline": False,

        "tagged": True,

        "numbered": True,

        "tagged_numbered": False,

    },

    "semicolon_merged": {

        "basic": True,

        "inline": True,

        "tagged": True,

        "numbered": True,

        "tagged_numbered": True,

    },

    "pipe_merged": {

        "basic": True,

        "inline": True,

        "tagged": True,

        "numbered": True,

        "tagged_numbered": True,

    }

}

