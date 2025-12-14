"""PDF extraction utilities.

This module uses PyMuPDF (fitz) to extract the textual content of
PDF pages. The extraction is intentionally minimal for v1: it does
not extract positional information, images or vector graphics. As the
project evolves, functions here may be extended to return blocks
with coordinates or to render page clips for assets.
"""

from __future__ import annotations

import fitz  # type: ignore

from typing import List, Dict


def extract_pdf(path: str) -> List[Dict[str, object]]:
    """Extract plain text from each page of a PDF.

    Args:
        path: Path to the PDF file.

    Returns:
        A list of dicts, one per page, containing:
          - ``page_index``: zero-based index of the page.
          - ``text``: extracted text as a single string.
    """
    pages: List[Dict[str, object]] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")  # simple text extraction
            pages.append({"page_index": i, "text": text})
    return pages