"""
pfix.audit — Audit trail for all code modifications.

Logs every fix to .pfix/audit.jsonl with full metadata for compliance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console(stderr=True)

DEFAULT_AUDIT_DIR = Path(".pfix")
DEFAULT_AUDIT_FILE = DEFAULT_AUDIT_DIR / "audit.jsonl"


@dataclass
class AuditEntry:
    """Single audit entry for a fix operation."""

    timestamp: str
    file: str
    function: str
    error: str
    error_type: str
    fix_applied: bool
    diff: str
    model: str
    confidence: float
    approved_by: str  # "auto" or "user:username"
    rollback_available: bool
    backup_path: str
    file_hash_before: str
    file_hash_after: str


def _calculate_hash(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def log_fix_audit(
    filepath: Path,
    function_name: str,
    error: str,
    error_type: str,
    fix_applied: bool,
    diff: str,
    model: str,
    confidence: float,
    approved_by: str = "auto",
    backup_path: Optional[Path] = None,
    original_content: Optional[str] = None,
    new_content: Optional[str] = None,
) -> None:
    """
    Log a fix operation to audit trail.

    Args:
        filepath: Path to modified file
        function_name: Function where error occurred
        error: Error message
        error_type: Exception type
        fix_applied: Whether fix was applied
        diff: The diff/patch applied
        model: LLM model used
        confidence: Fix confidence score
        approved_by: Who approved the fix
        backup_path: Path to backup file
        original_content: File content before fix
        new_content: File content after fix
    """
    DEFAULT_AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    entry = AuditEntry(
        timestamp=datetime.now().isoformat(),
        file=str(filepath),
        function=function_name,
        error=error,
        error_type=error_type,
        fix_applied=fix_applied,
        diff=diff[:2000] if diff else "",  # Truncate long diffs
        model=model,
        confidence=confidence,
        approved_by=approved_by,
        rollback_available=backup_path is not None and backup_path.exists(),
        backup_path=str(backup_path) if backup_path else "",
        file_hash_before=_calculate_hash(original_content) if original_content else "",
        file_hash_after=_calculate_hash(new_content) if new_content else "",
    )

    # Append to audit log
    with open(DEFAULT_AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def read_audit_log(
    since: Optional[str] = None,
    filepath: Optional[str] = None,
    limit: int = 100,
) -> list[AuditEntry]:
    """
    Read audit log with optional filtering.

    Args:
        since: ISO timestamp to filter from
        filepath: Filter by file path
        limit: Max entries to return

    Returns:
        List of audit entries
    """
    if not DEFAULT_AUDIT_FILE.exists():
        return []

    entries = []
    with open(DEFAULT_AUDIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)

                # Apply filters
                if since and data.get("timestamp", "") < since:
                    continue
                if filepath and filepath not in data.get("file", ""):
                    continue

                entries.append(AuditEntry(**data))

                if len(entries) >= limit:
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    return entries


def get_audit_summary(days: int = 7) -> dict:
    """Get summary statistics from audit log."""
    from datetime import timedelta

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = read_audit_log(since=cutoff)

    total = len(entries)
    applied = sum(1 for e in entries if e.fix_applied)
    auto_approved = sum(1 for e in entries if e.approved_by == "auto")
    with_rollback = sum(1 for e in entries if e.rollback_available)

    by_model: dict[str, int] = {}
    for e in entries:
        by_model[e.model] = by_model.get(e.model, 0) + 1

    return {
        "period_days": days,
        "total_fixes": total,
        "fixes_applied": applied,
        "auto_approved": auto_approved,
        "user_approved": total - auto_approved,
        "rollback_available": with_rollback,
        "by_model": by_model,
        "avg_confidence": sum(e.confidence for e in entries) / total if total > 0 else 0,
    }


def print_audit_report(days: int = 7) -> None:
    """Print formatted audit report."""
    from rich.table import Table

    summary = get_audit_summary(days)

    console.print(f"\n[bold]Audit Report (Last {days} days)[/]")
    console.print(f"Total fixes: {summary['total_fixes']}")
    console.print(f"Applied: {summary['fixes_applied']}")
    console.print(f"Auto-approved: {summary['auto_approved']}")
    console.print(f"User-approved: {summary['user_approved']}")

    if summary['by_model']:
        table = Table(title="Fixes by Model")
        table.add_column("Model", style="cyan")
        table.add_column("Count", style="green")
        for model, count in sorted(summary['by_model'].items(), key=lambda x: -x[1]):
            table.add_row(model, str(count))
        console.print(table)

    # Recent entries
    entries = read_audit_log(limit=10)
    if entries:
        console.print("\n[bold]Recent Entries:[/]")
        for e in entries:
            status = "[green]✓[/]" if e.fix_applied else "[red]✗[/]"
            console.print(f"{status} {e.timestamp[:19]} {e.file.split('/')[-1]} - {e.error_type}")
