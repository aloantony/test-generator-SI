"""Tests for HTML rendering functionality."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

from creador_tests.renderers import ubuvirtual


@pytest.fixture
def sample_exam_doc():
    """Sample exam document for testing."""
    return {
        "schema_version": "1.0",
        "source": {
            "file_name": "Test_Exam.pdf",
            "doc_type": "moodle_attempt_review",
            "page_count": 5
        },
        "questions": [
            {
                "id": "Q1",
                "number": 1,
                "kind": "single_choice",
                "stem": {
                    "text": "What is 2+2?",
                    "assets": []
                },
                "grading": {
                    "status": "Correcta",
                    "score_awarded": 1.0,
                    "score_max": 1.0,
                    "penalty_rule_text": None,
                    "feedback": None
                },
                "content": {
                    "options": ["3", "4", "5"],
                    "correct": [1],
                    "user": [1]
                },
                "raw": {
                    "block_text": "What is 2+2?",
                    "pages": [0]
                },
                "flags": {
                    "asset_required": False,
                    "math_or_symbols_risky": False,
                    "requires_external_media": False
                },
                "issues": []
            },
            {
                "id": "Q2",
                "number": 2,
                "kind": "short_answer_text",
                "stem": {
                    "text": "Name a programming language.",
                    "assets": []
                },
                "grading": {
                    "status": "Correcta",
                    "score_awarded": 1.0,
                    "score_max": 1.0,
                    "penalty_rule_text": None,
                    "feedback": "Good answer!"
                },
                "content": {
                    "expected": ["Python", "Java", "C++"],
                    "user": "Python"
                },
                "raw": {
                    "block_text": "Name a programming language.",
                    "pages": [1]
                },
                "flags": {
                    "asset_required": False,
                    "math_or_symbols_risky": False,
                    "requires_external_media": False
                },
                "issues": []
            }
        ],
        "issues": []
    }


def test_build_exam_context(sample_exam_doc):
    """Test building exam context from JSON document."""
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    
    assert "title" in context
    assert context["title"] == "Test_Exam"
    assert "questions" in context
    assert len(context["questions"]) == 2
    assert "debug_stub" in context["questions"][0]
    assert isinstance(context["questions"][0]["debug_stub"], str)


def test_render_question_stub_single_choice(sample_exam_doc):
    """Test rendering a single choice question."""
    q = sample_exam_doc["questions"][0]
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="que multichoice' in html
    assert 'Pregunta <span class="qno">1</span>' in html
    assert 'Correcta' in html
    assert 'Se puntúa 1.0 sobre 1.0' in html or 'Se puntúa 1,0 sobre 1,0' in html
    assert 'What is 2+2?' in html
    assert 'input type="radio"' in html


def test_render_question_stub_short_answer(sample_exam_doc):
    """Test rendering a short answer question."""
    q = sample_exam_doc["questions"][1]
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="que shortanswer' in html
    assert 'Pregunta <span class="qno">2</span>' in html
    assert 'Name a programming language.' in html
    assert 'input type="text"' in html


def test_render_question_stub_with_assets():
    """Test rendering a question with assets."""
    q = {
        "id": "Q1",
        "number": 1,
        "kind": "short_answer_text",
        "stem": {
            "text": "Question with image",
            "assets": ["/path/to/image1.png", "/path/to/image2.jpg"]
        },
        "grading": None,
        "content": {},
        "flags": {
            "asset_required": True,
            "math_or_symbols_risky": False,
            "requires_external_media": False
        }
    }
    
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="question-assets"' in html
    assert 'image1.png' in html
    assert 'image2.jpg' in html
    assert './assets/' in html


def test_render_question_stub_multi_select():
    """Test rendering a multi-select question."""
    q = {
        "id": "Q1",
        "number": 1,
        "kind": "multi_select",
        "stem": {"text": "Select all that apply", "assets": []},
        "grading": {"status": "Parcialmente correcta"},
        "content": {
            "options": ["Option A", "Option B", "Option C"],
            "correct": [0, 2],
            "user": [0, 1]
        },
        "flags": {"asset_required": False}
    }
    
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="que multichoice' in html
    assert 'input type="checkbox"' in html
    assert 'Option A' in html
    assert 'Option B' in html
    assert 'Option C' in html


def test_render_question_stub_matching():
    """Test rendering a matching question."""
    q = {
        "id": "Q1",
        "number": 1,
        "kind": "matching",
        "stem": {"text": "Match the items", "assets": []},
        "grading": None,
        "content": {
            "prompts": ["Prompt 1", "Prompt 2"],
            "responses": ["Response A", "Response B"],
            "pairs_correct": [[0, 0], [1, 1]],
            "pairs_user": [[0, 0], [1, 0]]
        },
        "flags": {"asset_required": False}
    }
    
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="que match' in html
    assert 'table' in html
    assert 'Prompt 1' in html
    assert 'Response A' in html


def test_render_question_stub_numeric():
    """Test rendering a numeric question."""
    q = {
        "id": "Q1",
        "number": 1,
        "kind": "numeric",
        "stem": {"text": "What is 5+3?", "assets": []},
        "grading": None,
        "content": {
            "expected": 8,
            "user": 8
        },
        "flags": {"asset_required": False}
    }
    
    html = ubuvirtual.render_question_stub(q)
    
    assert 'class="que numerical' in html
    assert 'input type="text"' in html
    assert 'value="8"' in html


@pytest.mark.skipif(not HAS_BS4, reason="beautifulsoup4 not installed")
def test_html_contains_title(sample_exam_doc, tmp_path):
    """Test that rendered HTML contains the exam title."""
    from jinja2 import Environment, FileSystemLoader
    
    # Create a minimal template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test.html"
    template_file.write_text("""<!DOCTYPE html>
<html>
<head><title>{{ exam.title }}</title></head>
<body>
    <h1>{{ exam.title }}</h1>
    {% for q in exam.questions %}
    {{ q.debug_stub|safe }}
    {% endfor %}
</body>
</html>""")
    
    # Build context and render
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("test.html")
    html_output = template.render(exam=context)
    
    # Parse and check
    soup = BeautifulSoup(html_output, "html.parser")
    h1 = soup.find("h1")
    assert h1 is not None
    assert "Test_Exam" in h1.get_text()


@pytest.mark.skipif(not HAS_BS4, reason="beautifulsoup4 not installed")
def test_html_question_count(sample_exam_doc, tmp_path):
    """Test that HTML contains correct number of question blocks."""
    from jinja2 import Environment, FileSystemLoader
    
    # Create a minimal template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test.html"
    template_file.write_text("""<!DOCTYPE html>
<html>
<body>
    {% for q in exam.questions %}
    {{ q.debug_stub|safe }}
    {% endfor %}
</body>
</html>""")
    
    # Build context and render
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("test.html")
    html_output = template.render(exam=context)
    
    # Parse and check
    soup = BeautifulSoup(html_output, "html.parser")
    question_divs = soup.find_all("div", class_=re.compile(r"que\s+\w+"))
    assert len(question_divs) == 2


def test_html_no_sensitive_data(sample_exam_doc, tmp_path):
    """Test that HTML does not contain sensitive Moodle data."""
    from jinja2 import Environment, FileSystemLoader
    
    # Create a minimal template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test.html"
    template_file.write_text("""<!DOCTYPE html>
<html>
<body>
    {% for q in exam.questions %}
    {{ q.debug_stub|safe }}
    {% endfor %}
</body>
</html>""")
    
    # Build context and render
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("test.html")
    html_output = template.render(exam=context)
    
    # Check for absence of sensitive strings
    assert "sesskey" not in html_output.lower()
    assert "logout.php" not in html_output.lower()
    assert "usted se ha identificado" not in html_output.lower()
    assert "you have been identified" not in html_output.lower()


def test_html_deterministic(sample_exam_doc, tmp_path):
    """Test that rendering is deterministic (same input = same output)."""
    from jinja2 import Environment, FileSystemLoader
    
    # Create a minimal template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test.html"
    template_file.write_text("""<!DOCTYPE html>
<html>
<body>
    <h1>{{ exam.title }}</h1>
    {% for q in exam.questions %}
    {{ q.debug_stub|safe }}
    {% endfor %}
</body>
</html>""")
    
    # Build context
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("test.html")
    
    # Render twice
    html1 = template.render(exam=context)
    html2 = template.render(exam=context)
    
    # Should be identical
    assert html1 == html2


def test_html_snapshot_normalized(sample_exam_doc, tmp_path):
    """Test HTML output with normalized whitespace (lightweight snapshot test)."""
    from jinja2 import Environment, FileSystemLoader
    
    # Create a minimal template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test.html"
    template_file.write_text("""<!DOCTYPE html>
<html>
<body>
    <h1>{{ exam.title }}</h1>
    {% for q in exam.questions %}
    {{ q.debug_stub|safe }}
    {% endfor %}
</body>
</html>""")
    
    # Build context and render
    context = ubuvirtual.build_exam_context(sample_exam_doc)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("test.html")
    html_output = template.render(exam=context)
    
    # Normalize whitespace (collapse multiple spaces/newlines)
    normalized = re.sub(r'\s+', ' ', html_output).strip()
    
    # Basic structural checks
    assert "<h1>" in normalized
    assert "Test_Exam" in normalized
    assert 'class="que' in normalized
    assert "Pregunta" in normalized
    assert len([m for m in re.finditer(r'class="que\s+\w+', normalized)]) == 2

