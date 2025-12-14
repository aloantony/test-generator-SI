"""Segmentation of normalized text into question blocks.

The segmentation logic searches for markers indicating the start of a
new question. These markers are defined in ``rules-1.0.yaml`` under
``segmentation.primary_markers`` and ``secondary_markers``. Only
primary markers are used for segmentation in v1; secondary markers may
be used in future versions to recover from missing primary markers.

Each block produced includes the question number extracted from the
marker, the text belonging to that question (across multiple pages if
necessary), and the list of page indices where the block appears.
"""

from __future__ import annotations

import re
from typing import List, Dict

import yaml
from pathlib import Path

# Load segmentation rules from YAML
# Determine the project root by ascending three directories from this file:
RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules-1.0.yaml"
with RULES_PATH.open("r", encoding="utf-8") as f:
    _RULES = yaml.safe_load(f)

# Compile primary marker regexes
_PRIMARY_MARKERS = []
for marker in _RULES.get("segmentation", {}).get("primary_markers", []):
    regex = marker.get("regex")
    if regex:
        # Decode backslash escapes from YAML (e.g. "\\s" -> "\s")
        pattern_decoded = regex.encode().decode("unicode_escape")
        _PRIMARY_MARKERS.append(re.compile(pattern_decoded, re.MULTILINE))


def segment_pages(pages: List[str]) -> List[Dict[str, object]]:
    """Segment normalized pages into question blocks.

    Args:
        pages: List of normalized page strings (one per page).

    Returns:
        List of blocks; each block is a dict with keys:
          - ``number``: integer question number
          - ``text``: concatenated text of the question
          - ``pages``: list of page indices where the question appears
    """
    blocks: List[Dict[str, object]] = []
    current_block: Dict[str, object] | None = None
    for page_index, page_text in enumerate(pages):
        lines = page_text.split("\n")
        for line in lines:
            # Check if line matches any primary marker
            match_num = None
            for regex in _PRIMARY_MARKERS:
                m = regex.match(line)
                if m:
                    try:
                        match_num = int(m.group(1))
                    except (IndexError, ValueError):
                        match_num = None
                    break
            if match_num is not None:
                # Start a new block
                if current_block is not None:
                    # Trim trailing whitespace/newlines
                    current_block["text"] = current_block["text"].strip()
                    blocks.append(current_block)
                current_block = {
                    "number": match_num,
                    "text": "",  # to accumulate lines
                    "pages": [page_index],
                }
                # Remove the marker itself from the text to avoid duplication
                continue
            # Append line to current block's text
            if current_block is not None:
                current_block["text"] += (line + "\n")
                # Record page index if not already present
                if current_block["pages"][-1] != page_index:
                    current_block["pages"].append(page_index)
    # Append last block if exists
    if current_block is not None:
        current_block["text"] = current_block["text"].strip()
        blocks.append(current_block)
    return blocks