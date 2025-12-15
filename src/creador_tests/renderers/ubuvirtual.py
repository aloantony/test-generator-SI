"""Renderer for UBUVirtual/Moodle-style HTML output.

This module provides functions to convert the canonical JSON format
into HTML that mimics the layout and structure of Moodle quiz review pages.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote


def build_exam_context(exam_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Build the context dictionary for Jinja2 template rendering.
    
    Args:
        exam_doc: The canonical JSON document (parsed from JSON file).
        
    Returns:
        A dictionary with 'title' and 'questions' keys suitable for
        rendering with the base.jinja.html template.
    """
    # Extract title from source file_name, removing extension and cleaning
    file_name = exam_doc.get("source", {}).get("file_name", "Examen")
    # Remove .pdf extension if present
    if file_name.lower().endswith(".pdf"):
        file_name = file_name[:-4]
    # Use file_name as title (could be enhanced to extract from PDF metadata)
    title = file_name
    
    # Build questions list with debug_stub for each question
    questions = []
    for q in exam_doc.get("questions", []):
        questions.append({
            "debug_stub": render_question_stub(q)
        })
    
    return {
        "title": title,
        "questions": questions
    }


def render_question_stub(q: Dict[str, Any]) -> str:
    """Render a single question as HTML stub compatible with Moodle layout.
    
    Args:
        q: A question dictionary from the canonical JSON format.
        
    Returns:
        HTML string containing a <div class="que ..."> block.
    """
    kind = q.get("kind", "short_answer_text")
    number = q.get("number", 0)
    stem_text = q.get("stem", {}).get("text", "")
    grading = q.get("grading", {})
    content = q.get("content", {})
    flags = q.get("flags", {})
    assets = q.get("stem", {}).get("assets", [])
    
    # Map kind to Moodle CSS class
    moodle_class = _kind_to_moodle_class(kind)
    
    # Determine status class from grading
    status = grading.get("status") if grading else None
    status_class = _status_to_class(status)
    
    # Build question div
    question_id = f"question-{q.get('id', f'Q{number}')}"
    classes = f"que {moodle_class} deferredfeedback {status_class}".strip()
    
    html_parts = [f'<div id="{question_id}" class="{classes}">']
    
    # Info section
    html_parts.append('<div class="info">')
    html_parts.append(f'<h3 class="no">Pregunta <span class="qno">{number}</span></h3>')
    if status:
        html_parts.append(f'<div class="state">{html.escape(status)}</div>')
    score_text = _format_score(grading)
    if score_text:
        html_parts.append(f'<div class="grade">{html.escape(score_text)}</div>')
    html_parts.append('</div>')  # .info
    
    # Content section
    html_parts.append('<div class="content">')
    html_parts.append('<div class="formulation clearfix">')
    html_parts.append('<h4 class="accesshide">Enunciado de la pregunta</h4>')
    
    # Question text (stem)
    html_parts.append('<div class="qtext">')
    html_parts.append('<div class="clearfix">')
    # Escape HTML in stem text but preserve line breaks
    stem_html = html.escape(stem_text).replace('\n', '<br>')
    html_parts.append(f'<p>{stem_html}</p>')
    
    # Add assets if required
    if flags.get("asset_required", False) and assets:
        html_parts.append('<div class="question-assets">')
        for asset in assets:
            # Assets can be dicts with 'file' key or strings
            if isinstance(asset, dict):
                asset_file = asset.get("file", "")
            else:
                asset_file = str(asset)
            
            if asset_file:
                # Use relative path from template location
                # Assets should be in templates/ubuvirtual_review/assets/
                asset_rel = f"./assets/{Path(asset_file).name}"
                html_parts.append(f'<img src="{html.escape(asset_rel)}" alt="Question asset" class="img-fluid">')
        html_parts.append('</div>')
    
    html_parts.append('</div>')  # .clearfix
    html_parts.append('</div>')  # .qtext
    
    # Render answer block based on kind
    answer_html = _render_answer_block(kind, content, grading)
    if answer_html:
        html_parts.append(answer_html)
    
    html_parts.append('</div>')  # .formulation
    html_parts.append('</div>')  # .content
    
    # Outcome/feedback section
    feedback_html = _render_feedback(grading)
    if feedback_html:
        html_parts.append(feedback_html)
    
    html_parts.append('</div>')  # .que
    
    return '\n'.join(html_parts)


def _kind_to_moodle_class(kind: str) -> str:
    """Map question kind to Moodle CSS class."""
    mapping = {
        "single_choice": "multichoice",
        "multi_select": "multichoice",
        "matching": "match",
        "numeric": "numerical",
        "short_answer_text": "shortanswer",
        "multipart_short_answer": "shortanswer",
        "cloze_labeled_blanks": "multianswer",
        "cloze_table": "multianswer",
        "external_media_reference": "multianswer",
    }
    return mapping.get(kind, "shortanswer")


def _status_to_class(status: str | None) -> str:
    """Map grading status to CSS class."""
    if not status:
        return ""
    status_lower = status.lower()
    if "correcta" in status_lower or "correct" in status_lower:
        return "correct"
    elif "incorrecta" in status_lower or "incorrect" in status_lower:
        return "incorrect"
    elif "parcial" in status_lower or "partial" in status_lower:
        return "partiallycorrect"
    return ""


def _format_score(grading: Dict[str, Any] | None) -> str:
    """Format score information from grading dict."""
    if not grading:
        return ""
    score_awarded = grading.get("score_awarded")
    score_max = grading.get("score_max")
    if score_awarded is not None and score_max is not None:
        return f"Se puntúa {score_awarded} sobre {score_max}"
    elif score_max is not None:
        return f"Se puntúa sobre {score_max}"
    return ""


def _render_answer_block(kind: str, content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render the answer/options block based on question kind."""
    if kind == "single_choice":
        return _render_single_choice(content, grading)
    elif kind == "multi_select":
        return _render_multi_select(content, grading)
    elif kind == "matching":
        return _render_matching(content, grading)
    elif kind == "numeric":
        return _render_numeric(content, grading)
    elif kind == "short_answer_text":
        return _render_short_answer(content, grading)
    elif kind == "multipart_short_answer":
        return _render_multipart_short_answer(content, grading)
    elif kind in ("cloze_labeled_blanks", "cloze_table"):
        return _render_cloze(content, grading)
    else:
        return _render_short_answer(content, grading)  # fallback


def _render_single_choice(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render single choice (radio buttons) options."""
    options = content.get("options", [])
    correct = content.get("correct", [])
    user = content.get("user", [])
    
    if not options:
        return ""
    
    html_parts = ['<fieldset class="ablock no-overflow visual-scroll-x">']
    html_parts.append('<legend class="prompt h6 fw-normal"><span class="visually-hidden">Seleccione una:</span> Seleccione una:</legend>')
    html_parts.append('<div class="answer">')
    
    for idx, option in enumerate(options):
        option_id = f"q_option_{idx}"
        is_correct = str(idx) in [str(c) for c in correct] if correct else False
        is_user = str(idx) in [str(u) for u in user] if user else False
        
        # Determine CSS classes
        classes = []
        if is_correct:
            classes.append("r1 correct")
        else:
            classes.append("r0")
        
        html_parts.append(f'<div class="{" ".join(classes)}">')
        html_parts.append(f'<input type="radio" name="q_answer" disabled="disabled" value="{idx}" id="{option_id}">')
        html_parts.append(f'<div class="d-flex w-auto" id="{option_id}_label" data-region="answer-label">')
        html_parts.append(f'<span class="answernumber">{chr(97 + idx)}. </span>')  # a, b, c, ...
        html_parts.append(f'<div class="flex-fill ms-1"><p>{html.escape(str(option))}</p></div>')
        html_parts.append('</div>')
        
        # Add icon if correct/incorrect
        if is_user:
            if is_correct:
                html_parts.append('<span class="ms-1"><i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta" role="img" aria-label="Correcta"></i></span>')
            else:
                html_parts.append('<span class="ms-1"><i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta" role="img" aria-label="Incorrecta"></i></span>')
        
        html_parts.append('</div>')
    
    html_parts.append('</div>')  # .answer
    html_parts.append('</fieldset>')
    return '\n'.join(html_parts)


def _render_multi_select(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render multi-select (checkboxes) options."""
    options = content.get("options", [])
    correct = content.get("correct", [])
    user = content.get("user", [])
    
    if not options:
        return ""
    
    html_parts = ['<fieldset class="ablock no-overflow visual-scroll-x">']
    html_parts.append('<legend class="prompt h6 fw-normal"><span class="visually-hidden">Seleccione una o más de una:</span> Seleccione una o más de una:</legend>')
    html_parts.append('<div class="answer">')
    
    for idx, option in enumerate(options):
        option_id = f"q_option_{idx}"
        is_correct = str(idx) in [str(c) for c in correct] if correct else False
        is_user = str(idx) in [str(u) for u in user] if user else False
        
        # Determine CSS classes
        classes = []
        if is_correct:
            classes.append("r1 correct")
        else:
            classes.append("r0")
        if not is_correct and is_user:
            classes.append("incorrect")
        
        html_parts.append(f'<div class="{" ".join(classes)}">')
        html_parts.append(f'<input type="checkbox" name="q_answer_{idx}" disabled="disabled" value="1" id="{option_id}" {"checked" if is_user else ""}>')
        html_parts.append(f'<div class="d-flex w-auto" id="{option_id}_label" data-region="answer-label">')
        html_parts.append(f'<span class="answernumber">{chr(97 + idx)}. </span>')  # a, b, c, ...
        html_parts.append(f'<div class="flex-fill ms-1"><p>{html.escape(str(option))}</p></div>')
        html_parts.append('</div>')
        
        # Add icon if correct/incorrect
        if is_user:
            if is_correct:
                html_parts.append('<span class="ms-1"><i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta" role="img" aria-label="Correcta"></i></span>')
            else:
                html_parts.append('<span class="ms-1"><i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta" role="img" aria-label="Incorrecta"></i></span>')
        
        html_parts.append('</div>')
    
    html_parts.append('</div>')  # .answer
    html_parts.append('</fieldset>')
    return '\n'.join(html_parts)


def _render_matching(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render matching question pairs."""
    prompts = content.get("prompts", [])
    responses = content.get("responses", [])
    pairs_correct = content.get("pairs_correct", [])
    pairs_user = content.get("pairs_user", [])
    
    if not prompts or not responses:
        return ""
    
    html_parts = ['<fieldset class="ablock no-overflow visual-scroll-x">']
    html_parts.append('<legend class="prompt h6 fw-normal"><span class="visually-hidden">Asociar:</span> Asociar:</legend>')
    html_parts.append('<div class="answer">')
    html_parts.append('<table class="flexible table table-striped table-hover generaltable generalbox">')
    html_parts.append('<thead><tr><th>Pregunta</th><th>Respuesta</th></tr></thead>')
    html_parts.append('<tbody>')
    
    for idx, prompt in enumerate(prompts):
        # Find matching response
        user_match = None
        correct_match = None
        
        # Check user pairs
        for pair in pairs_user:
            if isinstance(pair, dict) and pair.get("prompt_index") == idx:
                user_match = pair.get("response_index")
            elif isinstance(pair, (list, tuple)) and len(pair) >= 2 and pair[0] == idx:
                user_match = pair[1]
        
        # Check correct pairs
        for pair in pairs_correct:
            if isinstance(pair, dict) and pair.get("prompt_index") == idx:
                correct_match = pair.get("response_index")
            elif isinstance(pair, (list, tuple)) and len(pair) >= 2 and pair[0] == idx:
                correct_match = pair[1]
        
        is_correct = user_match == correct_match if user_match is not None and correct_match is not None else False
        
        html_parts.append('<tr>')
        html_parts.append(f'<td>{html.escape(str(prompt))}</td>')
        html_parts.append('<td>')
        if user_match is not None and user_match < len(responses):
            response_text = responses[user_match]
            html_parts.append(f'<select disabled="disabled" class="form-select {"correct" if is_correct else "incorrect"}">')
            html_parts.append(f'<option selected>{html.escape(str(response_text))}</option>')
            html_parts.append('</select>')
            if is_correct:
                html_parts.append('<i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta"></i>')
            else:
                html_parts.append('<i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta"></i>')
        else:
            html_parts.append('<select disabled="disabled" class="form-select"><option></option></select>')
        html_parts.append('</td>')
        html_parts.append('</tr>')
    
    html_parts.append('</tbody>')
    html_parts.append('</table>')
    html_parts.append('</div>')  # .answer
    html_parts.append('</fieldset>')
    return '\n'.join(html_parts)


def _render_numeric(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render numeric answer input."""
    expected = content.get("expected")
    user = content.get("user")
    
    html_parts = ['<div class="ablock d-flex flex-wrap align-items-center">']
    html_parts.append('<label>Respuesta: <span class="visually-hidden">Pregunta</span></label>')
    html_parts.append('<span class="answer">')
    
    user_value = str(user) if user is not None else ""
    is_correct = user == expected if user is not None and expected is not None else False
    input_class = "form-control d-inline correct" if is_correct else "form-control d-inline incorrect"
    
    html_parts.append(f'<input type="text" name="q_answer" value="{html.escape(user_value)}" size="30" class="{input_class}" readonly="readonly">')
    
    if is_correct:
        html_parts.append('<i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta" role="img" aria-label="Correcta"></i>')
    elif user is not None:
        html_parts.append('<i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta" role="img" aria-label="Incorrecta"></i>')
    
    html_parts.append('</span>')
    html_parts.append('</div>')
    return '\n'.join(html_parts)


def _render_short_answer(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render short answer text input."""
    expected = content.get("expected", [])
    user = content.get("user")
    
    html_parts = ['<div class="ablock d-flex flex-wrap align-items-center">']
    html_parts.append('<label>Respuesta: <span class="visually-hidden">Pregunta</span></label>')
    html_parts.append('<span class="answer">')
    
    user_value = str(user) if user is not None else ""
    is_correct = user in expected if user is not None and expected else False
    input_class = "form-control d-inline correct" if is_correct else "form-control d-inline"
    
    html_parts.append(f'<input type="text" name="q_answer" value="{html.escape(user_value)}" size="30" class="{input_class}" readonly="readonly">')
    
    if is_correct:
        html_parts.append('<i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta" role="img" aria-label="Correcta"></i>')
    elif user is not None:
        html_parts.append('<i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta" role="img" aria-label="Incorrecta"></i>')
    
    html_parts.append('</span>')
    html_parts.append('</div>')
    return '\n'.join(html_parts)


def _render_multipart_short_answer(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render multipart short answer (multiple text inputs)."""
    items = content.get("items", [])
    
    if not items:
        return ""
    
    html_parts = ['<div class="ablock">']
    
    for item in items:
        index = item.get("index", 0)
        expected = item.get("expected", "")
        user = item.get("user")
        
        html_parts.append(f'<label>Respuesta {index}: <span class="visually-hidden">Pregunta {index}</span></label>')
        html_parts.append('<span class="answer">')
        
        user_value = str(user) if user is not None else ""
        is_correct = user == expected if user is not None and expected else False
        input_class = "form-control d-inline mb-1 correct" if is_correct else "form-control d-inline mb-1 incorrect"
        
        html_parts.append(f'<input type="text" name="q_answer_{index}" value="{html.escape(user_value)}" size="4" class="{input_class}" readonly="readonly">')
        
        if is_correct:
            html_parts.append('<i class="icon fa-regular fa-circle-check text-success fa-fw" title="Correcta" role="img" aria-label="Correcta"></i>')
        elif user is not None:
            html_parts.append('<i class="icon fa-regular fa-circle-xmark text-danger fa-fw" title="Incorrecta" role="img" aria-label="Incorrecta"></i>')
        
        html_parts.append('</span>')
        html_parts.append('<br>')
    
    html_parts.append('</div>')
    return '\n'.join(html_parts)


def _render_cloze(content: Dict[str, Any], grading: Dict[str, Any] | None) -> str:
    """Render cloze question (embedded blanks)."""
    # For cloze questions, render as a simplified version
    # Full cloze rendering would require parsing the stem text for blanks
    html_parts = ['<div class="ablock">']
    html_parts.append('<p class="text-muted">[Pregunta tipo cloze - renderizado simplificado]</p>')
    html_parts.append('</div>')
    return '\n'.join(html_parts)


def _render_feedback(grading: Dict[str, Any] | None) -> str:
    """Render feedback/outcome section."""
    if not grading:
        return ""
    
    feedback = grading.get("feedback")
    status = grading.get("status")
    
    if not feedback and not status:
        return ""
    
    html_parts = ['<div class="outcome clearfix">']
    html_parts.append('<h4 class="accesshide">Retroalimentación</h4>')
    html_parts.append('<div class="feedback">')
    
    if feedback:
        html_parts.append(f'<div class="generalfeedback"><div class="clearfix"><p>{html.escape(str(feedback))}</p></div></div>')
    
    # Show correct answer if available
    html_parts.append('</div>')  # .feedback
    html_parts.append('</div>')  # .outcome
    
    return '\n'.join(html_parts)

