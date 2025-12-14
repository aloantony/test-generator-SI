"""Golden tests for question count and kind detection.

Tests that the parser correctly identifies the number of questions
and the kind of anchor questions in C1-C8 PDFs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from creador_tests.cli import _parse_pdf


# Expected question counts for each PDF
EXPECTED_COUNTS = {
    "C1": 12,
    "C2": None,  # Will be determined from actual PDFs
    "C3": None,
    "C4": None,
    "C5": None,
    "C6": None,
    "C7": None,
    "C8": None,
}

# Expected kinds for anchor questions (first question of each type)
# Format: {pdf_name: {question_number: expected_kind}}
EXPECTED_KINDS = {
    "C1": {
        2: "matching",  # Q2 is matching
        5: "matching",  # Q5 is matching
        8: "matching",  # Q8 is matching
        11: "matching",  # Q11 is matching
    },
}


@pytest.mark.parametrize("pdf_name", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
def test_question_count(pdf_name: str, tmp_path: Path):
    """Test that the correct number of questions is extracted."""
    project_root = Path(__file__).resolve().parents[1]
    fixtures_dir = project_root / "fixtures"
    
    # Find PDF file
    pdf_files = list(fixtures_dir.glob(f"{pdf_name}*.pdf"))
    if not pdf_files:
        pytest.skip(f"No PDF found for {pdf_name}")
    
    pdf_path = pdf_files[0]
    assets_out = tmp_path / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    
    result = _parse_pdf(pdf_path, assets_out)
    questions = result["questions"]
    
    # Check that we have questions
    assert len(questions) > 0, f"{pdf_name} should have at least one question"
    
    # Check expected count if known
    expected_count = EXPECTED_COUNTS.get(pdf_name)
    if expected_count is not None:
        assert len(questions) == expected_count, \
            f"{pdf_name} should have {expected_count} questions, got {len(questions)}"


@pytest.mark.parametrize("pdf_name,question_num,expected_kind", [
    ("C1", 2, "matching"),
    ("C1", 5, "matching"),
    ("C1", 8, "matching"),
    ("C1", 11, "matching"),
])
def test_question_kind(pdf_name: str, question_num: int, expected_kind: str, tmp_path: Path):
    """Test that anchor questions have the correct kind."""
    project_root = Path(__file__).resolve().parents[1]
    fixtures_dir = project_root / "fixtures"
    
    # Find PDF file
    pdf_files = list(fixtures_dir.glob(f"{pdf_name}*.pdf"))
    if not pdf_files:
        pytest.skip(f"No PDF found for {pdf_name}")
    
    pdf_path = pdf_files[0]
    assets_out = tmp_path / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    
    result = _parse_pdf(pdf_path, assets_out)
    questions = result["questions"]
    
    # Find question by number
    question = None
    for q in questions:
        if q["number"] == question_num:
            question = q
            break
    
    assert question is not None, f"Question {question_num} not found in {pdf_name}"
    assert question["kind"] == expected_kind, \
        f"Question {question_num} in {pdf_name} should be {expected_kind}, got {question['kind']}"

