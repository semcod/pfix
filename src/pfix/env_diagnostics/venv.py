"""
pfix.env_diagnostics.venv — Virtual environment diagnostics.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class VenvDiagnostic(BaseDiagnostic):
    """Diagnose virtual environment problems."""

    category = "virtual_environment"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all venv checks."""
        results = []
        results.extend(self._check_venv_active())
        results.extend(self._check_venv_integrity(project_root))
        results.extend(self._check_global_leaks())
        results.extend(self._check_requirements_sync(project_root))
        results.extend(self._check_pythonpath())
        results.extend(self._check_venv_stale())
        results.extend(self._check_no_manifest(project_root))
        results.extend(self._check_site_packages_writable())
        return results

    def _check_venv_active(self) -> list["DiagnosticResult"]:
        """Check if running in a virtual environment."""
        from ..types import DiagnosticResult

        results = []

        # Check for venv
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )

        if not in_venv and not os.environ.get("VIRTUAL_ENV"):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="no_venv",
                status="warning",
                message="Not running in a virtual environment",
                details={
                    "prefix": sys.prefix,
                    "base_prefix": getattr(sys, 'base_prefix', None),
                },
                suggestion="Create and activate a venv: python -m venv .venv",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_venv_integrity(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if venv is not broken."""
        from ..types import DiagnosticResult

        results = []

        venv_path = os.environ.get("VIRTUAL_ENV")
        if not venv_path:
            return results

        # Check python executable exists
        python_exe = Path(venv_path) / "bin" / "python"
        if not python_exe.exists():
            results.append(DiagnosticResult(
                category=self.category,
                check_name="broken_venv",
                status="error",
                message=f"Venv python executable missing: {python_exe}",
                details={"venv_path": venv_path},
                suggestion="Recreate the virtual environment",
                auto_fixable=False,
                abs_path=venv_path,
                line_number=None,
            ))

        return results

    def _check_global_leaks(self) -> list["DiagnosticResult"]:
        """Check for packages from global site-packages."""
        from ..types import DiagnosticResult

        results = []

        # Check sys.path for global site-packages
        venv_path = os.environ.get("VIRTUAL_ENV")
        if not venv_path:
            return results

        for path in sys.path:
            if "/usr/" in path and "site-packages" in path:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="global_site_packages",
                    status="warning",
                    message=f"Global site-packages in sys.path: {path}",
                    details={"path": path},
                    suggestion="Use venv with --system-site-packages carefully",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))
                break

        return results

    def _check_requirements_sync(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if requirements.txt matches installed packages."""
        from ..types import DiagnosticResult

        results = []
        req_file = project_root / "requirements.txt"

        if not req_file.exists():
            return results

        try:
            # Simple check - look for obviously missing packages
            reqs = req_file.read_text()
            installed = {
                pkg.metadata["Name"].lower()
                for pkg in __import__("importlib.metadata").metadata.distributions()
            }

            for line in reqs.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse package name
                pkg = line.split("==")[0].split(">=")[0].split("<")[0].strip().lower()

                if pkg and pkg not in installed:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="missing_requirement",
                        status="warning",
                        message=f"'{pkg}' in requirements.txt but not installed",
                        details={"package": pkg, "requirements": str(req_file)},
                        suggestion=f"pip install -r {req_file}",
                        auto_fixable=True,
                        abs_path=str(req_file),
                        line_number=None,
                    ))

        except Exception:
            pass

        return results

    def _check_pythonpath(self) -> list["DiagnosticResult"]:
        """Check for PYTHONPATH environment variable interference."""
        from ..types import DiagnosticResult
        results = []
        pythonpath = os.environ.get("PYTHONPATH")
        if pythonpath:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="pythonpath_set",
                status="warning",
                message=f"PYTHONPATH is set: {pythonpath}",
                details={"value": pythonpath},
                suggestion="Clear PYTHONPATH to avoid unexpected import behavior",
                auto_fixable=False,
            ))
        return results

    def _check_venv_stale(self) -> list["DiagnosticResult"]:
        """Check if virtualenv Python version matches system Python (stale venv)."""
        from ..types import DiagnosticResult
        results = []
        venv_path = os.environ.get("VIRTUAL_ENV")
        if not venv_path:
            return results

        try:
            # Check if bin/python is actually from this venv
            # This is a bit tricky, but we can check if it works
            import subprocess
            res = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode != 0:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="stale_venv",
                    status="critical",
                    message="Virtual environment Python is broken (stale)",
                    details={"venv_path": venv_path, "error": res.stderr},
                    suggestion="Recreate the virtual environment",
                    auto_fixable=False,
                ))
        except Exception:
            pass
        return results

    def _check_no_manifest(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if project lacks requirements.txt and pyproject.toml."""
        from ..types import DiagnosticResult
        results = []
        has_reqs = (project_root / "requirements.txt").exists()
        has_pyproject = (project_root / "pyproject.toml").exists()
        has_setup = (project_root / "setup.py").exists()

        if not (has_reqs or has_pyproject or has_setup):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="no_manifest",
                status="warning",
                message="Project lacks dependency manifest (requirements.txt or pyproject.toml)",
                suggestion="Use 'pfix deps generate' or create a manifest",
                auto_fixable=True,
            ))
        return results

    def _check_site_packages_writable(self) -> list["DiagnosticResult"]:
        """Check if venv site-packages is writable."""
        from ..types import DiagnosticResult
        results = []
        import site
        sp = site.getsitepackages()
        if not sp:
            return results

        target = Path(sp[0])
        if not os.access(target, os.W_OK):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="site_packages_readonly",
                status="error",
                message=f"site-packages is not writable: {target}",
                details={"path": str(target)},
                suggestion="Check permissions or run as appropriate user",
                auto_fixable=False,
            ))
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose venv-related exceptions."""
        return None
