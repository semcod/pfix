"""
pfix.integrations — External tool integrations for pfix.

Available integrations:
- sentry: Sentry SDK integration
- pytest_plugin: pytest plugin for auto-fixing tests
- web: FastAPI/Flask middleware
"""

from __future__ import annotations

# Conditional imports to avoid hard dependencies
try:
    from .sentry import PfixSentryIntegration, init_sentry
except ImportError:
    PfixSentryIntegration = None  # type: ignore
    init_sentry = None  # type: ignore

__all__ = [
    "PfixSentryIntegration",
    "init_sentry",
]
