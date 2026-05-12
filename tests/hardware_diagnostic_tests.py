import pytest
from pfix.env_diagnostics.hardware import HardwareDiagnostic
from pfix.types import ErrorContext

class TestHardwareDiagnostic:
    def test_initialization(self):
        diag = HardwareDiagnostic()
        assert diag.category == "hardware"

    def test_cpu_count_check(self, tmp_path):
        diag = HardwareDiagnostic()
        results = diag._check_cpu_count()
        assert isinstance(results, list)
        import multiprocessing
        if multiprocessing.cpu_count() == 1:
            assert len(results) == 1
            assert results[0].check_name == "single_cpu"
            assert results[0].status == "warning"

    def test_gpu_check_no_cuda(self, tmp_path, monkeypatch):
        diag = HardwareDiagnostic()
        monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
        results = diag._check_gpu_availability()
        assert isinstance(results, list)

    def test_docker_check_not_in_docker(self, tmp_path, monkeypatch):
        diag = HardwareDiagnostic()
        results = diag._check_docker_limits()
        assert isinstance(results, list)

    def test_diagnose_exception_cuda_error(self):
        diag = HardwareDiagnostic()
        ctx = ErrorContext(
            source_file="/test/file.py",
            line_number=10,
            exception_type="RuntimeError",
            exception_message="CUDA out of memory",
        )
        result = diag.diagnose_exception(RuntimeError("CUDA error"), ctx)
        assert result is None
