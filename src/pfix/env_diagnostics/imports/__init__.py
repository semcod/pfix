"""
pfix.env_diagnostics.imports — Import and dependency diagnostic subpackage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Re-export helper modules
from .checks import (
    DEPRECATED_MODULES,
    check_deprecated_apis,
    check_import_source,
    check_missing_imports,
    check_missing_inits,
    check_shadow_stdlib,
    check_stale_bytecode,
    check_version_conflicts,
)
from .extractor import (
    extract_imports,
    extract_module_name,
    get_installed_packages,
    get_module_name,
    resolve_relative_import,
)
from .graph_builder import (
    build_import_graph,
    create_cycle_result,
    find_cycle_dfs,
)

if TYPE_CHECKING:
    from ..import_diagnostic import ImportDiagnostic

__all__ = [
    # extractor
    "extract_imports",
    "extract_module_name",
    "get_installed_packages",
    "get_module_name",
    "resolve_relative_import",
    # graph_builder
    "build_import_graph",
    "create_cycle_result",
    "find_cycle_dfs",
    "ImportDiagnostic",
    # checks
    "DEPRECATED_MODULES",
    "check_deprecated_apis",
    "check_import_source",
    "check_missing_imports",
    "check_missing_inits",
    "check_shadow_stdlib",
    "check_stale_bytecode",
    "check_version_conflicts",
]


def __getattr__(name: str):
    if name == "ImportDiagnostic":
        from ..import_diagnostic import ImportDiagnostic as _ImportDiagnostic

        globals()[name] = _ImportDiagnostic
        return _ImportDiagnostic
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
