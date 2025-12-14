"""Extractor for multipart_short_answer questions.

Extracts numbered sub-items (1., 2., ...) with their prompts, expected,
and user answers.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List


def extract_multipart_short_answer(block_text: str) -> Dict[str, Any]:
    """Extract content for a multipart_short_answer question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with key: items (list of MultipartItem objects).
    """
    content: Dict[str, Any] = {
        "items": [],
    }
    
    # Extract numbered items (1., 2., 3., ...)
    item_pattern = re.compile(
        r'^(\d+)\.\s*(.+?)(?=\n\d+\.|\nLa respuesta|\nLas respuestas|\Z)',
        re.MULTILINE | re.DOTALL
    )
    matches = item_pattern.finditer(block_text)
    
    for match in matches:
        index = int(match.group(1))
        item_text = match.group(2).strip()
        
        # Try to extract prompt, expected, and user
        # This is heuristic and may need refinement
        prompt = item_text
        expected = None
        user = None
        
        # Look for "La respuesta correcta es:" within this item
        expected_pattern = re.compile(
            r'La respuesta correcta es:\s*([^\n\.]+)',
            re.IGNORECASE
        )
        expected_match = expected_pattern.search(item_text)
        if expected_match:
            expected = expected_match.group(1).strip()
            # Prompt is everything before "La respuesta correcta es:"
            prompt = item_text[:expected_match.start()].strip()
        
        # Look for labeled subitems (A:, B:, etc.) within this item
        subitems = []
        subitem_pattern = re.compile(r'([A-Za-z])\s*:\s*([^\n]+)', re.IGNORECASE)
        for sub_match in subitem_pattern.finditer(item_text):
            sub_label = sub_match.group(1)
            sub_value = sub_match.group(2).strip()
            subitems.append({
                "label": sub_label,
                "expected": sub_value,  # May need refinement
                "user": None,
            })
        
        content["items"].append({
            "index": index,
            "prompt": prompt,
            "expected": expected,
            "user": user,
            "subitems": subitems,
        })
    
    return content

