"""Tests for pfix decorator."""

from __future__ import annotations

import pytest

from pfix import pfix

from pfix.config import reset_config


# ── Decorator ───────────────────────────────────────────────────────

class TestDecorator:
    def setup_method(self):
        reset_config()

    def test_passthrough(self):
        @pfix(enabled=True)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_disabled(self):
        @pfix(enabled=False)
        def fail():
            raise ValueError("test")

        with pytest.raises(ValueError):
            fail()

    def test_metadata(self):
        @pfix(hint="test hint", deps=["foo"])
        def my_func():
            """Docstring."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Docstring."
        assert my_func._pfix_decorated is True
        assert my_func._pfix_hint == "test hint"

    def test_bare_decorator(self):
        @pfix
        def identity(x):
            return x

        assert identity(42) == 42
        assert identity._pfix_decorated is True