"""Utilities for determining question types based on textual cues.

This module reads the typing rules from the YAML file in ``rules/``
and applies them to blocks of text extracted from PDF pages. The
highest-priority detector whose conditions match is selected and its
associated ``kind`` returned. If no detector matches, a default
``unknown`` kind is returned.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Load the rules file once at module import. Fail fast if not present.
# Determine the project root by ascending three directories from this file:
# parse/typify.py -> parse -> creador_tests -> src -> project root (creador-de-tests)
RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules-1.0.yaml"
with RULES_PATH.open("r", encoding="utf-8") as f:
    _RULES = yaml.safe_load(f)


def _match_condition(text: str, condition: Dict[str, Any]) -> bool:
    """Evaluate a single condition against ``text``.

    Supported condition keys:
    - ``contains``: substring must appear in text (case-sensitive).
    - ``regex``: regular expression must match somewhere in text.
    - ``regex_repeated``: pattern must match at least ``min_count`` times across lines.
    - ``any``: list of conditions, at least one must be True.
    - ``all``: list of conditions, all must be True.

    Args:
        text: Block of text to test.
        condition: Dict describing the condition.

    Returns:
        True if the condition matches, False otherwise.
    """
    if "contains" in condition:
        return condition["contains"] in text
    if "regex" in condition:
        pattern = condition["regex"]
        # Decode backslash escapes from YAML (e.g. "\\s" -> "\s")
        pattern_decoded = pattern.encode().decode("unicode_escape")
        return re.search(pattern_decoded, text) is not None
    if "regex_repeated" in condition:
        spec = condition["regex_repeated"]
        pattern = spec["pattern"]
        # Decode escapes
        pattern_decoded = pattern.encode().decode("unicode_escape")
        min_count = spec.get("min_count", 1)
        count = len(re.findall(pattern_decoded, text, flags=re.MULTILINE))
        return count >= min_count
    if "any" in condition:
        subconds = condition["any"]
        return any(_match_condition(text, sc) for sc in subconds)
    if "all" in condition:
        subconds = condition["all"]
        return all(_match_condition(text, sc) for sc in subconds)
    # Unknown condition type
    return False


def detect_kind(text: str) -> str:
    """Return the first matching ``kind`` based on typing detectors.

    The detectors are defined in the rules YAML file under
    ``typing.detectors``. They are processed in descending order of
    ``priority``; the first detector whose conditions all match
    determines the ``kind``. If none match, ``unknown`` is returned.

    Args:
        text: Normalized block of text representing a question.

    Returns:
        Detected kind string.
    """
    detectors: List[Dict[str, Any]] = _RULES.get("typing", {}).get("detectors", [])
    # Sort detectors by priority descending; missing priority defaults to 0
    detectors_sorted = sorted(detectors, key=lambda d: d.get("priority", 0), reverse=True)
    for det in detectors_sorted:
        conditions: List[Dict[str, Any]] = det.get("when", [])
        if all(_match_condition(text, cond) for cond in conditions):
            return det.get("kind", "unknown")
    return "unknown"