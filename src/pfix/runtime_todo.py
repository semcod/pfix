"""
pfix.runtime_todo — Runtime error capture and TODO.md integration.

Backward compatibility facade. Actual implementation is in pfix.runtime_todo/
"""

from .runtime_todo import (
    ErrorFingerprint,
    TodoFile,
    RuntimeCollector,
    get_collector,
    capture_exception,
)

__all__ = ["ErrorFingerprint", "TodoFile", "RuntimeCollector", "get_collector", "capture_exception"]
