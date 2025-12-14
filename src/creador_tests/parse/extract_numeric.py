"""Extractor for numeric questions.

Extracts expected numeric values, user answer, and numeric format info.
"""

from __future__ import annotations

import re
from typing import Dict, Any


def extract_numeric(block_text: str) -> Dict[str, Any]:
    """Extract content for a numeric question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with keys: expected, user, numeric_format.
    """
    content: Dict[str, Any] = {
        "expected": [],
        "user": None,
        "numeric_format": {
            "decimal_separator": ".",
            "round_decimals": None,
            "tolerance": None,
        }
    }
    
    # Extract expected value from "La respuesta correcta es: ..."
    expected_pattern = re.compile(
        r'La respuesta correcta es:\s*([-+]?\d+[.,]?\d*)',
        re.IGNORECASE
    )
    expected_match = expected_pattern.search(block_text)
    if expected_match:
        expected_value = expected_match.group(1)
        content["expected"] = [expected_value]
        # Detect decimal separator
        if ',' in expected_value:
            content["numeric_format"]["decimal_separator"] = ","
        else:
            content["numeric_format"]["decimal_separator"] = "."
    
    # Extract user answer from "Respuesta:" or "Valor:"
    user_pattern = re.compile(
        r'(?:Respuesta|Valor):\s*([-+]?\d+[.,]?\d*)',
        re.IGNORECASE
    )
    user_match = user_pattern.search(block_text)
    if user_match:
        content["user"] = user_match.group(1)
    
    # Try to detect round_decimals and tolerance from the question text
    # This is heuristic and may not always work
    round_pattern = re.compile(r'redondea\s+a\s+(\d+)\s+decimal', re.IGNORECASE)
    round_match = round_pattern.search(block_text)
    if round_match:
        content["numeric_format"]["round_decimals"] = int(round_match.group(1))
    
    tolerance_pattern = re.compile(r'tolerancia\s+de\s+([-+]?\d+[.,]?\d*)', re.IGNORECASE)
    tolerance_match = tolerance_pattern.search(block_text)
    if tolerance_match:
        tolerance_value = tolerance_match.group(1).replace(',', '.')
        try:
            content["numeric_format"]["tolerance"] = float(tolerance_value)
        except ValueError:
            pass
    
    return content

