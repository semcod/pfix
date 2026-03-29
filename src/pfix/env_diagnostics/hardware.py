"""
pfix.env_diagnostics.hardware — Hardware diagnostics.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base import BaseDiagnostic

if TYPE_CHECKING:
    from ..types import DiagnosticResult, ErrorContext


class HardwareDiagnostic(BaseDiagnostic):
    """Diagnose hardware-related problems."""

    category = "hardware"

    def check(self, project_root: Path) -> list["DiagnosticResult"]:
        """Run all hardware checks."""
        results = []
        results.extend(self._check_gpu_availability())
        results.extend(self._check_cpu_count())
        results.extend(self._check_docker_limits())
        results.extend(self._check_thermal_throttling())
        results.extend(self._check_battery_status())
        results.extend(self._check_avx_support())
        return results

    def _check_gpu_availability(self) -> list["DiagnosticResult"]:
        """Check if GPU is available when CUDA is expected."""
        from ..types import DiagnosticResult

        results = []

        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")

        if cuda_visible is not None:
            # CUDA is expected - check if available
            try:
                # Try importing torch to check CUDA
                import importlib
                torch = importlib.import_module("torch")

                if not torch.cuda.is_available():
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="cuda_not_available",
                        status="warning",
                        message="CUDA_VISIBLE_DEVICES set but CUDA not available",
                        details={"cuda_visible_devices": cuda_visible},
                        suggestion="Check NVIDIA drivers and CUDA installation",
                        auto_fixable=False,
                        abs_path=None,
                        line_number=None,
                    ))

            except ImportError:
                # PyTorch not installed - can't check
                pass

        return results

    def _check_cpu_count(self) -> list["DiagnosticResult"]:
        """Check available CPU cores."""
        from ..types import DiagnosticResult
        import multiprocessing

        results = []

        cpu_count = multiprocessing.cpu_count()

        if cpu_count == 1:
            results.append(DiagnosticResult(
                category=self.category,
                check_name="single_cpu",
                status="warning",
                message=f"Only 1 CPU core available",
                details={"cpu_count": cpu_count},
                suggestion="Some parallel operations may be slow",
                auto_fixable=False,
                abs_path=None,
                line_number=None,
            ))

        return results

    def _check_docker_limits(self) -> list["DiagnosticResult"]:
        """Check for Docker resource limits."""
        from ..types import DiagnosticResult

        results = []

        # Check if running in Docker
        if not Path("/.dockerenv").exists():
            return results

        # Check cgroup limits
        try:
            memory_limit_file = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
            if memory_limit_file.exists():
                limit = int(memory_limit_file.read_text().strip())
                if limit < 1_000_000_000:  # < 1GB
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="docker_memory_limit",
                        status="warning",
                        message=f"Docker memory limit: {limit // (1024**2)} MB",
                        details={"memory_limit_bytes": limit},
                        suggestion="Increase Docker memory limit if needed",
                        auto_fixable=False,
                        abs_path=None,
                        line_number=None,
                    ))
        except Exception:
            pass

        return results

    def _check_thermal_throttling(self) -> list["DiagnosticResult"]:
        """Check for CPU thermal throttling (Linux)."""
        from ..types import DiagnosticResult
        results = []
        thermal_path = Path("/sys/class/thermal/")
        if thermal_path.exists():
            try:
                for zone in thermal_path.glob("thermal_zone*"):
                    temp = int((zone / "temp").read_text().strip()) / 1000
                    if temp > 90:
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="cpu_overheating",
                            status="critical",
                            message=f"CPU temperature is very high: {temp}°C",
                            suggestion="Check cooling or reduce system load",
                        ))
            except Exception:
                pass
        return results

    def _check_battery_status(self) -> list["DiagnosticResult"]:
        """Check if running on battery power (Linux)."""
        from ..types import DiagnosticResult
        results = []
        power_path = Path("/sys/class/power_supply/")
        if power_path.exists():
            try:
                for supply in power_path.glob("BAT*"):
                    status = (supply / "status").read_text().strip()
                    if status == "Discharging":
                        capacity = int((supply / "capacity").read_text().strip())
                        results.append(DiagnosticResult(
                            category=self.category,
                            check_name="battery_discharging",
                            status="warning",
                            message=f"Running on battery: {capacity}%",
                            suggestion="Plug in charger for maximum performance",
                        ))
            except Exception:
                pass
        return results

    def _check_avx_support(self) -> list["DiagnosticResult"]:
        """Check for AVX/AVX2 support in CPU (vital for many native libs)."""
        from ..types import DiagnosticResult
        results = []
        # Basic check via /proc/cpuinfo
        cpuinfo = Path("/proc/cpuinfo")
        if cpuinfo.exists():
            try:
                content = cpuinfo.read_text()
                if "avx" not in content.lower():
                    results.append(DiagnosticResult(
                        category=self.category,
                        check_name="no_avx_support",
                        status="warning",
                        message="CPU does not support AVX instructions",
                        suggestion="Some numerical libraries may be significantly slower",
                    ))
            except Exception:
                pass
        return results

    def diagnose_exception(
        self,
        exc: BaseException,
        ctx: "ErrorContext",
    ) -> Optional["DiagnosticResult"]:
        """Diagnose hardware-related exceptions."""
        return None
