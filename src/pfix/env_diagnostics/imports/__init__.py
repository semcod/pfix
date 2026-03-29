"""
pfix.env_diagnostics.imports — Import and dependency diagnostic subpackage.
"""

from __future__ import annotations

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
