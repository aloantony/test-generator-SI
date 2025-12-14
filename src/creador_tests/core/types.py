"""Data model definitions for the creador_tests project.

These classes mirror the JSON schema defined in
``schemas/exam_doc-1.0.schema.json``. They provide type hints and
convenience constructors for working with parsed exam documents and
their questions. While not strictly required for JSON serialization,
having a structured model simplifies testing and validation in
Python.

Only a subset of fields is implemented in v1. Additional fields may be
added as the parser becomes more sophisticated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Source:
    """Metadata about the source PDF file."""
    file_name: str
    doc_type: str
    page_count: int


@dataclass
class Issue:
    """Represents an issue encountered during parsing."""
    level: str
    code: str
    where: str
    msg: str


@dataclass
class Asset:
    """Represents an external asset (image snippet) associated with a question."""
    type: str  # e.g. "full_page" or "page_clip"
    page: int
    file: str
    bbox: Optional[List[float]] = None


@dataclass
class Stem:
    """Enunciado común para una pregunta, con texto y assets."""
    text: str
    assets: List[Asset] = field(default_factory=list)


@dataclass
class Flags:
    """Boolean flags describing supplemental requirements for a question."""
    asset_required: bool = False
    math_or_symbols_risky: bool = False
    requires_external_media: bool = False


@dataclass
class Grading:
    """Grading information for a question.

    All fields are optional to allow representing unresolved questions (e.g.
    when parsing an exam without correction).
    """
    status: Optional[str] = None
    score_awarded: Optional[float] = None
    score_max: Optional[float] = None
    penalty_rule_text: Optional[str] = None
    feedback: Optional[str] = None


@dataclass
class Raw:
    """Raw text and page indices for a question."""
    block_text: str
    pages: List[int]


@dataclass
class Question:
    """Represents a single question extracted from the PDF."""
    id: str
    number: int
    kind: str
    stem: Stem
    grading: Optional[Grading]
    content: Dict[str, Any] = field(default_factory=dict)
    raw: Raw = field(default_factory=lambda: Raw(block_text="", pages=[]))
    flags: Flags = field(default_factory=Flags)
    issues: List[Issue] = field(default_factory=list)


@dataclass
class ExamDoc:
    """Top-level representation of a parsed exam document."""
    schema_version: str
    source: Source
    questions: List[Question] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
