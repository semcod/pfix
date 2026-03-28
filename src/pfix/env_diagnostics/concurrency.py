"""
pfix.env_diagnostics.concurrency — Concurrency diagnostics.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ConcurrencyDiagnostic(BaseDiagnostic):
    """Diagnose concurrency-related problems."""

    category = "concurrency"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all concurrency checks."""
        results = []
        results.extend(self._check_thread_count())
        results.extend(self._check_asyncio_loop())
        return results

    def _check_thread_count(self) -> list["DiagnosticResult"]:
        """Check number of active threads."""
        from ..types import DiagnosticResult

        results = []

        thread_count = threading.active_count()

        if thread_count > 100:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="high_thread_count",
                status="warning",
                message=f"High number of active threads: {thread_count}",
                details={"thread_count": thread_count},
                suggestion="Review thread pool usage, consider async/threading balance",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_asyncio_loop(self) -> list["DiagnosticResult"]:
        """Check asyncio event loop status."""
        from ..types import DiagnosticResult

        results = []

        try:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="asyncio_loop_running",
                    status="ok",
                    message="Asyncio event loop is running",
                    details={"loop": str(loop)},
                    suggestion="",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))
            except RuntimeError:
                # No loop running - normal for sync code
                pass

        except ImportError:
            pass

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose concurrency-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, RuntimeError) and "already running" in str(exc):
            return DiagnosticResult(
                category=self.category,
                check_name="asyncio_loop_already_running",
                status="error",
                message="Asyncio event loop is already running",
                details={},
                suggestion="Use nest_asyncio or ensure single loop management",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
