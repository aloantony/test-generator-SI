"""Extractor for matching questions.

Extracts pairs of left-right associations from the question text.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List


def extract_matching(block_text: str) -> Dict[str, Any]:
    """Extract content for a matching question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with keys: pairs_user, pairs_correct, domain_hint.
    """
    content: Dict[str, Any] = {
        "pairs_user": [],
        "pairs_correct": [],
        "domain_hint": None,
    }
    
    # Extract correct pairs from "La respuesta correcta es: ..."
    # Pattern: "left → right" or "left -> right", separated by commas
    correct_pattern = re.compile(
        r'La respuesta correcta es:\s*(.+?)(?=\n\n|\n\d{2}/\d{2}/\d{2}|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    correct_match = correct_pattern.search(block_text)
    if correct_match:
        correct_text = correct_match.group(1)
        # Extract pairs with → or ->, handling commas between pairs
        # Pattern: "left → right, left2 → right2" or "left -> right, left2 -> right2"
        # Split by comma first, then extract pairs from each segment
        segments = re.split(r',\s*(?=[^,]+[→-]>)', correct_text)
        for segment in segments:
            # Look for arrow in this segment
            arrow_match = re.search(r'([^→]+?)[→-]>\s*(.+?)$', segment.strip(), re.IGNORECASE)
            if arrow_match:
                left = arrow_match.group(1).strip().strip('"\'«»')
                right = arrow_match.group(2).strip().strip('"\'«»')
                if left and right:
                    content["pairs_correct"].append({
                        "left": left,
                        "right": right
                    })
    
    # Extract user pairs (marked with ☑)
    # In matching questions, user selections are marked with checkmarks
    # Look for patterns like "left\nright ☑" or "left → right ☑"
    lines = block_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for checkmarks
        if '☑' in line or '✓' in line or '✔' in line:
            # Try to find the left part (previous line or same line before checkmark)
            # And right part (current line or next line)
            right_part = line.replace('☑', '').replace('✓', '').replace('✔', '').strip()
            
            # Look backwards for the left part
            if i > 0:
                left_part = lines[i-1].strip()
                # Remove checkmarks from left part too
                left_part = left_part.replace('☑', '').replace('✓', '').replace('✔', '').strip()
                
                # If both parts exist and aren't empty, add as user pair
                if left_part and right_part and len(left_part) > 2 and len(right_part) > 2:
                    # Avoid duplicates
                    pair_exists = any(
                        p.get("left") == left_part and p.get("right") == right_part
                        for p in content["pairs_user"]
                    )
                    if not pair_exists:
                        content["pairs_user"].append({
                            "left": left_part,
                            "right": right_part
                        })
        i += 1
    
    # Try to extract domain_hint from the question text
    # Look for phrases like "Asocia las siguientes X con Y"
    hint_pattern = re.compile(r'Asocia\s+las\s+siguientes\s+(\w+)\s+con', re.IGNORECASE)
    hint_match = hint_pattern.search(block_text)
    if hint_match:
        content["domain_hint"] = hint_match.group(1)
    
    return content

