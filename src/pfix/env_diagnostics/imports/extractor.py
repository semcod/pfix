"""
pfix.env_diagnostics.imports.extractor — Import extraction utilities.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...types import DiagnosticResult


def extract_imports(source: str) -> set[str]:
    """Extract top-level imports from source code."""
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


def get_module_name(pyfile: Path, project_root: Path) -> str:
    """Convert a file path to a module name."""
    rel_path = pyfile.relative_to(project_root)
    if pyfile.name == "__init__.py":
        return str(rel_path.parent).replace(os.sep, ".")
    return str(rel_path.with_suffix("")).replace(os.sep, ".")


def resolve_relative_import(node: ast.ImportFrom, module_name: str) -> str:
    """Convert a relative import to an absolute module name."""
    parts = module_name.split(".")
    base = parts[:-node.level] if node.level <= len(parts) else []
    if node.module:
        return ".".join(base + [node.module])
    return ".".join(base)


def extract_module_name(msg: str) -> str:
    """Extract module name from error message."""
    # "No module named 'pandas'" -> "pandas"
    # Try to find quoted module name first (most reliable)
    match = re.search(r"['\"]([a-zA-Z_][a-zA-Z0-9_.]*)['\"]", msg)
    if match:
        return match.group(1).split(".")[0]
    # Fallback: try to find first module-like name
    match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", msg)
    if match:
        # Filter out common words that aren't modules
        word = match.group(1)
        if word.lower() not in ('no', 'named', 'module', 'the', 'a', 'an'):
            return word
    return "unknown"


def get_installed_packages() -> set[str]:
    """Get lowercase names of currently installed packages."""
    try:
        return {
            pkg.metadata["Name"].lower()
            for pkg in __import__("importlib.metadata").metadata.distributions()
        }
    except Exception:
        return set()
