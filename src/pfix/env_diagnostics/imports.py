"""
pfix.env_diagnostics.imports — Import and dependency diagnostics.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ImportDiagnostic(BaseDiagnostic):
    """Diagnose import and dependency problems."""

    category = "import_dependency"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all import/dependency checks."""
        results = []
        results.extend(self._check_missing_imports(project_root))
        results.extend(self._check_circular_imports(project_root))
        results.extend(self._check_shadow_stdlib(project_root))
        results.extend(self._check_stale_bytecode(project_root))
        results.extend(self._check_version_conflicts())
        return results

    def _check_missing_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for imports that aren't installed."""
        from ..types import DiagnosticResult

        results = []

        try:
            # Get all imports from project
            all_imports = set()
            for pyfile in project_root.rglob("*.py"):
                if "__pycache__" in str(pyfile):
                    continue
                try:
                    imports = self._extract_imports(pyfile.read_text())
                    all_imports.update(imports)
                except Exception:
                    pass

            # Check which are installed
            try:
                installed = {
                    pkg.metadata["Name"].lower()
                    for pkg in __import__("importlib.metadata").metadata.distributions()
                }
            except Exception:
                installed = set()

            # Check stdlib
            stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()

            for imp in all_imports:
                top = imp.split(".")[0].lower()
                if top not in installed and top not in stdlib and not top.startswith("_"):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="missing_import",
                        status="error",
                        message=f"Module '{imp}' imported but not installed",
                        details={"module": imp, "top_level": top},
                        suggestion=f"pip install {top}",
                        auto_fixable=True,
                        abs_path=None,
                        line_number=None,
                    ))

        except Exception as e:
            pass

        return results

    def _check_circular_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Detect circular import patterns."""
        from ..types import DiagnosticResult
        results = []
        # Complex analysis - simplified for now
        return results

    def _check_shadow_stdlib(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for local files shadowing stdlib modules."""
        from ..types import DiagnosticResult

        results = []
        stdlib_names = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else {
            "json", "sys", "os", "re", "collections", "typing", "pathlib"
        }

        for pyfile in project_root.rglob("*.py"):
            name = pyfile.stem
            if name in stdlib_names and pyfile.parent == project_root:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="stdlib_shadow",
                    status="warning",
                    message=f"Local file '{name}.py' shadows stdlib module",
                    details={"file": str(pyfile), "stdlib_module": name},
                    suggestion="Rename the file to avoid conflicts",
                    auto_fixable=False,
                    abs_path=str(pyfile),
                    line_number=None,
                ))

        return results

    def _check_stale_bytecode(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for stale .pyc files."""
        from ..types import DiagnosticResult

        results = []
        for pyc in project_root.rglob("*.pyc"):
            py = pyc.with_suffix(".py")
            if py.exists():
                if pyc.stat().st_mtime > py.stat().st_mtime:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="stale_bytecode",
                        status="warning",
                        message=f"Stale .pyc file: {pyc}",
                        details={"pyc_file": str(pyc), "py_file": str(py)},
                        suggestion="Run: find . -name '*.pyc' -delete",
                        auto_fixable=True,
                        abs_path=str(pyc),
                        line_number=None,
                    ))

        return results

    def _check_version_conflicts(self) -> list["DiagnosticResult"]:
        """Check for dependency version conflicts."""
        from ..types import DiagnosticResult
        results = []
        # Complex - requires pip check or similar
        return results

    def _extract_imports(self, source: str) -> set[str]:
        """Extract top-level imports from source."""
        imports = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except SyntaxError:
            pass
        return imports

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose import-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, ModuleNotFoundError):
            module = self._extract_module_name(str(exc))
            return DiagnosticResult(
                category=self.category,
                check_name="missing_module",
                status="error",
                message=f"Module '{module}' not found",
                details={"module": module, "install_cmd": f"pip install {module}"},
                suggestion=f"pip install {module}",
                auto_fixable=True,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, ImportError):
            return DiagnosticResult(
                category=self.category,
                check_name="import_error",
                status="error",
                message=str(exc),
                details={"traceback": ctx.traceback_text[:500]},
                suggestion="Check import path and dependencies",
                auto_fixable=False,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None

    def _extract_module_name(self, msg: str) -> str:
        """Extract module name from error message."""
        # "No module named 'pandas'" -> "pandas"
        # Try to find quoted module name first (most reliable)
        match = __import__('re').search(r"['\"]([a-zA-Z_][a-zA-Z0-9_.]*)['\"]", msg)
        if match:
            return match.group(1).split(".")[0]
        # Fallback: try to find first module-like name
        match = __import__('re').search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", msg)
        if match:
            # Filter out common words that aren't modules
            word = match.group(1)
            if word.lower() not in ('no', 'named', 'module', 'the', 'a', 'an'):
                return word
        return "unknown"
