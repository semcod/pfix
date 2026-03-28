"""
pfix.analyzer — Extract structured error context for LLM analysis.

Gathers: traceback, source, local vars, imports, project deps,
pipreqs scan results, and decorator hints.
"""

from __future__ import annotations

import ast
import inspect
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

from .types import ErrorContext


def analyze_exception(
    exc: BaseException,
    func: Optional[Any] = None,
    local_vars: Optional[dict] = None,
    hints: Optional[dict] = None,
) -> ErrorContext:
    """Build ErrorContext from a caught exception."""
    ctx = ErrorContext()
    ctx.hints = hints or {}
    ctx.python_version = sys.version.split()[0]

    # 1. Extract traceback context
    ctx.exception_type, ctx.exception_message, ctx.traceback_text = _extract_exception_info(exc)

    # 2. Extract frame context from traceback
    frame_info = _extract_frame_context(exc, local_vars)
    ctx.source_file = frame_info.get("source_file", "")
    ctx.line_number = frame_info.get("line_number", 0)
    ctx.function_name = frame_info.get("function_name", "")
    ctx.local_vars = frame_info.get("local_vars", {})

    # 3. Extract function source if func provided
    func_info = _extract_function_source(func)
    if func_info["function_source"]:
        ctx.function_source = func_info["function_source"]
        ctx.function_name = func_info.get("function_name", ctx.function_name)
        ctx.source_file = func_info.get("source_file", ctx.source_file)

    # 4. Extract file context
    file_info = _extract_file_context(ctx.source_file, ctx.line_number)
    ctx.source_code = file_info.get("source_code", "")
    ctx.failing_line = file_info.get("failing_line", "")

    # 5. Extract environment
    ctx.imports = _extract_imports(ctx.source_code) if ctx.source_code else []
    ctx.missing_deps = _scan_missing_deps(ctx.source_file) if ctx.source_file else []

    return ctx


def _extract_exception_info(exc: BaseException) -> tuple[str, str, str]:
    """Extract exception type, message, and traceback text."""
    exc_type = type(exc).__name__
    exc_message = str(exc)
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return exc_type, exc_message, tb_text


def _extract_frame_context(
    exc: BaseException,
    local_vars: Optional[dict] = None,
) -> dict:
    """Extract context from innermost traceback frame."""
    result = {
        "source_file": "",
        "line_number": 0,
        "function_name": "",
        "local_vars": {},
    }

    tb = exc.__traceback__
    if tb is None:
        return result

    # Walk to innermost user-code frame
    while tb.tb_next is not None:
        tb = tb.tb_next

    frame = tb.tb_frame
    result["line_number"] = tb.tb_lineno
    result["source_file"] = frame.f_code.co_filename
    result["function_name"] = frame.f_code.co_name

    if local_vars is None:
        local_vars = frame.f_locals

    result["local_vars"] = {
        k: _safe_repr(v) for k, v in (local_vars or {}).items()
        if not k.startswith("__")
    }

    return result


def _extract_function_source(func: Optional[Any]) -> dict:
    """Extract function source code via inspect."""
    result = {
        "function_source": "",
        "function_name": "",
        "source_file": "",
    }

    if func is None:
        return result

    try:
        result["function_source"] = inspect.getsource(func)
        result["function_name"] = func.__qualname__
        result["source_file"] = inspect.getfile(func)
    except (OSError, TypeError):
        result["function_name"] = getattr(func, "__name__", "<unknown>")

    return result


def _extract_file_context(source_file: str, line_number: int) -> dict:
    """Read source file and extract failing line."""
    result = {
        "source_code": "",
        "failing_line": "",
    }

    if not source_file or not Path(source_file).is_file():
        return result

    try:
        result["source_code"] = Path(source_file).read_text(encoding="utf-8")
        lines = result["source_code"].splitlines()
        if 0 < line_number <= len(lines):
            result["failing_line"] = lines[line_number - 1]
    except Exception:
        pass

    return result


def _scan_missing_deps(source_file: str) -> list[str]:
    """Scan for missing deps via pipreqs."""
    if not source_file:
        return []
    try:
        return scan_missing_deps(Path(source_file).parent)
    except Exception:
        return []


def classify_error(ctx: ErrorContext) -> str:
    """Classify error to guide fix strategy."""
    exc = ctx.exception_type
    msg = ctx.exception_message.lower()

    if exc in ("ModuleNotFoundError", "ImportError"):
        return "missing_dependency"
    if exc == "NameError" and "is not defined" in msg:
        return "missing_import"
    if exc == "TypeError":
        return "type_error"
    if exc == "AttributeError":
        return "attribute_error"
    if exc == "SyntaxError":
        return "syntax_error"
    if exc == "IndexError":
        return "index_error"
    if exc == "KeyError":
        return "key_error"
    if exc == "ValueError":
        return "value_error"
    if exc == "FileNotFoundError":
        return "file_not_found"
    if exc == "PermissionError":
        return "permission_error"
    return "other"


def scan_missing_deps(project_dir: Path) -> list[str]:
    """Use pipreqs to detect imports that aren't installed."""
    try:
        from pipreqs import pipreqs
        imports = pipreqs.get_all_imports(str(project_dir))
        pkg_info = pipreqs.get_pkg_names(imports)
        # Compare with installed
        installed = {pkg.key for pkg in __import__("importlib.metadata").metadata.distributions()}
    except Exception:
        installed = set()

    missing = []
    try:
        from pipreqs import pipreqs
        all_imports = pipreqs.get_all_imports(str(project_dir))
        for imp in all_imports:
            top = imp.split(".")[0].lower()
            if top not in installed and top not in sys.stdlib_module_names:
                missing.append(imp)
    except Exception:
        pass

    return missing


def _extract_imports(source: str) -> list[str]:
    imports = []
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(a.name for a in node.names)
                imports.append(f"from {module} import {names}")
    except SyntaxError:
        pass
    return imports


def _safe_repr(obj: Any, max_len: int = 200) -> str:
    try:
        r = repr(obj)
        return r[:max_len] + "..." if len(r) > max_len else r
    except Exception:
        return f"<{type(obj).__name__}: repr failed>"
