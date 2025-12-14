"""Dispatcher for question content extractors.

Routes to the appropriate extractor based on question kind.
"""

from __future__ import annotations

from typing import Dict, Any

from . import (
    extract_single_choice,
    extract_multi_select,
    extract_matching,
    extract_numeric,
    extract_short_answer_text,
    extract_cloze_labeled_blanks,
    extract_cloze_table,
    extract_multipart_short_answer,
    extract_external_media_reference,
    extract_unknown,
)


_EXTRACTORS = {
    "single_choice": extract_single_choice.extract_single_choice,
    "multi_select": extract_multi_select.extract_multi_select,
    "matching": extract_matching.extract_matching,
    "numeric": extract_numeric.extract_numeric,
    "short_answer_text": extract_short_answer_text.extract_short_answer_text,
    "cloze_labeled_blanks": extract_cloze_labeled_blanks.extract_cloze_labeled_blanks,
    "cloze_table": extract_cloze_table.extract_cloze_table,
    "multipart_short_answer": extract_multipart_short_answer.extract_multipart_short_answer,
    "external_media_reference": extract_external_media_reference.extract_external_media_reference,
    "unknown": extract_unknown.extract_unknown,
}


def extract_content(kind: str, block_text: str) -> Dict[str, Any]:
    """Extract content for a question based on its kind.

    Args:
        kind: The question kind (e.g., "single_choice", "matching").
        block_text: The full text of the question block.

    Returns:
        A dict with the extracted content structure for that kind.
    """
    extractor = _EXTRACTORS.get(kind, extract_unknown.extract_unknown)
    return extractor(block_text)

