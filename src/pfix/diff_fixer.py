"""
pfix.diff_fixer — Diff-based fix application.

Instead of replacing entire files, apply unified diffs from LLM.
Benefits: fewer tokens, precise changes, easier review.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console(stderr=True)


class DiffParseError(Exception):
    """Raised when diff parsing fails."""
    pass


def parse_unified_diff(diff_text: str) -> list[tuple[str, str, list[str]]]:
    """
    Parse unified diff text into hunks.

    Returns list of (old_path, new_path, hunk_lines).
    """
    hunks = []
    lines = diff_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for diff header
        if line.startswith("--- "):
            old_path = line[4:].split("\t")[0].strip()
            i += 1
            if i >= len(lines):
                raise DiffParseError("Unexpected end of diff after ---")

            new_line = lines[i]
            if not new_line.startswith("+++ "):
                raise DiffParseError(f"Expected +++ after ---, got: {new_line[:20]}")
            new_path = new_line[4:].split("\t")[0].strip()
            i += 1

            # Collect hunk lines
            hunk_lines = []
            while i < len(lines):
                line = lines[i]
                if line.startswith("--- "):
                    # Next file
                    break
                if line.startswith("@@") or line.startswith("+") or line.startswith("-") or line.startswith(" ") or line == "":
                    hunk_lines.append(line)
                    i += 1
                else:
                    break

            hunks.append((old_path, new_path, hunk_lines))
        else:
            i += 1

    return hunks


def parse_hunk_header(line: str) -> tuple[int, int, int, int]:
    """
    Parse hunk header like @@ -1,5 +1,7 @@.

    Returns (old_start, old_count, new_start, new_count).
    """
    match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not match:
        raise DiffParseError(f"Invalid hunk header: {line}")

    old_start = int(match.group(1))
    old_count = int(match.group(2)) if match.group(2) else 1
    new_start = int(match.group(3))
    new_count = int(match.group(4)) if match.group(4) else 1

    return old_start, old_count, new_start, new_count


def apply_hunk(
    old_lines: list[str],
    hunk_lines: list[str],
    old_start: int,
) -> list[str]:
    """
    Apply a single hunk to old_lines.

    Args:
        old_lines: Original file lines
        hunk_lines: Diff hunk lines (starting with @@)
        old_start: 1-based starting line in old file

    Returns:
        New lines with hunk applied
    """
    if not hunk_lines:
        return old_lines[:]

    # Parse hunk header
    header = hunk_lines[0]
    if not header.startswith("@@"):
        raise DiffParseError(f"Hunk must start with @@, got: {header[:20]}")

    _, old_count, _, _ = parse_hunk_header(header)

    # Convert to 0-based index
    start_idx = old_start - 1

    # Collect context and changes
    old_idx = start_idx
    new_lines = old_lines[:start_idx]  # Lines before hunk

    # Process each line in hunk
    for line in hunk_lines[1:]:
        if not line:
            continue

        if line.startswith("-"):
            # Removed line - skip from old
            old_idx += 1
        elif line.startswith("+"):
            # Added line
            new_lines.append(line[1:])
        elif line.startswith(" "):
            # Context line - copy from old
            if old_idx < len(old_lines):
                new_lines.append(old_lines[old_idx])
            old_idx += 1
        # Skip other lines (like \\ No newline at end of file)

    # Add remaining lines after hunk
    # We consumed old_count lines from old
    end_idx = start_idx + old_count
    new_lines.extend(old_lines[end_idx:])

    return new_lines


def apply_diff(
    original_content: str,
    diff_text: str,
) -> str:
    """
    Apply unified diff to original content.

    Args:
        original_content: Original file content
        diff_text: Unified diff

    Returns:
        New content with diff applied
    """
    hunks = parse_unified_diff(diff_text)

    if not hunks:
        raise DiffParseError("No hunks found in diff")

    # For now, only support single-file diffs
    if len(hunks) > 1:
        # Multiple files - just apply first hunk
        console.print("[yellow]⚠ Multi-file diff detected, using first hunk[/]")

    old_path, new_path, hunk_lines = hunks[0]

    # Parse hunk header for line numbers
    if not hunk_lines or not hunk_lines[0].startswith("@@"):
        raise DiffParseError("Hunk missing @@ header")

    header = hunk_lines[0]
    old_start, _, _, _ = parse_hunk_header(header)

    # Apply to content
    old_lines = original_content.splitlines(keepends=True)

    # Normalize line endings
    if not any(line.endswith("\n") for line in old_lines if line):
        old_lines = original_content.splitlines()
        old_lines = [line + "\n" for line in old_lines]

    new_lines = apply_hunk(old_lines, hunk_lines, old_start)

    return "".join(new_lines)


def apply_diff_to_file(
    filepath: Path,
    diff_text: str,
    create_backup: bool = True,
) -> bool:
    """
    Apply diff directly to file.

    Args:
        filepath: Path to file to modify
        diff_text: Unified diff text
        create_backup: Create .bak file before modifying

    Returns:
        True if successful
    """
    try:
        original = filepath.read_text(encoding="utf-8")

        if create_backup:
            backup = filepath.with_suffix(filepath.suffix + ".bak")
            backup.write_text(original, encoding="utf-8")

        new_content = apply_diff(original, diff_text)

        # Validate syntax
        import ast
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            console.print(f"[red]✗ Syntax error in diff result: {e}[/]")
            return False

        filepath.write_text(new_content, encoding="utf-8")
        return True

    except DiffParseError as e:
        console.print(f"[red]✗ Failed to parse diff: {e}[/]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Failed to apply diff: {e}[/]")
        return False


def create_unified_diff(
    old_content: str,
    new_content: str,
    old_path: str = "a/file.py",
    new_path: str = "b/file.py",
) -> str:
    """
    Create unified diff between old and new content.

    This is a convenience wrapper around difflib.
    """
    import difflib

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    return "".join(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_path,
        tofile=new_path,
    ))
