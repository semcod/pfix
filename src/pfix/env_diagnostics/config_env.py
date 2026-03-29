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
        results.extend(self._check_pyproject_validity(project_root))
        results.extend(self._check_pfix_config_missing(project_root))
        results.extend(self._check_secret_exposure_env())
        results.extend(self._check_conflicting_manifests(project_root))
        return results

    def _check_dotenv(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check .env file for various issues."""
        results = []
        env_file = project_root / ".env"
        env_example = project_root / ".env.example"

        if env_example.exists() and not env_file.exists():
            results.append(self._create_missing_env_result(env_example))

        if env_file.exists():
            content = env_file.read_text()
            results.extend(self._check_secrets_in_env(content, project_root, env_file))
            results.extend(self._check_env_whitespace(content, env_file))

        return results

    def _create_missing_env_result(self, env_example: Path) -> "DiagnosticResult":
        from ..types import DiagnosticResult
        return DiagnosticResult(
            category=self.category,
            check_name="missing_dotenv",
            status="warning",
            message=".env.example exists but .env is missing",
            details={"example": str(env_example)},
            suggestion="Copy .env.example to .env and configure",
            auto_fixable=True,
            abs_path=str(env_example),
        )

    def _check_secrets_in_env(self, content: str, project_root: Path, env_file: Path) -> list["DiagnosticResult"]:
        from ..types import DiagnosticResult
        results = []
        risky_patterns = ["SECRET", "PASSWORD", "KEY", "TOKEN", "API_KEY"]
        
        if any(p in content.upper() for p in risky_patterns):
            gitignore = project_root / ".gitignore"
            if gitignore.exists() and ".env" not in gitignore.read_text():
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="env_not_gitignored",
                    status="critical",
                    message=".env file may contain secrets but is not in .gitignore!",
                    details={"env_file": str(env_file)},
                    suggestion="Add .env to .gitignore immediately!",
                    auto_fixable=True,
                    abs_path=str(env_file),
                ))
        return results

    def _check_env_whitespace(self, content: str, env_file: Path) -> list["DiagnosticResult"]:
        from ..types import DiagnosticResult
        results = []
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.startswith("#") and line.rstrip() != line:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="env_trailing_whitespace",
                    status="warning",
                    message=f".env line {i} has trailing whitespace",
                    details={"line": i},
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

    def _check_pyproject_validity(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if pyproject.toml is syntactically correct."""
        from ..types import DiagnosticResult
        results = []
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    return results
            
            try:
                with open(pyproject, "rb") as f:
                    tomllib.load(f)
            except Exception as e:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="invalid_pyproject",
                    status="error",
                    message=f"Syntax error in pyproject.toml: {e}",
                    suggestion="Fix TOML syntax in pyproject.toml",
                    abs_path=str(pyproject),
                ))
        return results

    def _check_pfix_config_missing(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if [tool.pfix] section is missing in pyproject.toml."""
        from ..types import DiagnosticResult
        results = []
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                if "tool" not in data or "pfix" not in data["tool"]:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="missing_pfix_config",
                        status="warning",
                        message="[tool.pfix] section is missing in pyproject.toml",
                        suggestion="Run 'pfix init' or add [tool.pfix] manually",
                    ))
            except Exception:
                pass
        return results

    def _check_secret_exposure_env(self) -> list["DiagnosticResult"]:
        """Check for potentially sensitive data in environment variables."""
        from ..types import DiagnosticResult
        results = []
        SEC_KEYWORDS = {"SECRET", "PASSWORD", "API_KEY", "AWS_ACCESS_KEY", "PRIVATE_KEY"}
        for key in os.environ:
            if any(kw in key.upper() for kw in SEC_KEYWORDS):
                # We don't want to show the value, just warn about exposure risk
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="secret_in_env",
                    status="warning",
                    message=f"Sensitive environment variable detected: {key}",
                    suggestion="Ensure environment variables are managed securely and not accidentally logged",
                ))
        return results

    def _check_conflicting_manifests(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if both requirements.txt and pyproject.toml exist (potential drift)."""
        from ..types import DiagnosticResult
        results = []
        has_reqs = (project_root / "requirements.txt").exists()
        has_pyproject = (project_root / "pyproject.toml").exists()
        if has_reqs and has_pyproject:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="conflicting_manifests",
                status="low",
                message="Both requirements.txt and pyproject.toml found",
                suggestion="Consolidate dependencies into pyproject.toml if possible",
            ))
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose config/env-related exceptions."""
        return None
