import pytest
from pfix.rules import ProjectRules

class TestRules:
    def test_load_nonexistent_rules(self, tmp_path):
        rules = ProjectRules(tmp_path / ".pfix" / "rules.md")
        assert not rules.has_rules()
    
    def test_load_rules(self, tmp_path):
        rules_file = tmp_path / ".pfix" / "rules.md"
        rules_file.parent.mkdir(parents=True)
        rules_file.write_text("""
# Project Rules

## Python Style
- Always use type hints
- Prefer pathlib over os.path

## Dependencies
- Use httpx instead of requests
""")
        rules = ProjectRules(rules_file)
        assert rules.has_rules()
        assert len(rules.rules) == 3
        assert "Always use type hints" in rules.rules
