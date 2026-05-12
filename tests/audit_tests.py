import json
from datetime import datetime
from pathlib import Path
import pytest
from pfix.audit import AuditEntry, log_fix_audit, read_audit_log

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
        audit_file = tmp_path / ".pfix" / "audit.jsonl"
        audit_file.parent.mkdir(parents=True)
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
        with open(audit_file, "w") as f:
            f.write(json.dumps(entry.__dict__) + "\n")
        with open(audit_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["error_type"] == "ValueError"
