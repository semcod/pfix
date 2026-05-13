from __future__ import annotations
from pathlib import Path
from pfix.permissions import check_blocked_path, get_environment


class TestPermissions:
    def test_get_environment(self, monkeypatch):
        monkeypatch.setenv("ENV", "production")
        assert get_environment() == "production"
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("ENV", raising=False)
        assert get_environment() == "staging"

    def test_check_blocked_path(self):
        blocked = Path("/project/migrations/001_add_users.py")
        allowed, reason = check_blocked_path(blocked)
        assert not allowed
        assert "migrations" in reason
        allowed_path = Path("/project/src/main.py")
        allowed, reason = check_blocked_path(allowed_path)
        assert allowed
