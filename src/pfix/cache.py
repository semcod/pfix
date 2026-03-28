"""
pfix.cache — Persistent caching of fix proposals to reduce LLM costs.

Cache key = hash(exception_type + exception_message + function_source)
Storage: SQLite in .pfix_cache/fixes.db (default) or diskcache if available
TTL: 7 days default
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .types import ErrorContext, FixProposal

DEFAULT_CACHE_DIR = Path(".pfix_cache")
DEFAULT_TTL_DAYS = 7


def _get_cache_path() -> Path:
    """Get cache directory path."""
    path = DEFAULT_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _init_sqlite_db(db_path: Path) -> None:
    """Initialize SQLite cache database."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fix_cache (
            cache_key TEXT PRIMARY KEY,
            exception_type TEXT,
            exception_message TEXT,
            function_source_hash TEXT,
            fix_proposal_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_expires ON fix_cache(expires_at)
    """)
    conn.commit()
    conn.close()


def _make_cache_key(ctx: ErrorContext) -> str:
    """Generate cache key from error context."""
    # Hash based on exception type, message, and function source
    content = f"{ctx.exception_type}:{ctx.exception_message}:{ctx.function_source}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def _proposal_to_json(proposal: FixProposal) -> str:
    """Serialize FixProposal to JSON."""
    data = {
        "diagnosis": proposal.diagnosis,
        "error_category": proposal.error_category,
        "fix_description": proposal.fix_description,
        "fixed_function": proposal.fixed_function,
        "fixed_file_content": proposal.fixed_file_content,
        "dependencies": proposal.dependencies,
        "new_imports": proposal.new_imports,
        "confidence": proposal.confidence,
        "breaking_changes": proposal.breaking_changes,
        "raw_response": proposal.raw_response,
    }
    return json.dumps(data, ensure_ascii=False)


def _json_to_proposal(json_str: str) -> FixProposal:
    """Deserialize FixProposal from JSON."""
    data = json.loads(json_str)
    return FixProposal(
        diagnosis=data.get("diagnosis", ""),
        error_category=data.get("error_category", ""),
        fix_description=data.get("fix_description", ""),
        fixed_function=data.get("fixed_function", ""),
        fixed_file_content=data.get("fixed_file_content", ""),
        dependencies=data.get("dependencies", []),
        new_imports=data.get("new_imports", []),
        confidence=data.get("confidence", 0.0),
        breaking_changes=data.get("breaking_changes", False),
        raw_response=data.get("raw_response", ""),
    )


class FixCache:
    """Cache for fix proposals to avoid redundant LLM calls."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_days: int = DEFAULT_TTL_DAYS):
        self.cache_dir = cache_dir or _get_cache_path()
        self.ttl_days = ttl_days
        self.db_path = self.cache_dir / "fixes.db"
        self._diskcache = None

        # Try diskcache first (faster), fall back to SQLite
        try:
            import diskcache
            self._diskcache = diskcache.Cache(str(self.cache_dir / "diskcache"))
        except ImportError:
            _init_sqlite_db(self.db_path)

    def get(self, ctx: ErrorContext) -> Optional[FixProposal]:
        """Get cached fix proposal for error context."""
        key = _make_cache_key(ctx)

        if self._diskcache is not None:
            # Use diskcache
            data = self._diskcache.get(key)
            if data is not None:
                return _json_to_proposal(data)
            return None

        # Use SQLite
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            "SELECT fix_proposal_json FROM fix_cache WHERE cache_key = ? AND expires_at > ?",
            (key, datetime.now())
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return _json_to_proposal(row[0])
        return None

    def set(self, ctx: ErrorContext, proposal: FixProposal) -> None:
        """Cache fix proposal for error context."""
        key = _make_cache_key(ctx)
        expires_at = datetime.now() + timedelta(days=self.ttl_days)
        json_data = _proposal_to_json(proposal)

        if self._diskcache is not None:
            # Use diskcache with TTL
            self._diskcache.set(key, json_data, expire=int(self.ttl_days * 86400))
            return

        # Use SQLite
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            INSERT OR REPLACE INTO fix_cache
            (cache_key, exception_type, exception_message, function_source_hash,
             fix_proposal_json, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                ctx.exception_type,
                ctx.exception_message,
                hashlib.sha256(ctx.function_source.encode()).hexdigest()[:16] if ctx.function_source else "",
                json_data,
                expires_at,
            )
        )
        conn.commit()
        conn.close()

    def clear(self) -> int:
        """Clear expired entries. Returns number of entries removed."""
        if self._diskcache is not None:
            # diskcache auto-expires, but we can trim
            return self._diskcache.cull()

        # SQLite: delete expired entries
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("DELETE FROM fix_cache WHERE expires_at <= ?", (datetime.now(),))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def stats(self) -> dict:
        """Get cache statistics."""
        if self._diskcache is not None:
            return {
                "backend": "diskcache",
                "size": len(self._diskcache),
                "volume": self._diskcache.volume(),
            }

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM fix_cache WHERE expires_at > ?", (datetime.now(),))
        valid_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM fix_cache")
        total_count = cursor.fetchone()[0]
        conn.close()

        return {
            "backend": "sqlite",
            "valid_entries": valid_count,
            "total_entries": total_count,
            "expired_entries": total_count - valid_count,
        }

    def close(self) -> None:
        """Close cache connections."""
        if self._diskcache is not None:
            self._diskcache.close()


# Global cache instance
_global_cache: Optional[FixCache] = None


def get_cache() -> FixCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = FixCache()
    return _global_cache


def get_cached_fix(ctx: ErrorContext) -> Optional[FixProposal]:
    """Get cached fix for error context (convenience function)."""
    return get_cache().get(ctx)


def cache_fix(ctx: ErrorContext, proposal: FixProposal) -> None:
    """Cache fix proposal (convenience function)."""
    get_cache().set(ctx, proposal)
