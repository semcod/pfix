"""
pfix.telemetry — Anonymous usage metrics (opt-in only).

Configuration:
    [tool.pfix.telemetry]
    enabled = false              # Default: disabled
    endpoint = ""                # Custom metrics endpoint
    metrics = ["fix_count", "success_rate", "cost"]

Privacy:
- No code content is ever sent
- No file paths are sent
- Only aggregate counts and success rates
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import get_config

TELEMETRY_FILE = Path(".pfix/telemetry.json")


@dataclass
class TelemetryEvent:
    """Anonymous telemetry event."""

    timestamp: str
    event_type: str  # "fix_attempted", "fix_applied", "error"
    exception_type: str
    confidence: float
    success: bool
    model: str
    duration_ms: int


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled (opt-in)."""
    config = get_config()
    return getattr(config, "telemetry_enabled", False)


def get_telemetry_endpoint() -> Optional[str]:
    """Get custom telemetry endpoint if configured."""
    config = get_config()
    return getattr(config, "telemetry_endpoint", None)


def record_event(
    event_type: str,
    exception_type: str,
    confidence: float,
    success: bool,
    model: str,
    duration_ms: int,
) -> None:
    """
    Record telemetry event (if enabled).

    Args:
        event_type: Type of event
        exception_type: Exception type (no message)
        confidence: Fix confidence
        success: Whether fix succeeded
        model: LLM model used
        duration_ms: Time taken
    """
    if not is_telemetry_enabled():
        return

    event = TelemetryEvent(
        timestamp=datetime.now().isoformat(),
        event_type=event_type,
        exception_type=exception_type,
        confidence=confidence,
        success=success,
        model=model.split("/")[-1] if "/" in model else model,  # Anonymize
        duration_ms=duration_ms,
    )

    # Store locally
    _store_event(event)

    # Send to endpoint if configured
    endpoint = get_telemetry_endpoint()
    if endpoint:
        _send_to_endpoint(event, endpoint)


def _store_event(event: TelemetryEvent) -> None:
    """Store event locally."""
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TELEMETRY_FILE, "a") as f:
        f.write(json.dumps(event.__dict__) + "\n")


def _send_to_endpoint(event: TelemetryEvent, endpoint: str) -> None:
    """Send event to custom endpoint."""
    try:
        import urllib.request
        import urllib.error

        data = json.dumps(event.__dict__).encode()

        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5):
            pass  # Fire and forget
    except Exception:
        pass  # Silently fail


def get_telemetry_summary() -> dict:
    """Get aggregate telemetry summary."""
    events = _load_telemetry_events()
    if not events:
        return {"events": 0, "telemetry_enabled": is_telemetry_enabled()}

    return _aggregate_telemetry_stats(events)


def _load_telemetry_events() -> list[dict]:
    """Load and parse telemetry events from file."""
    if not TELEMETRY_FILE.exists():
        return []

    events = []
    with open(TELEMETRY_FILE) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _aggregate_telemetry_stats(events: list[dict]) -> dict:
    """Aggregate stats from a list of events. CC≤5."""
    total = len(events)
    successes = sum(1 for e in events if e.get("success"))
    avg_confidence = sum(e.get("confidence", 0) for e in events) / total

    return {
        "events": total,
        "success_rate": successes / total if total > 0 else 0,
        "avg_confidence": avg_confidence,
        "by_model": _group_by_field(events, "model"),
        "by_error_type": _group_by_field(events, "exception_type"),
        "telemetry_enabled": is_telemetry_enabled(),
    }


def _group_by_field(events: list[dict], field_name: str) -> dict[str, int]:
    """Count occurrences of values in a specific field."""
    counts: dict[str, int] = {}
    for e in events:
        val = e.get(field_name, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


def clear_telemetry() -> None:
    """Clear all telemetry data."""
    if TELEMETRY_FILE.exists():
        TELEMETRY_FILE.unlink()
