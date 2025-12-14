"""Extractor for external_media_reference questions.

Extracts reference text about external media (videos, etc.).
"""

from __future__ import annotations

from typing import Dict, Any


def extract_external_media_reference(block_text: str) -> Dict[str, Any]:
    """Extract content for an external_media_reference question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with key: reference_text.
    """
    content: Dict[str, Any] = {
        "reference_text": block_text,  # In v1, use the full block text
    }
    
    return content

