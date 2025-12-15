#!/usr/bin/env python3
"""
generate_exam.py
=================

This script automates the conversion of a Moodle/UBUVirtual exam review PDF
into a structured JSON file and an HTML file. It wraps the `creador-tests`
command-line interface and copies any required assets for the rendered HTML.

Usage:

    python generate_exam.py <path-to-pdf> [--output-dir OUTPUT_DIR]

The default output directory is `dist/<basename-of-pdf>`.

The script assumes:
    - You have installed the `creador-tests` package and its CLI (`creador-tests`) is on your PATH.
    - You are running the script from within the repository root (where `schemas/` and `templates/` exist).
    - The template lives under `templates/ubuvirtual_review/` and contains `base.jinja.html` and an `assets/` subfolder.

Steps performed:
    1. Parse the PDF into JSON using `creador-tests parse`.
    2. Validate the JSON against the exam_doc schema using `creador-tests validate`.
    3. Render the HTML using `creador-tests render-html`.
    4. Copy the static assets from the template into the output directory.

If any step fails, the script will exit with a non-zero status.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    """Run a command and raise an exception if it fails."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JSON and HTML from a Moodle exam PDF.")
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Optional output directory. Defaults to dist/<pdf-base-name>.",
        default=None,
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Determine repository root (directory containing this script)
    repo_root = Path(__file__).resolve().parent

    # Determine output directory
    pdf_basename = pdf_path.stem
    if args.output_dir:
        out_dir = Path(args.output_dir).resolve()
    else:
        out_dir = repo_root / "dist" / pdf_basename

    # Create output directories
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Paths
    json_out = out_dir / f"{pdf_basename}.json"
    html_out = out_dir / f"{pdf_basename}.html"
    schema_path = repo_root / "schemas" / "exam_doc-1.0.schema.json"
    template_path = repo_root / "templates" / "ubuvirtual_review" / "base.jinja.html"
    template_assets_dir = repo_root / "templates" / "ubuvirtual_review" / "assets"

    print(f"[1/4] Parsing {pdf_path} to JSON …")
    run_command([
        "creador-tests",
        "parse",
        "--in",
        str(pdf_path),
        "--out",
        str(json_out),
        "--assets-out",
        str(assets_dir),
    ])

    print(f"[2/4] Validating {json_out} against schema …")
    run_command([
        "creador-tests",
        "validate",
        "--in",
        str(json_out),
        "--schema",
        str(schema_path),
    ])

    print(f"[3/4] Rendering HTML from JSON …")
    run_command([
        "creador-tests",
        "render-html",
        "--in",
        str(json_out),
        "--template",
        str(template_path),
        "--out",
        str(html_out),
    ])

    print(f"[4/4] Copying static assets …")
    if template_assets_dir.exists():
        # Copy the directory contents into assets_dir
        for item in template_assets_dir.iterdir():
            dest = assets_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    print("\nDone! Your output files are located at:")
    print(f"  JSON: {json_out}")
    print(f"  HTML: {html_out}")
    print(f"  Assets directory: {assets_dir}")


if __name__ == "__main__":
    main()