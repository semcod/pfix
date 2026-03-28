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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ErrorContext:
    """Structured error report for LLM consumption."""

    # Error
    exception_type: str = ""
    exception_message: str = ""
    traceback_text: str = ""

    # Source
    source_file: str = ""
    source_code: str = ""
    function_name: str = ""
    function_source: str = ""
    line_number: int = 0
    failing_line: str = ""

    # Environment
    local_vars: dict[str, str] = field(default_factory=dict)
    imports: list[str] = field(default_factory=list)
    python_version: str = ""

    # Project context
    project_deps: list[str] = field(default_factory=list)
    missing_deps: list[str] = field(default_factory=list)

    # Decorator metadata
    hints: dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        parts = [
            "## Error Report",
            f"**Exception**: `{self.exception_type}: {self.exception_message}`",
            f"**File**: `{self.source_file}` line {self.line_number}",
            f"**Function**: `{self.function_name}`",
            "",
            "### Traceback",
            f"```\n{self.traceback_text}\n```",
        ]

        if self.source_code:
            parts += ["", "### Full Source File", f"```python\n{self.source_code}\n```"]

        if self.function_source:
            parts += ["", "### Function Source", f"```python\n{self.function_source}\n```"]

        if self.local_vars:
            parts.append("\n### Local Variables")
            for k, v in list(self.local_vars.items())[:30]:
                parts.append(f"- `{k}` = `{v}`")

        if self.imports:
            parts.append("\n### File Imports")
            for imp in self.imports:
                parts.append(f"- `{imp}`")

        if self.missing_deps:
            parts.append("\n### Missing Dependencies (pipreqs scan)")
            for dep in self.missing_deps:
                parts.append(f"- `{dep}`")

        if self.hints:
            parts.append("\n### Developer Hints (@pfix decorator)")
            for k, v in self.hints.items():
                parts.append(f"- **{k}**: {v}")

        parts.append(f"\n### Python {self.python_version}")
        return "\n".join(parts)


def analyze_exception(
    exc: BaseException,
    func: Optional[Any] = None,
    local_vars: Optional[dict] = None,
    hints: Optional[dict] = None,
) -> ErrorContext:
    """Build ErrorContext from a caught exception."""
    ctx = ErrorContext()
    ctx.exception_type = type(exc).__name__
    ctx.exception_message = str(exc)
    ctx.traceback_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    ctx.python_version = sys.version.split()[0]

    # Walk traceback to innermost user-code frame
    tb = exc.__traceback__
    if tb is not None:
        while tb.tb_next is not None:
            tb = tb.tb_next
        frame = tb.tb_frame
        ctx.line_number = tb.tb_lineno
        ctx.source_file = frame.f_code.co_filename
        ctx.function_name = frame.f_code.co_name  # Get function name from frame
        if local_vars is None:
            local_vars = frame.f_locals
        ctx.local_vars = {
            k: _safe_repr(v) for k, v in (local_vars or {}).items()
            if not k.startswith("__")
        }

    # Function source
    if func is not None:
        try:
            ctx.function_source = inspect.getsource(func)
            ctx.function_name = func.__qualname__
            ctx.source_file = inspect.getfile(func)
        except (OSError, TypeError):
            ctx.function_name = getattr(func, "__name__", "<unknown>")

    # Full file source
    if ctx.source_file and Path(ctx.source_file).is_file():
        try:
            ctx.source_code = Path(ctx.source_file).read_text(encoding="utf-8")
            lines = ctx.source_code.splitlines()
            if 0 < ctx.line_number <= len(lines):
                ctx.failing_line = lines[ctx.line_number - 1]
        except Exception:
            pass

    # Extract imports
    if ctx.source_code:
        ctx.imports = _extract_imports(ctx.source_code)

    # Scan for missing deps via pipreqs
    if ctx.source_file:
        ctx.missing_deps = scan_missing_deps(Path(ctx.source_file).parent)

    ctx.hints = hints or {}
    return ctx


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
