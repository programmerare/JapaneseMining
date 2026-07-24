# -*- coding: utf-8 -*-
"""Text utilities: cleaning, furigana removal, regex helpers."""

import re

def clean_search_term(term: str, remove_furigana: bool = True) -> str:
    """Clean search term by removing furigana and whitespace."""
    if not term:
        return ""
    if remove_furigana:
        term = re.sub(r'\[.*?\]', '', term)
    term = term.replace('&nbsp;', '').replace('\xa0', '')
    return re.sub(r'\s+', '', term)

def clean_part_of_speech(pos_list: list, remove_ending: bool = True) -> list:
    """Clean part of speech by removing 'with x ending' patterns."""
    cleaned_pos = []
    for pos in pos_list:
        if remove_ending:
            pos = re.sub(r" with '.*?' ending", "", pos)
        if pos and pos not in cleaned_pos:
            cleaned_pos.append(pos)
    return cleaned_pos
