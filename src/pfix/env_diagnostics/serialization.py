"""
pfix.env_diagnostics.serialization — Serialization diagnostics.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class SerializationDiagnostic(BaseDiagnostic):
    """Diagnose serialization-related problems."""

    category = "serialization"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all serialization checks."""
        results = []
        results.extend(self._check_pickle_protocol())
        results.extend(self._check_cache_files(project_root))
        return results

    def _check_pickle_protocol(self) -> list["DiagnosticResult"]:
        """Check pickle protocol compatibility."""
        from ..types import DiagnosticResult
        import pickle

        results = []

        # Check default protocol
        default_protocol = pickle.DEFAULT_PROTOCOL
        highest_protocol = pickle.HIGHEST_PROTOCOL

        if highest_protocol > default_protocol:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="pickle_protocol",
                status="warning",
                message=f"Pickle highest protocol ({highest_protocol}) > default ({default_protocol})",
                details={
                    "default_protocol": default_protocol,
                    "highest_protocol": highest_protocol,
                },
                suggestion="Pickle files created with higher protocol may not load on older Python",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_cache_files(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for potentially corrupt cache files."""
        from ..types import DiagnosticResult

        results = []

        # Check __pycache__ for corrupt files
        for cache_dir in project_root.rglob("__pycache__"):
            try:
                # Try to list - if it fails, might be corrupt
                list(cache_dir.iterdir())
            except (OSError, PermissionError) as e:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="corrupt_pycache",
                    status="warning",
                    message=f"Cannot read __pycache__ directory: {e}",
                    details={"cache_dir": str(cache_dir)},
                    suggestion="Clear __pycache__ directories",
                    auto_fixable=True,
                    abs_path=str(cache_dir),
                    line_number=None,
                ))

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose serialization-related exceptions."""
        from ..types import DiagnosticResult

        exc_name = type(exc).__name__

        if "pickle" in exc_name.lower() or "unpickling" in str(exc).lower():
            return DiagnosticResult(
                category=self.category,
                check_name="pickle_error",
                status="error",
                message=f"Pickle error: {exc}",
                details={},
                suggestion="Check pickle protocol version and class compatibility",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if "json" in exc_name.lower() or isinstance(exc, (TypeError, ValueError)) and "json" in str(exc).lower():
            return DiagnosticResult(
                category=self.category,
                check_name="json_error",
                status="error",
                message=f"JSON error: {exc}",
                details={},
                suggestion="Check JSON format and encoding",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
