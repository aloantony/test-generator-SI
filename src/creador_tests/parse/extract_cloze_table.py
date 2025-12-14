"""Extractor for cloze_table questions.

For v1, table extraction is not fully implemented. Returns null table
and relies on assets for visual preservation.
"""

from __future__ import annotations

from typing import Dict, Any


def extract_cloze_table(block_text: str) -> Dict[str, Any]:
    """Extract content for a cloze_table question.

    In v1, table structure extraction is not reliable, so we return
    null and rely on assets to preserve the visual representation.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with key: table (null in v1).
    """
    content: Dict[str, Any] = {
        "table": None,
    }
    
    # In v1, we don't attempt to parse table structure from text
    # The table will be preserved via assets when asset_required=true
    
    return content

