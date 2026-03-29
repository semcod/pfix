"""
pfix.env_diagnostics.imports.graph_builder — Dependency graph construction.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...types import DiagnosticResult

from .extractor import get_module_name, resolve_relative_import


def build_import_graph(
    project_root: Path
) -> tuple[dict[str, set[str]], dict[str, Path]]:
    """Build import dependency graph from project files."""
    module_imports: dict[str, set[str]] = {}
    module_paths: dict[str, Path] = {}

    for pyfile in project_root.rglob("*.py"):
        if "__pycache__" in str(pyfile) or ".venv" in str(pyfile):
            continue

        module_name = get_module_name(pyfile, project_root)
        module_paths[module_name] = pyfile

        try:
            tree = ast.parse(pyfile.read_text())
            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.level > 0:
                        imports.add(resolve_relative_import(node, module_name))
                    else:
                        imports.add(node.module.split(".")[0])

            module_imports[module_name] = imports
        except (SyntaxError, UnicodeDecodeError):
            pass

    return module_imports, module_paths


def find_cycle_dfs(
    start: str,
    visited: set[str],
    path: list[str],
    module_imports: dict[str, set[str]]
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
            cycle = find_cycle_dfs(imp, visited, path + [start], module_imports)
            if cycle:
                return cycle
    return None


def create_cycle_result(
    cycle: list[str],
    module_paths: dict[str, Path],
    checked: set,
    category: str,
) -> "DiagnosticResult" | None:
    """Create a DiagnosticResult for a detected cycle.

    Returns:
        DiagnosticResult if new cycle, None if already reported
    """
    from ...types import DiagnosticResult

    # Check if we already reported this cycle
    cycle_key = tuple(sorted(cycle[:-1]))
    if cycle_key in checked:
        return None
    checked.add(cycle_key)

    cycle_str = " -> ".join(cycle)
    file_path = str(module_paths.get(cycle[0], "unknown"))

    return DiagnosticResult(
        category=category,
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
