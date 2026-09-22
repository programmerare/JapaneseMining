from anki.models import TemplateDict


def add_question_format_to_template(template: TemplateDict, question_format: str) -> TemplateDict:
    """Add a question format to the specified card template in the given model (note type)."""
    if not isinstance(question_format, str):
        raise TypeError(f"add_question_format_to_template expects a string, got {type(question_format).__name__}")
    if not isinstance(template, TemplateDict):
        raise TypeError(f"add_question_format_to_template expects a TemplateDict (dict), got {type(template).__name__}")
    template["qfmt"] = question_format
    return template

def add_answer_format_to_template(template: TemplateDict, answer_format: str) -> TemplateDict:
    """Add an answer format to the specified card template in the given model (note type)."""
    if not isinstance(answer_format, str):
        raise TypeError(f"add_answer_format_to_template expects a string, got {type(answer_format).__name__}")
    if not isinstance(template, TemplateDict):
        raise TypeError(f"add_answer_format_to_template expects a TemplateDict (dict), got {type(template).__name__}")
    template["afmt"] = answer_format
    return template