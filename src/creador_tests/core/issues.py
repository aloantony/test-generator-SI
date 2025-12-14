"""Definitions of issue codes and helper functions.

This module centralizes the list of issue codes used by the parser to
report anomalies or edge cases encountered during processing. Having
the codes defined in one place makes it easier to maintain
consistency between the rules (defined in ``rules-1.0.yaml``) and the
runtime parser logic.
"""

from enum import Enum


class IssueCode(str, Enum):
    OPTIONS_MISSING_TEXT = "OPTIONS_MISSING_TEXT"
    MATH_TEXT_LOSS = "MATH_TEXT_LOSS"
    TABLE_STRUCTURE_LOST = "TABLE_STRUCTURE_LOST"
    NO_CORRECT_ANSWER_FOUND = "NO_CORRECT_ANSWER_FOUND"
    USER_ANSWER_NOT_FOUND = "USER_ANSWER_NOT_FOUND"
    EXTERNAL_MEDIA_REQUIRED = "EXTERNAL_MEDIA_REQUIRED"
    PARTIAL_SCORING_DETECTED = "PARTIAL_SCORING_DETECTED"


def create_issue(code: IssueCode, where: str, msg: str, level: str = "warn") -> dict:
    """Factory to create issue dicts.

    Args:
        code: Enumerated issue code.
        where: Identifier of the element where the issue occurred.
        msg: Human readable description of the issue.
        level: Severity level (info/warn/error).

    Returns:
        A dict representing the issue.
    """
    return {
        "level": level,
        "code": code.value,
        "where": where,
        "msg": msg,
    }