"""Extractor for unknown question types.

Returns empty content dict for questions that couldn't be typed.
"""

from __future__ import annotations

from typing import Dict, Any


def extract_unknown(block_text: str) -> Dict[str, Any]:
    """Extract content for an unknown question type.

    Args:
        block_text: The full text of the question block.

    Returns:
        Empty dict (content will be empty, raw.block_text preserved).
    """
    return {}

