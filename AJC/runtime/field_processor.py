# -*- coding: utf-8 -*-
"""Field mapping and note filling logic."""

from typing import Dict, Any, List

from aqt import mw
from aqt.utils import showWarning

from .logger import logger

from .text_utils import clean_part_of_speech


LINE_BREAK = "<br>"
BLOCK_SEPARATOR = "<br><br>"
def _merge_definitions(defs: List[str], format_type: str) -> str:
    """Merge definition strings with the desired separator."""
    clean_defs = [d for d in defs if d]
    if not clean_defs:
        return ""
    if format_type == "semicolon_merged":
        return "; ".join(clean_defs)
    return " | ".join(clean_defs)


def _format_numbered_lines(defs: List[str], number_prefix: str = "", tag: str = "") -> str:
    """Format numbered lines with optional prefix and tag."""
    lines = []
    for idx, definition in enumerate(defs, start=1):
        if not definition:
            continue
        label = f"{number_prefix}{idx}."
        if tag:
            lines.append(f"{label} {tag} {definition}")
        else:
            lines.append(f"{label} {definition}")
    return LINE_BREAK.join(lines)


def format_multi_meaning(selected_senses: List[Dict[str, Any]], format_type: str = "pipe_merged") -> str:
    """Format meanings from selected senses (pipe_merged/numbered/semicolon_merged)."""
    defs = []
    for sense in selected_senses:
        sense_meanings = "; ".join(sense.get("english_definitions", []))
        if sense_meanings:
            defs.append(sense_meanings)

    if format_type == "numbered":
        return _format_numbered_lines(defs)
    return _merge_definitions(defs, format_type)


def format_multi_word_entries(entries: List[Dict[str, Any]], multi_word_format: str, multi_meaning_format: str) -> str:
    """Format multiple word entries based on multi-word and multi-meaning formats."""
    if not entries:
        return ""

    if multi_word_format == "inline":
        inline_items = []
        for entry in entries:
            merged = _merge_definitions(entry["defs"], multi_meaning_format)
            if merged:
                inline_items.append(merged)
        return " ".join(inline_items)

    blocks = []
    if multi_meaning_format == "numbered":
        for word_idx, entry in enumerate(entries, start=1):
            defs = entry["defs"]
            headword = entry["headword"]
            tag = f"[{headword}]" if headword else ""

            if multi_word_format == "tagged":
                block = _format_numbered_lines(defs, tag=tag)
            elif multi_word_format == "numbered":
                block = _format_numbered_lines(defs, number_prefix=f"{word_idx}.")
            elif multi_word_format == "tagged_numbered":
                block = _format_numbered_lines(defs, number_prefix=f"{word_idx}.", tag=tag)
            else:
                block = _format_numbered_lines(defs)

            if block:
                blocks.append(block)
        return BLOCK_SEPARATOR.join(blocks)

    for word_idx, entry in enumerate(entries, start=1):
        merged = _merge_definitions(entry["defs"], multi_meaning_format)
        if not merged:
            continue
        headword = entry["headword"]
        tag = f"[{headword}]" if headword else ""

        if multi_word_format == "tagged":
            block = f"{tag} {merged}".strip() if tag else merged
        elif multi_word_format == "numbered":
            block = f"{word_idx}. {merged}"
        elif multi_word_format == "tagged_numbered":
            block = f"{word_idx}. {tag} {merged}".strip()
        else:
            block = merged

        blocks.append(block)
    return BLOCK_SEPARATOR.join(blocks)



def apply_mappings_and_fill(note, entries_data, config: Dict[str, Any]):
    """Apply field mappings and fill note from multiple entries."""
    mappings = config.get("mappings", [])
    if isinstance(mappings, dict):
        mappings = [{"jisho": jisho, "field": field} for field, jisho in mappings.items()]
    elif not isinstance(mappings, list):
        mappings = []
    fill_mode = config.get("fill_mode", "replace")
    is_multi_word = len(entries_data) > 1
    multi_meaning_format = config.get("multi_meaning_format", "pipe_merged")

    def set_field(field_name: str, value: str):
        """Set field with append/replace mode handling."""
        if not value or field_name not in note:
            return
        current_content = note[field_name]
        if fill_mode == 'append' and current_content and value not in current_content:
            note[field_name] += ("" if current_content.endswith(' ') else " ") + value
        else:
            note[field_name] = value

    field_values = {}

    if fill_mode == 'replace':
        for mapping in mappings:
            field_name = mapping.get("field", "")
            if field_name and field_name in note:
                note[field_name] = ""

    # Prepare multi-word data if multi-word search
    multi_word_entries = [] if is_multi_word else None
    
    for entry_data_set in entries_data:
        entry = entry_data_set["entry_data"]
        selected_senses = entry_data_set["selected_senses"]
        selected_other_forms = entry_data_set["selected_other_forms"]
        
        first_jap = entry["japanese"][0] if entry.get("japanese") else {}
        headword = first_jap.get("word") or first_jap.get("reading", "")
        for mapping in mappings:
            field_name = mapping.get("field", "")
            map_type = mapping.get("jisho", "")
            if not field_name or not map_type:
                continue

            value = ""
            
            if map_type == "Part of speech":
                remove_ending = config.get("remove_pos_ending", True)
                pos_items = []
                for s in selected_senses:
                    pos_items.extend(s.get("parts_of_speech", []))
                value = "; ".join(clean_part_of_speech(pos_items, remove_ending))
             
            elif map_type == "Meaning":
                format_type = multi_meaning_format if len(selected_senses) > 1 else "pipe_merged"
                value = format_multi_meaning(selected_senses, format_type)
                if is_multi_word:
                    defs = []
                    for sense in selected_senses:
                        sense_meanings = "; ".join(sense.get("english_definitions", []))
                        if sense_meanings:
                            defs.append(sense_meanings)
                    if defs:
                        multi_word_entries.append({"headword": headword, "defs": defs})
                    continue
             
            elif map_type == "Info":
                ordered_info = []
                for s in selected_senses:
                    for info in s.get("info", []):
                        if info not in ordered_info:
                            ordered_info.append(info)
                value = "; ".join(ordered_info)

            elif map_type == "Tags":
                ordered_tags = []
                for s in selected_senses:
                    for tag in s.get("tags", []):
                        if tag not in ordered_tags:
                            ordered_tags.append(tag)
                value = "; ".join(ordered_tags)

            elif map_type == "See also":
                ordered_see_also = []
                for s in selected_senses:
                    for item in s.get("see_also", []):
                        if item not in ordered_see_also:
                            ordered_see_also.append(item)
                value = "; ".join(ordered_see_also)

            elif map_type == "Other forms":
                value = ", ".join(selected_other_forms) if selected_other_forms else ""
            
            elif map_type == "Word":
                value = first_jap.get("word", "")
            
            elif map_type == "Reading":
                value = first_jap.get("reading", "")
            
            elif map_type == "JLPT Level":
                value = ", ".join(entry.get("jlpt", [])) if entry.get("jlpt") else ""
            
            elif map_type == "Wanikani Level":
                value = ", ".join([tag for tag in entry.get("tags", []) if "wanikani" in tag]) if entry.get("tags") else ""
            
            elif map_type in ("Is Common", "Is_Common"):
                value = "common word" if entry.get("is_common") else ""

            if value:
                field_values.setdefault(field_name, []).append(value)

    # Apply multi-word formatting if applicable
    if is_multi_word and multi_word_entries:
        multi_word_format = config.get("multi_word_format", "basic")
        formatted_multi_word = format_multi_word_entries(
            multi_word_entries,
            multi_word_format,
            multi_meaning_format,
        )
        
        for mapping in mappings:
            if mapping.get("jisho") == "Meaning":
                field_name = mapping.get("field", "")
                if field_name:
                    set_field(field_name, formatted_multi_word)
                    if field_name in field_values:
                        del field_values[field_name]
                break

    for field_name, values in field_values.items():
        set_field(field_name, "; ".join(v for v in values if v))

    try:
        if note.id != 0:
            mw.col.update_note(note)
    except Exception as e:
        logger.exception("Error saving note")
        showWarning(f"Error saving note: {str(e)}")

