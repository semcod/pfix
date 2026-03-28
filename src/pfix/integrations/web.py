"""
pfix.integrations.web — Web framework middleware for FastAPI and Flask.

Captures 500 errors, analyzes them with pfix, and optionally notifies.

Usage (FastAPI):
    from fastapi import FastAPI
    from pfix.integrations.web import PfixMiddleware

    app = FastAPI()
    app.add_middleware(
        PfixMiddleware,
        auto_fix=False,  # Never auto-fix on production
        notify_url="https://hooks.slack.com/...",
    )

Usage (Flask):
    from flask import Flask
    from pfix.integrations.web import PfixFlaskExtension

    app = Flask(__name__)
    pfix_ext = PfixFlaskExtension(app, auto_fix=False)
"""

from __future__ import annotations

import sys
import traceback
from typing import Any, Callable, Optional

from ...analyzer import analyze_exception
from ...production import PfixMonitor


class PfixMiddleware:
    """ASGI middleware for FastAPI/Starlette that captures and analyzes errors."""

    def __init__(
        self,
        app: Any,
        auto_fix: bool = False,
        notify_url: Optional[str] = None,
        rate_limit: int = 10,
    ):
        """
        Initialize ASGI middleware.

        Args:
            app: ASGI application
            auto_fix: Never True on production (safety)
            notify_url: Webhook for notifications
            rate_limit: Max analyses per minute
        """
        self.app = app
        self.auto_fix = auto_fix
        self.monitor = PfixMonitor(
            webhook_url=notify_url,
            rate_limit=rate_limit,
            auto_apply=False,  # Enforced - middleware never fixes
        )

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """ASGI entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Wrap send to capture status
        status_code = 200

        async def wrapped_send(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as exc:
            # Check if it's a 500 error
            if status_code >= 500 or status_code == 200:  # Unhandled becomes 500
                self._handle_exception(exc, scope)
            raise

    def _handle_exception(self, exc: Exception, scope: dict) -> None:
        """Handle exception with pfix."""
        # Get request info
        request_info = {
            "method": scope.get("method", "UNKNOWN"),
            "path": scope.get("path", "unknown"),
        }

        try:
            # Analyze with pfix monitor (production-safe)
            result = self.monitor.handle_exception(exc)

            # Add request context
            if isinstance(result, dict):
                result["request"] = request_info

        except Exception:
            # Silently fail - don't break response
            pass


class PfixFlaskExtension:
    """Flask extension for pfix error monitoring."""

    def __init__(
        self,
        app: Optional[Any] = None,
        auto_fix: bool = False,
        notify_url: Optional[str] = None,
        rate_limit: int = 10,
    ):
        self.auto_fix = auto_fix
        self.monitor = PfixMonitor(
            webhook_url=notify_url,
            rate_limit=rate_limit,
            auto_apply=False,  # Enforced
        )

        if app:
            self.init_app(app)

    def init_app(self, app: Any) -> None:
        """Initialize Flask app with error handler."""
        # Register error handler
        app.register_error_handler(Exception, self._handle_exception)

        # Store for access
        app.extensions = getattr(app, "extensions", {})
        app.extensions["pfix"] = self

    def _handle_exception(self, exc: Exception) -> Optional[Any]:
        """Handle exception with pfix."""
        try:
            # Only handle 500-class errors
            import werkzeug

            if isinstance(exc, werkzeug.exceptions.HTTPException):
                if exc.code < 500:
                    return None  # Let Flask handle normally

            # Analyze with pfix monitor
            self.monitor.handle_exception(exc)

        except Exception:
            # Silently fail
            pass

        return None  # Let other handlers process


# Django middleware (if Django is available)
class PfixDjangoMiddleware:
    """Django middleware for pfix error monitoring."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.monitor = PfixMonitor(auto_apply=False)

    def __call__(self, request: Any) -> Any:
        """Django middleware entry point."""
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            self._handle_exception(exc, request)
            raise

    def _handle_exception(self, exc: Exception, request: Any) -> None:
        """Handle exception with pfix."""
        try:
            # Add request context
            request_info = {
                "method": request.method if hasattr(request, "method") else "UNKNOWN",
                "path": request.path if hasattr(request, "path") else "unknown",
            }

            result = self.monitor.handle_exception(exc)
            if isinstance(result, dict):
                result["request"] = request_info

        except Exception:
            pass


def create_error_handler(
    auto_fix: bool = False,
    notify_url: Optional[str] = None,
) -> Callable[[Exception], None]:
    """
    Create a generic error handler for custom frameworks.

    Example:
        handler = create_error_handler(notify_url="https://...")

        try:
            process_request()
        except Exception as e:
            handler(e)
            raise
    """
    monitor = PfixMonitor(
        webhook_url=notify_url,
        auto_apply=False,
    )

    def handle(exc: Exception) -> None:
        try:
            monitor.handle_exception(exc)
        except Exception:
            pass

    return handle
