from __future__ import annotations
import pytest
import multiprocessing
from pfix.env_diagnostics.hardware import HardwareDiagnostic
from pfix.env_diagnostics.concurrency import ConcurrencyDiagnostic
from pfix.types import ErrorContext

class TestHardwareDiagnostic:
    def test_initialization(self):
        diag = HardwareDiagnostic()
        assert diag.category == "hardware"

    def test_cpu_count_check(self):
        diag = HardwareDiagnostic()
        results = diag._check_cpu_count()
        assert isinstance(results, list)
        if multiprocessing.cpu_count() == 1:
            assert len(results) == 1
            assert results[0].check_name == "single_cpu"

class TestConcurrencyDiagnostic:
    def test_initialization(self):
        diag = ConcurrencyDiagnostic()
        assert diag.category == "concurrency"