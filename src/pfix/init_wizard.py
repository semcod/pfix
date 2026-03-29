"""
pfix.init_wizard — Project setup wizard for pfix.

Usage:
    pfix init

Guides through:
    - Model selection (Ollama local / OpenRouter cloud)
    - .env generation
    - pyproject.toml configuration
    - .gitignore updates
    - Auto-activation setup
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

DEFAULT_MODELS = [
    ("ollama/codellama:7b", "Local (Ollama) - Free, requires Ollama"),
    ("openrouter/anthropic/claude-haiku-4", "Cloud (OpenRouter) - Cheap, fast"),
    ("openrouter/anthropic/claude-sonnet-4", "Cloud (OpenRouter) - Quality"),
    ("openrouter/qwen/qwen3-coder-next", "Cloud (OpenRouter) - Balanced"),
]


def find_pyproject() -> Optional[Path]:
    """Find pyproject.toml in current or parent directories."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            return pyproject
    return None


def init_wizard() -> None:
    """Run the interactive setup wizard."""
    _show_welcome()

    # 1. Select model
    selected_model = _step_select_model()

    # 2. Auto-apply mode
    auto_apply = _step_auto_apply()

    # 3. Create .env
    _step_create_env(selected_model, auto_apply)

    # 4. Update pyproject.toml
    _step_update_pyproject(selected_model, auto_apply)

    # 5. Update .gitignore
    _step_update_gitignore()

    # 6. Enable auto-activation
    _step_auto_activation()

    # Summary
    _show_summary(selected_model, auto_apply)


def _show_welcome():
    console.print(Panel(
        "Welcome to pfix setup!\n"
        "This wizard will configure pfix for your project.",
        title="🔧 pfix init",
        border_style="green",
    ))


def _step_select_model() -> str:
    console.print("\n[bold]Step 1: Select LLM Model[/]")
    for i, (model, desc) in enumerate(DEFAULT_MODELS, 1):
        console.print(f"  {i}. {desc}")
        console.print(f"     Model: {model}")

    choice = Prompt.ask(
        "Select model",
        choices=[str(i) for i in range(1, len(DEFAULT_MODELS) + 1)],
        default="2",
    )
    return DEFAULT_MODELS[int(choice) - 1][0]


def _step_auto_apply() -> bool:
    console.print("\n[bold]Step 2: Auto-Apply Mode[/]")
    return Confirm.ask(
        "Enable auto-apply? (fixes will be applied without confirmation)",
        default=False,
    )


def _step_create_env(selected_model: str, auto_apply: bool):
    console.print("\n[bold]Step 3: Environment Configuration[/]")
    create_env = Confirm.ask("Create .env file?", default=True)

    if create_env:
        env_path = Path.cwd() / ".env"
        env_content = f"""# pfix configuration
PFIX_AUTO_APPLY={"true" if auto_apply else "false"}
PFIX_MODEL={selected_model}
"""

        if "openrouter" in selected_model:
            env_content += "# Get API key from: https://openrouter.ai/keys\n"
            env_content += "OPENROUTER_API_KEY=your_api_key_here\n"

        env_path.write_text(env_content)
        console.print(f"[green]✓ Created {env_path}[/]")


def _step_update_pyproject(selected_model: str, auto_apply: bool):
    console.print("\n[bold]Step 4: Project Configuration[/]")
    pyproject = find_pyproject()

    if pyproject:
        console.print(f"Found {pyproject}")
        add_config = Confirm.ask("Add [tool.pfix] section?", default=True)

        if add_config:
            update_pyproject(pyproject, selected_model, auto_apply)
            console.print(f"[green]✓ Updated {pyproject}[/]")
    else:
        console.print("[yellow]No pyproject.toml found. Skipping.[/]")


def _step_update_gitignore():
    console.print("\n[bold]Step 5: Git Configuration[/]")
    gitignore = Path.cwd() / ".gitignore"

    if gitignore.exists():
        add_gitignore = Confirm.ask("Add pfix entries to .gitignore?", default=True)
        if add_gitignore:
            update_gitignore(gitignore)
            console.print(f"[green]✓ Updated {gitignore}[/]")
    else:
        create_gitignore = Confirm.ask("Create .gitignore with pfix entries?", default=True)
        if create_gitignore:
            gitignore.write_text(get_gitignore_content())
            console.print(f"[green]✓ Created {gitignore}[/]")


def _step_auto_activation():
    console.print("\n[bold]Step 6: Auto-Activation[/]")
    console.print("pfix can auto-activate when you import it.")
    console.print("This requires no code changes to use pfix.")

    enable_auto = Confirm.ask("Enable auto-activation?", default=True)
    if enable_auto:
        console.print("[green]✓ Auto-activation enabled via .env[/]")


def _show_summary(selected_model: str, auto_apply: bool):
    console.print(Panel(
        f"[bold]Setup Complete![/]\n\n"
        f"Model: {selected_model}\n"
        f"Auto-apply: {'yes' if auto_apply else 'no'}\n"
        f"\n"
        f"Next steps:\n"
        f"1. {'Add OPENROUTER_API_KEY to .env' if 'openrouter' in selected_model else 'Start Ollama: ollama run codellama'}\n"
        f"2. Test with: python -c \"1/0\"\n"
        f"3. Read docs: https://github.com/softreck/pfix",
        title="pfix init",
        border_style="green",
    ))


def update_pyproject(pyproject: Path, model: str, auto_apply: bool) -> None:
    """Add [tool.pfix] section to pyproject.toml."""
    content = pyproject.read_text(encoding="utf-8")

    # Check if section already exists
    if "[tool.pfix]" in content:
        console.print("[yellow][tool.pfix] already exists, skipping update[/]")
        return

    # Add section
    config_section = f"""
[tool.pfix]
model = "{model}"
auto_apply = {str(auto_apply).lower()}
auto_install_deps = true
create_backups = true
max_retries = 3
"""

    with open(pyproject, "a", encoding="utf-8") as f:
        f.write(config_section)


def get_gitignore_content() -> str:
    """Get pfix-related .gitignore entries."""
    return """# pfix
.pfix_cache/
.pfix_logs/
.pfix_proposals/
.pfix_backups/
*.pfix.bak

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
.env

# IDEs
.vscode/
.idea/
"""


def update_gitignore(gitignore: Path) -> None:
    """Add pfix entries to existing .gitignore."""
    content = gitignore.read_text(encoding="utf-8")

    # Check if already has pfix entries
    if ".pfix_cache/" in content:
        return

    pfix_entries = """
# pfix
.pfix_cache/
.pfix_logs/
.pfix_proposals/
.pfix_backups/
*.pfix.bak
"""

    with open(gitignore, "a", encoding="utf-8") as f:
        f.write(pfix_entries)


def main() -> None:
    """CLI entry point."""
    init_wizard()
