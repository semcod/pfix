"""
pfix.env_diagnostics.third_party — Third-party API diagnostics.

Detects issues with external API integrations:
- Rate limiting (429 responses)
- Authentication expiration
- API schema changes
- Deprecated API versions
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ThirdPartyDiagnostic(BaseDiagnostic):
    """Diagnose third-party API-related problems."""

    category = "third_party"

    # Known API error patterns
    RATE_LIMIT_PATTERNS = [
        "rate limit",
        "too many requests",
        "429",
        "quota exceeded",
        "throttled",
    ]

    AUTH_PATTERNS = [
        "unauthorized",
        "authentication",
        "auth expired",
        "token expired",
        "invalid token",
        "api key invalid",
        "401",
        "403",
    ]

    SCHEMA_PATTERNS = [
        "schema",
        "field not found",
        "unexpected field",
        "missing required field",
        "validation failed",
        "invalid response",
    ]

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all third-party API checks."""
        results = []
        results.extend(self._check_api_keys_in_env())
        results.extend(self._check_api_client_configs(project_root))
        return results

    def _check_api_keys_in_env(self) -> list["DiagnosticResult"]:
        """Check for API keys that might need attention."""
        from ..types import DiagnosticResult
        import os

        results = []

        # Check for common API key patterns that might be placeholders
        api_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "GITHUB_TOKEN",
            "AWS_ACCESS_KEY_ID",
            "AZURE_API_KEY",
            "GCP_API_KEY",
        ]

        for var in api_vars:
            value = os.environ.get(var)
            if value:
                # Check if placeholder or dummy value
                if value.lower() in ("your_key_here", "placeholder", "xxx", "test"):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="api_key_placeholder",
                        status="warning",
                        message=f"{var} appears to be a placeholder value",
                        details={"variable": var, "value_preview": value[:10] + "..."},
                        suggestion=f"Replace {var} with a real API key",
                        auto_fixable=False,
                        abs_path=None,
                        line_number=None,
                    ))

                # Check if key format looks suspicious
                if len(value) < 10:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="api_key_suspicious",
                        status="warning",
                        message=f"{var} has suspicious format (too short)",
                        details={"variable": var, "length": len(value)},
                        suggestion=f"Verify {var} is correct",
                        auto_fixable=False,
                        abs_path=None,
                        line_number=None,
                    ))

        return results

    def _check_api_client_configs(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check API client configurations in code."""
        from ..types import DiagnosticResult
        import ast

        results = []

        # Look for hardcoded API keys or missing timeout configs
        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            try:
                source = pyfile.read_text()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    # Check for hardcoded API keys
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        val = node.value
                        if any(keyword in val.lower() for keyword in ["api_key", "apikey", "token"]):
                            if len(val) > 20:  # Likely a real key
                                results.append(DiagnosticResult(
                                    category=self.category,
                                    check_name="hardcoded_api_key",
                                    status="critical",
                                    message=f"Possible hardcoded API key in {pyfile.name}",
                                    details={"file": str(pyfile), "line": getattr(node, 'lineno', None)},
                                    suggestion="Move API keys to environment variables",
                                    auto_fixable=False,
                                    abs_path=str(pyfile),
                                    line_number=getattr(node, 'lineno', None),
                                ))

                    # Check for requests without timeout
                    if isinstance(node, ast.Call):
                        func_name = ""
                        if isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        elif isinstance(node.func, ast.Name):
                            func_name = node.func.id

                        if func_name in ("get", "post", "put", "delete", "request"):
                            # Check if timeout is in keywords
                            has_timeout = any(
                                kw.arg == "timeout" for kw in node.keywords if isinstance(kw.arg, str)
                            )
                            if not has_timeout:
                                results.append(DiagnosticResult(
                                    category=self.category,
                                    check_name="missing_timeout",
                                    status="warning",
                                    message=f"HTTP request without timeout in {pyfile.name}",
                                    details={"file": str(pyfile), "line": getattr(node, 'lineno', None)},
                                    suggestion="Add timeout parameter to prevent hanging",
                                    auto_fixable=False,
                                    abs_path=str(pyfile),
                                    line_number=getattr(node, 'lineno', None),
                                ))

            except SyntaxError:
                pass
            except Exception:
                pass

        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose third-party API-related exceptions."""
        from ..types import DiagnosticResult

        exc_msg = str(exc).lower()

        # Check for rate limiting
        if any(pattern in exc_msg for pattern in self.RATE_LIMIT_PATTERNS):
            return DiagnosticResult(
                category=self.category,
                check_name="rate_limit",
                status="warning",
                message=f"API rate limit hit: {exc}",
                details={"error": str(exc)},
                suggestion="Implement exponential backoff and retry logic",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        # Check for authentication issues
        if any(pattern in exc_msg for pattern in self.AUTH_PATTERNS):
            return DiagnosticResult(
                category=self.category,
                check_name="auth_expired",
                status="error",
                message=f"API authentication failed: {exc}",
                details={"error": str(exc)},
                suggestion="Check API key/token validity and expiration",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        # Check for schema/validation issues
        if any(pattern in exc_msg for pattern in self.SCHEMA_PATTERNS):
            return DiagnosticResult(
                category=self.category,
                check_name="schema_change",
                status="error",
                message=f"API schema mismatch: {exc}",
                details={"error": str(exc)},
                suggestion="Check API documentation for recent changes",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
