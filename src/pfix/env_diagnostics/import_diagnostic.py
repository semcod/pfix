"""
pfix.env_diagnostics.imports — Import and dependency diagnostics.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic
from .imports.checks import (
    check_deprecated_apis,
    check_import_source,
    check_missing_imports,
    check_missing_inits,
    check_shadow_stdlib,
    check_stale_bytecode,
    check_version_conflicts,
)
from .imports.extractor import extract_imports, extract_module_name
from .imports.graph_builder import build_import_graph, create_cycle_result, find_cycle_dfs

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
        results.extend(self._check_missing_inits(project_root))
        results.extend(self._check_deprecated_apis(project_root))
        results.extend(self._check_import_source(project_root))
        return results

    def _check_missing_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for imports that aren't installed."""
        return check_missing_imports(
            project_root,
            self.category,
            self._get_all_project_imports,
        )

    def _check_shadow_stdlib(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for local files shadowing standard-library modules."""
        return check_shadow_stdlib(project_root, self.category)

    def _check_stale_bytecode(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for stale .pyc files."""
        return check_stale_bytecode(project_root, self.category)

    def _check_version_conflicts(self) -> list["DiagnosticResult"]:
        """Check for dependency version conflicts."""
        return check_version_conflicts(self.category)

    def _check_missing_inits(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for missing __init__.py files."""
        return check_missing_inits(project_root, self.category)

    def _check_deprecated_apis(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for deprecated API usage."""
        return check_deprecated_apis(project_root, self.category)

    def _check_import_source(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check that imports resolve from the expected source."""
        return check_import_source(project_root, self.category)

    def _get_all_project_imports(self, project_root: Path) -> set[str]:
        """Collect all imports from Python files in the project."""
        all_imports = set()
        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
                continue
            try:
                imports = extract_imports(pyfile.read_text())
                all_imports.update(imports)
            except Exception:
                pass
        return all_imports

    def _check_circular_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Detect circular import patterns using module dependency graph."""
        results = []
        checked = set()

        module_imports, module_paths = build_import_graph(project_root)

        for module in module_imports:
            if module not in checked:
                cycle = find_cycle_dfs(module, set(), [], module_imports)
                if cycle and len(cycle) > 1:
                    result = create_cycle_result(
                        cycle, module_paths, checked, self.category
                    )
                    if result:
                        results.append(result)

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose import-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, ModuleNotFoundError):
            module = extract_module_name(str(exc))
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
