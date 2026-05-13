"""Tests for pfix analyzer."""

from __future__ import annotations


from pfix.analyzer import ErrorContext, analyze_exception, classify_error, _extract_imports


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
