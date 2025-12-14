"""Command line interface for creador_tests.

This module exposes a minimal CLI for converting UBUVirtual/Moodle PDF
quiz reviews into the canonical JSON format defined in this project.
The CLI is intentionally simple for v1: it supports parsing a single
PDF, validating a JSON file against the schema, and running a batch
conversion across a directory of PDFs.

Usage examples::

    # Convert a single PDF to JSON with assets stored in ``assets_out``
    python -m creador_tests.cli parse --in input.pdf --out output.json --assets-out assets/

    # Validate an existing JSON file against the schema
    python -m creador_tests.cli validate --in output.json --schema schemas/exam_doc-1.0.schema.json

    # Batch convert all PDFs in a directory
    python -m creador_tests.cli batch --in fixtures/ --out outputs/ --assets-out assets_out/

This CLI is built on ``argparse`` and intentionally avoids third-party
dependencies so that it can run in constrained environments.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List

from .core import normalize
from .pdf import extract as pdf_extract
from .pdf import segment as pdf_segment
from .parse import typify as parse_typify
from .parse import extract as parse_extract
from .parse import grading as parse_grading
from .parse import flags as parse_flags
from .assets import render as assets_render
from .validate import schema_validate
from .core.types import ExamDoc


def _parse_pdf(in_path: Path, assets_out: Path) -> dict:
    """Parse a single PDF and return its JSON representation.

    Implements the full v1 pipeline:
    1. Extract and normalize text from PDF
    2. Segment into question blocks
    3. Detect question kind
    4. Extract content based on kind
    5. Extract grading information
    6. Detect flags
    7. Render assets if required
    8. Build final JSON structure

    Args:
        in_path: Path to the input PDF.
        assets_out: Directory where image assets should be written.

    Returns:
        A Python dict compliant with the JSON schema.
    """
    pages = pdf_extract.extract_pdf(str(in_path))
    # Normalize each page
    normalized_pages: List[str] = []
    for page in pages:
        text = page["text"]
        normalized_pages.append(normalize.normalize_text(text))

    blocks = pdf_segment.segment_pages(normalized_pages)
    questions: List[dict] = []
    for block in blocks:
        block_text = block["text"]
        
        # Determine kind via typify rules
        kind = parse_typify.detect_kind(block_text)
        
        # If kind is unknown, use short_answer_text as fallback (schema doesn't allow "unknown")
        if kind == "unknown":
            kind = "short_answer_text"
        
        # Extract content based on kind
        content = parse_extract.extract_content(kind, block_text)
        
        # If we had to use fallback, add an issue
        issues = []
        if parse_typify.detect_kind(block_text) == "unknown":
            issues.append({
                "level": "warn",
                "code": "NO_CORRECT_ANSWER_FOUND",
                "where": f"Q{block['number']}",
                "msg": "Question type could not be reliably detected, using short_answer_text as fallback"
            })
        
        # Extract grading information
        grading_dict = parse_grading.extract_grading(block_text)
        # Convert to schema format (all fields required, nullable)
        grading = {
            "status": grading_dict.get("status"),
            "score_awarded": grading_dict.get("score_awarded"),
            "score_max": grading_dict.get("score_max"),
            "penalty_rule_text": grading_dict.get("penalty_rule_text"),
            "feedback": grading_dict.get("feedback"),
        }
        
        # Detect flags (needs content to check for empty options)
        flags = parse_flags.detect_flags(block_text, content)
        
        question = {
            "id": f"Q{block['number']}",
            "number": block["number"],
            "kind": kind,
            "stem": {
                "text": block_text,  # Will be updated with assets below
                "assets": []
            },
            "grading": grading,
            "content": content,
            "raw": {
                "block_text": block_text,
                "pages": block["pages"]
            },
            "flags": flags,
            "issues": issues
        }
        
        # Render assets if required
        if flags.get("asset_required", False):
            assets = assets_render.render_assets_for_question(
                in_path, question, assets_out, question["id"]
            )
            question["stem"]["assets"] = assets
        
        questions.append(question)

    exam_doc: dict = {
        "schema_version": "1.0",
        "source": {
            "file_name": in_path.name,
            "doc_type": "moodle_attempt_review",
            "page_count": len(pages)
        },
        "questions": questions,
        "issues": []
    }
    return exam_doc


def _cmd_parse(args: argparse.Namespace) -> None:
    """Handler for the ``parse`` subcommand."""
    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    assets_out = Path(args.assets_out).resolve()
    assets_out.mkdir(parents=True, exist_ok=True)
    result = _parse_pdf(in_path, assets_out)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path}")


def _cmd_validate(args: argparse.Namespace) -> None:
    """Handler for the ``validate`` subcommand."""
    json_path = Path(args.input).resolve()
    schema_path = Path(args.schema).resolve()
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    schema_validate.validate(data, schema_path)
    print(f"{json_path} is valid according to {schema_path}")


def _cmd_batch(args: argparse.Namespace) -> None:
    """Handler for the ``batch`` subcommand."""
    in_dir = Path(args.input).resolve()
    out_dir = Path(args.output).resolve()
    assets_dir = Path(args.assets_out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    for pdf in in_dir.iterdir():
        if pdf.suffix.lower() != ".pdf":
            continue
        json_name = pdf.stem + ".json"
        out_path = out_dir / json_name
        pdf_assets_dir = assets_dir / pdf.stem
        pdf_assets_dir.mkdir(parents=True, exist_ok=True)
        result = _parse_pdf(pdf, pdf_assets_dir)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Processed {pdf} -> {out_path}")


def main(argv: List[str] | None = None) -> None:
    """Entry point for the CLI.

    Args:
        argv: Optional list of arguments. If None, ``sys.argv[1:]`` is used.
    """
    parser = argparse.ArgumentParser(description="Creador de tests CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse subcommand
    p_parse = subparsers.add_parser("parse", help="Convert a PDF into canonical JSON")
    p_parse.add_argument("--in", dest="input", required=True, help="Input PDF file")
    p_parse.add_argument("--out", dest="output", required=True, help="Output JSON file")
    p_parse.add_argument("--assets-out", dest="assets_out", required=True, help="Directory for image assets")
    p_parse.set_defaults(func=_cmd_parse)

    # Validate subcommand
    p_validate = subparsers.add_parser("validate", help="Validate JSON against schema")
    p_validate.add_argument("--in", dest="input", required=True, help="Input JSON file")
    p_validate.add_argument("--schema", dest="schema", required=True, help="JSON schema file")
    p_validate.set_defaults(func=_cmd_validate)

    # Batch subcommand
    p_batch = subparsers.add_parser("batch", help="Convert all PDFs in a directory")
    p_batch.add_argument("--in", dest="input", required=True, help="Input directory with PDFs")
    p_batch.add_argument("--out", dest="output", required=True, help="Output directory for JSON files")
    p_batch.add_argument("--assets-out", dest="assets_out", required=True, help="Directory for assets")
    p_batch.set_defaults(func=_cmd_batch)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()