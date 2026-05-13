"""Tests for pfix CLI."""

from __future__ import annotations


from pfix.cli import main

from pathlib import Path


# ── CLI ─────────────────────────────────────────────────────────────


class TestCLI:
    def test_version(self, capsys):
        version = Path("VERSION").read_text().strip()
        ret = main(["version"])
        assert ret == 0
        assert version in capsys.readouterr().out

    def test_check_no_key(self, monkeypatch, tmp_path):
        # Create empty .env in temp dir to avoid loading real .env
        empty_env = tmp_path / ".env"
        empty_env.write_text("")
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
