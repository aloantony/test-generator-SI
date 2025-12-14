"""Complete golden tests: schema validation, determinism, and type counts."""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any

import pytest

from creador_tests.cli import _parse_pdf
from creador_tests.validate import schema_validate


# Expected minimum counts per type for each PDF
# Format: {pdf_name: {kind: min_count}}
# These are minimums based on actual golden files
EXPECTED_MIN_COUNTS = {
    "C1": {
        "matching": 5,
        "short_answer_text": 7,
    },
    "C2": {
        "matching": 1,
        "single_choice": 2,
        "multi_select": 2,
        "numeric": 1,
        "short_answer_text": 2,
    },
    "C3": {
        "multipart_short_answer": 1,
    },
    "C4": {
        "multipart_short_answer": 1,
    },
    "C5": {
        "single_choice": 4,
        "multi_select": 2,
        "matching": 1,
        "cloze_table": 1,
        "multipart_short_answer": 1,
        "short_answer_text": 3,
    },
    "C6": {
        "matching": 3,
        "multi_select": 1,
        "numeric": 1,
        "short_answer_text": 7,  # multipart_short_answer converted to short_answer_text
    },
    "C7": {
        "cloze_labeled_blanks": 2,
        "numeric": 2,
        "short_answer_text": 2,
    },
    "C8": {
        "matching": 5,
        "single_choice": 4,
        "multi_select": 1,  # One was converted to short_answer_text due to missing options
        "short_answer_text": 6,
    },
}


@pytest.mark.parametrize("pdf_name", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
def test_golden_schema_validation(pdf_name: str):
    """Test that each golden JSON file validates against the schema."""
    project_root = Path(__file__).resolve().parents[1]
    golden_json = project_root / "outputs" / f"{pdf_name}.json"
    schema_path = project_root / "schemas" / "exam_doc-1.0.schema.json"
    
    if not golden_json.exists():
        pytest.skip(f"{golden_json} does not exist. Generate it first.")
    
    with golden_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Should not raise
    schema_validate.validate(data, schema_path)


@pytest.mark.parametrize("pdf_name", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
def test_golden_determinism(pdf_name: str, tmp_path: Path):
    """Test that parsing the same PDF twice produces identical results."""
    project_root = Path(__file__).resolve().parents[1]
    fixtures_dir = project_root / "fixtures"
    
    # Find PDF
    pdf_files = list(fixtures_dir.glob(f"{pdf_name}*.pdf"))
    if not pdf_files:
        pytest.skip(f"No PDF found for {pdf_name}")
    
    pdf_path = pdf_files[0]
    assets_out1 = tmp_path / "assets1"
    assets_out2 = tmp_path / "assets2"
    assets_out1.mkdir(parents=True, exist_ok=True)
    assets_out2.mkdir(parents=True, exist_ok=True)
    
    # Parse twice
    result1 = _parse_pdf(pdf_path, assets_out1)
    result2 = _parse_pdf(pdf_path, assets_out2)
    
    # Compare (excluding asset file paths which may differ)
    def normalize_for_comparison(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize document for comparison, removing non-deterministic paths."""
        normalized = json.loads(json.dumps(doc))  # Deep copy
        for q in normalized.get("questions", []):
            # Remove asset file paths (they may have different temp paths)
            for asset in q.get("stem", {}).get("assets", []):
                if "file" in asset:
                    asset["file"] = "<normalized>"
        return normalized
    
    norm1 = normalize_for_comparison(result1)
    norm2 = normalize_for_comparison(result2)
    
    # Should be identical
    assert norm1 == norm2, f"{pdf_name} parsing is not deterministic"


@pytest.mark.parametrize("pdf_name", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
def test_golden_type_counts(pdf_name: str):
    """Test that each golden file has minimum expected counts per question type."""
    project_root = Path(__file__).resolve().parents[1]
    golden_json = project_root / "outputs" / f"{pdf_name}.json"
    
    if not golden_json.exists():
        pytest.skip(f"{golden_json} does not exist. Generate it first.")
    
    with golden_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    
    # Count by kind
    kind_counts = Counter(q.get("kind", "unknown") for q in questions)
    
    # Check minimum counts
    expected_mins = EXPECTED_MIN_COUNTS.get(pdf_name, {})
    for kind, min_count in expected_mins.items():
        actual_count = kind_counts.get(kind, 0)
        assert actual_count >= min_count, \
            f"{pdf_name} should have at least {min_count} questions of kind '{kind}', got {actual_count}"
    
    # All questions should have valid kinds (no "unknown" allowed by schema)
    assert "unknown" not in kind_counts, \
        f"{pdf_name} has {kind_counts.get('unknown', 0)} questions with kind='unknown' (not allowed by schema)"
    
    # Verify total count matches sum of individual counts
    total_from_counts = sum(kind_counts.values())
    assert total_from_counts == len(questions), \
        f"{pdf_name} count mismatch: {total_from_counts} from kind counts vs {len(questions)} total questions"


@pytest.mark.parametrize("pdf_name", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
def test_golden_structure_integrity(pdf_name: str):
    """Test that each golden file has proper structure integrity."""
    project_root = Path(__file__).resolve().parents[1]
    golden_json = project_root / "outputs" / f"{pdf_name}.json"
    
    if not golden_json.exists():
        pytest.skip(f"{golden_json} does not exist. Generate it first.")
    
    with golden_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check required top-level fields
    assert "schema_version" in data
    assert data["schema_version"] == "1.0"
    assert "source" in data
    assert "questions" in data
    assert "issues" in data
    
    # Check source structure
    source = data["source"]
    assert "file_name" in source
    assert "doc_type" in source
    assert source["doc_type"] == "moodle_attempt_review"
    assert "page_count" in source
    assert isinstance(source["page_count"], int)
    assert source["page_count"] > 0
    
    # Check questions structure
    questions = data["questions"]
    assert isinstance(questions, list)
    assert len(questions) > 0
    
    for i, q in enumerate(questions):
        # Required fields
        assert "id" in q, f"Question {i} missing 'id'"
        assert "number" in q, f"Question {i} missing 'number'"
        assert "kind" in q, f"Question {i} missing 'kind'"
        assert "stem" in q, f"Question {i} missing 'stem'"
        assert "grading" in q, f"Question {i} missing 'grading'"
        assert "content" in q, f"Question {i} missing 'content'"
        assert "raw" in q, f"Question {i} missing 'raw'"
        assert "flags" in q, f"Question {i} missing 'flags'"
        assert "issues" in q, f"Question {i} missing 'issues'"
        
        # Grading is nullable but must be present
        assert q["grading"] is None or isinstance(q["grading"], dict)
        
        # Raw must have block_text and pages
        raw = q["raw"]
        assert "block_text" in raw, f"Question {i} raw missing 'block_text'"
        assert "pages" in raw, f"Question {i} raw missing 'pages'"
        assert isinstance(raw["pages"], list)
        assert len(raw["pages"]) > 0
        
        # Flags structure
        flags = q["flags"]
        assert "asset_required" in flags
        assert "math_or_symbols_risky" in flags
        assert "requires_external_media" in flags
        
        # If asset_required, should have assets
        if flags.get("asset_required", False):
            assets = q.get("stem", {}).get("assets", [])
            assert len(assets) > 0, \
                f"Question {q['id']} has asset_required=True but no assets"

