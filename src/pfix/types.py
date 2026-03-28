"""
pfix.types — Pure dataclasses for shared types.

This module contains only dataclass definitions with no imports from other pfix modules,
eliminating circular dependency issues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ErrorContext:
    """Structured error report for LLM consumption."""

    # Error
    exception_type: str = ""
    exception_message: str = ""
    traceback_text: str = ""

    # Source
    source_file: str = ""
    source_code: str = ""
    function_name: str = ""
    function_source: str = ""
    line_number: int = 0
    failing_line: str = ""

    # Environment
    local_vars: dict[str, str] = field(default_factory=dict)
    imports: list[str] = field(default_factory=list)
    python_version: str = ""

    # Project context
    project_deps: list[str] = field(default_factory=list)
    missing_deps: list[str] = field(default_factory=list)

    # Decorator metadata
    hints: dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        parts = [
            "## Error Report",
            f"**Exception**: `{self.exception_type}: {self.exception_message}`",
            f"**File**: `{self.source_file}` line {self.line_number}",
            f"**Function**: `{self.function_name}`",
            "",
            "### Traceback",
            f"```\n{self.traceback_text}\n```",
        ]

        if self.source_code:
            parts += ["", "### Full Source File", f"```python\n{self.source_code}\n```"]

        if self.function_source:
            parts += ["", "### Function Source", f"```python\n{self.function_source}\n```"]

        if self.local_vars:
            parts.append("\n### Local Variables")
            for k, v in list(self.local_vars.items())[:30]:
                parts.append(f"- `{k}` = `{v}`")

        if self.imports:
            parts.append("\n### File Imports")
            for imp in self.imports:
                parts.append(f"- `{imp}`")

        if self.missing_deps:
            parts.append("\n### Missing Dependencies (pipreqs scan)")
            for dep in self.missing_deps:
                parts.append(f"- `{dep}`")

        if self.hints:
            parts.append("\n### Developer Hints (@pfix decorator)")
            for k, v in self.hints.items():
                parts.append(f"- **{k}**: {v}")

        parts.append(f"\n### Python {self.python_version}")
        return "\n".join(parts)


@dataclass
class FixProposal:
    """Structured fix from LLM."""

    diagnosis: str = ""
    error_category: str = ""
    fix_description: str = ""
    fixed_function: str = ""
    fixed_file_content: str = ""
    dependencies: list[str] = field(default_factory=list)
    new_imports: list[str] = field(default_factory=list)
    confidence: float = 0.0
    breaking_changes: bool = False
    raw_response: str = ""

    @property
    def has_code_fix(self) -> bool:
        return bool(self.fixed_function or self.fixed_file_content)

    @property
    def has_dependency_fix(self) -> bool:
        return bool(self.dependencies)


@dataclass
class PfixConfig:
    """Runtime configuration for pfix."""

    # LLM settings
    llm_model: str = "openrouter/qwen/qwen3-coder-next"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None

    # Behavior
    auto_apply: bool = False
    auto_install_deps: bool = True
    auto_restart: bool = False
    confirm_fixes: bool = True
    create_backups: bool = True
    dry_run: bool = False
    max_retries: int = 3

    # Git integration
    git_auto_commit: bool = False
    git_commit_prefix: str = "fix: "

    # Package management
    pkg_manager: str = "pip"  # or "uv"

    # Extra context for prompts
    extra_context: Optional[dict[str, str]] = None

    # Decorators
    enabled: bool = True


@dataclass
class FixEvent:
    """Structured log event for each fix operation."""

    timestamp: str = ""
    exception_type: str = ""
    exception_message: str = ""
    source_file: str = ""
    function_name: str = ""
    error_category: str = ""
    diagnosis: str = ""
    fix_applied: bool = False
    confidence: float = 0.0
    duration_ms: int = 0
    llm_model: str = ""
    llm_tokens_used: int = 0
    dependencies_installed: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
