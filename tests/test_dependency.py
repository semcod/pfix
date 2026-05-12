"""Tests for pfix dependency."""

from __future__ import annotations

import pytest

from pfix.dependency import resolve_package_name, detect_missing_from_error


# ── Dependency ──────────────────────────────────────────────────────

class TestDependency:
    def test_resolve_known(self):
        assert resolve_package_name("cv2") == "opencv-python"
        assert resolve_package_name("PIL") == "Pillow"
        assert resolve_package_name("yaml") == "pyyaml"
        assert resolve_package_name("sklearn") == "scikit-learn"
        assert resolve_package_name("git") == "gitpython"

    def test_resolve_unknown(self):
        assert resolve_package_name("requests") == "requests"

    def test_detect_missing(self):
        assert detect_missing_from_error("No module named 'pandas'") == "pandas"
        assert detect_missing_from_error("No module named 'foo.bar'") == "foo.bar"

    def test_detect_none(self):
        assert detect_missing_from_error("some other error") is None