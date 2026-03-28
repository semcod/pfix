"""Tests for pfix."""

from __future__ import annotations

import textwrap
import pytest

from pfix.analyzer import ErrorContext, analyze_exception, classify_error, _extract_imports
from pfix.config import PfixConfig, configure, reset_config
from pfix.dependency import resolve_package_name, detect_missing_from_error
from pfix.llm import FixProposal, _parse_response


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


# ── Analyzer ────────────────────────────────────────────────────────

class TestAnalyzer:
    def test_analyze_name_error(self):
        try:
            _ = undefined_variable  # noqa: F821
        except NameError as e:
            ctx = analyze_exception(e)
            assert ctx.exception_type == "NameError"
            assert "undefined_variable" in ctx.exception_message

    def test_analyze_with_func(self):
        def buggy():
            return 1 / 0

        try:
            buggy()
        except ZeroDivisionError as e:
            ctx = analyze_exception(e, func=buggy)
            assert "buggy" in ctx.function_name
            assert "buggy" in ctx.function_source

    def test_classify_module_not_found(self):
        ctx = ErrorContext(exception_type="ModuleNotFoundError", exception_message="No module named 'foo'")
        assert classify_error(ctx) == "missing_dependency"

    def test_classify_name_error(self):
        ctx = ErrorContext(exception_type="NameError", exception_message="name 'x' is not defined")
        assert classify_error(ctx) == "missing_import"

    def test_classify_type_error(self):
        ctx = ErrorContext(exception_type="TypeError", exception_message="unsupported")
        assert classify_error(ctx) == "type_error"

    def test_classify_file_not_found(self):
        ctx = ErrorContext(exception_type="FileNotFoundError", exception_message="no such file")
        assert classify_error(ctx) == "file_not_found"

    def test_extract_imports(self):
        source = "import os\nimport sys\nfrom pathlib import Path\n"
        imports = _extract_imports(source)
        assert "import os" in imports
        assert "from pathlib import Path" in imports
        assert len(imports) == 3

    def test_to_prompt(self):
        ctx = ErrorContext(
            exception_type="ValueError",
            exception_message="invalid",
            source_file="test.py",
            function_name="parse",
            line_number=10,
            missing_deps=["pandas"],
        )
        prompt = ctx.to_prompt()
        assert "ValueError" in prompt
        assert "pandas" in prompt
        assert "pipreqs" in prompt


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


# ── LLM Parsing ────────────────────────────────────────────────────

class TestLLMParsing:
    def test_parse_valid_json(self):
        raw = '{"diagnosis": "Missing import", "confidence": 0.9, "dependencies": ["numpy"]}'
        p = _parse_response(raw)
        assert p.diagnosis == "Missing import"
        assert p.confidence == 0.9
        assert p.dependencies == ["numpy"]

    def test_parse_markdown_fenced(self):
        raw = '```json\n{"diagnosis": "Type issue", "confidence": 0.8}\n```'
        p = _parse_response(raw)
        assert p.diagnosis == "Type issue"

    def test_parse_invalid(self):
        p = _parse_response("not json")
        assert p.confidence == 0.0

    def test_has_code_fix(self):
        assert FixProposal(fixed_function="def f(): pass").has_code_fix
        assert not FixProposal().has_code_fix

    def test_has_dep_fix(self):
        assert FixProposal(dependencies=["numpy"]).has_dependency_fix
        assert not FixProposal().has_dependency_fix


# ── Decorator ───────────────────────────────────────────────────────

class TestDecorator:
    def setup_method(self):
        reset_config()

    def test_passthrough(self):
        from pfix import pfix

        @pfix(enabled=True)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_disabled(self):
        from pfix import pfix

        @pfix(enabled=False)
        def fail():
            raise ValueError("test")

        with pytest.raises(ValueError):
            fail()

    def test_metadata(self):
        from pfix import pfix

        @pfix(hint="test hint", deps=["foo"])
        def my_func():
            """Docstring."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Docstring."
        assert my_func._pfix_decorated is True
        assert my_func._pfix_hint == "test hint"

    def test_bare_decorator(self):
        from pfix import pfix

        @pfix
        def identity(x):
            return x

        assert identity(42) == 42
        assert identity._pfix_decorated is True


# ── Fixer ───────────────────────────────────────────────────────────

class TestFixer:
    def test_validate_syntax(self):
        from pfix.fixer import _validate_syntax

        assert _validate_syntax("def foo(): return 1") is True
        assert _validate_syntax("def foo(: return") is False

    def test_make_diff(self):
        from pfix.fixer import _make_diff

        old = "line1\nline2\nline3\n"
        new = "line1\nline2_changed\nline3\n"
        diff = _make_diff(old, new, "test.py")
        assert "-line2" in diff
        assert "+line2_changed" in diff


# ── CLI ─────────────────────────────────────────────────────────────

class TestCLI:
    def test_version(self, capsys):
        from pfix.cli import main
        from pathlib import Path

        version = Path("VERSION").read_text().strip()
        ret = main(["version"])
        assert ret == 0
        assert version in capsys.readouterr().out

    def test_check_no_key(self, monkeypatch, tmp_path):
        from pfix.cli import main
        import pfix.config as config_module

        # Create empty .env in temp dir to avoid loading real .env
        empty_env = tmp_path / ".env"
        empty_env.write_text("")
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        
        # Reset and load from empty env
        reset_config()
        # Temporarily change cwd to avoid loading .env
        monkeypatch.chdir(tmp_path)
        config_module._config = None
        
        ret = main(["check"])
        assert ret == 1

    def test_run_missing_file(self):
        from pfix.cli import main

        ret = main(["run", "/nonexistent.py"])
        assert ret == 1
