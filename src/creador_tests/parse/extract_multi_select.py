"""Extractor for multi_select questions.

Extracts options (a., b., c., ...), correct answers, and user answers.
"""

from __future__ import annotations

import re
from typing import Dict, Any


def extract_multi_select(block_text: str) -> Dict[str, Any]:
    """Extract content for a multi_select question.

    Args:
        block_text: The full text of the question block.

    Returns:
        Dict with keys: options, correct, user.
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
        if text:
            content["options"].append({
                "key": key,
                "text": text
            })
    
    # Extract correct answers from "Las respuestas correctas son: ..."
    correct_pattern = re.compile(r'Las respuestas correctas son:\s*([^\.\n]+)', re.IGNORECASE)
    correct_match = correct_pattern.search(block_text)
    if correct_match:
        correct_text = correct_match.group(1)
        # Extract option keys from the text
        correct_keys = re.findall(r'\b([a-eA-E])\b', correct_text, re.IGNORECASE)
        content["correct"] = [k.lower() for k in correct_keys]
    
    # Extract user answers (marked with ☑)
    user_keys = []
    for option in content["options"]:
        key = option["key"]
        # Look for this option key followed by a checkmark
        pattern = re.compile(rf'{key}\.\s*[^\n]*[☑✓✔]', re.IGNORECASE)
        if pattern.search(block_text):
            user_keys.append(key)
    content["user"] = user_keys
    
    return content

