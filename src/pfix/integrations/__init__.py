"""
pfix.integrations — External tool integrations for pfix.

Available integrations:
- sentry: Sentry SDK integration
- pytest_plugin: pytest plugin for auto-fixing tests
- web: FastAPI/Flask middleware
- precommit: pre-commit hook
"""

from __future__ import annotations

# Conditional imports to avoid hard dependencies
try:
    from .sentry import PfixSentryIntegration, init_sentry
except ImportError:
    PfixSentryIntegration = None  # type: ignore
    init_sentry = None  # type: ignore

try:
    from .web import PfixMiddleware, PfixFlaskExtension, PfixDjangoMiddleware
except ImportError:
    PfixMiddleware = None  # type: ignore
    PfixFlaskExtension = None  # type: ignore
    PfixDjangoMiddleware = None  # type: ignore

try:
    from .precommit import main as precommit_main
except ImportError:
    precommit_main = None  # type: ignore

__all__ = [
    "PfixSentryIntegration",
    "init_sentry",
    "PfixMiddleware",
    "PfixFlaskExtension",
    "PfixDjangoMiddleware",
    "precommit_main",
]
