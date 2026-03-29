"""
pfix.classifiers — Error classification strategies.

Breaks down error classification into focused, testable classifiers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ErrorContext


class ErrorClassifier:
    """Base class for error classification strategies."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        """Return classification label or None if not applicable."""
        raise NotImplementedError


class ImportErrorClassifier(ErrorClassifier):
    """Classify import-related errors."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        if exc_type in ("ModuleNotFoundError", "ImportError"):
            return "missing_dependency"
        if exc_type == "NameError" and "is not defined" in exc_msg.lower():
            return "missing_import"
        return None


class TypeErrorClassifier(ErrorClassifier):
    """Classify type-related errors."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        if exc_type == "TypeError":
            return "type_error"
        if exc_type == "AttributeError":
            return "attribute_error"
        return None


class DataStructureErrorClassifier(ErrorClassifier):
    """Classify data structure access errors."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        if exc_type == "IndexError":
            return "index_error"
        if exc_type == "KeyError":
            return "key_error"
        if exc_type == "ValueError":
            return "value_error"
        return None


class IOErrorClassifier(ErrorClassifier):
    """Classify file/IO related errors."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        if exc_type == "FileNotFoundError":
            return "file_not_found"
        if exc_type == "PermissionError":
            return "permission_error"
        return None


class SyntaxErrorClassifier(ErrorClassifier):
    """Classify syntax errors."""

    def classify(self, exc_type: str, exc_msg: str) -> str | None:
        if exc_type == "SyntaxError":
            return "syntax_error"
        return None


# Registry of classifiers in priority order
_CLASSIFIERS: list[ErrorClassifier] = [
    SyntaxErrorClassifier(),
    ImportErrorClassifier(),
    TypeErrorClassifier(),
    DataStructureErrorClassifier(),
    IOErrorClassifier(),
]


def classify_error(ctx: ErrorContext) -> str:
    """Classify error using registered classifiers.

    Iterates through classifiers in priority order,
    returning the first match or 'other' if none match.
    """
    exc_type = ctx.exception_type
    exc_msg = ctx.exception_message

    for classifier in _CLASSIFIERS:
        result = classifier.classify(exc_type, exc_msg)
        if result:
            return result

    return "other"


def get_error_category(exc_type: str) -> str:
    """Get broad category for an exception type without full context."""
    mapping = {
        "ModuleNotFoundError": "import",
        "ImportError": "import",
        "NameError": "name",
        "TypeError": "type",
        "AttributeError": "attribute",
        "SyntaxError": "syntax",
        "IndexError": "index",
        "KeyError": "key",
        "ValueError": "value",
        "FileNotFoundError": "file",
        "PermissionError": "permission",
        "RuntimeError": "runtime",
        "AssertionError": "assertion",
        "ZeroDivisionError": "math",
        "RecursionError": "recursion",
        "MemoryError": "memory",
        "TimeoutError": "timeout",
        "ConnectionError": "network",
    }
    return mapping.get(exc_type, "other")
