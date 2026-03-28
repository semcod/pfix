"""
pfix.env_diagnostics.filesystem — Filesystem diagnostics.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class FilesystemDiagnostic(BaseDiagnostic):
    """Diagnose filesystem-related problems."""

    category = "filesystem"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all filesystem checks."""
        results = []
        results.extend(self._check_disk_space(project_root))
        results.extend(self._check_file_references(project_root))
        results.extend(self._check_symlinks(project_root))
        results.extend(self._check_large_files(project_root))
        results.extend(self._check_writable(project_root))
        return results

    def _check_disk_space(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check available disk space."""
        from ..types import DiagnosticResult

        results = []
        try:
            usage = shutil.disk_usage(project_root)
            free_percent = usage.free / usage.total * 100

            if free_percent < 5:
                status = "critical"
            elif free_percent < 10:
                status = "error"
            elif free_percent < 20:
                status = "warning"
            else:
                return results

            results.append(DiagnosticResult(
                category=self.category,
                check_name="disk_space",
                status=status,
                message=f"Low disk space: {free_percent:.1f}% free ({usage.free // (1024**3)} GB)",
                details={
                    "free_bytes": usage.free,
                    "total_bytes": usage.total,
                    "free_percent": free_percent,
                },
                suggestion="Free up disk space or expand storage",
                auto_fixable=False,
                abs_path=str(project_root),
                line_number=None,
            ))
        except Exception:
            pass

        return results

    def _check_file_references(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for references to non-existent files."""
        from ..types import DiagnosticResult
        results = []
        # Would scan code for open() calls - simplified
        return results

    def _check_symlinks(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for broken symlinks."""
        from ..types import DiagnosticResult

        results = []
        for item in project_root.rglob("*"):
            if item.is_symlink():
                if not item.exists():
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="broken_symlink",
                        status="warning",
                        message=f"Broken symlink: {item}",
                        details={"symlink": str(item), "target": str(os.readlink(item))},
                        suggestion="Remove or fix the symlink",
                        auto_fixable=False,
                        abs_path=str(item),
                        line_number=None,
                    ))
        return results

    def _check_large_files(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for unexpectedly large files."""
        from ..types import DiagnosticResult

        results = []
        for item in project_root.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                if item.suffix == ".py" and size > 1_000_000:  # 1MB
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="large_python_file",
                        status="warning",
                        message=f"Large Python file: {item.name} ({size // 1024} KB)",
                        details={"size_bytes": size, "file": str(item)},
                        suggestion="Consider splitting into modules",
                        auto_fixable=False,
                        abs_path=str(item),
                        line_number=None,
                    ))
                elif item.suffix == ".log" and size > 100_000_000:  # 100MB
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="large_log_file",
                        status="warning",
                        message=f"Large log file: {item.name} ({size // (1024**2)} MB)",
                        details={"size_bytes": size, "file": str(item)},
                        suggestion="Rotate or truncate logs",
                        auto_fixable=True,
                        abs_path=str(item),
                        line_number=None,
                    ))
        return results

    def _check_writable(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if project directory is writable."""
        from ..types import DiagnosticResult

        results = []
        if not os.access(project_root, os.W_OK):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="read_only",
                status="critical",
                message=f"Project directory is not writable: {project_root}",
                details={"path": str(project_root)},
                suggestion="Check permissions or run with appropriate privileges",
                auto_fixable=False,
                abs_path=str(project_root),
                line_number=None,
            ))
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose filesystem-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, FileNotFoundError):
            return DiagnosticResult(
                category=self.category,
                check_name="file_not_found",
                status="error",
                message=str(exc),
                details={"cwd": os.getcwd()},
                suggestion="Verify file path exists",
                auto_fixable=False,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, PermissionError):
            return DiagnosticResult(
                category=self.category,
                check_name="permission_denied",
                status="critical",
                message=str(exc),
                details={"user": os.getenv("USER"), "euid": os.geteuid()},
                suggestion="Check file ownership and permissions",
                auto_fixable=False,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, (IsADirectoryError, NotADirectoryError)):
            return DiagnosticResult(
                category=self.category,
                check_name="path_type_mismatch",
                status="error",
                message=str(exc),
                details={},
                suggestion="Check if path is file vs directory",
                auto_fixable=False,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
