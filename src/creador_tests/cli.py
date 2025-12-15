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
from .validate import schema_validate
from .core.types import ExamDoc
from .renderers import ubuvirtual


def _parse_pdf(in_path: Path, assets_out: Path) -> dict:
    """Parse a single PDF and return its JSON representation.

    This function currently implements a minimal pipeline: it extracts
    text from the PDF using PyMuPDF, normalizes it, segments it into
    question blocks based on markers defined in the rules file, and
    assigns each block a placeholder ``kind``. A full implementation
    should invoke the type-specific extractors to populate the
    ``content`` field of each question. In v1 this is left as an
    exercise for the implementer.

    Args:
        in_path: Path to the input PDF.
        assets_out: Directory where image assets should be written.

    Returns:
        A Python dict compliant with the JSON schema (to the extent
        currently implemented).
    """
    pages = pdf_extract.extract_pdf(str(in_path))
    # Flatten all page texts into a single string with page breaks
    normalized_pages: List[str] = []
    for page in pages:
        text = page["text"]
        normalized_pages.append(normalize.normalize_text(text))

    blocks = pdf_segment.segment_pages(normalized_pages)
    questions: List[dict] = []
    for block in blocks:
        # Determine kind via typify rules
        kind = parse_typify.detect_kind(block["text"])
        question = {
            "id": f"Q{block['number']}",
            "number": block["number"],
            "kind": kind,
            "stem": {
                "text": block["text"],
                "assets": []
            },
            "grading": None,
            "content": {},
            "raw": {
                "block_text": block["text"],
                "pages": block["pages"]
            },
            "flags": {
                "asset_required": False,
                "math_or_symbols_risky": False,
                "requires_external_media": False
            },
            "issues": []
        }
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


def _cmd_render_html(args: argparse.Namespace) -> None:
    """Handler for the ``render-html`` subcommand."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    
    json_path = Path(args.input).resolve()
    template_path = Path(args.template).resolve()
    out_path = Path(args.output).resolve()
    include_solutions = getattr(args, "include_solutions", False)
    
    # Load JSON
    with json_path.open("r", encoding="utf-8") as f:
        exam_doc = json.load(f)
    
    # Build context
    context = ubuvirtual.build_exam_context(exam_doc)
    
    # Setup Jinja2 environment
    template_dir = template_path.parent
    template_name = template_path.name
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(template_name)
    
    # Render
    html_output = template.render(exam=context, include_solutions=include_solutions)
    
    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html_output)
    
    print(f"Rendered HTML to {out_path}")


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

    # Render HTML subcommand
    p_render = subparsers.add_parser("render-html", help="Render JSON to HTML using Jinja2 template")
    p_render.add_argument("--in", dest="input", required=True, help="Input JSON file")
    p_render.add_argument("--template", dest="template", required=True, help="Jinja2 template file")
    p_render.add_argument("--out", dest="output", required=True, help="Output HTML file")
    p_render.add_argument("--include-solutions", dest="include_solutions", action="store_true", 
                         help="Include solution information in output")
    p_render.set_defaults(func=_cmd_render_html)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()