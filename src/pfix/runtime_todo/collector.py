from __future__ import annotations

import linecache
import os
import platform
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import RuntimeIssue, TraceFrame
    from .todo_file import TodoFile

from ..types import RuntimeIssue, TraceFrame
from .fingerprint import ErrorFingerprint


class RuntimeCollector:
    """Captures runtime errors and writes to TODO.md.

    Collection modes:
    1. sys.excepthook — catches unhandled exceptions
    2. @pfix decorator — catches decorated function exceptions
    3. Logging handler — catches ERROR/CRITICAL log records
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

        # Extract location info from top frame
        location = self._get_location_info(top_frame)

        # Build issue with grouped field extraction
        issue = RuntimeIssue(
            abs_filepath=location["filepath"],
            line_number=location["line_number"],
            function_name=location["function_name"],
            module_name=self._filepath_to_module(top_frame.filepath) if top_frame else "",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            traceback_frames=frames,
            **self._get_system_info(),  # Grouped system fields
            **self._get_timestamps(),   # Grouped timestamp fields
            category=self._classify(exc),
            severity=self._severity(exc),
            fingerprint="",  # computed below
            local_vars_snapshot=self._capture_locals(exc) if self.include_local_vars else None,
            related_files=[f.filepath for f in frames[1:]],
        )
        issue.fingerprint = ErrorFingerprint.compute(issue)
        return issue

    def _get_location_info(self, top_frame: Optional[TraceFrame]) -> dict[str, str | int]:
        """Extract location information from top frame."""
        if top_frame:
            return {
                "filepath": top_frame.filepath,
                "line_number": top_frame.line_number,
                "function_name": top_frame.function_name,
            }
        return {"filepath": "<unknown>", "line_number": 0, "function_name": "<unknown>"}

    def _get_system_info(self) -> dict[str, str | int | list[str]]:
        """Get system information fields."""
        return {
            "python_version": platform.python_version(),
            "venv_path": os.environ.get("VIRTUAL_ENV"),
            "hostname": platform.node(),
            "pid": os.getpid(),
            "working_dir": os.getcwd(),
            "argv": sys.argv[:],
        }

    def _get_timestamps(self) -> dict[str, datetime]:
        """Get timestamp fields (all set to same value)."""
        now = datetime.now(timezone.utc)
        return {
            "timestamp": now,
            "first_seen": now,
            "last_seen": now,
            "occurrence_count": 1,
        }

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
        # Order matters: check most specific exceptions first
        import socket
        mapping = {
            # Import errors (most specific first)
            ModuleNotFoundError: "import_error",
            ImportError: "import_error",
            # Network errors
            ConnectionRefusedError: "network_error",
            ConnectionResetError: "network_error",
            ConnectionError: "network_error",
            TimeoutError: "network_error",
            # Filesystem errors
            FileNotFoundError: "filesystem_error",
            PermissionError: "filesystem_error",
            IsADirectoryError: "filesystem_error",
            NotADirectoryError: "filesystem_error",
            # Process errors
            ChildProcessError: "process_error",
            ProcessLookupError: "process_error",
            # Memory errors
            MemoryError: "memory_error",
            RecursionError: "memory_error",
            # General OS error
            OSError: "os_error",
            # Other errors
            TypeError: "type_error",
            ValueError: "value_error",
            KeyError: "key_error",
            IndexError: "index_error",
            AttributeError: "attribute_error",
            NameError: "name_error",
            SyntaxError: "syntax_error",
            UnicodeDecodeError: "encoding_error",
            UnicodeEncodeError: "encoding_error",
            UnicodeError: "encoding_error",
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
