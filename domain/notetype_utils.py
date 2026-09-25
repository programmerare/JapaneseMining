from anki.models import TemplateDict


def set_template_question_format(template: TemplateDict, question_format: str) -> TemplateDict:
    """Set the question format for the specified card template in the given model (note type)."""
    if not isinstance(question_format, str):
        raise TypeError(f"set_template_question_format expects a string, got {type(question_format).__name__}")
    if not isinstance(template, TemplateDict):
        raise TypeError(f"set_template_question_format expects a TemplateDict (dict), got {type(template).__name__}")
    template["qfmt"] = question_format
    return template


def set_template_answer_format(template: TemplateDict, answer_format: str) -> TemplateDict:
    """Set the answer format for the specified card template in the given model (note type)."""
    if not isinstance(answer_format, str):
        raise TypeError(f"set_template_answer_format expects a string, got {type(answer_format).__name__}")
    if not isinstance(template, TemplateDict):
        raise TypeError(f"set_template_answer_format expects a TemplateDict (dict), got {type(template).__name__}")
    template["afmt"] = answer_format
    return template