"""
pfix.env_diagnostics.python_version — Python version diagnostics.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class PythonVersionDiagnostic(BaseDiagnostic):
    """Diagnose Python version compatibility problems."""

    category = "python_version"

    # Feature -> (min_version, description)
    VERSION_FEATURES = {
        "match": (3, 10, "match/case syntax"),
        "tomllib": (3, 11, "tomllib module (use tomli for older)"),
        "exception_groups": (3, 11, "exception groups"),
        "typing_self": (3, 11, "typing.Self"),
        "typing_override": (3, 12, "typing.override"),
        "walrus": (3, 8, "walrus operator :="),
        "positional_only": (3, 8, "positional-only parameters /"),
        "fstring_debug": (3, 8, "f-string debug {var=}"),
        "union_types": (3, 10, "X | Y union types"),
        "type_params": (3, 12, "type parameter syntax[T]"),
    }

    DEPRECATED_MODULES = {
        3.10: ["distutils"],
        3.11: ["distutils", "imp", "sunau"],
        3.12: ["distutils", "imp", "asyncore", "smtpd"],
    }

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all Python version checks."""
        results = []
        results.extend(self._check_pyproject_requires(project_root))
        results.extend(self._check_version_features(project_root))
        results.extend(self._check_deprecated_imports(project_root))
        return results

    def _check_pyproject_requires(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check pyproject.toml requires-python vs current version."""
        from ..types import DiagnosticResult

        results = []
        pyproject = project_root / "pyproject.toml"

        if not pyproject.exists():
            return results

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return results

        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)

            requires = data.get("project", {}).get("requires-python", "")
            if requires:
                # Simple version check
                current = sys.version_info[:2]
                # Parse requires like ">=3.10,<3.13"
                import re
                min_ver = None
                max_ver = None

                if match := re.search(r">=\s*(\d+)\.(\d+)", requires):
                    min_ver = (int(match[1]), int(match[2]))
                if match := re.search(r"<\s*(\d+)\.(\d+)", requires):
                    max_ver = (int(match[1]), int(match[2]))

                if min_ver and current < min_ver:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="python_version_too_low",
                        status="error",
                        message=f"Python {current[0]}.{current[1]} < required {min_ver[0]}.{min_ver[1]}",
                        details={
                            "current": f"{current[0]}.{current[1]}",
                            "required": requires,
                        },
                        suggestion=f"Upgrade Python to {min_ver[0]}.{min_ver[1]}+",
                        auto_fixable=False,
                        abs_path=str(pyproject),
                        line_number=None,
                    ))

                if max_ver and current >= max_ver:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="python_version_too_high",
                        status="warning",
                        message=f"Python {current[0]}.{current[1]} >= max {max_ver[0]}.{max_ver[1]}",
                        details={
                            "current": f"{current[0]}.{current[1]}",
                            "max": f"{max_ver[0]}.{max_ver[1]}",
                        },
                        suggestion="Verify compatibility with newer Python",
                        auto_fixable=False,
                        abs_path=str(pyproject),
                        line_number=None,
                    ))
        except Exception:
            pass

        return results

    def _check_version_features(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for version-specific features in code."""
        from ..types import DiagnosticResult

        results = []
        current = sys.version_info[:2]

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            try:
                source = pyfile.read_text()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    # Check match statements (Python 3.10+)
                    if isinstance(node, ast.Match):
                        if current < (3, 10):
                            results.append(DiagnosticResult(
                                category=self.category,
                                check_name="match_requires_py310",
                                status="error",
                                message=f"match/case requires Python 3.10+, have {current[0]}.{current[1]}",
                                details={"feature": "match/case", "file": str(pyfile)},
                                suggestion="Upgrade Python or avoid match/case",
                                auto_fixable=False,
                                abs_path=str(pyfile),
                                line_number=getattr(node, 'lineno', None),
                            ))

                    # Check walrus operator (Python 3.8+)
                    if isinstance(node, ast.NamedExpr):
                        if current < (3, 8):
                            results.append(DiagnosticResult(
                                category=self.category,
                                check_name="walrus_requires_py38",
                                status="error",
                                message=f"Walrus operator requires Python 3.8+, have {current[0]}.{current[1]}",
                                details={"feature": "walrus :=", "file": str(pyfile)},
                                suggestion="Upgrade Python or use traditional assignment",
                                auto_fixable=False,
                                abs_path=str(pyfile),
                                line_number=getattr(node, 'lineno', None),
                            ))

            except SyntaxError:
                pass  # Let syntax check handle this
            except Exception:
                pass

        return results

    def _check_deprecated_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for deprecated stdlib imports."""
        from ..types import DiagnosticResult

        results = []
        current = sys.version_info[:2]

        deprecated = set()
        for ver, mods in self.DEPRECATED_MODULES.items():
            if current >= (ver, 0):
                deprecated.update(mods)

        if not deprecated:
            return results

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            try:
                source = pyfile.read_text()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in deprecated:
                                results.append(DiagnosticResult(
                                    category=self.category,
                                    check_name="deprecated_import",
                                    status="warning",
                                    message=f"Deprecated module: {alias.name}",
                                    details={
                                        "module": alias.name,
                                        "deprecated_since": self._get_deprecated_version(alias.name),
                                    },
                                    suggestion=f"Replace {alias.name} with modern alternative",
                                    auto_fixable=False,
                                    abs_path=str(pyfile),
                                    line_number=getattr(node, 'lineno', None),
                                ))

            except Exception:
                pass

        return results

    def _get_deprecated_version(self, module: str) -> str:
        """Get the Python version when module was deprecated."""
        for ver, mods in self.DEPRECATED_MODULES.items():
            if module in mods:
                return f"3.{ver}"
        return "unknown"

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose Python version-related exceptions."""
        return None
