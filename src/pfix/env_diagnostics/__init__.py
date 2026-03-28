"""
pfix.env_diagnostics — Comprehensive environment diagnostics.

Detects 14 categories of environment problems:
1. Import/dependency   2. Filesystem         3. Virtual environment
4. Python version       5. Memory             6. Network
7. Process/OS           8. Encoding           9. Path/working dir
10. Config/env vars     11. Concurrency       12. Serialization
13. Hardware/resource    14. Third-party API

Usage:
    from pfix.env_diagnostics import EnvDiagnostics
    diag = EnvDiagnostics()
    results = diag.check_all()  # Run all diagnostics

    # Diagnose specific exception
    results = diag.diagnose_exception(exc, error_context)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext

from .base import BaseDiagnostic
from .config_env import ConfigEnvDiagnostic
from .concurrency import ConcurrencyDiagnostic
from .encoding import EncodingDiagnostic
from .filesystem import FilesystemDiagnostic
from .hardware import HardwareDiagnostic
from .imports import ImportDiagnostic
from .memory import MemoryDiagnostic
from .network import NetworkDiagnostic
from .paths import PathDiagnostic
from .process import ProcessDiagnostic
from .python_version import PythonVersionDiagnostic
from .serialization import SerializationDiagnostic
from .third_party import ThirdPartyDiagnostic
from .venv import VenvDiagnostic


class EnvDiagnostics:
    """Orchestrator for all environment diagnostics."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = Path(project_root or ".").resolve()
        self.diagnostics: list[BaseDiagnostic] = [
            ImportDiagnostic(),
            FilesystemDiagnostic(),
            VenvDiagnostic(),
            PythonVersionDiagnostic(),
            MemoryDiagnostic(),
            NetworkDiagnostic(),
            ProcessDiagnostic(),
            EncodingDiagnostic(),
            PathDiagnostic(),
            ConfigEnvDiagnostic(),
            ConcurrencyDiagnostic(),
            SerializationDiagnostic(),
            HardwareDiagnostic(),
            ThirdPartyDiagnostic(),
        ]

    def check_all(self, categories: list[str] | None = None) -> list["DiagnosticResult"]:
        """Run all or selected proactive diagnostics.

        Args:
            categories: If provided, only run these categories.
                       e.g., ["filesystem", "venv"]
        """
        results: list["DiagnosticResult"] = []

        for diag in self.diagnostics:
            if categories and diag.category not in categories:
                continue

            try:
                results.extend(diag.check(self.project_root))
            except Exception as e:
                from ..types import DiagnosticResult
                results.append(DiagnosticResult(
                    category=diag.category,
                    check_name="_diagnostic_error",
                    status="warning",
                    message=f"Diagnostic {diag.category} failed: {e}",
                    details={},
                    suggestion="",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> list["DiagnosticResult"]:
        """Diagnose a specific exception through all diagnostics."""
        results: list["DiagnosticResult"] = []

        for diag in self.diagnostics:
            try:
                result = diag.diagnose_exception(exc, ctx)
                if result is not None:
                    results.append(result)
            except Exception:
                pass

        return results

    def generate_report(self, results: list["DiagnosticResult"]) -> str:
        """Generate formatted text report from results."""
        if not results:
            return "✅ No environment issues detected."

        lines = ["# Environment Diagnostics Report", ""]

        # Group by status
        critical = [r for r in results if r.status == "critical"]
        errors = [r for r in results if r.status == "error"]
        warnings = [r for r in results if r.status == "warning"]
        ok = [r for r in results if r.status == "ok"]

        if critical:
            lines.append("## 🔴 Critical Issues")
            for r in critical:
                lines.append(self._format_result(r))
            lines.append("")

        if errors:
            lines.append("## ❌ Errors")
            for r in errors:
                lines.append(self._format_result(r))
            lines.append("")

        if warnings:
            lines.append("## ⚠️ Warnings")
            for r in warnings:
                lines.append(self._format_result(r))
            lines.append("")

        if ok and len(ok) < 10:  # Only show OK if few
            lines.append("## ✅ OK")
            for r in ok:
                lines.append(f"- {r.category}/{r.check_name}")
            lines.append("")

        # Summary
        lines.append(f"**Summary**: {len(critical)} critical, {len(errors)} errors, "
                    f"{len(warnings)} warnings, {len(ok)} OK")

        return "\n".join(lines)

    def _format_result(self, r: "DiagnosticResult") -> str:
        """Format single result as markdown."""
        lines = [f"### [{r.category}] {r.check_name}"]
        lines.append(f"**Status**: {r.status}")
        lines.append(f"**Message**: {r.message}")

        if r.abs_path:
            if r.line_number:
                lines.append(f"**Location**: `{r.abs_path}:{r.line_number}`")
            else:
                lines.append(f"**Location**: `{r.abs_path}`")

        if r.details:
            lines.append("**Details**:")
            for k, v in r.details.items():
                lines.append(f"  - {k}: {v}")

        if r.suggestion:
            lines.append(f"**Suggestion**: {r.suggestion}")

        if r.auto_fixable:
            lines.append("*Auto-fix available* ✨")

        lines.append("")
        return "\n".join(lines)

    def to_todo_issues(self, results: list["DiagnosticResult"]) -> list[dict]:
        """Convert DiagnosticResults to TODO.md issue format."""
        from ..types import RuntimeIssue, TraceFrame

        issues = []
        severity_map = {
            "critical": "critical",
            "error": "high",
            "warning": "medium",
        }

        for r in results:
            if r.status == "ok":
                continue

            issue = RuntimeIssue(
                abs_filepath=r.abs_path or "<environment>",
                line_number=r.line_number or 0,
                function_name=r.check_name,
                module_name=r.category,
                exception_type=r.check_name,
                exception_message=r.message,
                traceback_frames=[TraceFrame(
                    filepath=r.abs_path or "",
                    line_number=r.line_number or 0,
                    function_name=r.check_name,
                    code_line=r.message,
                )] if r.abs_path else [],
                category=r.category,
                severity=severity_map.get(r.status, "low"),
            )
            issues.append(issue)

        return issues


__all__ = [
    "EnvDiagnostics",
    "BaseDiagnostic",
    "ImportDiagnostic",
    "FilesystemDiagnostic",
    "VenvDiagnostic",
    "PythonVersionDiagnostic",
    "MemoryDiagnostic",
    "NetworkDiagnostic",
    "ProcessDiagnostic",
    "EncodingDiagnostic",
    "PathDiagnostic",
    "ConfigEnvDiagnostic",
    "ConcurrencyDiagnostic",
    "SerializationDiagnostic",
    "HardwareDiagnostic",
    "ThirdPartyDiagnostic",
]
