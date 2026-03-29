"""
pfix.env_diagnostics.network — Network diagnostics.
"""

from __future__ import annotations

import socket
import ssl
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class NetworkDiagnostic(BaseDiagnostic):
    """Diagnose network-related problems."""

    category = "network"

    # Common endpoints to check
    ENDPOINTS = [
        ("pypi.org", 443, "PyPI"),
        ("github.com", 443, "GitHub"),
        ("8.8.8.8", 53, "DNS (Google)"),
    ]

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all network checks."""
        results = []
        results.extend(self._check_dns())
        results.extend(self._check_outbound())
        results.extend(self._check_ssl_certs())
        results.extend(self._check_proxy())
        results.extend(self._check_latency())
        results.extend(self._check_system_clock())
        return results

    def _check_dns(self) -> list["DiagnosticResult"]:
        """Check DNS resolution."""
        from ..types import DiagnosticResult

        results = []

        try:
            socket.getaddrinfo("pypi.org", None)
        except socket.gaierror as e:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="dns_failure",
                status="error",
                message=f"DNS resolution failed: {e}",
                details={"error": str(e)},
                suggestion="Check network connection and DNS settings",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_outbound(self) -> list["DiagnosticResult"]:
        """Check outbound connectivity."""
        from ..types import DiagnosticResult

        results = []

        for host, port, name in self.ENDPOINTS:
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name=f"connect_{host}",
                    status="warning",
                    message=f"Cannot reach {name} ({host}:{port}): {e}",
                    details={"host": host, "port": port, "error": str(e)},
                    suggestion="Check firewall and network connectivity",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        return results

    def _check_ssl_certs(self) -> list["DiagnosticResult"]:
        """Check SSL certificate validity."""
        from ..types import DiagnosticResult

        results = []

        try:
            context = ssl.create_default_context()
            with socket.create_connection(("pypi.org", 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname="pypi.org") as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="ssl_no_cert",
                            status="error",
                            message="SSL certificate missing from pypi.org",
                            details={},
                            suggestion="Check system CA certificates",
                            auto_fixable=False,
                            abs_path=None,
                            line_number=None,
                        ))
        except ssl.SSLError as e:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="ssl_error",
                status="error",
                message=f"SSL error: {e}",
                details={"error": str(e)},
                suggestion="Update CA certificates or check system clock",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))
        except Exception:
            pass

        return results

    def _check_proxy(self) -> list["DiagnosticResult"]:
        """Check proxy configuration."""
        from ..types import DiagnosticResult
        import os

        results = []

        proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
        proxies = {v: os.environ.get(v) for v in proxy_vars if os.environ.get(v)}

        if proxies:
            # Check if proxy is working
            try:
                socket.create_connection(("pypi.org", 443), timeout=5)
            except Exception as e:
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="proxy_issue",
                    status="warning",
                    message=f"Proxy configured but connectivity issues: {e}",
                    details={"proxies": proxies},
                    suggestion="Verify proxy settings or unset proxy vars",
                    auto_fixable=False,
                    abs_path=None,
                    line_number=None,
                ))

        return results

    def _check_latency(self) -> list["DiagnosticResult"]:
        """Check network latency to PyPI."""
        from ..types import DiagnosticResult
        import time

        results = []
        try:
            start = time.time()
            with socket.create_connection(("pypi.org", 443), timeout=5):
                latency = (time.time() - start) * 1000

            if latency > 500:  # > 500ms
                results.append(DiagnosticResult(
                    category=self.category,
                    check_name="high_latency",
                    status="warning",
                    message=f"High network latency: {latency:.1f}ms",
                    details={"latency_ms": latency},
                    suggestion="Check your internet connection or use a local mirror",
                ))
        except Exception:
            pass
        return results

    def _check_system_clock(self) -> list["DiagnosticResult"]:
        """Check if system clock is reasonably accurate (vital for SSL/TLS)."""
        from ..types import DiagnosticResult
        import time
        from datetime import datetime

        results = []
        # We can't easily get network time without ntp lib,
        # but we can check if it's before a 'sane' date (e.g. 2024-01-01)
        sane_date = datetime(2024, 1, 1).timestamp()
        if time.time() < sane_date:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="stale_clock",
                status="critical",
                message=f"System clock seems wrong: {datetime.now()}",
                suggestion="Update system clock using NTP",
            ))
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose network-related exceptions."""
        from ..types import DiagnosticResult

        if isinstance(exc, ConnectionRefusedError):
            import re
            msg = str(exc)
            # Try to extract host:port
            match = re.search(r"\[([^\]]+)\]:(\d+)", msg) or re.search(r"(\S+):(\d+)", msg)
            if match:
                host, port = match.groups()
                return DiagnosticResult(
                    category=self.category,
                    check_name="connection_refused",
                    status="error",
                    message=f"Connection refused to {host}:{port}",
                    details={"host": host, "port": port},
                    suggestion="Check if service is running and accessible",
                    auto_fixable=False,
                    abs_path=ctx.source_file if ctx.source_file else None,
                    line_number=ctx.line_number,
                )

        if isinstance(exc, socket.timeout):
            return DiagnosticResult(
                category=self.category,
                check_name="network_timeout",
                status="error",
                message=f"Network timeout: {exc}",
                details={},
                suggestion="Check network latency and timeout settings",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        if isinstance(exc, ConnectionError):
            return DiagnosticResult(
                category=self.category,
                check_name="connection_error",
                status="error",
                message=f"Connection error: {exc}",
                details={},
                suggestion="Check network connectivity and firewall",
                auto_fixable=False,
                abs_path=ctx.source_file if ctx.source_file else None,
                line_number=ctx.line_number,
            )

        return None
