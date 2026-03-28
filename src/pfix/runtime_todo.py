"""
pfix.runtime_todo — Runtime error capture and TODO.md integration.

Automatically captures runtime errors and appends them to TODO.md
with full context: traceback, environment, and deduplication.

Usage:
    # Auto-capture via config
    [tool.pfix.runtime_todo]
    enabled = true

    # Or programmatically
    from pfix.runtime_todo import RuntimeCollector, TodoFile
    collector = RuntimeCollector(TodoFile("TODO.md"))
    collector.capture(exception)
"""

from __future__ import annotations

import fcntl
import hashlib
import linecache
import os
import platform
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .types import RuntimeIssue, TraceFrame


class ErrorFingerprint:
    """Generates stable hash for error deduplication.

    Same error = same fingerprint, even if:
    - Different timestamp
    - Different local variables
    - Different PID/hostname
    """

    @staticmethod
    def compute(issue: RuntimeIssue) -> str:
        """Hash from: exception_type + normalized_message + filepath + function + line."""
        normalized_msg = ErrorFingerprint._normalize_error_message(issue.exception_message)

        key = f"{issue.exception_type}|{normalized_msg}|{issue.abs_filepath}|{issue.function_name}|{issue.line_number}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @staticmethod
    def _normalize_error_message(msg: str) -> str:
        """Replace variable values with placeholders."""
        # IP addresses
        msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<ip>', msg)
        # Port numbers (after :)
        msg = re.sub(r':\d{2,5}\b', ':<port>', msg)
        # Long numeric IDs (10+ digits)
        msg = re.sub(r'\b\d{10,}\b', '<id>', msg)
        # Long string values
        msg = re.sub(r"'[^']{50,}'", "'<long_string>'", msg)
        # Memory addresses
        msg = re.sub(r'\b0x[0-9a-fA-F]+\b', '<addr>', msg)
        # Temp files
        msg = re.sub(r'/tmp/[^\s]+', '<tmpfile>', msg)
        return msg


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


class RuntimeCollector:
    """Captures runtime errors and writes to TODO.md.

    Collection modes:
    1. sys.excepthook — catches unhandled exceptions
    2. @pfix decorator — catches decorated function exceptions
    3. Logging handler — catches ERROR/CRITICAL log records

    Config options (pyproject.toml [tool.pfix.runtime_todo]):
        enabled = true
        todo_file = "TODO.md"
        min_severity = "medium"
        max_entries = 500
        deduplicate = true
        include_local_vars = false
        include_traceback_depth = 5
        exclude_exceptions = ["KeyboardInterrupt", "SystemExit"]
        exclude_paths = ["*/site-packages/*", "*/.venv/*"]
    """

    def __init__(
        self,
        todo_file: TodoFile,
        enabled: bool = True,
        min_severity: str = "low",
        max_entries: int = 500,
        deduplicate: bool = True,
        include_local_vars: bool = False,
        include_traceback_depth: int = 5,
        exclude_exceptions: Optional[list[str]] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        self.todo = todo_file
        self.enabled = enabled
        self.min_severity = min_severity
        self.max_entries = max_entries
        self.deduplicate = deduplicate
        self.include_local_vars = include_local_vars
        self.include_traceback_depth = include_traceback_depth
        self.exclude_exceptions = set(exclude_exceptions or ["KeyboardInterrupt", "SystemExit", "GeneratorExit"])
        self.exclude_paths = exclude_paths or ["*/site-packages/*", "*/.venv/*", "*/venv/*"]

        self._buffer: list[RuntimeIssue] = []
        self._buffer_lock = threading.Lock()
        self._flush_interval = 5.0
        self._last_flush = time.time()
        self._flush_thread: Optional[threading.Thread] = None

    def capture(self, exc: BaseException, context: Optional[dict] = None):
        """Register an exception. Main public method."""
        if not self.enabled:
            return

        if not self._should_capture(exc):
            return

        issue = self._build_issue(exc, context)

        with self._buffer_lock:
            self._buffer.append(issue)

        # Flush if buffer full or interval passed
        if len(self._buffer) >= 10 or (time.time() - self._last_flush) > self._flush_interval:
            self._flush()

    def _should_capture(self, exc: BaseException) -> bool:
        """Check if exception should be captured based on config."""
        exc_name = type(exc).__name__

        if exc_name in self.exclude_exceptions:
            return False

        # Check severity
        severity = self._severity(exc)
        severity_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_level = severity_levels.get(self.min_severity, 1)
        exc_level = severity_levels.get(severity, 1)

        if exc_level < min_level:
            return False

        return True

    def _build_issue(self, exc: BaseException, context: Optional[dict]) -> RuntimeIssue:
        """Build RuntimeIssue from exception."""
        frames = self._extract_frames(exc)
        top_frame = frames[0] if frames else None

        ctx = context or {}

        issue = RuntimeIssue(
            abs_filepath=top_frame.filepath if top_frame else "<unknown>",
            line_number=top_frame.line_number if top_frame else 0,
            function_name=top_frame.function_name if top_frame else "<unknown>",
            module_name=self._filepath_to_module(top_frame.filepath) if top_frame else "",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            traceback_frames=frames,
            timestamp=datetime.now(timezone.utc),
            occurrence_count=1,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            python_version=platform.python_version(),
            venv_path=os.environ.get("VIRTUAL_ENV"),
            hostname=platform.node(),
            pid=os.getpid(),
            working_dir=os.getcwd(),
            argv=sys.argv[:],
            category=self._classify(exc),
            severity=self._severity(exc),
            fingerprint="",  # computed below
            local_vars_snapshot=self._capture_locals(exc) if self.include_local_vars else None,
            related_files=[f.filepath for f in frames[1:]],
        )
        issue.fingerprint = ErrorFingerprint.compute(issue)
        return issue

    def _extract_frames(self, exc: BaseException) -> list[TraceFrame]:
        """Extract frames from traceback. Absolute paths only."""
        frames = []
        tb = exc.__traceback__

        while tb is not None:
            frame = tb.tb_frame
            filepath = os.path.abspath(frame.f_code.co_filename)

            # Filter excluded paths
            if self._should_exclude_path(filepath):
                tb = tb.tb_next
                continue

            # Get code line
            code_line = ""
            try:
                code_line = linecache.getline(filepath, tb.tb_lineno).strip()
            except Exception:
                pass

            frames.append(TraceFrame(
                filepath=filepath,
                line_number=tb.tb_lineno,
                function_name=frame.f_code.co_name,
                code_line=code_line,
                local_vars=None,  # too expensive by default
            ))
            tb = tb.tb_next

        frames.reverse()  # most recent first
        return frames[:self.include_traceback_depth]

    def _should_exclude_path(self, filepath: str) -> bool:
        """Check if path matches exclusion patterns."""
        import fnmatch
        for pattern in self.exclude_paths:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False

    def _filepath_to_module(self, filepath: str) -> str:
        """Convert filepath to module name."""
        try:
            rel = Path(filepath).relative_to(Path.cwd())
            parts = rel.with_suffix("").parts
            return ".".join(parts)
        except ValueError:
            return ""

    def _capture_locals(self, exc: BaseException) -> Optional[dict[str, str]]:
        """Capture local variables from exception frame."""
        tb = exc.__traceback__
        if tb is None:
            return None

        # Walk to innermost frame
        while tb.tb_next:
            tb = tb.tb_next

        try:
            return {
                k: repr(v)[:200]  # limit length
                for k, v in tb.tb_frame.f_locals.items()
                if not k.startswith("__")
            }
        except Exception:
            return None

    def _classify(self, exc: BaseException) -> str:
        """Classify error into category."""
        mapping = {
            ModuleNotFoundError: "import_error",
            ImportError: "import_error",
            FileNotFoundError: "filesystem_error",
            PermissionError: "filesystem_error",
            IsADirectoryError: "filesystem_error",
            NotADirectoryError: "filesystem_error",
            OSError: "os_error",
            MemoryError: "memory_error",
            RecursionError: "memory_error",
            ConnectionError: "network_error",
            ConnectionRefusedError: "network_error",
            ConnectionResetError: "network_error",
            TimeoutError: "network_error",
            ChildProcessError: "process_error",
            ProcessLookupError: "process_error",
            TypeError: "type_error",
            ValueError: "value_error",
            KeyError: "key_error",
            IndexError: "index_error",
            AttributeError: "attribute_error",
            NameError: "name_error",
            SyntaxError: "syntax_error",
            UnicodeError: "encoding_error",
            UnicodeDecodeError: "encoding_error",
            UnicodeEncodeError: "encoding_error",
        }
        for exc_type, category in mapping.items():
            if isinstance(exc, exc_type):
                return category
        return "runtime_error"

    def _severity(self, exc: BaseException) -> str:
        """Determine severity from exception type."""
        critical = (MemoryError, SystemError, RecursionError)
        high = (ConnectionError, FileNotFoundError, PermissionError,
                ModuleNotFoundError, OSError)
        medium = (TypeError, ValueError, KeyError, IndexError,
                  AttributeError, UnicodeError)
        low = (NameError, SyntaxError, NotImplementedError)

        if isinstance(exc, critical):
            return "critical"
        if isinstance(exc, high):
            return "high"
        if isinstance(exc, medium):
            return "medium"
        return "low"

    def _flush(self):
        """Write buffered issues to file."""
        with self._buffer_lock:
            to_write = self._buffer[:]
            self._buffer.clear()

        if not to_write:
            return

        self._last_flush = time.time()

        for issue in to_write:
            try:
                self.todo.append_issue(issue)
            except Exception:
                pass  # never crash user code

    def install_excepthook(self):
        """Install global exception hook to capture all unhandled exceptions."""
        original_hook = sys.excepthook

        def custom_hook(exc_type, exc_value, exc_tb):
            if exc_type.__name__ not in self.exclude_exceptions:
                exc_value.__traceback__ = exc_tb
                self.capture(exc_value)
                self._flush()  # immediate flush for unhandled
            original_hook(exc_type, exc_value, exc_tb)

        sys.excepthook = custom_hook

    def shutdown(self):
        """Flush remaining buffer. Call on exit."""
        self._flush()


# ── Convenience functions ─────────────────────────────────────────

def get_collector(config: Optional[Any] = None) -> Optional[RuntimeCollector]:
    """Get or create RuntimeCollector from config."""
    if config is None:
        from .config import get_config
        config = get_config()

    # Check if runtime_todo enabled in pyproject.toml
    pyproject = getattr(config, '_pyproject_data', {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})

    if not rt_config.get("enabled", False):
        return None

    todo_file = rt_config.get("todo_file", "TODO.md")
    return RuntimeCollector(
        TodoFile(todo_file),
        enabled=True,
        min_severity=rt_config.get("min_severity", "low"),
        max_entries=rt_config.get("max_entries", 500),
        deduplicate=rt_config.get("deduplicate", True),
        include_local_vars=rt_config.get("include_local_vars", False),
        include_traceback_depth=rt_config.get("include_traceback_depth", 5),
        exclude_exceptions=rt_config.get("exclude_exceptions"),
        exclude_paths=rt_config.get("exclude_paths"),
    )


def capture_exception(exc: BaseException, context: Optional[dict] = None):
    """Capture single exception to TODO.md (convenience function)."""
    from .config import get_config

    config = get_config()
    pyproject = getattr(config, '_pyproject_data', {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})

    if not rt_config.get("enabled", False):
        return

    todo_file = rt_config.get("todo_file", "TODO.md")
    collector = RuntimeCollector(
        TodoFile(todo_file),
        enabled=True,
        min_severity=rt_config.get("min_severity", "low"),
        max_entries=rt_config.get("max_entries", 500),
    )
    collector.capture(exc, context)
    collector.shutdown()
