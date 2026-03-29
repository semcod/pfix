"""
pfix.env_diagnostics.encoding — Encoding diagnostics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class EncodingDiagnostic(BaseDiagnostic):
    """Diagnose encoding-related problems."""

    category = "encoding"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all encoding checks."""
        results = []
        results.extend(self._check_locale())
        results.extend(self._check_file_encoding(project_root))
        results.extend(self._check_line_endings(project_root))
        results.extend(self._check_stdio_encoding())
        results.extend(self._check_os_environ_encoding())
        return results

    def _check_locale(self) -> list["DiagnosticResult"]:
        """Check system locale settings."""
        from ..types import DiagnosticResult

        results = []

        # Check filesystem encoding
        fs_encoding = sys.getfilesystemencoding()
        if fs_encoding.lower() not in ("utf-8", "utf8"):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="non_utf8_filesystem",
                status="warning",
                message=f"Non-UTF8 filesystem encoding: {fs_encoding}",
                details={"filesystem_encoding": fs_encoding},
                suggestion="Set LANG=en_US.UTF-8 or similar",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        # Check default encoding
        default_encoding = sys.getdefaultencoding()
        if default_encoding.lower() not in ("utf-8", "utf8"):
            results.append(DiagnosticResult(
                category=self.category,
                check_name="non_utf8_default",
                status="warning",
                message=f"Non-UTF8 default encoding: {default_encoding}",
                details={"default_encoding": default_encoding},
                suggestion="Set PYTHONIOENCODING=utf-8",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_file_encoding(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check Python files for encoding issues."""
        from ..types import DiagnosticResult

        results = []

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            try:
                with open(pyfile, "rb") as f:
                    content = f.read()

                # Check for BOM
                if content.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="utf8_bom",
                        status="warning",
                        message=f"File has UTF-8 BOM: {pyfile.name}",
                        details={"file": str(pyfile)},
                        suggestion="Remove BOM: sed -i '1s/^\xef\xbb\xbf//'",
                        auto_fixable=True,
                        abs_path=str(pyfile),
                        line_number=1,
                    ))

                # Try to decode as UTF-8
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError as e:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="non_utf8_encoding",
                        status="error",
                        message=f"File not valid UTF-8: {pyfile.name} ({e})",
                        details={"file": str(pyfile), "error": str(e)},
                        suggestion="Re-encode file to UTF-8",
                        auto_fixable=False,
                        abs_path=str(pyfile),
                        line_number=None,
                    ))

            except Exception:
                pass

        return results

    def _check_line_endings(self, project_root: Path) -> list["DiagnosticResult"]:
        """Check for mixed line endings."""
        from ..types import DiagnosticResult

        results = []

        for pyfile in project_root.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            try:
                content = pyfile.read_bytes()

                has_crlf = b"\r\n" in content
                has_lf = b"\n" in content.replace(b"\r\n", b"")

                if has_crlf and has_lf:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="mixed_line_endings",
                        status="warning",
                        message=f"Mixed line endings (CRLF + LF): {pyfile.name}",
                        details={"file": str(pyfile)},
                        suggestion="Convert to LF: dos2unix {file}",
                        auto_fixable=True,
                        abs_path=str(pyfile),
                        line_number=None,
                    ))

            except Exception:
                pass

        return results

    def _check_stdio_encoding(self) -> list["DiagnosticResult"]:
        """Check if standard I/O streams are using UTF-8."""
        from ..types import DiagnosticResult
        results = []
        for stream_name in ("stdout", "stderr", "stdin"):
            stream = getattr(sys, stream_name)
            if stream and hasattr(stream, "encoding"):
                enc = stream.encoding
                if enc and enc.lower() not in ("utf-8", "utf8", "utf_8"):
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name=f"non_utf8_{stream_name}",
                        status="warning",
                        message=f"Stream {stream_name} uses non-UTF8 encoding: {enc}",
                        details={"stream": stream_name, "encoding": enc},
                        suggestion="Set PYTHONIOENCODING=utf-8",
                    ))
        return results

    def _check_os_environ_encoding(self) -> list["DiagnosticResult"]:
        """Check for environment variables that cannot be decoded as UTF-8."""
        from ..types import DiagnosticResult
        import os
        results = []
        try:
            # os.environ uses sys.getfilesystemencoding(), but some values might be raw bytes
            # that were mis-decoded.
            for key, value in os.environ.items():
                try:
                    key.encode('utf-8').decode('utf-8')
                    value.encode('utf-8').decode('utf-8')
                except UnicodeError:
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="env_var_encoding_error",
                        status="error",
                        message=f"Environment variable '{key}' has invalid encoding",
                        suggestion="Ensure all environment variables are valid UTF-8",
                    ))
        except Exception:
            pass
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose encoding-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, (UnicodeDecodeError, UnicodeEncodeError)):
            return DiagnosticResult(
                category=self.category,
                check_name="unicode_error",
                status="error",
                message=str(exc),
                details={
                    "encoding": getattr(exc, 'encoding', 'unknown'),
                    "object": getattr(exc, 'object', None),
                },
                suggestion="Ensure UTF-8 encoding or handle encoding explicitly",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
