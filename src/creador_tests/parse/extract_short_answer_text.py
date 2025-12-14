"""Extractor for short_answer_text questions.

Extracts expected text answers and user answer.
"""

from __future__ import annotations

import re
from typing import Dict, Any


def extract_short_answer_text(block_text: str) -> Dict[str, Any]:
    """Extract content for a short_answer_text question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with keys: expected, user.
    """
    content: Dict[str, Any] = {
        "expected": [],
        "user": None,
    }
    
    # Extract expected answer from "La respuesta correcta es: ..."
    expected_pattern = re.compile(
        r'La respuesta correcta es:\s*([^\n\.]+)',
        re.IGNORECASE
    )
    expected_match = expected_pattern.search(block_text)
    if expected_match:
        expected_text = expected_match.group(1).strip()
        # Split by comma if multiple expected answers
        expected_list = [e.strip() for e in expected_text.split(',')]
        content["expected"] = expected_list
    
    # Extract user answer from "Respuesta: ..."
    user_pattern = re.compile(
        r'Respuesta:\s*([^\n\.]+)',
        re.IGNORECASE
    )
    user_match = user_pattern.search(block_text)
    if user_match:
        content["user"] = user_match.group(1).strip()
    
    return content

