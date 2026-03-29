"""
pfix.env_diagnostics.imports — Import and dependency diagnostics.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class ImportDiagnostic(BaseDiagnostic):
    """Diagnose import and dependency problems."""

    category = "import_dependency"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all import/dependency checks."""
        results = []
        results.extend(self._check_missing_imports(project_root))
        results.extend(self._check_circular_imports(project_root))
        results.extend(self._check_shadow_stdlib(project_root))
        results.extend(self._check_stale_bytecode(project_root))
        results.extend(self._check_version_conflicts())
        results.extend(self._check_missing_inits(project_root))
        results.extend(self._check_deprecated_apis(project_root))
        results.extend(self._check_import_source(project_root))
        return results

    def _check_missing_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for imports that aren't installed."""
        from ..types import DiagnosticResult

        results = []

        try:
            # Get all imports from project
            all_imports = self._get_all_project_imports(project_root)

            # Check which are installed
            installed = self._get_installed_packages()
            stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()

            for imp in all_imports:
                top = imp.split(".")[0].lower()
                if top not in installed and top not in stdlib and not top.startswith("_"):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="missing_import",
                        status="error",
                        message=f"Module '{imp}' imported but not installed",
                        details={"module": imp, "top_level": top},
                        suggestion=f"pip install {top}",
                        auto_fixable=True,
                        abs_path=None,
                        line_number=None,
                    ))

        except Exception:
            pass

        return results

    def _get_all_project_imports(self, project_root: Path) -> set[str]:
        """Collect all imports from Python files in the project."""
        all_imports = set()
        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
                continue
            try:
                imports = self._extract_imports(pyfile.read_text())
                all_imports.update(imports)
            except Exception:
                pass
        return all_imports

    def _get_installed_packages(self) -> set[str]:
        """Get lowercase names of currently installed packages."""
        try:
            return {
                pkg.metadata["Name"].lower()
                for pkg in __import__("importlib.metadata").metadata.distributions()
            }
        except Exception:
            return set()

    def _build_import_graph(
        self, project_root: Path
    ) -> tuple[dict[str, set[str]], dict[str, Path]]:
        """Build import dependency graph from project files."""
        module_imports: dict[str, set[str]] = {}
        module_paths: dict[str, Path] = {}

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
                continue

            module_name = self._get_module_name(pyfile, project_root)
            module_paths[module_name] = pyfile

            try:
                tree = ast.parse(pyfile.read_text())
                imports = set()

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.level > 0:
                            imports.add(self._resolve_relative_import(node, module_name))
                        else:
                            imports.add(node.module.split(".")[0])

                module_imports[module_name] = imports
            except (SyntaxError, UnicodeDecodeError):
                pass

        return module_imports, module_paths

    def _get_module_name(self, pyfile: Path, project_root: Path) -> str:
        """Convert a file path to a module name."""
        rel_path = pyfile.relative_to(project_root)
        if pyfile.name == "__init__.py":
            return str(rel_path.parent).replace(os.sep, ".")
        return str(rel_path.with_suffix("")).replace(os.sep, ".")

    def _resolve_relative_import(self, node: ast.ImportFrom, module_name: str) -> str:
        """Convert a relative import to an absolute module name."""
        parts = module_name.split(".")
        base = parts[:-node.level] if node.level <= len(parts) else []
        if node.module:
            return ".".join(base + [node.module])
        return ".".join(base)

    def _find_cycle_dfs(
        self, start: str, visited: set[str], path: list[str], module_imports: dict[str, set[str]]
    ) -> list[str] | None:
        """Find a cycle starting from a module using DFS.

        Args:
            start: Starting module name
            visited: Set of already visited modules
            path: Current path being explored
            module_imports: Import graph dict

        Returns:
            Cycle path if found, None otherwise
        """
        if start in path:
            return path[path.index(start):] + [start]
        if start in visited:
            return None
        visited.add(start)
        for imp in module_imports.get(start, set()):
            if imp in module_imports:
                cycle = self._find_cycle_dfs(imp, visited, path + [start], module_imports)
                if cycle:
                    return cycle
        return None

    def _create_cycle_result(
        self, cycle: list[str], module_paths: dict[str, Path], checked: set
    ) -> "DiagnosticResult" | None:
        """Create a DiagnosticResult for a detected cycle.

        Returns:
            DiagnosticResult if new cycle, None if already reported
        """
        from ..types import DiagnosticResult

        # Check if we already reported this cycle
        cycle_key = tuple(sorted(cycle[:-1]))
        if cycle_key in checked:
            return None
        checked.add(cycle_key)

        cycle_str = " -> ".join(cycle)
        file_path = str(module_paths.get(cycle[0], "unknown"))

        return DiagnosticResult(
            category=self.category,
            check_name="circular_import",
            status="error",
            message=f"Circular import detected: {cycle_str}",
            details={
                "cycle": cycle,
                "modules_involved": len(cycle) - 1,
            },
            suggestion="Refactor to break the cycle (use interface classes or lazy imports)",
            auto_fixable=False,
            abs_path=file_path if file_path != "unknown" else None,
            line_number=None,
        )

    def _check_circular_imports(self, project_root: Path) -> list["DiagnosticResult"]:
        """Detect circular import patterns using module dependency graph."""
        results = []
        checked = set()

        # Build import graph
        module_imports, module_paths = self._build_import_graph(project_root)

        # Find cycles using DFS
        for module in module_imports:
            if module not in checked:
                cycle = self._find_cycle_dfs(module, set(), [], module_imports)
                if cycle and len(cycle) > 1:
                    result = self._create_cycle_result(cycle, module_paths, checked)
                    if result:
                        results.append(result)

        return results

    def _check_shadow_stdlib(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for local files shadowing stdlib modules."""
        from ..types import DiagnosticResult

        results = []
        stdlib_names = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else {
            "json", "sys", "os", "re", "collections", "typing", "pathlib"
        }

        for pyfile in project_root.rglob("*.py"):
            name = pyfile.stem
            if name in stdlib_names and pyfile.parent == project_root:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="stdlib_shadow",
                    status="warning",
                    message=f"Local file '{name}.py' shadows stdlib module",
                    details={"file": str(pyfile), "stdlib_module": name},
                    suggestion="Rename the file to avoid conflicts",
                    auto_fixable=False,
                    abs_path=str(pyfile),
                    line_number=None,
                ))

        return results

    def _check_stale_bytecode(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for stale .pyc files."""
        from ..types import DiagnosticResult

        results = []
        for pyc in project_root.rglob("*.pyc"):
            py = pyc.with_suffix(".py")
            if py.exists():
                if pyc.stat().st_mtime > py.stat().st_mtime:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="stale_bytecode",
                        status="warning",
                        message=f"Stale .pyc file: {pyc}",
                        details={"pyc_file": str(pyc), "py_file": str(py)},
                        suggestion="Run: find . -name '*.pyc' -delete",
                        auto_fixable=True,
                        abs_path=str(pyc),
                        line_number=None,
                    ))

        return results

    def _check_version_conflicts(self) -> list["DiagnosticResult"]:
        """Check for dependency version conflicts using pip check."""
        from ..types import DiagnosticResult
        results = []

        try:
            import subprocess
            import re

            # Run pip check to find conflicts
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0 and result.stdout:
                # Parse conflict lines
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if not line or "has requirement" not in line:
                        continue

                    # Extract package info from lines like:
                    # "package-a 1.0 has requirement package-b>=2.0, but you have package-b 1.0"
                    match = re.search(
                        r"(\S+)\s+(\S+)\s+has requirement\s+(.+?),\s+but you have\s+(.+)",
                        line
                    )
                    if match:
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="version_conflict",
                            status="error",
                            message=line,
                            details={
                                "package": match.group(1),
                                "version": match.group(2),
                                "requirement": match.group(3),
                                "installed": match.group(4),
                            },
                            suggestion="Upgrade/downgrade packages to resolve conflict",
                            auto_fixable=False,  # Risky to auto-fix version conflicts
                            abs_path=None,
                            line_number=None,
                        ))

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # pip not available or timeout
            pass

        return results

    def _check_missing_inits(self, project_root: Path) -> list["DiagnosticResult"]:
        """Find directories containing .py files but no __init__.py."""
        from ..types import DiagnosticResult

        results = []
        for root, dirs, files in os.walk(project_root):
            if "__pycache__" in root or ".git" in root or ".venv" in root:
                continue

            # If there are .py files, it might be a package
            if any(f.endswith(".py") for f in files) and "__init__.py" not in files:
                rel_path = Path(root).relative_to(project_root)
                if str(rel_path) == ".":
                    continue

                # Check if parent expects this to be a package
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="missing_init",
                    status="warning",
                    message=f"Directory '{rel_path}' contains .py files but no __init__.py",
                    details={"path": str(rel_path)},
                    suggestion=f"Create {rel_path}/__init__.py",
                    auto_fixable=True,
                    abs_path=os.path.join(root, "__init__.py"),
                ))
        return results

    def _check_deprecated_apis(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for use of deprecated standard library or third-party APIs."""
        from ..types import DiagnosticResult
        results = []
        DEPRECATED = {
            "distutils": "Use 'setuptools' or 'sysconfig' instead",
            "cgi": "Deprecated in Python 3.11+",
            "crypt": "Deprecated in Python 3.11+",
            "pkg_resources": "Use 'importlib.metadata' or 'importlib.resources'",
            "imp": "Use 'importlib' instead",
            "telnetlib": "Deprecated in Python 3.11+",
        }

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
                continue
            try:
                content = pyfile.read_text()
                imports = self._extract_imports(content)
                for imp in imports:
                    if imp in DEPRECATED:
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="deprecated_api",
                            status="warning",
                            message=f"Use of deprecated module '{imp}' in {pyfile.name}",
                            details={"module": imp, "alternative": DEPRECATED[imp]},
                            suggestion=DEPRECATED[imp],
                            auto_fixable=False,
                            abs_path=str(pyfile),
                        ))
            except Exception:
                pass
        return results

    def _check_import_source(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check if local modules are being overshadowed by installed packages."""
        from ..types import DiagnosticResult
        results = []
        # Find all local modules (top-level .py files or dirs with __init__.py)
        local_modules = []
        for item in project_root.iterdir():
            if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                local_modules.append(item.stem)
            elif item.is_dir() and (item / "__init__.py").exists():
                local_modules.append(item.name)

        # Check if any of these are also installed in site-packages
        try:
            installed = {
                pkg.metadata["Name"].lower(): pkg
                for pkg in __import__("importlib.metadata").metadata.distributions()
            }
            for mod in local_modules:
                if mod.lower() in installed:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="import_overshadow",
                        status="warning",
                        message=f"Local module '{mod}' has the same name as an installed package",
                        details={"installed_version": installed[mod.lower()].version},
                        suggestion=f"Rename local {mod} or be careful with import order",
                        auto_fixable=False,
                        abs_path=str(project_root / f"{mod}"),
                    ))
        except Exception:
            pass
        return results

    def _extract_imports(self, source: str) -> set[str]:
        """Extract top-level imports from source."""
        imports = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except SyntaxError:
            pass
        return imports

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose import-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, ModuleNotFoundError):
            module = self._extract_module_name(str(exc))
            return DiagnosticResult(
                category=self.category,
                check_name="missing_module",
                status="error",
                message=f"Module '{module}' not found",
                details={"module": module, "install_cmd": f"pip install {module}"},
                suggestion=f"pip install {module}",
                auto_fixable=True,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, ImportError):
            return DiagnosticResult(
                category=self.category,
                check_name="import_error",
                status="error",
                message=str(exc),
                details={"traceback": ctx.traceback_text[:500]},
                suggestion="Check import path and dependencies",
                auto_fixable=False,
                abs_path=os.path.abspath(ctx.source_file) if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None

    def _extract_module_name(self, msg: str) -> str:
        """Extract module name from error message."""
        # "No module named 'pandas'" -> "pandas"
        # Try to find quoted module name first (most reliable)
        match = __import__('re').search(r"['\"]([a-zA-Z_][a-zA-Z0-9_.]*)['\"]", msg)
        if match:
            return match.group(1).split(".")[0]
        # Fallback: try to find first module-like name
        match = __import__('re').search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", msg)
        if match:
            # Filter out common words that aren't modules
            word = match.group(1)
            if word.lower() not in ('no', 'named', 'module', 'the', 'a', 'an'):
                return word
        return "unknown"
