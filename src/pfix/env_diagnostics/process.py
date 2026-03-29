"""
pfix.env_diagnostics.process — Process and OS diagnostics.
"""

from __future__ import annotations

import os
import signal
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ProcessDiagnostic(BaseDiagnostic):
    """Diagnose process and OS-related problems."""

    category = "process"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all process/OS checks."""
        results = []
        results.extend(self._check_ulimits())
        results.extend(self._check_signal_handlers())
        results.extend(self._check_tmp_writable())
        results.extend(self._check_zombies())
        results.extend(self._check_nice_priority())
        results.extend(self._check_fd_usage())
        results.extend(self._check_core_dumps())
        results.extend(self._check_parent_alive())
        return results

    def _check_ulimits(self) -> list["DiagnosticResult"]:
        """Check ulimits for file descriptors and processes."""
        from ..types import DiagnosticResult

        results = []

        try:
            import resource

            # Check open files limit
            soft_fd, hard_fd = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft_fd < 1024:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_fd_limit",
                    status="warning",
                    message=f"Low file descriptor limit: {soft_fd} (hard: {hard_fd})",
                    details={"soft_limit": soft_fd, "hard_limit": hard_fd},
                    suggestion="Increase with ulimit -n or setrlimit()",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

            # Check process limit
            soft_proc, hard_proc = resource.getrlimit(resource.RLIMIT_NPROC)
            if soft_proc < 100:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_proc_limit",
                    status="warning",
                    message=f"Low process limit: {soft_proc}",
                    details={"soft_limit": soft_proc, "hard_limit": hard_proc},
                    suggestion="Increase with ulimit -u",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        except ImportError:
            pass  # Windows

        return results

    def _check_signal_handlers(self) -> list["DiagnosticResult"]:
        """Check for overwritten signal handlers."""
        from ..types import DiagnosticResult

        results = []

        # Check if critical signals have handlers
        for sig_name in ["SIGINT", "SIGTERM"]:
            sig_num = getattr(signal, sig_name, None)
            if sig_num is None:
                continue

            handler = signal.getsignal(sig_num)
            if handler == signal.SIG_IGN:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name=f"signal_{sig_name}_ignored",
                    status="warning",
                    message=f"{sig_name} is being ignored",
                    details={"signal": sig_name},
                    suggestion="Ensure proper signal handling for graceful shutdown",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        return results

    def _check_tmp_writable(self) -> list["DiagnosticResult"]:
        """Check if /tmp is writable."""
        from ..types import DiagnosticResult

        results = []

        tmp_dirs = ["/tmp", os.environ.get("TMPDIR", "/tmp")]

        for tmp_dir in set(tmp_dirs):
            if os.path.exists(tmp_dir):
                if not os.access(tmp_dir, os.W_OK):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="tmp_not_writable",
                        status="critical",
                        message=f"Temporary directory not writable: {tmp_dir}",
                        details={"tmp_dir": tmp_dir},
                        suggestion="Check permissions or set TMPDIR",
                        auto_fixable=False,
                        abs_path=tmp_dir,
                        line_number=None,
                    ))
                break

        return results

    def _check_zombies(self) -> list["DiagnosticResult"]:
        """Check for zombie (defunct) child processes."""
        from ..types import DiagnosticResult
        results = []
        try:
            import psutil
            parent = psutil.Process(os.getpid())
            zombies = [p for p in parent.children() if p.status() == psutil.STATUS_ZOMBIE]
            if zombies:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="zombie_processes",
                    status="warning",
                    message=f"Detected {len(zombies)} zombie processes",
                    details={"pids": [p.pid for p in zombies]},
                    suggestion="Ensure child processes are waited on (os.waitpid)",
                ))
        except (ImportError, Exception):
            pass
        return results

    def _check_nice_priority(self) -> list["DiagnosticResult"]:
        """Check if process is running with low CPU priority."""
        from ..types import DiagnosticResult
        results = []
        try:
            priority = os.nice(0)
            if priority > 15:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="low_cpu_priority",
                    status="warning",
                    message=f"Process running with very low priority: nice {priority}",
                    suggestion="Increase priority if performance is an issue",
                ))
        except (AttributeError, Exception):
            pass
        return results

    def _check_fd_usage(self) -> list["DiagnosticResult"]:
        """Check current file descriptor usage against limit."""
        from ..types import DiagnosticResult
        results = []
        try:
            import resource
            import psutil
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            proc = psutil.Process(os.getpid())
            num_fds = proc.num_fds()
            
            if num_fds > soft * 0.8:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="high_fd_usage",
                    status="error" if num_fds > soft * 0.95 else "warning",
                    message=f"High file descriptor usage: {num_fds}/{soft}",
                    suggestion="Close unused file handles or increase ulimit -n",
                ))
        except (ImportError, Exception):
            pass
        return results

    def _check_core_dumps(self) -> list["DiagnosticResult"]:
        """Check if core dumps are enabled."""
        from ..types import DiagnosticResult
        results = []
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
            if soft > 0:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="core_dumps_enabled",
                    status="low",
                    message=f"Core dumps are enabled (limit: {soft})",
                    suggestion="This can fill disk space if crashes occur frequently",
                ))
        except (ImportError, Exception):
            pass
        return results

    def _check_parent_alive(self) -> list["DiagnosticResult"]:
        """Check if parent process is still alive (detect orphan status)."""
        from ..types import DiagnosticResult
        results = []
        try:
            # On Linux, if parent dies, process is re-parented to init (PID 1)
            if os.getppid() == 1:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="orphan_process",
                    status="warning",
                    message="Process is orphaned (parent is init)",
                    suggestion="Check if the launching process terminated unexpectedly",
                ))
        except Exception:
            pass
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose process/OS-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, ChildProcessError):
            return DiagnosticResult(
                category=self.category,
                check_name="child_process_error",
                status="error",
                message=str(exc),
                details={},
                suggestion="Check subprocess arguments and permissions",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, ProcessLookupError):
            return DiagnosticResult(
                category=self.category,
                check_name="process_not_found",
                status="error",
                message=str(exc),
                details={},
                suggestion="Process may have already terminated",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, OSError) and exc.errno == 24:  # EMFILE
            return DiagnosticResult(
                category=self.category,
                check_name="too_many_open_files",
                status="critical",
                message="Too many open files (EMFILE)",
                details={},
                suggestion="Close file handles or increase ulimit -n",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
