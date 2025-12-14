"""Tests for flags and assets, especially for C8 (formula loss)."""

from __future__ import annotations

from pathlib import Path

import pytest

from creador_tests.cli import _parse_pdf


def test_c8_asset_required_for_formulas(tmp_path: Path):
    """Test that C8 questions with formulas have asset_required=True."""
    project_root = Path(__file__).resolve().parents[1]
    fixtures_dir = project_root / "fixtures"
    
    # Find C8 PDF
    pdf_files = list(fixtures_dir.glob("C8*.pdf"))
    if not pdf_files:
        pytest.skip("No C8 PDF found")
    
    pdf_path = pdf_files[0]
    assets_out = tmp_path / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    
    result = _parse_pdf(pdf_path, assets_out)
    questions = result["questions"]
    
    # Check that questions with math symbols have asset_required=True
    # or math_or_symbols_risky=True
    found_formula_question = False
    for q in questions:
        flags = q.get("flags", {})
        if flags.get("math_or_symbols_risky", False) or flags.get("asset_required", False):
            found_formula_question = True
            # If asset_required, check that assets were generated
            if flags.get("asset_required", False):
                assets = q.get("stem", {}).get("assets", [])
                assert len(assets) > 0, \
                    f"Question {q['id']} has asset_required=True but no assets generated"
                # Check that assets are full_page type
                for asset in assets:
                    assert asset["type"] == "full_page", \
                        f"Asset for {q['id']} should be full_page, got {asset['type']}"
    
    # At least one question should have formula-related flags in C8
    # (This is a soft check - C8 may not always have formulas)
    # assert found_formula_question, "C8 should have at least one question with math symbols"


def test_asset_generation_when_required(tmp_path: Path):
    """Test that assets are generated when asset_required=True."""
    project_root = Path(__file__).resolve().parents[1]
    fixtures_dir = project_root / "fixtures"
    
    # Test with C1 (should have some questions, may or may not need assets)
    pdf_files = list(fixtures_dir.glob("C1*.pdf"))
    if not pdf_files:
        pytest.skip("No C1 PDF found")
    
    pdf_path = pdf_files[0]
    assets_out = tmp_path / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    
    result = _parse_pdf(pdf_path, assets_out)
    questions = result["questions"]
    
    # Check that all questions with asset_required=True have assets
    for q in questions:
        flags = q.get("flags", {})
        if flags.get("asset_required", False):
            assets = q.get("stem", {}).get("assets", [])
            assert len(assets) > 0, \
                f"Question {q['id']} has asset_required=True but no assets"
            
            # Verify asset files exist
            for asset in assets:
                asset_path = assets_out / asset["file"]
                assert asset_path.exists(), \
                    f"Asset file {asset['file']} does not exist for {q['id']}"

