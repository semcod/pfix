"""
pfix.env_diagnostics.imports.checks — Specific import diagnostic checks.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...types import DiagnosticResult

from .extractor import extract_imports, get_installed_packages


def check_missing_imports(
    project_root: Path,
    category: str,
    get_all_project_imports: callable,
) -> list["DiagnosticResult"]:
    """Check for imports that aren't installed."""
    from ...types import DiagnosticResult

    results = []

    try:
        all_imports = get_all_project_imports(project_root)
        installed = get_installed_packages()
        stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()

        for imp in all_imports:
            top = imp.split(".")[0].lower()
            if top not in installed and top not in stdlib and not top.startswith("_"):
                results.append(DiagnosticResult(
                    category=category,
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


def check_shadow_stdlib(project_root: Path, category: str) -> list["DiagnosticResult"]:
    """Check for local files shadowing stdlib modules."""
    from ...types import DiagnosticResult

    results = []
    stdlib_names = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else {
        "json", "sys", "os", "re", "collections", "typing", "pathlib"
    }

    for pyfile in project_root.rglob("*.py"):
        name = pyfile.stem
        if name in stdlib_names and pyfile.parent == project_root:
            results.append(DiagnosticResult(
                category=category,
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


def check_stale_bytecode(project_root: Path, category: str) -> list["DiagnosticResult"]:
    """Check for stale .pyc files."""
    from ...types import DiagnosticResult

    results = []
    for pyc in project_root.rglob("*.pyc"):
        py = pyc.with_suffix(".py")
        if py.exists():
            if pyc.stat().st_mtime > py.stat().st_mtime:
                results.append(DiagnosticResult(
                    category=category,
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


def check_version_conflicts(category: str) -> list["DiagnosticResult"]:
    """Check for dependency version conflicts using pip check."""
    from ...types import DiagnosticResult
    results = []

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0 and result.stdout:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line or "has requirement" not in line:
                    continue

                match = re.search(
                    r"(\S+)\s+(\S+)\s+has requirement\s+(.+?),\s+but you have\s+(.+)",
                    line
                )
                if match:
                    results.append(DiagnosticResult(
                        category=category,
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
                        auto_fixable=False,
                        abs_path=None,
                        line_number=None,
                    ))

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return results


def check_missing_inits(project_root: Path, category: str) -> list["DiagnosticResult"]:
    """Find directories containing .py files but no __init__.py."""
    from ...types import DiagnosticResult

    results = []
    for root, dirs, files in os.walk(project_root):
        if "__pycache__" in root or ".git" in root or ".venv" in root:
            continue

        if any(f.endswith(".py") for f in files) and "__init__.py" not in files:
            rel_path = Path(root).relative_to(project_root)
            if str(rel_path) == ".":
                continue

            results.append(DiagnosticResult(
                category=category,
                check_name="missing_init",
                status="warning",
                message=f"Directory '{rel_path}' contains .py files but no __init__.py",
                details={"path": str(rel_path)},
                suggestion=f"Create {rel_path}/__init__.py",
                auto_fixable=True,
                abs_path=os.path.join(root, "__init__.py"),
            ))
    return results


# Deprecated API mappings
DEPRECATED_MODULES = {
    "distutils": "Use 'setuptools' or 'sysconfig' instead",
    "cgi": "Deprecated in Python 3.11+",
    "crypt": "Deprecated in Python 3.11+",
    "pkg_resources": "Use 'importlib.metadata' or 'importlib.resources'",
    "imp": "Use 'importlib' instead",
    "telnetlib": "Deprecated in Python 3.11+",
}


def check_deprecated_apis(project_root: Path, category: str) -> list["DiagnosticResult"]:
    """Check for use of deprecated standard library or third-party APIs."""
    from ...types import DiagnosticResult
    results = []

    for pyfile in project_root.rglob("*.py"):
        if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
            continue
        try:
            content = pyfile.read_text()
            imports = extract_imports(content)
            for imp in imports:
                if imp in DEPRECATED_MODULES:
                    results.append(DiagnosticResult(
                        category=category,
                        check_name="deprecated_api",
                        status="warning",
                        message=f"Use of deprecated module '{imp}' in {pyfile.name}",
                        details={"module": imp, "alternative": DEPRECATED_MODULES[imp]},
                        suggestion=DEPRECATED_MODULES[imp],
                        auto_fixable=False,
                        abs_path=str(pyfile),
                    ))
        except Exception:
            pass
    return results


def check_import_source(project_root: Path, category: str) -> list["DiagnosticResult"]:
    """Check if local modules are being overshadowed by installed packages."""
    from ...types import DiagnosticResult
    results = []

    local_modules = []
    for item in project_root.iterdir():
        if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
            local_modules.append(item.stem)
        elif item.is_dir() and (item / "__init__.py").exists():
            local_modules.append(item.name)

    try:
        installed = {
            pkg.metadata["Name"].lower(): pkg
            for pkg in __import__("importlib.metadata").metadata.distributions()
        }
        for mod in local_modules:
            if mod.lower() in installed:
                results.append(DiagnosticResult(
                    category=category,
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
