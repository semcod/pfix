"""Tests for pfix fixer."""

from __future__ import annotations


from pfix.fixer import _validate_syntax, _make_diff


# ── Fixer ───────────────────────────────────────────────────────────


class TestFixer:
    def test_validate_syntax(self):
        assert _validate_syntax("def foo(): return 1") is True
        assert _validate_syntax("def foo(: return") is False

    def test_make_diff(self):
        old = "line1\nline2\nline3\n"
        new = "line1\nline2_changed\nline3\n"
        diff = _make_diff(old, new, "test.py")
        assert "-line2" in diff
        assert "+line2_changed" in diff
