from datetime import datetime

from pfix.telemetry import TelemetryEvent, is_telemetry_enabled


class TestTelemetry:
    def test_telemetry_disabled_by_default(self, monkeypatch) -> None:
        monkeypatch.delenv("PFIX_TELEMETRY_ENABLED", raising=False)
        assert not is_telemetry_enabled()

    def test_telemetry_event_creation(self) -> None:
        event = TelemetryEvent(
            timestamp=datetime.now().isoformat(),
            event_type="fix_applied",
            exception_type="ValueError",
            confidence=0.95,
            success=True,
            model="test-model",
            duration_ms=1500,
        )
        assert event.event_type == "fix_applied"
        assert event.duration_ms == 1500
