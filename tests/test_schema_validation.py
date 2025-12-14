"""Tests for schema validation of generated JSON files."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from creador_tests.validate import schema_validate


def test_outputs_tmp_json_validates():
    """Test that outputs/tmp.json validates against the schema."""
    project_root = Path(__file__).resolve().parents[1]
    tmp_json = project_root / "outputs" / "tmp.json"
    schema_path = project_root / "schemas" / "exam_doc-1.0.schema.json"
    
    if not tmp_json.exists():
        pytest.skip(f"{tmp_json} does not exist. Run the parser first to generate it.")
    
    with tmp_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Should not raise
    schema_validate.validate(data, schema_path)

