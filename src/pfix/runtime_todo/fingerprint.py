from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import RuntimeIssue


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
        # UUIDs / GUIDs
        msg = re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '<uuid>', msg)
        # IP addresses
        msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<ip>', msg)
        # Port numbers (after :)
        msg = re.sub(r':\d{2,5}\b', ':<port>', msg)
        # Long numeric IDs (10+ digits)
        msg = re.sub(r'\b\d{10,}\b', '<id>', msg)
        # Long hex strings (8+ chars)
        msg = re.sub(r'\b[0-9a-fA-F]{8,}\b', '<hex>', msg)
        # Long string values
        msg = re.sub(r"'[^']{40,}'", "'<long_string>'", msg)
        msg = re.sub(r'"[^"]{40,}"', '"<long_string>"', msg)
        # Memory addresses (0x...)
        msg = re.sub(r'\b0x[0-9a-fA-F]+\b', '<addr>', msg)
        # Temp files
        msg = re.sub(r'/tmp/[^\s]+', '<tmpfile>', msg)
        return msg
