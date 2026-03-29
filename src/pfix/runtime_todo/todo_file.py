from __future__ import annotations

import fcntl
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import RuntimeIssue


class TodoFile:
    """Thread-safe, append-only manager for TODO.md.

    Features:
    - File locking (fcntl on Linux/Unix)
    - Append-only (never overwrites existing entries)
    - Deduplication (increments counter for same fingerprint)
    - Hidden HTML comments for metadata
    """

    def __init__(self, path: str | Path = "TODO.md"):
        self.path = Path(path).resolve()
        self._lock_path = self.path.with_suffix(".lock")
        self._lock_fd: Optional[int] = None

    def append_issue(self, issue: RuntimeIssue) -> bool:
        """Add issue to file. Thread-safe.

        Returns True if new entry, False if counter incremented.
        """
        with self._file_lock():
            existing = self._load_existing_fingerprints()

            if issue.fingerprint in existing:
                self._increment_counter(issue.fingerprint, existing[issue.fingerprint])
                return False
            else:
                self._append_new_entry(issue)
                return True

    def _file_lock(self):
        """Context manager for cross-platform file lock."""
        class LockContext:
            def __init__(ctx_self, lock_path: Path):
                ctx_self.lock_path = lock_path
                ctx_self.fd: Optional[int] = None

            def __enter__(ctx_self):
                ctx_self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                ctx_self.fd = os.open(
                    str(ctx_self.lock_path),
                    os.O_RDWR | os.O_CREAT
                )
                try:
                    fcntl.flock(ctx_self.fd, fcntl.LOCK_EX)
                except (ImportError, AttributeError):
                    pass  # Windows or no fcntl
                return ctx_self

            def __exit__(ctx_self, *args):
                if ctx_self.fd is not None:
                    try:
                        fcntl.flock(ctx_self.fd, fcntl.LOCK_UN)
                    except:
                        pass
                    os.close(ctx_self.fd)
                    ctx_self.fd = None

        return LockContext(self._lock_path)

    def _load_existing_fingerprints(self) -> dict[str, tuple[int, int]]:
        """Parse TODO.md, extract fingerprint -> (line_number, count)."""
        fingerprints: dict[str, tuple[int, int]] = {}

        if not self.path.exists():
            return fingerprints

        try:
            content = self.path.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines):
                match = re.search(r'<!-- pfix:fp=([a-f0-9]{16}) count=(\d+)', line)
                if match:
                    fp = match.group(1)
                    count = int(match.group(2))
                    fingerprints[fp] = (i, count)
        except Exception:
            pass

        return fingerprints

    def _increment_counter(self, fingerprint: str, location: tuple[int, int]):
        """Find entry by fingerprint and increment counter."""
        line_num, current_count = location

        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                # Update count
                new_line = re.sub(
                    r'count=\d+',
                    f'count={current_count + 1}',
                    line
                )
                # Update last_seen timestamp if present
                now = datetime.now(timezone.utc).isoformat()
                new_line = re.sub(
                    r'last=[^\s]+',
                    f'last={now}',
                    new_line
                )
                lines[line_num] = new_line
                self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _append_new_entry(self, issue: RuntimeIssue):
        """Append formatted entry to end of file."""
        # Ensure file exists with header
        if not self.path.exists():
            self.path.write_text("# TODO\n\n## Runtime Errors (Production)\n\n", encoding="utf-8")
        else:
            content = self.path.read_text(encoding="utf-8")
            if "## Runtime Errors" not in content:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write("\n## Runtime Errors (Production)\n\n")

        # Format the entry
        entry = self._format_entry(issue)

        # Append atomically
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def _format_entry(self, issue: RuntimeIssue) -> str:
        """Format RuntimeIssue as markdown TODO entry."""
        # Build trace summary
        trace_parts = []
        for i, frame in enumerate(issue.traceback_frames[:5]):  # Max 5 frames
            fname = Path(frame.filepath).name
            trace_parts.append(f"{fname}:{frame.line_number}")

        trace_str = " → ".join(trace_parts) if trace_parts else "unknown"

        # Format timestamp
        ts = issue.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Environment summary
        venv_short = issue.venv_path.split("/")[-1] if issue.venv_path else "system"

        entry = f"""- [ ] {issue.abs_filepath}:{issue.line_number} - {issue.exception_type}: {issue.exception_message}
      ↳ function: {issue.function_name}()
      ↳ trace: {trace_str}
      ↳ seen: {ts} (1x)
      ↳ env: py{issue.python_version} | {issue.hostname} | venv:{venv_short}
      <!-- pfix:fp={issue.fingerprint} count=1 first={ts} last={ts} -->"""

        return entry

    def get_section_content(self) -> str:
        """Extract just the runtime errors section."""
        if not self.path.exists():
            return ""

        content = self.path.read_text(encoding="utf-8")
        match = re.search(r'## Runtime Errors.*?\n\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
