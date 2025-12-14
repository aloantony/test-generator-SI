"""Grading information extraction from question blocks.

This module extracts grading-related information from the text of a
question block, including status, scores, penalty rules, and feedback.
The extraction follows the patterns defined in rules/rules-1.0.yaml.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

# Load grading rules from YAML
RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules-1.0.yaml"
with RULES_PATH.open("r", encoding="utf-8") as f:
    _RULES = yaml.safe_load(f)


def extract_grading(block_text: str) -> Dict[str, Any]:
    """Extract grading information from a question block.

    Extracts:
    - status: "Correcta", "Parcialmente correcta", "Incorrecta", or None
    - score_awarded: numeric score obtained (can be negative)
    - score_max: maximum score for the question
    - penalty_rule_text: text about penalty rules if present
    - feedback: feedback text if present

    Args:
        block_text: The full text of the question block.

    Returns:
        A dict with keys: status, score_awarded, score_max, penalty_rule_text, feedback.
        All values can be None if not found.
    """
    grading_config = _RULES.get("grading", {})
    status_markers = grading_config.get("status_markers", {})
    
    # Extract status
    status = None
    for status_type, marker in status_markers.items():
        if marker in block_text:
            if status_type == "correct":
                status = "Correcta"
            elif status_type == "partial":
                status = "Parcialmente correcta"
            elif status_type == "incorrect":
                status = "Incorrecta"
            break
    
    # Extract score_awarded and score_max
    score_awarded = None
    score_max = None
    score_regex_config = grading_config.get("score_regex", {})
    score_pattern = score_regex_config.get("awarded_max", "")
    if score_pattern:
        # Decode backslash escapes from YAML
        pattern_decoded = score_pattern.encode().decode("unicode_escape")
        match = re.search(pattern_decoded, block_text, re.IGNORECASE)
        if match:
            try:
                # Handle comma or point as decimal separator
                awarded_str = match.group(1).replace(",", ".")
                max_str = match.group(2).replace(",", ".")
                score_awarded = float(awarded_str)
                score_max = float(max_str)
            except (IndexError, ValueError):
                pass
    
    # Extract penalty_rule_text
    penalty_rule_text = None
    penalty_patterns = grading_config.get("penalty_text_regex", [])
    for pattern in penalty_patterns:
        # Decode escapes if needed
        pattern_decoded = pattern.encode().decode("unicode_escape") if "\\" in pattern else pattern
        match = re.search(pattern_decoded, block_text, re.IGNORECASE)
        if match:
            # Extract the full line containing the penalty text
            lines = block_text.split("\n")
            for line in lines:
                if re.search(pattern_decoded, line, re.IGNORECASE):
                    penalty_rule_text = line.strip()
                    break
            break
    
    # Extract feedback
    # Feedback typically appears after the score line, often starting with "¡Correcto!" or similar
    feedback = None
    feedback_patterns = [
        r"¡Correcto!.*",
        r"¡Incorrecto!.*",
        r"Efectivamente.*",
        r"No existe.*",
    ]
    for pattern in feedback_patterns:
        match = re.search(pattern, block_text, re.IGNORECASE | re.DOTALL)
        if match:
            feedback_text = match.group(0).strip()
            # Limit feedback length to avoid capturing too much
            if len(feedback_text) < 500:  # Reasonable limit
                feedback = feedback_text
                break
    
    return {
        "status": status,
        "score_awarded": score_awarded,
        "score_max": score_max,
        "penalty_rule_text": penalty_rule_text,
        "feedback": feedback,
    }

