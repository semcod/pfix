"""
pfix.dashboard — TUI Dashboard for pfix statistics and history.

Usage:
    pfix dashboard

Requires textual: pip install pfix[tui]
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live

console = Console()

# Try to import textual for full TUI, fall back to rich console
try:
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable, Static, Header, Footer, Label
    from textual.containers import Vertical, Horizontal
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


def get_log_stats(log_dir: Path = Path(".pfix_logs")) -> dict[str, Any]:
    """Calculate statistics from log files."""
    if not log_dir.exists():
        return {"total_events": 0, "fixes_applied": 0, "avg_confidence": 0.0, "recent_errors": []}

    stats = {"total": 0, "fixes": 0}
    confidences = []
    recent_errors = []

    # Read last 7 days of logs
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        log_file = log_dir / f"pfix_{date}.jsonl"
        if not log_file.exists():
            continue
        
        _process_log_file(log_file, stats, confidences, recent_errors)

    return {
        "total_events": stats["total"],
        "fixes_applied": stats["fixes"],
        "fix_rate": stats["fixes"] / stats["total"] if stats["total"] > 0 else 0,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
        "recent_errors": list(reversed(recent_errors)),
    }


def _process_log_file(log_file: Path, stats: dict, confidences: list, recent_errors: list):
    """Process single log file and update stats/history."""
    try:
        content = log_file.read_text(encoding="utf-8").strip()
        if not content:
            return

        for line in content.split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
                _update_stats_from_entry(entry, stats, confidences, recent_errors)
            except json.JSONDecodeError:
                continue
    except Exception:
        pass


def _update_stats_from_entry(entry: dict, stats: dict, confidences: list, recent_errors: list):
    """Update stats and recent errors from a single log entry."""
    stats["total"] += 1
    if entry.get("fix_applied"):
        stats["fixes"] += 1
    
    conf = entry.get("confidence", 0)
    if conf:
        confidences.append(conf)

    # Collect recent errors (limited to 10)
    if len(recent_errors) < 10:
        recent_errors.append({
            "time": entry.get("timestamp", "?")[11:19] if entry.get("timestamp") else "?",
            "type": entry.get("exception_type", "Unknown"),
            "file": entry.get("source_file", "?").split("/")[-1],
            "confidence": conf,
        })


def get_cache_stats(cache_dir: Path = Path(".pfix_cache")) -> dict[str, Any]:
    """Get cache statistics."""
    db_file = cache_dir / "fixes.db"
    if not db_file.exists():
        return {"valid_entries": 0}

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        cursor = conn.execute("SELECT COUNT(*) FROM fix_cache")
        total = cursor.fetchone()[0]
        conn.close()
        return {"valid_entries": total}
    except Exception:
        return {"valid_entries": 0}


def render_dashboard() -> Layout:
    """Render rich console dashboard."""
    layout = Layout()

    # Header
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
    )

    # Header content
    header = Panel(
        "[bold green]🔧 pfix Dashboard[/] - Real-time error analysis stats",
        border_style="green",
    )
    layout["header"].update(header)

    # Main split
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="recent", ratio=2),
    )

    # Stats
    log_stats = get_log_stats()
    cache_stats = get_cache_stats()

    stats_table = Table(title="Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    stats_table.add_row("Total Events", str(log_stats["total_events"]))
    stats_table.add_row("Fixes Applied", str(log_stats["fixes_applied"]))
    stats_table.add_row("Fix Rate", f"{log_stats['fix_rate']:.1%}")
    stats_table.add_row("Avg Confidence", f"{log_stats['avg_confidence']:.1%}")
    stats_table.add_row("Cache Entries", str(cache_stats["valid_entries"]))

    layout["stats"].update(Panel(stats_table, border_style="blue"))

    # Recent errors
    recent_table = Table(title="Recent Errors (Last 24h)")
    recent_table.add_column("Time", style="dim", width=8)
    recent_table.add_column("Type", style="red")
    recent_table.add_column("File", style="cyan")
    recent_table.add_column("Confidence", style="green", justify="right")

    for err in log_stats["recent_errors"][:10]:
        recent_table.add_row(
            err["time"],
            err["type"][:30],
            err["file"][:30],
            f"{err['confidence']:.0%}" if err["confidence"] else "N/A",
        )

    layout["recent"].update(Panel(recent_table, border_style="yellow"))

    return layout


def run_console_dashboard() -> None:
    """Run rich console-based dashboard."""
    console.clear()
    layout = render_dashboard()
    console.print(layout)


# Textual App (if available)
if TEXTUAL_AVAILABLE:
    class PfixDashboardApp(App):
        """Textual TUI Dashboard."""

        CSS = """
        Screen {
            layout: grid;
            grid-size: 2;
            grid-columns: 1fr 2fr;
        }
        .stats {
            border: solid green;
        }
        .recent {
            border: solid yellow;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("Statistics", classes="stats")
            yield Static("Recent Errors", classes="recent")
            yield Footer()

        def on_mount(self) -> None:
            self.title = "pfix Dashboard"


def run_dashboard() -> None:
    """Main entry point for dashboard command."""
    if TEXTUAL_AVAILABLE:
        try:
            app = PfixDashboardApp()
            app.run()
        except Exception as e:
            console.print(f"[yellow]Textual failed, using console: {e}[/]")
            run_console_dashboard()
    else:
        console.print("[dim]Textual not installed, using console view[/]")
        run_console_dashboard()
