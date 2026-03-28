"""
pfix.rules — Load and apply custom project rules from .pfix/rules.md

Example .pfix/rules.md:
    # Project Rules
    
    ## Python Style
    - Always use `from __future__ import annotations`
    - Prefer `pathlib.Path` over `os.path`
    
    ## Dependencies  
    - Use `httpx` instead of `requests`
    
    ## Database
    - Database connections must use context managers
    
    ## Types
    - All functions must have type hints
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


DEFAULT_RULES_FILE = Path(".pfix/rules.md")


class ProjectRules:
    """Loaded project rules."""

    def __init__(self, rules_file: Optional[Path] = None):
        self.rules_file = rules_file or DEFAULT_RULES_FILE
        self.raw_content = ""
        self.sections: dict[str, list[str]] = {}
        self.rules: list[str] = []

        if self.rules_file.exists():
            self._load()

    def _load(self) -> None:
        """Load and parse rules file."""
        self.raw_content = self.rules_file.read_text(encoding="utf-8")

        # Parse markdown sections
        current_section = "general"
        current_rules: list[str] = []

        for line in self.raw_content.splitlines():
            line = line.strip()

            # Section headers
            if line.startswith("## "):
                if current_rules:
                    self.sections[current_section] = current_rules
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_rules = []

            # Rules (bullet points)
            elif line.startswith("- ") or line.startswith("* "):
                rule = line[2:].strip()
                if rule:
                    current_rules.append(rule)
                    self.rules.append(rule)

        # Save last section
        if current_rules:
            self.sections[current_section] = current_rules

    def get_rules_text(self) -> str:
        """Get formatted rules for LLM prompt."""
        if not self.rules:
            return ""

        parts = ["\n### Project-Specific Rules"]
        parts.append("The following rules must be followed when generating fixes:")
        parts.append("")

        for rule in self.rules:
            parts.append(f"- {rule}")

        return "\n".join(parts)

    def get_section(self, name: str) -> list[str]:
        """Get rules for a specific section."""
        key = name.lower().replace(" ", "_")
        return self.sections.get(key, [])

    def has_rules(self) -> bool:
        """Check if any rules are loaded."""
        return len(self.rules) > 0


def load_project_rules(path: Optional[Path] = None) -> ProjectRules:
    """Load project rules from file."""
    return ProjectRules(path)


def get_rules_for_prompt() -> str:
    """Get rules formatted for LLM prompt."""
    rules = load_project_rules()
    return rules.get_rules_text()
