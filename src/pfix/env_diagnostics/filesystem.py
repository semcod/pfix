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
        results.extend(self._check_inodes(project_root))
        results.extend(self._check_permissions(project_root))
        results.extend(self._check_filename_encoding(project_root))
        results.extend(self._check_case_conflicts(project_root))
        results.extend(self._check_hidden_pollution(project_root))
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

    def _check_inodes(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for inode exhaustion (Linux/Unix)."""
        from ..types import DiagnosticResult
        results = []
        try:
            st = os.statvfs(project_root)
            if st.f_files > 0:
                free_percent = st.f_ffree / st.f_files * 100
                if free_percent < 5:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="inode_exhaustion",
                        status="critical" if free_percent < 1 else "error",
                        message=f"Low inode availability: {free_percent:.1f}% free",
                        details={"free_inodes": st.f_ffree, "total_inodes": st.f_files},
                        suggestion="Remove many small files (e.g. caches, sessions)",
                    ))
        except (AttributeError, OSError):
            pass  # Not available on all platforms
        return results

    def _check_permissions(self, project_root: Path) -> list["DiagnosticResult"]:
        """Perform granular permission checks for vital files."""
        from ..types import DiagnosticResult
        results = []
        vital = ["pyproject.toml", "requirements.txt", "TODO.md", ".env"]
        for name in vital:
            p = project_root / name
            if p.exists():
                if not os.access(p, os.R_OK):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="no_read_access",
                        status="error",
                        message=f"No read access to {name}",
                        abs_path=str(p),
                        suggestion=f"chmod +r {name}",
                    ))
                if not os.access(p, os.O_RDWR):
                    # We don't check execute for these
                    pass
        return results

    def _check_filename_encoding(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for filenames that might cause issues due to encoding."""
        from ..types import DiagnosticResult
        results = []
        for item in project_root.rglob("*"):
            try:
                item.name.encode('ascii')
            except UnicodeEncodeError:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="non_ascii_filename",
                    status="warning",
                    message=f"Non-ASCII filename detected: {item.name}",
                    details={"path": str(item)},
                    suggestion="Rename using ASCII characters to avoid portable issues",
                    abs_path=str(item),
                ))
        return results

    def _check_case_conflicts(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for multiple files with same name but different cases."""
        from ..types import DiagnosticResult
        results = []
        for root, dirs, files in os.walk(project_root):
            if ".git" in root or "__pycache__" in root:
                continue
            lower_to_orig = {}
            for name in files + dirs:
                lower = name.lower()
                if lower in lower_to_orig:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="case_conflict",
                        status="error",
                        message=f"Case conflict: '{name}' and '{lower_to_orig[lower]}'",
                        details={"path": root, "conflict": [name, lower_to_orig[lower]]},
                        suggestion="Rename one of the files to avoid issues on case-insensitive systems",
                        abs_path=os.path.join(root, name),
                    ))
                else:
                    lower_to_orig[lower] = name
        return results

    def _check_hidden_pollution(self, project_root: Path) -> list["DiagnosticResult"]:
        """Detect unexpected hidden files that might pollute the environment."""
        from ..types import DiagnosticResult
        results = []
        POLLUTANTS = [".DS_Store", "Thumbs.db", ".directory", "*.swp", "*~"]
        import fnmatch
        for root, dirs, files in os.walk(project_root):
            for name in files:
                for pattern in POLLUTANTS:
                    if fnmatch.fnmatch(name, pattern):
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="hidden_pollution",
                            status="low",
                            message=f"Environment pollutant found: {name}",
                            suggestion=f"Remove {name} or add to .gitignore",
                            abs_path=os.path.join(root, name),
                            auto_fixable=True,
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
