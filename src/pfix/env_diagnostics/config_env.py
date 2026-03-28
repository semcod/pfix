"""
pfix.env_diagnostics.config_env — Configuration and environment variable diagnostics.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ConfigEnvDiagnostic(BaseDiagnostic):
    """Diagnose configuration and environment variable problems."""

    category = "config_env"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all config/env checks."""
        results = []
        results.extend(self._check_dotenv(project_root))
        results.extend(self._check_required_vars(project_root))
        results.extend(self._check_env_gitignore(project_root))
        return results

    def _check_dotenv(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check .env file."""
        from ..types import DiagnosticResult

        results = []

        env_file = project_root / ".env"
        env_example = project_root / ".env.example"

        if env_example.exists() and not env_file.exists():
            results.append(DiagnosticResult(
                category=self.category,
                check_name="missing_dotenv",
                status="warning",
                message=".env.example exists but .env is missing",
                details={"example": str(env_example)},
                suggestion="Copy .env.example to .env and configure",
                auto_fixable=True,
                abs_path=str(env_example),
                line_number=None,
            ))

        if env_file.exists():
            # Check for secrets
            content = env_file.read_text()
            risky_patterns = ["SECRET", "PASSWORD", "KEY", "TOKEN", "API_KEY"]

            for pattern in risky_patterns:
                if pattern in content.upper():
                    # Check if in gitignore
                    gitignore = project_root / ".gitignore"
                    if gitignore.exists():
                        gi_content = gitignore.read_text()
                        if ".env" not in gi_content:
                            results.append(DiagnosticResult(
                                category=self.category,
                                check_name="env_not_gitignored",
                                status="critical",
                                message=".env file may contain secrets but is not in .gitignore!",
                                details={"env_file": str(env_file)},
                                suggestion="Add .env to .gitignore immediately!",
                                auto_fixable=True,
                                abs_path=str(env_file),
                                line_number=None,
                            ))
                            break

            # Check for trailing whitespace in values
            for i, line in enumerate(content.splitlines(), 1):
                if line.strip() and not line.startswith("#"):
                    if line.rstrip() != line:
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="env_trailing_whitespace",
                            status="warning",
                            message=f".env line {i} has trailing whitespace",
                            details={"line": i, "content": line[:50]},
                            suggestion="Remove trailing whitespace from .env values",
                            auto_fixable=True,
                            abs_path=str(env_file),
                            line_number=i,
                        ))

        return results

    def _check_required_vars(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for required environment variables."""
        from ..types import DiagnosticResult

        results = []

        # Check .env.example for required vars
        env_example = project_root / ".env.example"
        if not env_example.exists():
            return results

        try:
            example_content = env_example.read_text()
            required_vars = []

            for line in example_content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    var = line.split("=")[0].strip()
                    required_vars.append(var)

            for var in required_vars:
                if not os.environ.get(var):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="missing_env_var",
                        status="error",
                        message=f"Required environment variable not set: {var}",
                        details={"variable": var},
                        suggestion=f"Set {var} in .env or environment",
                        auto_fixable=False,
                        abs_path=str(env_example),
                        line_number=None,
                    ))

        except Exception:
            pass

        return results

    def _check_env_gitignore(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if .env is properly gitignored."""
        from ..types import DiagnosticResult

        results = []

        env_file = project_root / ".env"
        gitignore = project_root / ".gitignore"

        if env_file.exists() and gitignore.exists():
            gi_content = gitignore.read_text()
            if ".env" not in gi_content:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="env_not_gitignored",
                    status="critical",
                    message=".env file is not in .gitignore!",
                    details={"env_file": str(env_file)},
                    suggestion="Add .env to .gitignore to prevent leaking secrets",
                    auto_fixable=True,
                    abs_path=str(gitignore),
                    line_number=None,
                ))

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose config/env-related exceptions."""
        return None
