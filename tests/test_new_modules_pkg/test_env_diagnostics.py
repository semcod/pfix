"""Tests for env_diagnostics hardware, concurrency, and serialization diagnostics."""

from pfix.env_diagnostics.hardware import HardwareDiagnostic
from pfix.env_diagnostics.concurrency import ConcurrencyDiagnostic
from pfix.env_diagnostics.serialization import SerializationDiagnostic
from pfix.types import ErrorContext


class TestHardwareDiagnostic:
    def test_initialization(self) -> None:
        diag = HardwareDiagnostic()
        assert diag.category == 'hardware'

    def test_cpu_count_check(self, tmp_path) -> None:
        diag = HardwareDiagnostic()
        results = diag._check_cpu_count()
        assert isinstance(results, list)
        import multiprocessing
        if multiprocessing.cpu_count() == 1:
            assert len(results) == 1
            assert results[0].check_name == 'single_cpu'
            assert results[0].status == 'warning'

    def test_gpu_check_no_cuda(self, tmp_path, monkeypatch) -> None:
        diag = HardwareDiagnostic()
        monkeypatch.delenv('CUDA_VISIBLE_DEVICES', raising=False)
        results = diag._check_gpu_availability()
        assert isinstance(results, list)

    def test_docker_check_not_in_docker(self, tmp_path, monkeypatch) -> None:
        diag = HardwareDiagnostic()
        results = diag._check_docker_limits()
        assert isinstance(results, list)

    def test_diagnose_exception_cuda_error(self) -> None:
        diag = HardwareDiagnostic()
        ctx = ErrorContext(source_file='/test/file.py', line_number=10, exception_type='RuntimeError', exception_message='CUDA out of memory')
        result = diag.diagnose_exception(RuntimeError('CUDA error'), ctx)
        assert result is None


class TestConcurrencyDiagnostic:
    def test_initialization(self) -> None:
        diag = ConcurrencyDiagnostic()
        assert diag.category == 'concurrency'

    def test_thread_count_normal(self) -> None:
        diag = ConcurrencyDiagnostic()
        results = diag._check_thread_count()
        assert isinstance(results, list)

    def test_asyncio_loop_check(self) -> None:
        diag = ConcurrencyDiagnostic()
        results = diag._check_asyncio_loop()
        assert isinstance(results, list)

    def test_diagnose_asyncio_loop_error(self) -> None:
        diag = ConcurrencyDiagnostic()
        ctx = ErrorContext(source_file='/test/file.py', line_number=20, exception_type='RuntimeError', exception_message='asyncio loop is already running')
        exc = RuntimeError('asyncio loop is already running')
        result = diag.diagnose_exception(exc, ctx)
        assert result is not None
        assert result.check_name == 'asyncio_loop_already_running'
        assert result.status == 'error'
        assert result.category == 'concurrency'

    def test_diagnose_other_exception_returns_none(self) -> None:
        diag = ConcurrencyDiagnostic()
        ctx = ErrorContext(source_file='/test/file.py', line_number=20, exception_type='ValueError', exception_message='some other error')
        exc = ValueError('some other error')
        result = diag.diagnose_exception(exc, ctx)
        assert result is None


class TestSerializationDiagnostic:
    def test_initialization(self) -> None:
        diag = SerializationDiagnostic()
        assert diag.category == 'serialization'

    def test_pickle_protocol_check(self) -> None:
        diag = SerializationDiagnostic()
        results = diag._check_pickle_protocol()
        assert isinstance(results, list)
        if results:
            assert results[0].check_name == 'pickle_protocol'
            assert 'protocol' in results[0].message.lower()

    def test_cache_files_check(self, tmp_path) -> None:
        diag = SerializationDiagnostic()
        results = diag._check_cache_files(tmp_path)
        assert isinstance(results, list)
