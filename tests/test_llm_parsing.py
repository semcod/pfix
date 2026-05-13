"""Tests for LLM response parsing."""

from pfix.llm import FixProposal, _parse_response


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
