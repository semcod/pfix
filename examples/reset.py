#!/usr/bin/env python3
"""
Reset script for pfix examples.

Restores all example files to their original buggy state using git checkout.
This allows re-running pfix demonstrations from scratch.
"""

import subprocess
import sys
from pathlib import Path


def run_git_checkout(paths: list[str]) -> bool:
    """Run git checkout to restore files."""
    cmd = ["git", "checkout", "HEAD", "--"] + paths
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return False
    return True


def main():
    """Reset all example directories to original buggy state."""
    examples_dir = Path(__file__).parent
    repo_root = examples_dir.parent

    # Files to reset (all example scripts and main.py files)
    files_to_reset = [
        # Types
        "examples/types/main.py",
        "examples/types/attribute_errors.py",
        "examples/types/type_errors.py",
        "examples/types/pattern_errors.py",
        # Data
        "examples/data/main.py",
        "examples/data/numeric_errors.py",
        "examples/data/parse_errors.py",
        # Concurrency
        "examples/concurrency/main.py",
        "examples/concurrency/async_mistakes.py",
        "examples/concurrency/race_conditions.py",
        # Network
        "examples/network/main.py",
        "examples/network/connection_errors.py",
        # Memory
        "examples/memory/main.py",
        "examples/memory/recursion_and_alloc.py",
        "examples/memory/resource_leaks.py",
        # Imports
        "examples/imports/main.py",
        "examples/imports/circular.py",
        "examples/imports/missing_module.py",
        "examples/imports/shadowing.py",
        "examples/imports/wrong_names.py",
        "examples/imports/platform_specific.py",
        # Edge cases
        "examples/edge_cases/main.py",
        "examples/edge_cases/class_errors.py",
        "examples/edge_cases/python_gotchas.py",
        "examples/edge_cases/tricky_errors.py",
        # Encoding
        "examples/encoding/main.py",
        "examples/encoding/codec_errors.py",
        "examples/encoding/unicode_errors.py",
        # Filesystem
        "examples/filesystem/main.py",
        "examples/filesystem/file_errors.py",
        # Environment
        "examples/environment/main.py",
        "examples/environment/env_var_errors.py",
        "examples/environment/venv_issues.py",
        # Deps
        "examples/deps/main.py",
        "examples/deps/package_traps.py",
        "examples/deps/version_conflicts.py",
        "examples/deps/requirements.txt",
        # Production
        "examples/production/main.py",
        "examples/production/api_patterns.py",
        "examples/production/cascading_errors.py",
        "examples/production/degradation.py",
    ]

    print("Resetting pfix examples to original buggy state...")
    print("=" * 60)

    # Change to repo root
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(repo_root)

        # Run git checkout
        if run_git_checkout(files_to_reset):
            print("✓ All example files restored successfully")
            print("\nYou can now run examples with pfix to see automatic fixes:")
            print("  cd examples/types && python main.py")
            print("  cd examples/data && python main.py")
            print("  etc.")
        else:
            print("✗ Failed to restore some files", file=sys.stderr)
            sys.exit(1)
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
