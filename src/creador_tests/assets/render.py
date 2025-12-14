"""Asset rendering for questions.

Renders page images when asset_required flag is set.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from .policy import render_full_pages


def render_assets_for_question(
    pdf_path: Path,
    question: Dict[str, Any],
    assets_out_dir: Path,
    question_id: str,
) -> List[Dict[str, Any]]:
    """Render assets for a question if asset_required is True.

    Args:
        pdf_path: Path to the source PDF.
        question: Question dict with flags and raw.pages.
        assets_out_dir: Directory where assets should be saved.
        question_id: ID of the question (e.g., "Q1") for organizing assets.

    Returns:
        List of Asset dicts to add to stem.assets.
    """
    assets: List[Dict[str, Any]] = []
    
    flags = question.get("flags", {})
    if not flags.get("asset_required", False):
        return assets
    
    raw = question.get("raw", {})
    pages = raw.get("pages", [])
    
    if not pages:
        return assets
    
    # Create subdirectory for this question's assets
    question_assets_dir = assets_out_dir / question_id
    question_assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Render full pages
    rendered_files = render_full_pages(pdf_path, pages, question_assets_dir)
    
    # Create Asset objects
    for page_index, filename in zip(pages, rendered_files):
        assets.append({
            "type": "full_page",
            "page": page_index,
            "bbox": None,
            "file": f"{question_id}/{filename}",
        })
    
    return assets

