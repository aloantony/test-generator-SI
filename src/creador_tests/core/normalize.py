"""Utilities for normalizing extracted text.

PDF extraction often yields text with inconsistent whitespace,
unexpected line breaks or unicode anomalies. Normalization provides a
clean input for downstream rules and heuristics. The functions here
should be deterministic: given the same input string, they must
always produce the same output.
"""

import re

def normalize_text(text: str) -> str:
    """Normalize extracted text for parsing.

    This function performs simple normalization steps:
    - Replace non-breaking spaces with regular spaces.
    - Collapse runs of whitespace into a single space.
    - Strip leading/trailing whitespace on each line.
    - Ensure consistent line breaks (``\n``).

    Args:
        text: Raw text extracted from PDF.

    Returns:
        Normalized text.
    """
    # Replace non-breaking spaces with regular spaces
    text = text.replace("\u00a0", " ")
    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    # Collapse runs of whitespace to a single space within each line
    lines = [re.sub(r"\s+", " ", line) for line in lines]
    # Filter out empty lines while preserving order
    normalized = "\n".join([ln for ln in lines if ln])
    return normalized