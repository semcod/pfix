#!/usr/bin/env python3
"""
Run all pfix examples and reset to original state.

Usage:
    python run_all.py           # Run all tests interactively
    python run_all.py --reset   # Only reset without running tests
    python run_all.py --dry-run # Show what would be run without executing
"""

import subprocess
import sys
from pathlib import Path
import argparse


EXAMPLES = [
    ("types", "main.py"),
    ("data", "main.py"),
    ("concurrency", "main.py"),
    ("network", "main.py"),
    ("memory", "main.py"),
    ("imports", "main.py"),
    ("edge_cases", "main.py"),
    ("encoding", "main.py"),
    ("filesystem", "main.py"),
    ("environment", "main.py"),
    ("deps", "main.py"),
    ("production", "main.py"),
]


def run_example(examples_dir: Path, category: str, script: str) -> bool:
    """Run a single example and return success status."""
    example_path = examples_dir / category / script
    if not example_path.exists():
        print(f"  ⚠ Skipping {category}/{script} (not found)")
        return True

    print(f"\n{'='*60}")
    print(f"Running: {category}/{script}")
    print('='*60)

    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=examples_dir / category,
            timeout=120,
            capture_output=False,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Timeout for {category}/{script}")
        return False
    except Exception as e:
        print(f"  ✗ Error running {category}/{script}: {e}")
        return False


def reset_examples(examples_dir: Path) -> bool:
    """Reset all examples to original state using git."""
    repo_root = examples_dir.parent

    files_to_reset = [
        f"examples/{cat}/{file}"
        for cat, file in EXAMPLES
    ]

    # Add other example files
    files_to_reset.extend([
        # Types
        "examples/types/attribute_errors.py",
        "examples/types/type_errors.py",
        "examples/types/pattern_errors.py",
        # Data
        "examples/data/numeric_errors.py",
        "examples/data/parse_errors.py",
        # Concurrency
        "examples/concurrency/async_mistakes.py",
        "examples/concurrency/race_conditions.py",
        # Network
        "examples/network/connection_errors.py",
        # Memory
        "examples/memory/recursion_and_alloc.py",
        "examples/memory/resource_leaks.py",
        # Imports
        "examples/imports/circular.py",
        "examples/imports/missing_module.py",
        "examples/imports/shadowing.py",
        "examples/imports/wrong_names.py",
        "examples/imports/platform_specific.py",
        # Edge cases
        "examples/edge_cases/class_errors.py",
        "examples/edge_cases/python_gotchas.py",
        "examples/edge_cases/tricky_errors.py",
        # Encoding
        "examples/encoding/codec_errors.py",
        "examples/encoding/unicode_errors.py",
        # Filesystem
        "examples/filesystem/file_errors.py",
        # Environment
        "examples/environment/env_var_errors.py",
        "examples/environment/venv_issues.py",
        # Deps
        "examples/deps/package_traps.py",
        "examples/deps/version_conflicts.py",
        "examples/deps/requirements.txt",
        # Production
        "examples/production/api_patterns.py",
        "examples/production/cascading_errors.py",
        "examples/production/degradation.py",
    ])

    print("\n" + "="*60)
    print("RESETTING: Restoring original buggy versions...")
    print("="*60)

    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(repo_root)

        cmd = ["git", "checkout", "HEAD", "--"] + files_to_reset
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ All examples reset to original state")
            return True
        else:
            print(f"✗ Reset failed: {result.stderr}", file=sys.stderr)
            return False
    finally:
        os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(
        description="Run all pfix examples and optionally reset"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Only reset without running tests"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be run without executing"
    )
    parser.add_argument(
        "--no-reset", action="store_true",
        help="Run tests but don't reset at the end"
    )
    args = parser.parse_args()

    examples_dir = Path(__file__).parent
    repo_root = examples_dir.parent

    if args.dry_run:
        print("Would run the following examples:")
        for cat, file in EXAMPLES:
            print(f"  - {cat}/{file}")
        print("\nWould then reset all files to original state")
        return

    if args.reset:
        reset_examples(examples_dir)
        return

    # Run all examples
    print("="*60)
    print("RUNNING ALL PFIX EXAMPLES")
    print("="*60)

    passed = 0
    failed = 0

    for category, script in EXAMPLES:
        if run_example(examples_dir, category, script):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("="*60)

    # Always reset at the end unless --no-reset is specified
    if not args.no_reset:
        reset_examples(examples_dir)
    else:
        print("\n⚠ Skipping reset (--no-reset specified)")
        print("  Modified files kept. Use 'python reset.py' to restore.")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
