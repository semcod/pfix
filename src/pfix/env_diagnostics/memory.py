"""
pfix.env_diagnostics.memory — Memory diagnostics.
"""

from __future__ import annotations

import gc
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class MemoryDiagnostic(BaseDiagnostic):
    """Diagnose memory-related problems."""

    category = "memory"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all memory checks."""
        results = []
        results.extend(self._check_available_memory())
        results.extend(self._check_recursion_limit())
        results.extend(self._check_gc_pressure())
        results.extend(self._check_object_count())
        results.extend(self._check_swap_usage())
        results.extend(self._check_ulimits())
        results.extend(self._check_shm_usage())
        results.extend(self._check_process_memory())
        return results

    def _check_available_memory(self) -> list["DiagnosticResult"]:
        """Check available system memory."""
        from ..types import DiagnosticResult

        results = []

        try:
            import psutil
            mem = psutil.virtual_memory()

            if mem.available < 100 * 1024 * 1024:  # < 100MB
                status = "critical"
            elif mem.available < 500 * 1024 * 1024:  # < 500MB
                status = "error"
            elif mem.percent > 90:
                status = "warning"
            else:
                return results

            results.append(DiagnosticResult(
                category=self.category,
                check_name="low_memory",
                status=status,
                message=f"Low memory: {mem.available // (1024**2)} MB available ({mem.percent}% used)",
                details={
                    "available_mb": mem.available // (1024**2),
                    "total_mb": mem.total // (1024**2),
                    "percent_used": mem.percent,
                },
                suggestion="Free up memory or increase RAM/swap",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        except ImportError:
            # psutil not installed - try fallback
            try:
                import resource
                mem_info = resource.getrusage(resource.RUSAGE_SELF)
                # This is process memory, not system
                pass
            except Exception:
                pass

        return results

    def _check_recursion_limit(self) -> list["DiagnosticResult"]:
        """Check current recursion depth vs limit."""
        from ..types import DiagnosticResult

        results = []

        limit = sys.getrecursionlimit()
        current = sys._getframe().f_back.f_back.f_back if hasattr(sys, '_getframe') else None

        # Just check if limit is unusually low
        if limit < 500:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="low_recursion_limit",
                status="warning",
                message=f"Very low recursion limit: {limit}",
                details={"limit": limit},
                suggestion="Consider increasing with sys.setrecursionlimit()",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_gc_pressure(self) -> list["DiagnosticResult"]:
        """Check garbage collector statistics."""
        from ..types import DiagnosticResult

        results = []

        try:
            gc_stats = gc.get_stats()

            # Check for high collection counts (pressure indicator)
            total_collections = sum(s['collections'] for s in gc_stats)

            if total_collections > 100000:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="high_gc_pressure",
                    status="warning",
                    message=f"High GC activity: {total_collections} collections",
                    details={"gc_stats": gc_stats},
                    suggestion="Review object creation patterns, use object pools",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        except Exception:
            pass

        return results

    def _check_object_count(self) -> list["DiagnosticResult"]:
        """Check for unusually high object count."""
        from ..types import DiagnosticResult

        results = []

        try:
            # Get approximate object count without full collection
            gc.collect(0)  # Young generation only
            count = len(gc.get_objects())

            if count > 5_000_000:  # 5 million objects
                status = "error"
            elif count > 1_000_000:  # 1 million objects
                status = "warning"
            else:
                return results

            results.append(DiagnosticResult(
                category=self.category,
                check_name="high_object_count",
                status=status,
                message=f"High object count: ~{count:,} objects",
                details={"object_count": count},
                suggestion="Check for memory leaks, clear caches, use generators",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        except Exception:
            pass

        return results

    def _check_swap_usage(self) -> list["DiagnosticResult"]:
        """Check system swap availability."""
        from ..types import DiagnosticResult
        results = []
        try:
            import psutil
            swap = psutil.swap_memory()
            if swap.percent > 95:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_swap",
                    status="error",
                    message=f"System swap nearly full: {swap.percent}%",
                    details={"total": swap.total, "used": swap.used, "free": swap.free},
                    suggestion="Add more swap space or reduce background load",
                ))
        except (ImportError, Exception):
            pass
        return results

    def _check_ulimits(self) -> list["DiagnosticResult"]:
        """Check for potentially restrictive memory ulimits."""
        from ..types import DiagnosticResult
        results = []
        try:
            import resource
            # RLIMIT_AS: Max address space
            soft_as, hard_as = resource.getrlimit(resource.RLIMIT_AS)
            if soft_as != resource.RLIM_INFINITY and soft_as < 2 * 1024**3: # < 2GB
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_rlimit_as",
                    status="warning",
                    message=f"Low address space limit (RLIMIT_AS): {soft_as // (1024**2)} MB",
                    suggestion="Increase ulimit -v",
                ))
            # RLIMIT_DATA: Max data segment size
            soft_data, hard_data = resource.getrlimit(resource.RLIMIT_DATA)
            if soft_data != resource.RLIM_INFINITY and soft_data < 512 * 1024**2: # < 512MB
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_rlimit_data",
                    status="warning",
                    message=f"Low data segment limit (RLIMIT_DATA): {soft_data // (1024**2)} MB",
                    suggestion="Increase ulimit -d",
                ))
        except (ImportError, Exception):
            pass
        return results

    def _check_shm_usage(self) -> list["DiagnosticResult"]:
        """Check shared memory (/dev/shm) availability."""
        from ..types import DiagnosticResult
        results = []
        if sys.platform == "linux" and os.path.exists("/dev/shm"):
            try:
                import shutil
                usage = shutil.disk_usage("/dev/shm")
                if usage.free < 10 * 1024**2: # < 10MB
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="low_shm",
                        status="error",
                        message=f"Shared memory (/dev/shm) nearly full: {usage.free // (1024**2)} MB free",
                        suggestion="Clear /dev/shm or increase its size",
                    ))
            except Exception:
                pass
        return results

    def _check_process_memory(self) -> list["DiagnosticResult"]:
        """Check if current process occupies too much of system memory."""
        from ..types import DiagnosticResult
        results = []
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            mem_info = proc.memory_info()
            total_mem = psutil.virtual_memory().total
            
            percent_of_system = (mem_info.rss / total_mem) * 100
            if percent_of_system > 50: # More than 50% of system RAM
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="high_process_rss",
                    status="error",
                    message=f"Process consumes {percent_of_system:.1f}% of total system RAM",
                    details={"rss": mem_info.rss, "percent": percent_of_system},
                    suggestion="Optimize process memory footprint or check for leaks",
                ))
        except (ImportError, Exception):
            pass
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose memory-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, MemoryError):
            return DiagnosticResult(
                category=self.category,
                check_name="out_of_memory",
                status="critical",
                message=f"MemoryError: {exc}",
                details={
                    "recursion_limit": sys.getrecursionlimit(),
                    "gc_stats": gc.get_stats() if hasattr(gc, 'get_stats') else None,
                },
                suggestion="Reduce memory usage, check for leaks, or increase system memory",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, RecursionError):
            return DiagnosticResult(
                category=self.category,
                check_name="recursion_error",
                status="critical",
                message=f"RecursionError: {exc}",
                details={"recursion_limit": sys.getrecursionlimit()},
                suggestion="Check for infinite recursion or increase recursion limit",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
