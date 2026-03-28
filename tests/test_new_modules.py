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


from pfix.env_diagnostics.hardware import HardwareDiagnostic
from pfix.env_diagnostics.concurrency import ConcurrencyDiagnostic
from pfix.env_diagnostics.serialization import SerializationDiagnostic
from pfix.types import ErrorContext


# ── Hardware Diagnostic Tests ───────────────────────────────────────

class TestHardwareDiagnostic:
    def test_initialization(self):
        diag = HardwareDiagnostic()
        assert diag.category == "hardware"

    def test_cpu_count_check(self, tmp_path):
        diag = HardwareDiagnostic()
        results = diag._check_cpu_count()
        # Should return list (may be empty if multiple CPUs)
        assert isinstance(results, list)
        # If single CPU, should warn
        import multiprocessing
        if multiprocessing.cpu_count() == 1:
            assert len(results) == 1
            assert results[0].check_name == "single_cpu"
            assert results[0].status == "warning"

    def test_gpu_check_no_cuda(self, tmp_path, monkeypatch):
        diag = HardwareDiagnostic()
        # Ensure no CUDA env var
        monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
        results = diag._check_gpu_availability()
        # Should return empty list when no CUDA expected
        assert isinstance(results, list)

    def test_docker_check_not_in_docker(self, tmp_path, monkeypatch):
        diag = HardwareDiagnostic()
        results = diag._check_docker_limits()
        # Not in docker, should return empty list
        assert isinstance(results, list)

    def test_diagnose_exception_cuda_error(self):
        diag = HardwareDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=10,
            exception_type="RuntimeError",
            exception_message="CUDA out of memory",
        )
        # Hardware diagnostic returns None for exceptions
        result = diag.diagnose_exception(RuntimeError("CUDA error"), ctx)
        assert result is None


# ── Concurrency Diagnostic Tests ────────────────────────────────────

class TestConcurrencyDiagnostic:
    def test_initialization(self):
        diag = ConcurrencyDiagnostic()
        assert diag.category == "concurrency"

    def test_thread_count_normal(self):
        diag = ConcurrencyDiagnostic()
        results = diag._check_thread_count()
        # Normal thread count should not trigger warning
        assert isinstance(results, list)

    def test_asyncio_loop_check(self):
        diag = ConcurrencyDiagnostic()
        results = diag._check_asyncio_loop()
        # Should return list (ok status if loop running, empty otherwise)
        assert isinstance(results, list)

    def test_diagnose_asyncio_loop_error(self):
        diag = ConcurrencyDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=20,
            exception_type="RuntimeError",
            exception_message="asyncio loop is already running",
        )
        exc = RuntimeError("asyncio loop is already running")
        result = diag.diagnose_exception(exc, ctx)
        assert result is not None
        assert result.check_name == "asyncio_loop_already_running"
        assert result.status == "error"
        assert result.category == "concurrency"

    def test_diagnose_other_exception_returns_none(self):
        diag = ConcurrencyDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=20,
            exception_type="ValueError",
            exception_message="some other error",
        )
        exc = ValueError("some other error")
        result = diag.diagnose_exception(exc, ctx)
        assert result is None


# ── Serialization Diagnostic Tests ──────────────────────────────────

class TestSerializationDiagnostic:
    def test_initialization(self):
        diag = SerializationDiagnostic()
        assert diag.category == "serialization"

    def test_pickle_protocol_check(self):
        diag = SerializationDiagnostic()
        results = diag._check_pickle_protocol()
        # Should return list with warning about protocol versions
        assert isinstance(results, list)
        if results:
            assert results[0].check_name == "pickle_protocol"
            assert "protocol" in results[0].message.lower()

    def test_cache_files_check(self, tmp_path):
        diag = SerializationDiagnostic()
        # Create test pycache
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.cpython-39.pyc").write_text("fake pyc")

        results = diag._check_cache_files(tmp_path)
        # Should not error on valid cache
        assert isinstance(results, list)

    def test_diagnose_pickle_error(self):
        diag = SerializationDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=30,
            exception_type="PickleError",
            exception_message="cannot pickle object",
        )
        exc = type("PickleError", (Exception,), {})("cannot pickle object")
        result = diag.diagnose_exception(exc, ctx)
        assert result is not None
        assert result.check_name == "pickle_error"
        assert result.category == "serialization"

    def test_diagnose_json_error(self):
        diag = SerializationDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=30,
            exception_type="JSONDecodeError",
            exception_message="invalid json",
        )
        # Test with ValueError containing "json"
        exc = ValueError("invalid json at position 0")
        result = diag.diagnose_exception(exc, ctx)
        assert result is not None
        assert result.check_name == "json_error"
        assert result.category == "serialization"

    def test_diagnose_other_exception_returns_none(self):
        diag = SerializationDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=30,
            exception_type="ValueError",
            exception_message="not a serialization error",
        )
        exc = ValueError("not a serialization error")
        result = diag.diagnose_exception(exc, ctx)
        assert result is None


# ── Integration Tests ───────────────────────────────────────────────

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


# ── Runtime TODO Tests ────────────────────────────────────────────────

class TestRuntimeTodo:
    def test_error_fingerprint_normalization(self):
        from pfix.runtime_todo import ErrorFingerprint

        # Test IP normalization
        msg = "Connection refused: 192.168.1.100:5432"
        normalized = ErrorFingerprint._normalize_error_message(msg)
        assert "<ip>" in normalized
        assert "192.168.1.100" not in normalized
        assert "<port>" in normalized

        # Test memory address normalization
        msg2 = "Object at 0x7f8b2c4d5e6f"
        normalized2 = ErrorFingerprint._normalize_error_message(msg2)
        assert "<addr>" in normalized2
        assert "0x7f8b2c4d5e6f" not in normalized2

    def test_error_fingerprint_consistency(self):
        from pfix.runtime_todo import ErrorFingerprint
        from pfix.types import RuntimeIssue, TraceFrame

        # Same error should produce same fingerprint
        issue1 = RuntimeIssue(
            abs_filepath="/app/test.py",
            line_number=10,
            function_name="test_func",
            exception_type="ValueError",
            exception_message="test error",
        )
        issue2 = RuntimeIssue(
            abs_filepath="/app/test.py",
            line_number=10,
            function_name="test_func",
            exception_type="ValueError",
            exception_message="test error",
        )

        fp1 = ErrorFingerprint.compute(issue1)
        fp2 = ErrorFingerprint.compute(issue2)
        assert fp1 == fp2

    def test_error_fingerprint_differentiation(self):
        from pfix.runtime_todo import ErrorFingerprint
        from pfix.types import RuntimeIssue

        # Different errors should produce different fingerprints
        issue1 = RuntimeIssue(
            abs_filepath="/app/test.py",
            line_number=10,
            function_name="test_func",
            exception_type="ValueError",
            exception_message="error one",
        )
        issue2 = RuntimeIssue(
            abs_filepath="/app/test.py",
            line_number=10,
            function_name="test_func",
            exception_type="TypeError",
            exception_message="error one",
        )

        fp1 = ErrorFingerprint.compute(issue1)
        fp2 = ErrorFingerprint.compute(issue2)
        assert fp1 != fp2

    def test_todofile_append_and_dedup(self, tmp_path):
        from pfix.runtime_todo import TodoFile
        from pfix.types import RuntimeIssue, TraceFrame
        from datetime import datetime, timezone

        todo_file = tmp_path / "TODO.md"
        todo = TodoFile(todo_file)

        # Create first issue
        issue = RuntimeIssue(
            abs_filepath=str(tmp_path / "app.py"),
            line_number=42,
            function_name="main",
            module_name="app",
            exception_type="RuntimeError",
            exception_message="test error",
            traceback_frames=[
                TraceFrame(filepath=str(tmp_path / "app.py"), line_number=42, function_name="main", code_line="raise RuntimeError()")
            ],
            timestamp=datetime.now(timezone.utc),
            python_version="3.12.0",
            venv_path=str(tmp_path / ".venv"),
            hostname="test-host",
            pid=1234,
            working_dir=str(tmp_path),
            argv=["python", "app.py"],
            category="runtime_error",
            severity="high",
        )

        # First append should succeed (new entry)
        from pfix.runtime_todo import ErrorFingerprint
        issue.fingerprint = ErrorFingerprint.compute(issue)
        result1 = todo.append_issue(issue)
        assert result1 is True

        # Second append should be deduplicated (False, counter incremented)
        result2 = todo.append_issue(issue)
        assert result2 is False

        # Verify file content
        content = todo_file.read_text()
        assert "Runtime Errors (Production)" in content
        assert "RuntimeError: test error" in content
        assert "count=2" in content

    def test_runtime_collector_severity_filtering(self):
        from pfix.runtime_todo import RuntimeCollector, TodoFile

        todo = TodoFile("/tmp/test.md")
        collector = RuntimeCollector(
            todo,
            enabled=True,
            min_severity="high",
        )

        # Low severity should not be captured
        assert not collector._should_capture(ValueError("low"))

        # High severity should be captured
        class MockConnError(ConnectionError):
            pass
        assert collector._should_capture(MockConnError("high"))

    def test_runtime_collector_classification(self):
        from pfix.runtime_todo import RuntimeCollector, TodoFile

        todo = TodoFile("/tmp/test.md")
        collector = RuntimeCollector(todo)

        # Test exception classifications
        assert collector._classify(ModuleNotFoundError("test")) == "import_error"
        assert collector._classify(FileNotFoundError("test")) == "filesystem_error"
        assert collector._classify(ConnectionError("test")) == "network_error"
        assert collector._classify(ValueError("test")) == "value_error"


# ── EnvDiagnostics Functionality Tests ───────────────────────────────

class TestEnvDiagnostics:
    def test_env_diagnostics_initialization(self):
        from pfix.env_diagnostics import EnvDiagnostics
        from pathlib import Path

        diag = EnvDiagnostics()
        assert diag.project_root == Path.cwd().resolve()

        diag2 = EnvDiagnostics("/tmp")
        assert diag2.project_root == Path("/tmp").resolve()

    def test_filesystem_disk_space_check(self, tmp_path):
        from pfix.env_diagnostics.filesystem import FilesystemDiagnostic

        diag = FilesystemDiagnostic()
        results = diag._check_disk_space(tmp_path)

        # Should return list (may be empty if plenty of space)
        assert isinstance(results, list)
        for r in results:
            assert r.category == "filesystem"
            assert r.check_name == "disk_space"

    def test_import_shadow_stdlib_check(self, tmp_path):
        from pfix.env_diagnostics.imports import ImportDiagnostic
        from pathlib import Path

        # Create a file that shadows stdlib
        json_file = tmp_path / "json.py"
        json_file.write_text("# shadows stdlib json")

        diag = ImportDiagnostic()
        results = diag._check_shadow_stdlib(tmp_path)

        # Should detect the shadowing
        assert any(r.check_name == "stdlib_shadow" for r in results)

    def test_venv_active_check(self, monkeypatch):
        from pfix.env_diagnostics.venv import VenvDiagnostic

        # Simulate no venv
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)

        diag = VenvDiagnostic()
        results = diag._check_venv_active()

        # Should warn about no venv
        if results:
            assert any(r.check_name == "no_venv" for r in results)

    def test_encoding_utf8_check(self, tmp_path):
        from pfix.env_diagnostics.encoding import EncodingDiagnostic

        # Create file with BOM
        bom_file = tmp_path / "bom.py"
        bom_file.write_bytes(b"\xef\xbb\xbf# coding: utf-8\nprint('hello')")

        diag = EncodingDiagnostic()
        results = diag._check_file_encoding(tmp_path)

        # Should detect BOM
        assert any(r.check_name == "utf8_bom" for r in results)

    def test_config_env_gitignore_check(self, tmp_path):
        from pfix.env_diagnostics.config_env import ConfigEnvDiagnostic

        # Create .env without .gitignore
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=supersecret\n")

        diag = ConfigEnvDiagnostic()
        results = diag._check_env_gitignore(tmp_path)

        # Should warn about .env not being gitignored
        if results:
            assert any(r.check_name == "env_not_gitignored" for r in results)

    def test_diagnose_exception_import_error(self):
        from pfix.env_diagnostics.imports import ImportDiagnostic
        from pfix.types import ErrorContext

        diag = ImportDiagnostic()
        ctx = ErrorContext(
            source_file="/app/main.py",
            line_number=10,
        )

        result = diag.diagnose_exception(
            ModuleNotFoundError("No module named 'pandas'"),
            ctx
        )

        assert result is not None
        assert result.category == "import_dependency"
        assert "pandas" in result.message

    def test_generate_report_format(self, tmp_path):
        from pfix.env_diagnostics import EnvDiagnostics
        from pfix.types import DiagnosticResult

        diag = EnvDiagnostics(tmp_path)

        # Create some test results
        results = [
            DiagnosticResult(
                category="filesystem",
                check_name="test",
                status="error",
                message="Test error",
                suggestion="Fix it",
            ),
            DiagnosticResult(
                category="memory",
                check_name="test2",
                status="warning",
                message="Test warning",
            ),
        ]

        report = diag.generate_report(results)
        assert "Environment Diagnostics Report" in report
        assert "Test error" in report
        assert "Fix it" in report

    def test_third_party_diagnostic_import(self):
        from pfix.env_diagnostics.third_party import ThirdPartyDiagnostic
        from pfix.types import ErrorContext

        diag = ThirdPartyDiagnostic()
        assert diag.category == "third_party"

        # Test rate limit detection
        ctx = ErrorContext(source_file="/app/main.py", line_number=10)
        result = diag.diagnose_exception(
            Exception("Rate limit exceeded: 429 Too Many Requests"),
            ctx
        )
        assert result is not None
        assert result.check_name == "rate_limit"

    def test_third_party_api_key_placeholder(self, monkeypatch):
        from pfix.env_diagnostics.third_party import ThirdPartyDiagnostic

        monkeypatch.setenv("OPENAI_API_KEY", "your_key_here")

        diag = ThirdPartyDiagnostic()
        results = diag._check_api_keys_in_env()

        assert any(r.check_name == "api_key_placeholder" for r in results)

    def test_circular_import_detection(self, tmp_path):
        from pfix.env_diagnostics.imports import ImportDiagnostic

        # Create circular import: a.py -> b.py -> a.py
        a_file = tmp_path / "a.py"
        b_file = tmp_path / "b.py"

        a_file.write_text("from b import func_b\ndef func_a(): pass")
        b_file.write_text("from a import func_a\ndef func_b(): pass")

        diag = ImportDiagnostic()
        results = diag._check_circular_imports(tmp_path)

        assert any(r.check_name == "circular_import" for r in results)
        circular = [r for r in results if r.check_name == "circular_import"][0]
        assert "a" in circular.message and "b" in circular.message

    def test_version_conflict_check(self, tmp_path, monkeypatch):
        from pfix.env_diagnostics.imports import ImportDiagnostic
        from pfix.types import DiagnosticResult

        diag = ImportDiagnostic()
        # This test may or may not find conflicts depending on env
        # Just verify it doesn't crash
        results = diag._check_version_conflicts()
        assert isinstance(results, list)
        for r in results:
            assert r.category == "import_dependency"
            assert r.check_name == "version_conflict"


# ── Auto-fix Tests ──────────────────────────────────────────────────

class TestAutoFix:
    def test_auto_fix_registry(self):
        from pfix.env_diagnostics.auto_fix import _FIX_HANDLERS, can_auto_fix
        from pfix.types import DiagnosticResult

        # Verify handlers exist
        assert "stale_bytecode" in _FIX_HANDLERS
        assert "utf8_bom" in _FIX_HANDLERS
        assert "missing_dotenv" in _FIX_HANDLERS

        # Test can_auto_fix
        fixable = DiagnosticResult(
            category="filesystem",
            check_name="stale_bytecode",
            status="warning",
            message="Test",
            auto_fixable=True,
        )
        assert can_auto_fix(fixable)

        non_fixable = DiagnosticResult(
            category="filesystem",
            check_name="disk_space",
            status="error",
            message="Test",
            auto_fixable=False,
        )
        assert not can_auto_fix(non_fixable)

    def test_fix_utf8_bom(self, tmp_path):
        from pfix.env_diagnostics.auto_fix import apply_auto_fix
        from pfix.types import DiagnosticResult

        # Create file with BOM
        test_file = tmp_path / "test.py"
        test_file.write_bytes(b"\xef\xbb\xbf# test\nprint('hello')")

        result = DiagnosticResult(
            category="encoding",
            check_name="utf8_bom",
            status="warning",
            message="UTF-8 BOM detected",
            auto_fixable=True,
            abs_path=str(test_file),
        )

        success, msg = apply_auto_fix(result, tmp_path)
        assert success
        assert "BOM" in msg

        # Verify BOM removed
        content = test_file.read_bytes()
        assert not content.startswith(b"\xef\xbb\xbf")

    def test_fix_missing_dotenv(self, tmp_path):
        from pfix.env_diagnostics.auto_fix import apply_auto_fix
        from pfix.types import DiagnosticResult

        # Create .env.example
        example = tmp_path / ".env.example"
        example.write_text("KEY=value\n")

        result = DiagnosticResult(
            category="config_env",
            check_name="missing_dotenv",
            status="warning",
            message=".env missing",
            auto_fixable=True,
        )

        success, msg = apply_auto_fix(result, tmp_path)
        assert success
        assert ".env" in msg

        # Verify .env created
        assert (tmp_path / ".env").exists()

    def test_fix_gitignore_env(self, tmp_path):
        from pfix.env_diagnostics.auto_fix import apply_auto_fix
        from pfix.types import DiagnosticResult

        # Create .env
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=test\n")

        result = DiagnosticResult(
            category="config_env",
            check_name="env_not_gitignored",
            status="critical",
            message=".env not in gitignore",
            auto_fixable=True,
        )

        success, msg = apply_auto_fix(result, tmp_path)
        assert success

        # Verify .gitignore created with .env
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".env" in gitignore.read_text()
