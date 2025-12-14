"""Flag detection for questions.

Detects asset_required, math_or_symbols_risky, and requires_external_media flags.
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Dict, Any

# Load flags rules from YAML
RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules-1.0.yaml"
with RULES_PATH.open("r", encoding="utf-8") as f:
    _RULES = yaml.safe_load(f)


def detect_flags(block_text: str, content: Dict[str, Any]) -> Dict[str, bool]:
    """Detect flags for a question based on its text and extracted content.

    Args:
        block_text: The full text of the question block.
        content: The extracted content dict (to check for empty options, etc.).

    Returns:
        Dict with keys: asset_required, math_or_symbols_risky, requires_external_media.
    """
    flags_config = _RULES.get("flags", {})
    
    asset_required = False
    math_or_symbols_risky = False
    requires_external_media = False
    
    # Check asset_required
    asset_config = flags_config.get("asset_required", {})
    
    # Check any_contains
    any_contains = asset_config.get("any_contains", [])
    for phrase in any_contains:
        if phrase.lower() in block_text.lower():
            asset_required = True
            break
    
    # Check any_regex
    any_regex = asset_config.get("any_regex", [])
    for pattern in any_regex:
        pattern_decoded = pattern.encode().decode("unicode_escape")
        if re.search(pattern_decoded, block_text, re.IGNORECASE):
            asset_required = True
            break
    
    # Check option_text_minlen (if options exist and are too short)
    option_minlen = asset_config.get("option_text_minlen", 2)
    if "options" in content and isinstance(content["options"], list):
        for option in content["options"]:
            if isinstance(option, dict) and "text" in option:
                if len(option["text"].strip()) < option_minlen:
                    asset_required = True
                    break
    
    # Check math_or_symbols_risky
    math_config = flags_config.get("math_or_symbols_risky", {})
    math_regexes = math_config.get("any_regex", [])
    for pattern in math_regexes:
        pattern_decoded = pattern.encode().decode("unicode_escape")
        if re.search(pattern_decoded, block_text):
            math_or_symbols_risky = True
            break
    
    # Check requires_external_media
    media_config = flags_config.get("requires_external_media", {})
    media_regexes = media_config.get("any_regex", [])
    for pattern in media_regexes:
        pattern_decoded = pattern.encode().decode("unicode_escape")
        if re.search(pattern_decoded, block_text, re.IGNORECASE):
            requires_external_media = True
            break
    
    return {
        "asset_required": asset_required,
        "math_or_symbols_risky": math_or_symbols_risky,
        "requires_external_media": requires_external_media,
    }

