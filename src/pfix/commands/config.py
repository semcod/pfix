from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def cmd_check(args) -> int:
    from pfix.config import get_config

    config = get_config()
    warnings = config.validate()

    table = Table(title="pfix Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    rows = [
        ("Model", config.llm_model),
        ("API Key", "✓ set" if config.llm_api_key else "[red]✗ missing[/]"),
        ("API Base", config.llm_api_base),
        ("Pkg Manager", config.pkg_manager),
        ("Auto Apply", str(config.auto_apply)),
        ("Auto Install Deps", str(config.auto_install_deps)),
        ("Auto Restart", str(config.auto_restart)),
        ("Max Retries", str(config.max_retries)),
        ("Dry Run", str(config.dry_run)),
        ("Enabled", str(config.enabled)),
        ("MCP Enabled", str(config.mcp_enabled)),
        ("MCP Transport", config.mcp_transport),
        ("Git Auto-Commit", str(config.git_auto_commit)),
        ("Project Root", str(config.project_root)),
    ]
    for k, v in rows:
        table.add_row(k, v)

    console.print(table)

    if warnings:
        console.print()
        for w in warnings:
            console.print(f"[yellow]⚠ {w}[/]")
        return 1

    console.print("\n[green]✓ Configuration valid[/]")
    return 0


def cmd_status() -> int:
    """Show diagnostic status of pfix."""
    from pfix import __version__
    from pfix.config import get_config

    config = get_config()
    warnings = config.validate()

    # Header
    console.print(f"\n[bold cyan]pfix {__version__}[/bold cyan]")
    console.print("[dim]Self-healing Python — fix code & deps via LLM + MCP[/]\n")

    # Installation Status
    inst_table, pth_file = _get_installation_status_table(config)
    console.print(inst_table)

    # Configuration Status
    console.print()
    cfg_table = _get_config_table(config)
    console.print(cfg_table)

    # Warnings and issues
    if warnings:
        console.print()
        for w in warnings:
            console.print(f"[yellow]⚠ {w}[/]")

    return _print_status_summary(warnings, pth_file, config)


def _get_installation_status_table(config) -> tuple[Table, Path | None]:
    """Build the installation status table. Returns (table, pth_file)."""
    import site

    table = Table(title="Installation Status", show_header=False)
    table.add_column("Item", style="cyan")
    table.add_column("Status")

    # Check if pfix is importable
    table.add_row("pfix package", "[green]✓ installed[/]")

    # Check auto-activation .pth file
    site_packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not site_packages:
        site_packages = Path(site.getusersitepackages()) if site.getusersitepackages() else None

    pth_file = site_packages / "pfix_auto.pth" if site_packages else None
    if pth_file and pth_file.exists():
        table.add_row("Auto-activation", f"[green]✓ enabled[/] ([dim]{pth_file}[/dim])")
    else:
        table.add_row("Auto-activation", "[yellow]⚠ disabled[/] ([dim]run: pfix enable[/dim])")

    # Check pyproject.toml
    pyproject = Path.cwd() / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        if "[tool.pfix]" in content:
            table.add_row("Configuration", f"[green]✓ found[/] ([dim]{pyproject}[/dim])")
        else:
            table.add_row("Configuration", f"[yellow]⚠ missing [tool.pfix] section[/] ([dim]{pyproject}[/dim])")
    else:
        table.add_row("Configuration", "[yellow]⚠ no pyproject.toml[/]")

    # Check .env file
    env_file = None
    for parent in [Path.cwd(), *Path.cwd().parents]:
        e = parent / ".env"
        if e.exists():
            env_file = e
            break
    if env_file:
        table.add_row("Environment", f"[green]✓ .env found[/] ([dim]{env_file}[/dim])")
    else:
        table.add_row("Environment", "[yellow]⚠ no .env file[/]")

    return table, pth_file


def _get_config_table(config) -> Table:
    """Build the configuration status table."""
    table = Table(title="Configuration", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Model", config.llm_model)
    table.add_row("API Key", "[green]✓ set[/]" if config.llm_api_key else "[red]✗ missing[/]")
    table.add_row("API Base", config.llm_api_base)
    table.add_row("Pkg Manager", config.pkg_manager)
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Working Directory", str(Path.cwd()))

    return table


def _print_status_summary(warnings: list, pth_file: Path | None, config) -> int:
    """Print status summary and return exit code."""
    console.print()
    if not warnings and (pth_file and pth_file.exists()):
        console.print("[green]✓ pfix is properly configured and ready[/]")
    elif not config.llm_api_key:
        console.print("[yellow]⚠ pfix requires an API key to function[/]")
        console.print("[dim]  Set OPENROUTER_API_KEY in .env or environment[/]")
    else:
        console.print("[green]✓ pfix is functional[/]")
        if not (pth_file and pth_file.exists()):
            console.print("[dim]  (run 'pfix enable' for auto-activation)[/]")

    console.print()
    return 0 if not warnings else 1
