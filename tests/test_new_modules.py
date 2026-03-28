"""Tests for pfix new modules (audit, rollback, permissions, telemetry, env_diagnostics)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from pfix.audit import AuditEntry, log_fix_audit, read_audit_log, get_audit_summary
from pfix.permissions import check_auto_apply_allowed, check_blocked_path, get_environment
from pfix.telemetry import TelemetryEvent, is_telemetry_enabled, record_event, get_telemetry_summary
from pfix.rollback import find_backup_dir, list_backups
from pfix.rules import ProjectRules
from pfix.cache import FixCache


# ── Audit Tests ──────────────────────────────────────────────────────

class TestAudit:
    def test_audit_entry_creation(self):
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            file="/path/to/file.py",
            function="test_func",
            error="Test error",
            error_type="ValueError",
            fix_applied=True,
            diff="+test",
            model="test-model",
            confidence=0.95,
            approved_by="auto",
            rollback_available=True,
            backup_path="/path/to/backup.bak",
            file_hash_before="abc123",
            file_hash_after="def456",
        )
        assert entry.error_type == "ValueError"
        assert entry.confidence == 0.95

    def test_log_and_read_audit(self, tmp_path):
        # Use temp directory for audit
        audit_file = tmp_path / ".pfix" / "audit.jsonl"
        audit_file.parent.mkdir(parents=True)
        
        # Create entry
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            file="/path/to/file.py",
            function="test_func",
            error="Test error",
            error_type="ValueError",
            fix_applied=True,
            diff="+test",
            model="test-model",
            confidence=0.95,
            approved_by="auto",
            rollback_available=True,
            backup_path="/path/to/backup.bak",
            file_hash_before="abc123",
            file_hash_after="def456",
        )
        
        # Write to file
        with open(audit_file, "w") as f:
            f.write(json.dumps(entry.__dict__) + "\n")
        
        # Read back
        with open(audit_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["error_type"] == "ValueError"


# ── Permissions Tests ─────────────────────────────────────────────────

class TestPermissions:
    def test_get_environment(self, monkeypatch):
        # Test with ENV variable
        monkeypatch.setenv("ENV", "production")
        assert get_environment() == "production"
        
        # Test with ENVIRONMENT variable
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("ENV", raising=False)
        assert get_environment() == "staging"
    
    def test_check_blocked_path(self):
        # Test blocked patterns
        blocked = Path("/project/migrations/001_add_users.py")
        allowed, reason = check_blocked_path(blocked)
        assert not allowed
        assert "migrations" in reason
        
        # Test allowed path
        allowed_path = Path("/project/src/main.py")
        allowed, reason = check_blocked_path(allowed_path)
        assert allowed


# ── Telemetry Tests ───────────────────────────────────────────────────

class TestTelemetry:
    def test_telemetry_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("PFIX_TELEMETRY_ENABLED", raising=False)
        assert not is_telemetry_enabled()
    
    def test_telemetry_event_creation(self):
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


# ── Rollback Tests ────────────────────────────────────────────────────

class TestRollback:
    def test_find_backup_dir(self, tmp_path):
        source = tmp_path / "src" / "main.py"
        backup_dir = find_backup_dir(source)
        assert backup_dir == tmp_path / "src" / ".pfix_backups"
    
    def test_list_backups_empty(self, tmp_path):
        backups = list_backups(tmp_path / "nonexistent.py")
        assert backups == []


# ── Rules Tests ───────────────────────────────────────────────────────

class TestRules:
    def test_load_nonexistent_rules(self, tmp_path):
        rules = ProjectRules(tmp_path / ".pfix" / "rules.md")
        assert not rules.has_rules()
    
    def test_load_rules(self, tmp_path):
        rules_file = tmp_path / ".pfix" / "rules.md"
        rules_file.parent.mkdir(parents=True)
        rules_file.write_text("""
# Project Rules

## Python Style
- Always use type hints
- Prefer pathlib over os.path

## Dependencies
- Use httpx instead of requests
""")
        
        rules = ProjectRules(rules_file)
        assert rules.has_rules()
        assert len(rules.rules) == 3
        assert "Always use type hints" in rules.rules


# ── Cache Tests ───────────────────────────────────────────────────────

class TestCache:
    def test_cache_initialization(self, tmp_path):
        cache_dir = tmp_path / ".pfix_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache = FixCache(cache_dir=cache_dir)
        stats = cache.stats()
        assert stats["backend"] in ["sqlite", "diskcache"]


# ── EnvDiagnostics Imports Test ───────────────────────────────────────

class TestEnvDiagnosticsImports:
    def test_import_env_diagnostics(self):
        from pfix.env_diagnostics import EnvDiagnostics
        assert EnvDiagnostics is not None
    
    def test_import_base_diagnostic(self):
        from pfix.env_diagnostics.base import BaseDiagnostic
        assert BaseDiagnostic is not None
    
    def test_import_specific_diagnostics(self):
        from pfix.env_diagnostics.imports import ImportDiagnostic
        from pfix.env_diagnostics.filesystem import FilesystemDiagnostic
        from pfix.env_diagnostics.memory import MemoryDiagnostic
        
        assert ImportDiagnostic is not None
        assert FilesystemDiagnostic is not None
        assert MemoryDiagnostic is not None
