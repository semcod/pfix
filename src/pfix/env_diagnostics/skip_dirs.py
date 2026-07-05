"""Shared "should this path be skipped" logic for env_diagnostics tree walks.

Every diagnostic that walks a project tree needs to skip virtualenvs,
VCS metadata, and caches. Centralizing it here fixes two recurring bugs
found across the diagnostics:

1. Checks used ``if ".venv" in root: continue`` inside an ``os.walk`` loop
   without pruning ``dirs``, so the walk still fully recursed into every
   subdirectory of a populated virtualenv before each file got discarded —
   a real multi-minute-hang risk on any project with a populated venv.
2. Checks matched the skip name as a substring of the *full path string*
   (e.g. ``".venv" in str(path)``), which both over-matches (a project
   checked out under `~/.venvs/myproject/...` has every file excluded) and
   is unrelated to whether a path *component* is actually a venv/cache dir.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        "site-packages",
    }
)


def prune_walk_dirs(dirs: list[str]) -> None:
    """Mutate an ``os.walk`` ``dirs`` list in place to skip venvs/VCS/caches.

    Call this once per ``os.walk`` iteration, before processing files in
    the current directory, so the walk never descends into excluded dirs:

        for root, dirs, files in os.walk(project_root):
            prune_walk_dirs(dirs)
            ...
    """
    dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]


def has_skippable_component(path: Path | str) -> bool:
    """True if any path *component* (not substring of the full path) is a
    venv/VCS/cache directory name."""
    return any(part in SKIP_DIR_NAMES for part in Path(path).parts)


def walk_paths(root: Path, *, files_only: bool = False) -> Iterator[Path]:
    """``rglob("*")`` equivalent that prunes venvs/VCS/caches during the walk,
    instead of walking everything and filtering afterward."""
    for dirpath, dirs, files in os.walk(root):
        prune_walk_dirs(dirs)
        base = Path(dirpath)
        if not files_only:
            for d in dirs:
                yield base / d
        for f in files:
            yield base / f


def walk_py_files(root: Path) -> Iterator[Path]:
    """``rglob("*.py")`` equivalent that prunes venvs/VCS/caches during the walk."""
    for dirpath, dirs, files in os.walk(root):
        prune_walk_dirs(dirs)
        base = Path(dirpath)
        for f in files:
            if f.endswith(".py"):
                yield base / f
