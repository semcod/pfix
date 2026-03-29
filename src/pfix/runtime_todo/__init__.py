from __future__ import annotations

import os
from typing import Optional, Any

from .fingerprint import ErrorFingerprint
from .todo_file import TodoFile
from .collector import RuntimeCollector

__all__ = ["ErrorFingerprint", "TodoFile", "RuntimeCollector", "get_collector", "capture_exception"]


def get_collector(config: Optional[Any] = None) -> Optional[RuntimeCollector]:
    """Get or create RuntimeCollector from config."""
    if config is None:
        from ..config import get_config
        config = get_config()

    # Check if runtime_todo enabled in pyproject.toml
    pyproject = getattr(config, '_pyproject_data', {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})

    if not rt_config.get("enabled", False):
        return None

    todo_file = rt_config.get("todo_file", "TODO.md")
    return RuntimeCollector(
        TodoFile(todo_file),
        enabled=True,
        min_severity=rt_config.get("min_severity", "low"),
        max_entries=rt_config.get("max_entries", 500),
        deduplicate=rt_config.get("deduplicate", True),
        include_local_vars=rt_config.get("include_local_vars", False),
        include_traceback_depth=rt_config.get("include_traceback_depth", 5),
        exclude_exceptions=rt_config.get("exclude_exceptions"),
        exclude_paths=rt_config.get("exclude_paths"),
    )


def capture_exception(exc: BaseException, context: Optional[dict] = None):
    """Capture single exception to TODO.md (convenience function)."""
    from ..config import get_config

    config = get_config()
    pyproject = getattr(config, '_pyproject_data', {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})

    if not rt_config.get("enabled", False):
        return

    todo_file = rt_config.get("todo_file", "TODO.md")
    collector = RuntimeCollector(
        TodoFile(todo_file),
        enabled=True,
        min_severity=rt_config.get("min_severity", "low"),
        max_entries=rt_config.get("max_entries", 500),
    )
    collector.capture(exc, context)
    collector.shutdown()
