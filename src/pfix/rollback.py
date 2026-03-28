"""
pfix.rollback — Rollback manager for pfix fixes.

Usage:
    pfix rollback last              # Rollback most recent fix
    pfix rollback --file src/x.py # Rollback fixes in specific file
    pfix rollback --before 2026-03-27  # Rollback all fixes before date
    pfix history                    # Show fix history with rollback options
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from .audit import DEFAULT_AUDIT_FILE, read_audit_log

console = Console()


def find_backup_dir(filepath: Path) -> Path:
    """Find backup directory for a file."""
    return filepath.parent / ".pfix_backups"


def list_backups(filepath: Optional[Path] = None) -> list[Path]:
    """List available backup files."""
    backups = []

    if filepath:
        # Backups for specific file
        backup_dir = find_backup_dir(filepath)
        if backup_dir.exists():
            pattern = f"{filepath.name}.*.bak"
            backups.extend(backup_dir.glob(pattern))
    else:
        # All backups in project
        for backup_dir in Path.cwd().rglob(".pfix_backups"):
            backups.extend(backup_dir.glob("*.bak"))

    return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)


def rollback_last() -> bool:
    """Rollback the most recent fix."""
    entries = read_audit_log(limit=1)

    if not entries:
        console.print("[yellow]No fixes found in audit log[/]")
        return False

    entry = entries[0]

    if not entry.backup_path:
        console.print("[red]No backup available for last fix[/]")
        return False

    backup = Path(entry.backup_path)
    target = Path(entry.file)

    if not backup.exists():
        console.print(f"[red]Backup not found: {backup}[/]")
        return False

    try:
        shutil.copy2(backup, target)
        console.print(f"[green]✓ Rolled back {target.name} to {backup.name}[/]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Rollback failed: {e}[/]")
        return False


def rollback_file(filepath: str, before: Optional[str] = None) -> int:
    """
    Rollback all fixes to a specific file.

    Args:
        filepath: Path to file to rollback
        before: Only rollback fixes before this date (ISO format)

    Returns:
        Number of rollbacks performed
    """
    target = Path(filepath)
    backup_dir = find_backup_dir(target)

    if not backup_dir.exists():
        console.print(f"[yellow]No backups found for {filepath}[/]")
        return 0

    # Find all backups for this file
    pattern = f"{target.name}.*.bak"
    backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

    if not backups:
        console.print(f"[yellow]No backups found for {filepath}[/]")
        return 0

    # Filter by date if specified
    if before:
        before_dt = datetime.fromisoformat(before)
        backups = [
            b for b in backups
            if datetime.fromtimestamp(b.stat().st_mtime) < before_dt
        ]

    if not backups:
        console.print(f"[yellow]No backups matching criteria[/]")
        return 0

    # Rollback to oldest backup in range
    oldest = backups[0]

    try:
        shutil.copy2(oldest, target)
        console.print(f"[green]✓ Rolled back {target.name} to {oldest.name}[/]")
        console.print(f"  (rolled back {len(backups)} fix(es))")
        return len(backups)
    except Exception as e:
        console.print(f"[red]✗ Rollback failed: {e}[/]")
        return 0


def rollback_before(cutoff_date: str) -> int:
    """
    Rollback all fixes before a specific date.

    Args:
        cutoff_date: ISO date string (e.g., "2026-03-27")

    Returns:
        Number of rollbacks performed
    """
    entries = read_audit_log(since=cutoff_date)

    if not entries:
        console.print(f"[yellow]No fixes found before {cutoff_date}[/]")
        return 0

    count = 0
    rolled_files = set()

    for entry in entries:
        if entry.file in rolled_files:
            continue  # Already rolled back this file

        if entry.backup_path and Path(entry.backup_path).exists():
            if rollback_file(entry.file, before=cutoff_date):
                count += 1
                rolled_files.add(entry.file)

    console.print(f"[green]Rolled back {count} file(s)[/]")
    return count


def show_history(limit: int = 20) -> None:
    """Show fix history with rollback options."""
    entries = read_audit_log(limit=limit)

    if not entries:
        console.print("[yellow]No fix history found[/]")
        return

    table = Table(title="pfix History")
    table.add_column("#", style="dim", width=3)
    table.add_column("Time", style="cyan", width=16)
    table.add_column("File", style="green")
    table.add_column("Error", style="red", max_width=30)
    table.add_column("Status", style="yellow", width=8)
    table.add_column("Can Rollback", style="dim", width=12)

    for i, entry in enumerate(entries, 1):
        filename = entry.file.split("/")[-1][:25]
        error_type = entry.error_type[:28]
        status = "Applied" if entry.fix_applied else "Skipped"
        rollback = "Yes" if entry.rollback_available else "No"

        table.add_row(
            str(i),
            entry.timestamp[:16],
            filename,
            error_type,
            status,
            rollback,
        )

    console.print(table)
    console.print("\n[dim]Use 'pfix rollback last' or 'pfix rollback --file <path>'[/]")


def rollback_command(
    last: bool = False,
    filepath: Optional[str] = None,
    before: Optional[str] = None,
) -> bool:
    """
    Main entry point for rollback CLI command.

    Args:
        last: Rollback the most recent fix
        filepath: Rollback fixes for specific file
        before: Rollback all fixes before this date

    Returns:
        True if any rollbacks were performed
    """
    if last:
        return rollback_last()
    elif filepath:
        count = rollback_file(filepath, before=before)
        return count > 0
    elif before:
        count = rollback_before(before)
        return count > 0
    else:
        # Show history if no specific action
        show_history()
        return False
