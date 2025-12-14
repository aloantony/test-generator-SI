"""Asset policy management.

This module defines the policy for when and how to create image assets
from PDF pages. In v1 the policy is simple: if the ``asset_required``
flag is set on a question, the entire page is rendered into an image
asset. Future versions may attempt to clip to the question bounding
box.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

# PyMuPDF import kept inside the function to avoid unnecessary
# dependencies for callers that do not need rendering.

def render_full_pages(pdf_path: Path, pages: List[int], out_dir: Path) -> List[str]:
    """Render specified pages of a PDF as PNG images.

    Args:
        pdf_path: Path to the source PDF.
        pages: List of zero-based page indices to render.
        out_dir: Directory where images should be saved. Must exist.

    Returns:
        List of file paths (relative to ``out_dir``) for the rendered images.
    """
    import fitz  # type: ignore
    out_files: List[str] = []
    with fitz.open(str(pdf_path)) as doc:
        for page_index in pages:
            page = doc.load_page(page_index)
            pix = page.get_pixmap()
            filename = f"page_{page_index}.png"
            out_path = out_dir / filename
            pix.save(str(out_path))
            out_files.append(filename)
    return out_files