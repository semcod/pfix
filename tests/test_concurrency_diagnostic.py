from pfix.env_diagnostics.concurrency import ConcurrencyDiagnostic
from pfix.types import ErrorContext


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