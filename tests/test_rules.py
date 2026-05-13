from pfix.rules import ProjectRules


class TestRules:
    def test_load_nonexistent_rules(self, tmp_path) -> None:
        rules = ProjectRules(tmp_path / ".pfix" / "rules.md")
        assert not rules.has_rules()

    def test_load_rules(self, tmp_path) -> None:
        rules_file = tmp_path / ".pfix" / "rules.md"
        rules_file.parent.mkdir(parents=True)
        rules_file.write_text(
            "\n# Project Rules\n\n## Python Style\n- Always use type hints\n- Prefer pathlib over os.path\n\n## Dependencies\n- Use httpx instead of requests\n"
        )
        rules = ProjectRules(rules_file)
        assert rules.has_rules()
        assert len(rules.rules) == 3
        assert "Always use type hints" in rules.rules
