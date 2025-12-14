"""Extractor for single_choice questions.

Extracts options (a., b., c., ...), correct answer, and user answer.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List


def extract_single_choice(block_text: str) -> Dict[str, Any]:
    """Extract content for a single_choice question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with keys: options, correct, user.
        If extraction fails, returns empty dict and issues should be added.
    """
    content: Dict[str, Any] = {
        "options": [],
        "correct": [],
        "user": [],
    }
    
    # Extract options (a., b., c., d., e.)
    option_pattern = re.compile(r'^([a-eA-E])\.\s*(.+?)(?=\n[a-eA-E]\.|\nLa respuesta|\nLas respuestas|\Z)', re.MULTILINE | re.DOTALL)
    matches = option_pattern.finditer(block_text)
    
    for match in matches:
        key = match.group(1).lower()
        text = match.group(2).strip()
        # Remove checkmarks and other markers
        text = re.sub(r'[☑☐✓✗✔]', '', text).strip()
        if text:  # Only add if there's actual text
            content["options"].append({
                "key": key,
                "text": text
            })
    
    # Extract correct answer from "La respuesta correcta es: ..."
    # For single_choice, only one answer is allowed (schema maxItems: 1)
    correct_pattern = re.compile(r'La respuesta correcta es:\s*([a-eA-E])', re.IGNORECASE)
    correct_match = correct_pattern.search(block_text)
    if correct_match:
        correct_key = correct_match.group(1).lower()
        content["correct"] = [correct_key]
    # If we find "Las respuestas correctas son:" instead, this might be misclassified
    # but we'll only take the first one to satisfy schema
    elif "Las respuestas correctas son:" in block_text:
        # This should probably be multi_select, but if we're here, take first
        multi_pattern = re.compile(r'Las respuestas correctas son:\s*([^\.\n]+)', re.IGNORECASE)
        multi_match = multi_pattern.search(block_text)
        if multi_match:
            correct_text = multi_match.group(1)
            correct_keys = re.findall(r'\b([a-eA-E])\b', correct_text, re.IGNORECASE)
            if correct_keys:
                # Schema allows max 1, so take only the first
                content["correct"] = [correct_keys[0].lower()]
    
    # Final safety check: ensure correct has at most 1 element
    if len(content["correct"]) > 1:
        content["correct"] = content["correct"][:1]
    
    # Extract user answer (marked with ☑ or similar, or from "Seleccione una:" context)
    # Look for option keys followed by checkmarks
    user_pattern = re.compile(r'([a-eA-E])\.\s*[^\n]*[☑✓✔]', re.IGNORECASE)
    user_match = user_pattern.search(block_text)
    if user_match:
        user_key = user_match.group(1).lower()
        content["user"] = [user_key]
    
    return content

