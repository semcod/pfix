#!/usr/bin/env python3
"""
pfix pre-commit hook — Check syntax and dependencies before commit.

Usage in .pre-commit-config.yaml:
    repos:
      - repo: https://github.com/softreck/pfix
        rev: v0.3.0
        hooks:
          - id: pfix-check
            name: pfix syntax & deps check
            language: python
            types: [python]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def check_syntax(filepath: Path) -> tuple[bool, str]:
    """Check Python file syntax."""
    try:
        content = filepath.read_text(encoding="utf-8")
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error in {filepath}:{e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading {filepath}: {e}"


def check_imports(filepath: Path) -> tuple[bool, list[str]]:
    """Check for potentially missing imports."""
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        # Check against stdlib
        stdlib_modules = getattr(sys, "stdlib_module_names", set())
        third_party = imports - stdlib_modules - {"__future__"}

        # Try to check if they're available
        missing = []
        for module in third_party:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        return len(missing) == 0, missing
    except Exception:
        return True, []


def main(argv: list[str] | None = None) -> int:
    """Pre-commit hook entry point."""
    parser = argparse.ArgumentParser(description="pfix pre-commit hook")
    parser.add_argument("files", nargs="*", help="Files to check")
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency checking",
    )
    args = parser.parse_args(argv)

    files = [Path(f) for f in args.files if f.endswith(".py")]

    if not files:
        return 0

    errors = []

    for filepath in files:
        # Check syntax
        ok, msg = check_syntax(filepath)
        if not ok:
            errors.append(msg)
            continue

        # Check imports
        if not args.skip_deps:
            ok, missing = check_imports(filepath)
            if not ok:
                errors.append(f"{filepath}: Potentially missing imports: {', '.join(missing)}")

    if errors:
        print("pfix pre-commit errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1

    print(f"pfix: Checked {len(files)} files ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
