"""
pfix.env_diagnostics.base — Base diagnostic interface.

All environment diagnostics inherit from BaseDiagnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..types import DiagnosticResult
    from ..types import ErrorContext


class BaseDiagnostic(ABC):
    """Base class for all environment diagnostics.

    Each diagnostic checks a specific aspect of the environment
    and can diagnose exceptions to provide context.
    """

    category: str = ""

    @abstractmethod
    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run proactive diagnostics. Return list of results."""
        raise NotImplementedError

    @abstractmethod
    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose a specific exception. Return None if not applicable."""
        raise NotImplementedError

    def can_auto_fix(self, result: "DiagnosticResult") -> bool:
        """Check if this problem can be auto-fixed."""
        return result.auto_fixable
