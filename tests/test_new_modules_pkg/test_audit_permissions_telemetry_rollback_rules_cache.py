"""Tests for audit, permissions, telemetry, rollback, rules, and cache modules."""

import json
from datetime import datetime
from pathlib import Path

from pfix.audit import AuditEntry
from pfix.permissions import check_blocked_path, get_environment
from pfix.telemetry import TelemetryEvent, is_telemetry_enabled
from pfix.rollback import find_backup_dir, list_backups
from pfix.rules import ProjectRules
from pfix.cache import FixCache


class TestAudit:
    def test_audit_entry_creation(self) -> None:
        entry = AuditEntry(timestamp=datetime.now().isoformat(), file='/path/to/file.py', function='test_func', error='Test error', error_type='ValueError', fix_applied=True, diff='+test', model='test-model', confidence=0.95, approved_by='auto', rollback_available=True, backup_path='/path/to/backup.bak', file_hash_before='abc123', file_hash_after='def456')
        assert entry.error_type == 'ValueError'
        assert entry.confidence == 0.95

    def test_log_and_read_audit(self, tmp_path) -> None:
        audit_file = tmp_path / '.pfix' / 'audit.jsonl'
        audit_file.parent.mkdir(parents=True)
        entry = AuditEntry(timestamp=datetime.now().isoformat(), file='/path/to/file.py', function='test_func', error='Test error', error_type='ValueError', fix_applied=True, diff='+test', model='test-model', confidence=0.95, approved_by='auto', rollback_available=True, backup_path='/path/to/backup.bak', file_hash_before='abc123', file_hash_after='def456')
        with open(audit_file, 'w') as f:
            f.write(json.dumps(entry.__dict__) + '\n')
        with open(audit_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data['error_type'] == 'ValueError'


class TestPermissions:
    def test_get_environment(self, monkeypatch) -> None:
        monkeypatch.setenv('ENV', 'production')
        assert get_environment() == 'production'
        monkeypatch.setenv('ENVIRONMENT', 'staging')
        monkeypatch.delenv('ENV', raising=False)
        assert get_environment() == 'staging'

    def test_check_blocked_path(self) -> None:
        blocked = Path('/project/migrations/001_add_users.py')
        allowed, reason = check_blocked_path(blocked)
        assert not allowed
        assert 'migrations' in reason
        allowed_path = Path('/project/src/main.py')
        allowed, reason = check_blocked_path(allowed_path)
        assert allowed


class TestTelemetry:
    def test_telemetry_disabled_by_default(self, monkeypatch) -> None:
        monkeypatch.delenv('PFIX_TELEMETRY_ENABLED', raising=False)
        assert not is_telemetry_enabled()

    def test_telemetry_event_creation(self) -> None:
        event = TelemetryEvent(timestamp=datetime.now().isoformat(), event_type='fix_applied', exception_type='ValueError', confidence=0.95, success=True, model='test-model', duration_ms=1500)
        assert event.event_type == 'fix_applied'
        assert event.duration_ms == 1500


class TestRollback:
    def test_find_backup_dir(self, tmp_path) -> None:
        source = tmp_path / 'src' / 'main.py'
        backup_dir = find_backup_dir(source)
        assert backup_dir == tmp_path / 'src' / '.pfix_backups'

    def test_list_backups_empty(self, tmp_path) -> None:
        backups = list_backups(tmp_path / 'nonexistent.py')
        assert backups == []


class TestRules:
    def test_load_nonexistent_rules(self, tmp_path) -> None:
        rules = ProjectRules(tmp_path / '.pfix' / 'rules.md')
        assert not rules.has_rules()

    def test_load_rules(self, tmp_path) -> None:
        rules_file = tmp_path / '.pfix' / 'rules.md'
        rules_file.parent.mkdir(parents=True)
        rules_file.write_text('\n# Project Rules\n\n## Python Style\n- Always use type hints\n- Prefer pathlib over os.path\n\n## Dependencies\n- Use httpx instead of requests\n')
        rules = ProjectRules(rules_file)
        assert rules.has_rules()
        assert len(rules.rules) == 3
        assert 'Always use type hints' in rules.rules


class TestCache:
    def test_cache_initialization(self, tmp_path) -> None:
        cache_dir = tmp_path / '.pfix_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache = FixCache(cache_dir=cache_dir)
        stats = cache.stats()
        assert stats['backend'] in ['sqlite', 'diskcache']
