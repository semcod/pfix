"""
pfix.integrations.sentry — Sentry SDK integration for pfix.

Adds pfix diagnosis to Sentry error events as extra context.
"""

from __future__ import annotations

from typing import Any, Optional

from ...analyzer import analyze_exception
from ...llm import request_fix
from ...types import ErrorContext, FixProposal


class PfixSentryIntegration:
    """Sentry integration that adds pfix diagnosis to error events."""

    def __init__(self, auto_analyze: bool = True, min_confidence: float = 0.3):
        """
        Initialize Sentry integration.

        Args:
            auto_analyze: Automatically analyze exceptions with pfix
            min_confidence: Only include fixes with confidence above threshold
        """
        self.auto_analyze = auto_analyze
        self.min_confidence = min_confidence
        self._client = None

    def setup_once(self, sentry_sdk: Any, hub: Any) -> None:
        """Called by Sentry SDK during initialization."""
        from sentry_sdk.integrations import Integration

        # Register event processor
        scope = sentry_sdk.get_global_scope()
        scope.add_event_processor(self._process_event)

    def _process_event(self, event: dict, hint: dict) -> dict:
        """Process Sentry event to add pfix context."""
        if not self.auto_analyze:
            return event

        # Get exception info from hint
        exc_info = hint.get("exc_info")
        if not exc_info or len(exc_info) < 3:
            return event

        exc_type, exc_value, exc_tb = exc_info
        if exc_value is None:
            return event

        try:
            # Analyze with pfix
            ctx = analyze_exception(exc_value)
            proposal = request_fix(ctx)

            # Add to event extras
            if "extra" not in event:
                event["extra"] = {}

            event["extra"]["pfix_diagnosis"] = proposal.diagnosis
            event["extra"]["pfix_error_category"] = proposal.error_category
            event["extra"]["pfix_confidence"] = proposal.confidence

            if proposal.confidence >= self.min_confidence:
                event["extra"]["pfix_proposed_fix"] = proposal.fix_description
                if proposal.dependencies:
                    event["extra"]["pfix_dependencies"] = proposal.dependencies

        except Exception:
            # Silently fail - don't break Sentry reporting
            pass

        return event


def init_sentry(
    dsn: Optional[str] = None,
    auto_analyze: bool = True,
    min_confidence: float = 0.3,
    **kwargs: Any,
) -> Any:
    """
    Initialize Sentry with pfix integration.

    Convenience function that wraps sentry_sdk.init().

    Example:
        import pfix.integrations.sentry as pfix_sentry
        sentry = pfix_sentry.init_sentry(
            dsn="your-dsn-here",
            auto_analyze=True,
        )
    """
    try:
        import sentry_sdk
    except ImportError:
        raise ImportError(
            "Sentry integration requires sentry-sdk. "
            "Install with: pip install pfix[sentry]"
        )

    # Add pfix integration
    integrations = kwargs.pop("integrations", [])
    integrations.append(PfixSentryIntegration(auto_analyze, min_confidence))

    return sentry_sdk.init(
        dsn=dsn,
        integrations=integrations,
        **kwargs,
    )
