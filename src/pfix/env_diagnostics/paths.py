"""
pfix.env_diagnostics.paths — Path and working directory diagnostics.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class PathDiagnostic(BaseDiagnostic):
    """Diagnose path-related problems."""

    category = "paths"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all path checks."""
        results = []
        results.extend(self._check_sys_path())
        results.extend(self._check_pythonpath())
        results.extend(self._check_cwd_space())
        results.extend(self._check_long_paths(project_root))
        return results

    def _check_sys_path(self) -> list["DiagnosticResult"]:
        """Check sys.path for issues."""
        from ..types import DiagnosticResult

        results = []

        # Check for empty string in sys.path (current dir injection)
        if "" in sys.path:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="empty_sys_path",
                status="warning",
                message="Empty string in sys.path (current directory injection)",
                details={"sys_path": sys.path},
                suggestion="Remove '' from sys.path to avoid import confusion",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        # Check for duplicate entries
        seen = set()
        duplicates = []
        for p in sys.path:
            if p in seen:
                duplicates.append(p)
            seen.add(p)

        if duplicates:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="duplicate_sys_path",
                status="warning",
                message=f"Duplicate entries in sys.path: {duplicates}",
                details={"duplicates": duplicates},
                suggestion="Clean up sys.path initialization",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_pythonpath(self) -> list["DiagnosticResult"]:
        """Check PYTHONPATH environment variable."""
        from ..types import DiagnosticResult

        results = []
        pythonpath = os.environ.get("PYTHONPATH", "")

        if pythonpath:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="pythonpath_set",
                status="warning",
                message=f"PYTHONPATH is set: {pythonpath[:100]}...",
                details={"pythonpath": pythonpath},
                suggestion="PYTHONPATH can cause import confusion - verify it's needed",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_cwd_space(self) -> list["DiagnosticResult"]:
        """Check if CWD has spaces."""
        from ..types import DiagnosticResult

        results = []
        cwd = os.getcwd()

        if " " in cwd:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="cwd_has_spaces",
                status="warning",
                message=f"Current directory contains spaces: {cwd}",
                details={"cwd": cwd},
                suggestion="Some tools have issues with spaces in paths",
                auto_fixable=False,
                abs_path=cwd,
                line_number=None,
            ))

        return results

    def _check_long_paths(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for paths that might be too long on Windows."""
        from ..types import DiagnosticResult

        results = []

        # Windows has ~260 char limit by default
        if sys.platform != "win32":
            return results

        for item in project_root.rglob("*"):
            if len(str(item)) > 200:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="long_path",
                    status="warning",
                    message=f"Very long path ({len(str(item))} chars): {item.name}",
                    details={"path": str(item), "length": len(str(item))},
                    suggestion="Move project to shorter path or enable Windows long paths",
                    auto_fixable=False,
                    abs_path=str(item),
                    line_number=None,
                ))

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose path-related exceptions."""
        return None
