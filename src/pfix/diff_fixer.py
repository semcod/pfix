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
        if lines[i].startswith("--- "):
            old_path, new_path, next_i = _parse_file_header(lines, i)
            hunk_lines, next_i = _collect_hunk_lines(lines, next_i)
            hunks.append((old_path, new_path, hunk_lines))
            i = next_i
        else:
            i += 1

    return hunks


def _parse_file_header(lines: list[str], i: int) -> tuple[str, str, int]:
    """Parse --- and +++ lines."""
    old_line = lines[i]
    old_path = old_line[4:].split("\t")[0].strip()
    
    i += 1
    if i >= len(lines):
        raise DiffParseError("Unexpected end of diff after ---")

    new_line = lines[i]
    if not new_line.startswith("+++ "):
        raise DiffParseError(f"Expected +++ after ---, got: {new_line[:20]}")
    
    new_path = new_line[4:].split("\t")[0].strip()
    return old_path, new_path, i + 1


def _collect_hunk_lines(lines: list[str], i: int) -> tuple[list[str], int]:
    """Collect lines belonging to a hunk until next file or end."""
    hunk_lines = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- "):
            break
        
        if any(line.startswith(p) for p in ("@@", "+", "-", " ")) or line == "":
            hunk_lines.append(line)
            i += 1
        else:
            break
    return hunk_lines, i


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
    Returns New lines with hunk applied.
    """
    if not hunk_lines:
        return old_lines[:]

    header = hunk_lines[0]
    if not header.startswith("@@"):
        raise DiffParseError(f"Hunk must start with @@, got: {header[:20]}")

    _, old_count, _, _ = parse_hunk_header(header)
    start_idx = old_start - 1
    
    processed_lines, lines_consumed = _process_hunk_body(hunk_lines[1:], old_lines[start_idx:])
    
    return old_lines[:start_idx] + processed_lines + old_lines[start_idx + old_count:]


def _process_hunk_body(hunk_lines: list[str], old_lines_from_start: list[str]) -> tuple[list[str], int]:
    """Process lines within a hunk body and return new lines and count of old lines consumed."""
    new_lines = []
    old_ptr = 0
    
    for line in hunk_lines:
        if not line: continue
        
        if line.startswith("-"):
            old_ptr += 1
        elif line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith(" "):
            if old_ptr < len(old_lines_from_start):
                new_lines.append(old_lines_from_start[old_ptr])
            old_ptr += 1
            
    return new_lines, old_ptr


def apply_diff(
    original_content: str,
    diff_text: str,
) -> str:
    """
    Apply unified diff to original content.
    Returns New content with diff applied.
    """
    hunks = parse_unified_diff(diff_text)

    if not hunks:
        raise DiffParseError("No hunks found in diff")

    if len(hunks) > 1:
        console.print("[yellow]⚠ Multi-file diff detected, using first hunk[/]")

    old_path, new_path, hunk_lines = hunks[0]

    if not hunk_lines or not hunk_lines[0].startswith("@@"):
        raise DiffParseError("Hunk missing @@ header")

    header = hunk_lines[0]
    old_start, _, _, _ = parse_hunk_header(header)

    old_lines = original_content.splitlines(keepends=True)
    if not any(line.endswith("\n") for line in old_lines if line):
        old_lines = [line + "\n" for line in original_content.splitlines()]

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
