"""
pfix.validation — Test-driven fix validation.

After applying a fix, run tests to verify:
- If tests pass: keep the fix
- If tests fail: rollback to backup

Configuration:
    [tool.pfix]
    test_command = "pytest tests/ -x -q"
    test_timeout = 60
    rollback_on_test_failure = true
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console

from .config import get_config
from .types import ErrorContext, FixProposal

console = Console(stderr=True)


@dataclass
class ValidationResult:
    """Result of test validation."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    rollback_performed: bool = False


def run_tests(
    command: Optional[str] = None,
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None,
) -> ValidationResult:
    """
    Run tests and return result.

    Args:
        command: Test command (e.g., "pytest tests/ -x -q")
        timeout: Timeout in seconds
        cwd: Working directory for tests

    Returns:
        ValidationResult with success status and output
    """
    config = get_config()
    cmd = command or getattr(config, "test_command", "pytest tests/ -x -q")
    timeout_val = timeout or getattr(config, "test_timeout", 60)

    import time
    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_val,
            cwd=cwd,
        )
        duration_ms = int((time.time() - start) * 1000)

        return ValidationResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start) * 1000)
        return ValidationResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=f"Test command timed out after {timeout_val}s",
            duration_ms=duration_ms,
        )
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return ValidationResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=str(e),
            duration_ms=duration_ms,
        )


def validate_fix(
    source_file: Path,
    proposal: FixProposal,
    backup_path: Optional[Path] = None,
    command: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a fix by running tests.

    If tests fail and rollback is enabled, restore from backup.

    Args:
        source_file: Path to the fixed file
        proposal: The fix proposal that was applied
        backup_path: Path to backup file (if None, no rollback possible)
        command: Test command override

    Returns:
        ValidationResult with success status
    """
    config = get_config()
    should_rollback = getattr(config, "rollback_on_test_failure", True)

    # Run tests
    result = run_tests(command)

    if result.success:
        console.print(f"[green]✓ Tests passed after fix ({result.duration_ms}ms)[/]")
        return result

    # Tests failed
    console.print(f"[yellow]✗ Tests failed (exit code {result.exit_code})[/]")

    if should_rollback and backup_path and backup_path.exists():
        console.print(f"[yellow]  Rolling back {source_file}...[/]")
        try:
            # Restore from backup
            import shutil
            shutil.copy2(backup_path, source_file)
            console.print(f"[green]  ✓ Rolled back to {backup_path.name}[/]")
            result.rollback_performed = True
        except Exception as e:
            console.print(f"[red]  ✗ Rollback failed: {e}[/]")

    return result


def quick_validate_syntax(filepath: Path) -> bool:
    """Quick syntax validation for a single file."""
    import ast
    try:
        content = filepath.read_text(encoding="utf-8")
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def validate_with_fallback(
    ctx: ErrorContext,
    proposal: FixProposal,
    backup_path: Optional[Path],
) -> ValidationResult:
    """
    Full validation workflow with fallback.

    1. Validate syntax
    2. Run tests
    3. Rollback if needed
    """
    source_file = Path(ctx.source_file)

    # First: quick syntax check
    if proposal.has_code_fix and not quick_validate_syntax(source_file):
        console.print("[red]✗ Syntax error in fixed file - rolling back[/]")
        if backup_path and backup_path.exists():
            import shutil
            shutil.copy2(backup_path, source_file)
        return ValidationResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr="Syntax error in fixed file",
            duration_ms=0,
            rollback_performed=True,
        )

    # Run full test suite
    return validate_fix(source_file, proposal, backup_path)
