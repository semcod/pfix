"""
pfix.production — Production-safe monitoring mode for pfix.

Philosophy: NEVER modify code on production. Only monitor, log, and notify.

Features:
- Webhook/callback notifications (Slack, email, Sentry)
- Rate limiting (max N analyses per minute)
- Circuit breaker (disable after X consecutive errors)
- Proposal logging to file/DB
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .analyzer import analyze_exception
from .cache import get_cached_fix, cache_fix
from .config import get_config
from .llm import request_fix
from .types import ErrorContext, FixProposal


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern for LLM calls."""
    threshold: int = 5
    reset_timeout: int = 300  # 5 minutes

    _failures: int = 0
    _last_failure: float = 0.0
    _open: bool = False

    def record_success(self) -> None:
        """Record a successful operation."""
        self._failures = 0
        self._open = False

    def record_failure(self) -> bool:
        """Record a failed operation. Returns True if circuit is now open."""
        self._failures += 1
        self._last_failure = time.time()

        if self._failures >= self.threshold:
            self._open = True
            return True
        return False

    def is_open(self) -> bool:
        """Check if circuit is open (broken)."""
        if not self._open:
            return False

        # Auto-reset after timeout
        if time.time() - self._last_failure > self.reset_timeout:
            self._open = False
            self._failures = 0
            return False

        return True


@dataclass
class RateLimiter:
    """Rate limiter for LLM calls (token bucket algorithm)."""
    max_calls: int = 10  # per minute
    window: int = 60  # seconds

    _calls: list[float] = field(default_factory=list)

    def can_call(self) -> bool:
        """Check if a call is allowed under rate limit."""
        now = time.time()
        # Remove old calls outside window
        self._calls = [t for t in self._calls if now - t < self.window]
        return len(self._calls) < self.max_calls

    def record_call(self) -> None:
        """Record a call."""
        self._calls.append(time.time())

    def get_remaining(self) -> int:
        """Get remaining calls in current window."""
        now = time.time()
        self._calls = [t for t in self._calls if now - t < self.window]
        return max(0, self.max_calls - len(self._calls))


@dataclass
class ProductionConfig:
    """Configuration for production mode."""
    mode: str = "monitor"  # "monitor" | "disabled"
    webhook_url: Optional[str] = None
    rate_limit_per_minute: int = 10
    circuit_breaker_threshold: int = 5
    log_proposals_dir: Path = field(default_factory=lambda: Path(".pfix_proposals"))
    notify_channels: list[str] = field(default_factory=list)
    auto_apply: bool = False  # ALWAYS False in production


class PfixMonitor:
    """Production-safe error monitor. Never modifies code."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        rate_limit: int = 10,
        circuit_breaker: int = 5,
        auto_apply: bool = False,
        log_proposals: bool = True,
        log_dir: Optional[Path] = None,
    ):
        """
        Initialize production monitor.

        Args:
            webhook_url: URL for webhook notifications (Slack, etc.)
            rate_limit: Max LLM analyses per minute
            circuit_breaker: Disable after N consecutive errors
            auto_apply: MUST be False (enforced)
            log_proposals: Save proposals to files
            log_dir: Directory for proposal logs
        """
        self.config = ProductionConfig(
            webhook_url=webhook_url,
            rate_limit_per_minute=rate_limit,
            circuit_breaker_threshold=circuit_breaker,
            auto_apply=False,  # Always False in production
        )

        if auto_apply:
            raise ValueError("auto_apply=True is forbidden in production mode")

        self.rate_limiter = RateLimiter(max_calls=rate_limit)
        self.circuit_breaker = CircuitBreaker(threshold=circuit_breaker)

        if log_proposals:
            self.config.log_proposals_dir = log_dir or Path(".pfix_proposals")
            self.config.log_proposals_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "errors_seen": 0,
            "analyses_sent": 0,
            "cache_hits": 0,
            "notifications_sent": 0,
            "circuit_breaks": 0,
        }

    def watch(self, func: Callable) -> Callable:
        """Decorator to monitor a function for errors."""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                self.handle_exception(exc, func=func)
                raise  # Re-raise after monitoring

        return wrapper

    def handle_exception(
        self,
        exc: BaseException,
        func: Optional[Callable] = None,
        local_vars: Optional[dict] = None,
    ) -> dict:
        """
        Handle exception in production mode.

        Returns dict with diagnosis info (for logging/webhook).
        """
        self.stats["errors_seen"] += 1

        # Build context
        ctx = analyze_exception(exc, func=func, local_vars=local_vars)

        # Check cache first
        cached = get_cached_fix(ctx)
        if cached:
            self.stats["cache_hits"] += 1
            proposal = cached
        else:
            # Check circuit breaker
            if self.circuit_breaker.is_open():
                return {
                    "error": "Circuit breaker open - LLM calls disabled",
                    "exception_type": ctx.exception_type,
                    "exception_message": ctx.exception_message,
                }

            # Check rate limit
            if not self.rate_limiter.can_call():
                return {
                    "error": "Rate limit exceeded",
                    "exception_type": ctx.exception_type,
                    "exception_message": ctx.exception_message,
                }

            # Request fix from LLM
            self.rate_limiter.record_call()
            try:
                proposal = request_fix(ctx)
                self.circuit_breaker.record_success()
                self.stats["analyses_sent"] += 1

                # Cache the result
                if proposal.confidence > 0.3:
                    cache_fix(ctx, proposal)
            except Exception as llm_err:
                self.circuit_breaker.record_failure()
                if self.circuit_breaker.is_open():
                    self.stats["circuit_breaks"] += 1
                return {
                    "error": f"LLM request failed: {llm_err}",
                    "exception_type": ctx.exception_type,
                    "exception_message": ctx.exception_message,
                }

        # Build result
        result = {
            "timestamp": datetime.now().isoformat(),
            "exception_type": ctx.exception_type,
            "exception_message": ctx.exception_message,
            "source_file": ctx.source_file,
            "line_number": ctx.line_number,
            "function_name": ctx.function_name,
            "diagnosis": proposal.diagnosis,
            "fix_description": proposal.fix_description,
            "confidence": proposal.confidence,
            "dependencies": proposal.dependencies,
            "cached": cached is not None,
        }

        # Log proposal to file
        if self.config.log_proposals_dir:
            self._log_proposal(result, proposal)

        # Send notification
        if self.config.webhook_url:
            self._send_webhook(result)

        return result

    def _log_proposal(self, result: dict, proposal: FixProposal) -> None:
        """Log proposal to JSON Lines file."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result['exception_type']}_{ts}.json"
        filepath = self.config.log_proposals_dir / filename

        log_entry = {
            "timestamp": result["timestamp"],
            "error": {
                "type": result["exception_type"],
                "message": result["exception_message"],
                "file": result["source_file"],
                "line": result["line_number"],
            },
            "diagnosis": proposal.diagnosis,
            "proposed_fix": {
                "description": proposal.fix_description,
                "confidence": proposal.confidence,
                "dependencies": proposal.dependencies,
                "has_code_fix": proposal.has_code_fix,
            },
            "cached": result.get("cached", False),
        }

        filepath.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))

    def _send_webhook(self, result: dict) -> None:
        """Send notification to webhook."""
        if not self.config.webhook_url:
            return

        try:
            import urllib.request
            import urllib.error

            payload = json.dumps({
                "text": f"🐛 pfix detected error: {result['exception_type']}",
                "error": result,
            }, ensure_ascii=False).encode()

            req = urllib.request.Request(
                self.config.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201, 204):
                    self.stats["notifications_sent"] += 1
        except Exception:
            # Silently fail - don't break production for notifications
            pass

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            **self.stats,
            "rate_limit_remaining": self.rate_limiter.get_remaining(),
            "circuit_breaker_open": self.circuit_breaker.is_open(),
        }


# Convenience function for simple usage
def monitor(
    webhook_url: Optional[str] = None,
    rate_limit: int = 10,
) -> PfixMonitor:
    """Create a production monitor with sensible defaults."""
    return PfixMonitor(
        webhook_url=webhook_url,
        rate_limit=rate_limit,
        auto_apply=False,  # Enforced
    )
