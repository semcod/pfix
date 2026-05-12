"""Tests for pfix config."""

from __future__ import annotations

import pytest

from pfix.config import PfixConfig, configure, reset_config

CONSTANT_3 = 3
CONSTANT_5 = 5
CONSTANT_7 = 7
CONSTANT_42 = 42



# ── Config ──────────────────────────────────────────────────────────

class TestConfig:
    def setup_method(self):
        reset_config()

    def test_defaults(self):
        cfg = PfixConfig()
        assert cfg.max_retries == 3
        assert cfg.auto_apply is False
        assert cfg.enabled is True
        assert cfg.auto_restart is False

    def test_configure_override(self):
        cfg = configure(max_retries=10, auto_apply=True, auto_restart=True)
        assert cfg.max_retries == 10
        assert cfg.auto_apply is True
        assert cfg.auto_restart is True
        reset_config()

    def test_uv_detection(self):
        cfg = PfixConfig()
        assert cfg.pkg_manager in ("pip", "uv")

    def test_validate_no_key(self):
        cfg = PfixConfig()
        assert any("API key" in w for w in cfg.validate())

    def test_validate_with_key(self):
        cfg = PfixConfig(llm_api_key="test-key")
        assert not any("API key" in w for w in cfg.validate())

    def test_git_config(self):
        cfg = PfixConfig(git_auto_commit=True, git_commit_prefix="fix: ")
        assert cfg.git_auto_commit is True
        assert cfg.git_commit_prefix == "fix: "