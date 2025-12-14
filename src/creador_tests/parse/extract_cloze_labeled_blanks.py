"""Extractor for cloze_labeled_blanks questions.

Extracts labeled blanks (TP:, TN:, a:, b:, etc.) with expected and user values.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List


def extract_cloze_labeled_blanks(block_text: str) -> Dict[str, Any]:
    """Extract content for a cloze_labeled_blanks question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with key: blanks (list of LabeledBlank objects).
    """
    content: Dict[str, Any] = {
        "blanks": [],
    }
    
    # Extract labeled blanks: pattern like "TP:", "TN:", "a:", "b:", etc.
    blank_pattern = re.compile(r'^([A-Za-z]{1,4})\s*:\s*(.+?)(?=\n[A-Za-z]{1,4}\s*:|\nLa respuesta|\Z)', re.MULTILINE | re.DOTALL)
    matches = blank_pattern.finditer(block_text)
    
    blanks_seen = {}
    for match in matches:
        label = match.group(1).strip()
        value_text = match.group(2).strip()
        
        # Remove checkmarks
        value_text = re.sub(r'[☑☐✓✗✔]', '', value_text).strip()
        
        # Try to extract expected and user values
        # This is heuristic - may need refinement based on actual format
        expected = None
        user = None
        
        # Look for patterns like "expected_value ☑" or just the value
        if value_text:
            # If there's a checkmark, it might be the user answer
            if '☑' in match.group(0) or '✓' in match.group(0):
                user = value_text
            else:
                # Could be expected or user, try to infer from context
                expected = value_text
        
        if label not in blanks_seen:
            blanks_seen[label] = {
                "label": label,
                "expected": expected,
                "user": user,
            }
        else:
            # Update if we have more information
            if expected and not blanks_seen[label]["expected"]:
                blanks_seen[label]["expected"] = expected
            if user and not blanks_seen[label]["user"]:
                blanks_seen[label]["user"] = user
    
    # Also try to extract from "La respuesta correcta es:" section
    correct_pattern = re.compile(
        r'La respuesta correcta es:\s*(.+?)(?=\n\n|\n14/12|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    correct_match = correct_pattern.search(block_text)
    if correct_match:
        correct_text = correct_match.group(1)
        # Look for patterns like "TP: value" or "TP → value"
        correct_blank_pattern = re.compile(r'([A-Za-z]{1,4})\s*[:\-→]\s*([^,]+)', re.IGNORECASE)
        for match in correct_blank_pattern.finditer(correct_text):
            label = match.group(1).strip()
            value = match.group(2).strip().strip('"\'«»')
            if label in blanks_seen:
                blanks_seen[label]["expected"] = value
            else:
                blanks_seen[label] = {
                    "label": label,
                    "expected": value,
                    "user": None,
                }
    
    content["blanks"] = list(blanks_seen.values())
    
    return content

