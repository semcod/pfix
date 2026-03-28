"""
pfix.logging — Structured logging for fix operations.

Each analysis/fix generates structured FixEvent.
Exports: JSON Lines, SQLite, optional Sentry integration.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .types import ErrorContext, FixProposal

DEFAULT_LOG_DIR = Path(".pfix_logs")


@dataclass
class FixEvent:
    """Structured log event for each fix operation."""

    timestamp: str = ""
    exception_type: str = ""
    exception_message: str = ""
    source_file: str = ""
    function_name: str = ""
    error_category: str = ""
    diagnosis: str = ""
    fix_applied: bool = False
    confidence: float = 0.0
    duration_ms: int = 0
    llm_model: str = ""
    llm_tokens_used: int = 0
    dependencies_installed: list[str] = field(default_factory=list)
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class JsonLinesLogger:
    """JSON Lines format logger for FixEvents."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = self._get_log_file()

    def _get_log_file(self) -> Path:
        """Get current log file (rotated daily)."""
        date = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"pfix_{date}.jsonl"

    def log(self, event: FixEvent) -> None:
        """Append event to JSON Lines file."""
        # Rotate if needed
        log_file = self._get_log_file()

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")

    def read_events(self, days: int = 7) -> list[FixEvent]:
        """Read events from last N days."""
        events = []
        for i in range(days):
            date = (datetime.now() - __import__("datetime").timedelta(days=i)).strftime("%Y%m%d")
            log_file = self.log_dir / f"pfix_{date}.jsonl"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                events.append(FixEvent(**data))
                            except (json.JSONDecodeError, TypeError):
                                continue
        return events


class SQLiteLogger:
    """SQLite-based logger for FixEvents with querying capabilities."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = DEFAULT_LOG_DIR / "events.db"
        self.db_path = db_path
        DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fix_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                exception_type TEXT,
                exception_message TEXT,
                source_file TEXT,
                function_name TEXT,
                error_category TEXT,
                diagnosis TEXT,
                fix_applied INTEGER,
                confidence REAL,
                duration_ms INTEGER,
                llm_model TEXT,
                llm_tokens_used INTEGER,
                dependencies_installed TEXT,
                cost_usd REAL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON fix_events(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_exception ON fix_events(exception_type)
        """)
        conn.commit()
        conn.close()

    def log(self, event: FixEvent) -> None:
        """Insert event into database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            INSERT INTO fix_events
            (timestamp, exception_type, exception_message, source_file, function_name,
             error_category, diagnosis, fix_applied, confidence, duration_ms,
             llm_model, llm_tokens_used, dependencies_installed, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp,
                event.exception_type,
                event.exception_message,
                event.source_file,
                event.function_name,
                event.error_category,
                event.diagnosis,
                1 if event.fix_applied else 0,
                event.confidence,
                event.duration_ms,
                event.llm_model,
                event.llm_tokens_used,
                json.dumps(event.dependencies_installed),
                event.cost_usd,
            )
        )
        conn.commit()
        conn.close()

    def query(
        self,
        exception_type: Optional[str] = None,
        source_file: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[FixEvent]:
        """Query events with filters."""
        conn = sqlite3.connect(str(self.db_path))
        query = "SELECT * FROM fix_events WHERE 1=1"
        params = []

        if exception_type:
            query += " AND exception_type = ?"
            params.append(exception_type)
        if source_file:
            query += " AND source_file = ?"
            params.append(source_file)
        if since:
            query += " AND timestamp > ?"
            params.append(since)

        query += f" ORDER BY timestamp DESC LIMIT {limit}"

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append(FixEvent(
                timestamp=row[1],
                exception_type=row[2],
                exception_message=row[3],
                source_file=row[4],
                function_name=row[5],
                error_category=row[6],
                diagnosis=row[7],
                fix_applied=bool(row[8]),
                confidence=row[9],
                duration_ms=row[10],
                llm_model=row[11],
                llm_tokens_used=row[12],
                dependencies_installed=json.loads(row[13]) if row[13] else [],
                cost_usd=row[14],
            ))
        return events

    def get_stats(self) -> dict:
        """Get aggregate statistics."""
        conn = sqlite3.connect(str(self.db_path))

        total = conn.execute("SELECT COUNT(*) FROM fix_events").fetchone()[0]
        applied = conn.execute(
            "SELECT COUNT(*) FROM fix_events WHERE fix_applied = 1"
        ).fetchone()[0]
        avg_confidence = conn.execute(
            "SELECT AVG(confidence) FROM fix_events"
        ).fetchone()[0] or 0.0
        total_cost = conn.execute(
            "SELECT SUM(cost_usd) FROM fix_events"
        ).fetchone()[0] or 0.0

        conn.close()

        return {
            "total_events": total,
            "fixes_applied": applied,
            "fix_rate": applied / total if total > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "total_cost_usd": total_cost,
        }


class SentryIntegration:
    """Optional Sentry integration for error tracking."""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn
        self._sentry = None

        if dsn:
            try:
                import sentry_sdk
                self._sentry = sentry_sdk
                sentry_sdk.init(dsn=dsn)
            except ImportError:
                pass

    def capture_event(self, ctx: ErrorContext, proposal: FixProposal) -> Optional[str]:
        """Capture event in Sentry with pfix diagnosis."""
        if not self._sentry:
            return None

        with self._sentry.push_scope() as scope:
            scope.set_extra("pfix_diagnosis", proposal.diagnosis)
            scope.set_extra("pfix_proposed_fix", proposal.fix_description)
            scope.set_extra("pfix_confidence", proposal.confidence)
            scope.set_extra("pfix_dependencies", proposal.dependencies)

            event_id = self._sentry.capture_exception(
                __import__("builtins").Exception(ctx.exception_message)
            )
            return event_id


class Logger:
    """Main logger combining multiple backends."""

    def __init__(
        self,
        jsonl: bool = True,
        sqlite: bool = True,
        sentry_dsn: Optional[str] = None,
    ):
        self.backends = []

        if jsonl:
            self.backends.append(JsonLinesLogger())
        if sqlite:
            self.backends.append(SQLiteLogger())
        if sentry_dsn:
            self.sentry = SentryIntegration(sentry_dsn)
        else:
            self.sentry = None

    def log(
        self,
        ctx: ErrorContext,
        proposal: FixProposal,
        fix_applied: bool = False,
        duration_ms: int = 0,
        llm_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> FixEvent:
        """Log a fix event to all backends."""
        event = FixEvent(
            timestamp=datetime.now().isoformat(),
            exception_type=ctx.exception_type,
            exception_message=ctx.exception_message,
            source_file=ctx.source_file,
            function_name=ctx.function_name,
            error_category=proposal.error_category,
            diagnosis=proposal.diagnosis,
            fix_applied=fix_applied,
            confidence=proposal.confidence,
            duration_ms=duration_ms,
            llm_model="",  # Set by caller
            llm_tokens_used=llm_tokens,
            dependencies_installed=proposal.dependencies,
            cost_usd=cost_usd,
        )

        for backend in self.backends:
            backend.log(event)

        if self.sentry:
            self.sentry.capture_event(ctx, proposal)

        return event

    def get_stats(self) -> dict:
        """Get statistics from SQLite backend if available."""
        for backend in self.backends:
            if isinstance(backend, SQLiteLogger):
                return backend.get_stats()
        return {}


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """Get or create global logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger


def log_fix(
    ctx: ErrorContext,
    proposal: FixProposal,
    fix_applied: bool = False,
    duration_ms: int = 0,
) -> FixEvent:
    """Convenience function to log a fix event."""
    return get_logger().log(ctx, proposal, fix_applied, duration_ms)
