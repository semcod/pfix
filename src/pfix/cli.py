"""
pfix.cli — Command-line interface.

    pfix run script.py          # Run with global exception hook
    pfix run script.py --auto   # Auto-apply fixes
    pfix dev script.py          # Run with dependency dev mode (fix site-packages)
    pfix check                  # Validate config
    pfix deps scan              # Scan for missing deps (pipreqs)
    pfix deps install           # Install missing deps
    pfix deps generate          # Generate requirements.txt
    pfix server                 # Start MCP server (stdio)
    pfix server --http 3001     # Start MCP server (HTTP)
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pfix", description="Self-healing Python — fix code & deps via LLM + MCP")
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run a script with pfix active")
    run_p.add_argument("script", help="Python script path")
    run_p.add_argument("args", nargs="*")
    run_p.add_argument("--auto", action="store_true", help="Auto-apply fixes")
    run_p.add_argument("--dry-run", action="store_true")
    run_p.add_argument("--restart", action="store_true", help="Restart process after fix")

    # dev (dependency development mode)
    dev_p = sub.add_parser("dev", help="Run with dependency development mode (fixes site-packages)")
    dev_p.add_argument("script", help="Python script path")
    dev_p.add_argument("args", nargs="*")
    dev_p.add_argument("--auto", action="store_true", help="Auto-apply fixes")
    dev_p.add_argument("--dry-run", action="store_true")

    # check
    sub.add_parser("check", help="Validate config")

    # deps
    deps_p = sub.add_parser("deps", help="Dependency management")
    deps_sub = deps_p.add_subparsers(dest="deps_command")
    deps_sub.add_parser("scan", help="Scan for missing deps (pipreqs)")
    deps_sub.add_parser("install", help="Install missing deps")
    deps_sub.add_parser("generate", help="Generate requirements.txt")

    # server
    srv_p = sub.add_parser("server", help="Start MCP server")
    srv_p.add_argument("--http", type=int, default=None, metavar="PORT", help="HTTP port (default: stdio)")
    srv_p.add_argument("--host", default="127.0.0.1")

    # enable (auto-activation setup)
    sub.add_parser("enable", help="Enable pfix auto-activation and add config to pyproject.toml")
    
    # disable (remove auto-activation)
    sub.add_parser("disable", help="Disable pfix auto-activation")

    # rollback
    rollback_p = sub.add_parser("rollback", help="Rollback fixes")
    rollback_p.add_argument("--last", action="store_true", help="Rollback most recent fix")
    rollback_p.add_argument("--file", type=str, help="Rollback fixes for specific file")
    rollback_p.add_argument("--before", type=str, help="Rollback all fixes before date (YYYY-MM-DD)")
    rollback_p.add_argument("--history", action="store_true", help="Show fix history")

    # audit
    audit_p = sub.add_parser("audit", help="Audit trail and compliance")
    audit_p.add_argument("--report", action="store_true", help="Show audit report")
    audit_p.add_argument("--days", type=int, default=7, help="Report period in days")

    # init
    sub.add_parser("init", help="Interactive setup wizard")

    # dashboard
    sub.add_parser("dashboard", help="TUI dashboard with statistics")

    # explain
    explain_p = sub.add_parser("explain", help="Explain errors and fixes (educational)")
    explain_p.add_argument("what", nargs="?", default="last", help="'last' or exception type (e.g., TypeError)")
    explain_p.add_argument("--file", type=str, help="Explain specific file:line")

    # version
    sub.add_parser("version", help="Show version")

    # status
    sub.add_parser("status", help="Show diagnostic status")

    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "dev":
        return cmd_dev(args)
    elif args.command == "check":
        return cmd_check()
    elif args.command == "enable":
        return cmd_enable()
    elif args.command == "disable":
        return cmd_disable()
    elif args.command == "deps":
        return cmd_deps(args)
    elif args.command == "server":
        return cmd_server(args)
    elif args.command == "version":
        from pfix import __version__
        console.print(f"pfix {__version__}")
        return 0
    elif args.command == "status":
        return cmd_status()
    elif args.command == "rollback":
        return cmd_rollback(args)
    elif args.command == "audit":
        return cmd_audit(args)
    elif args.command == "init":
        return cmd_init()
    elif args.command == "dashboard":
        return cmd_dashboard()
    elif args.command == "explain":
        return cmd_explain(args)
    else:
        parser.print_help()
        return 0


def cmd_run(args) -> int:
    from pfix import configure

    script = Path(args.script).resolve()
    if not script.is_file():
        console.print(f"[red]✗ Not found: {script}[/]")
        return 1

    configure(
        auto_apply=args.auto,
        dry_run=args.dry_run,
        auto_restart=args.restart,
        project_root=script.parent,
    )
    _install_excepthook()

    sys.argv = [str(script)] + (args.args or [])
    spec = importlib.util.spec_from_file_location("__main__", str(script))
    if spec is None or spec.loader is None:
        console.print(f"[red]✗ Cannot load: {script}[/]")
        return 1

    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module
    try:
        spec.loader.exec_module(module)
    except SyntaxError as e:
        # Handle SyntaxError with pfix
        from pfix.syntax_error_handler import handle_syntax_error
        handle_syntax_error(e, auto_apply=args.auto)
        return 1
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        console.print(f"[red]💥 Unhandled: {type(e).__name__}: {e}[/]")
        return 1
    return 0


def cmd_dev(args) -> int:
    """Run with dependency development mode active."""
    from pfix import configure
    from pfix.dev_mode import install_dev_mode_hook

    script = Path(args.script).resolve()
    if not script.is_file():
        console.print(f"[red]✗ Not found: {script}[/]")
        return 1

    configure(
        auto_apply=True,  # Dev mode always auto-applies
        dry_run=args.dry_run,
        auto_restart=False,  # Don't restart in dev mode
        project_root=script.parent,
    )

    console.print("[cyan]🛠️  Development mode active - will fix site-packages errors[/]")
    console.print("[dim]   Any errors in pandas/numpy/etc will be auto-fixed[/]")
    console.print()

    # Install dev mode hook
    install_dev_mode_hook()

    sys.argv = [str(script)] + (args.args or [])
    spec = importlib.util.spec_from_file_location("__main__", str(script))
    if spec is None or spec.loader is None:
        console.print(f"[red]✗ Cannot load: {script}[/]")
        return 1

    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module
    try:
        spec.loader.exec_module(module)
    except SyntaxError as e:
        # Handle SyntaxError with pfix
        from pfix.syntax_error_handler import handle_syntax_error
        handle_syntax_error(e, auto_apply=args.auto)
        return 1
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        console.print(f"[red]💥 Unhandled: {type(e).__name__}: {e}[/]")
        return 1
    return 0


def cmd_check() -> int:
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


def cmd_enable() -> int:
    """Enable pfix auto-activation and add config to pyproject.toml."""
    import shutil
    import site

    # Find pfix package location
    import pfix
    pfix_pkg = Path(pfix.__file__).parent

    # Find site-packages directory
    site_packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not site_packages:
        site_packages = Path(site.getusersitepackages())

    if not site_packages or not site_packages.exists():
        console.print("[red]✗ Cannot find site-packages directory[/]")
        return 1

    # Install .pth file for auto-activation
    source_file = pfix_pkg / "auto_activate.pth"
    dest_file = site_packages / "pfix_auto.pth"

    if source_file.exists():
        try:
            shutil.copy2(source_file, dest_file)
            console.print(f"[green]✓ pfix auto-activation enabled[/]")
            console.print(f"[dim]  Installed: {dest_file}[/]")
        except Exception as e:
            console.print(f"[red]✗ Failed to install .pth file: {e}[/]")
            return 1
    else:
        console.print(f"[yellow]⚠ Source file not found: {source_file}[/]")
    
    # 2. Add config to pyproject.toml if it exists
    pyproject = Path.cwd() / "pyproject.toml"
    config_added = False
    
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.pfix]" not in content:
                # Append config to existing pyproject.toml
                config_block = '''\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'''
                with open(pyproject, "a") as f:
                    f.write(config_block)
                console.print(f"[green]✓ Added [tool.pfix] to {pyproject}[/]")
                config_added = True
            else:
                console.print(f"[dim]  [tool.pfix] already exists in {pyproject}[/]")
        except Exception as e:
            console.print(f"[yellow]⚠ Could not update {pyproject}: {e}[/]")
    else:
        # Create new pyproject.toml
        try:
            config_block = '''[build-system]\nrequires = ["setuptools>=61"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "my-project"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'''
            pyproject.write_text(config_block)
            console.print(f"[green]✓ Created {pyproject} with pfix config[/]")
            config_added = True
        except Exception as e:
            console.print(f"[yellow]⚠ Could not create {pyproject}: {e}[/]")
    
    # Summary
    console.print()
    console.print("[cyan]✓ pfix is now enabled![/]")
    console.print()
    if config_added:
        console.print("[dim]Configuration added to pyproject.toml.[/]")
        console.print("[dim]Add your API key:[/]")
        console.print('  echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env')
    else:
        console.print("[dim]Edit pyproject.toml to customize settings.[/]")
    console.print()
    console.print("[dim]Run: python your_script.py (no import needed!)[/]")
    console.print()
    console.print("[dim]To disable: pfix disable[/]")
    return 0


def cmd_disable() -> int:
    """Disable pfix auto-activation."""
    import site

    # Find site-packages directory
    site_packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not site_packages:
        site_packages = Path(site.getusersitepackages())

    if not site_packages or not site_packages.exists():
        console.print("[red]✗ Cannot find site-packages directory[/]")
        return 1

    # Remove .pth file
    dest_file = site_packages / "pfix_auto.pth"

    if dest_file.exists():
        try:
            dest_file.unlink()
            console.print(f"[green]✓ pfix auto-activation disabled[/]")
            console.print(f"[dim]  Removed: {dest_file}[/]")
            console.print()
            console.print("[dim]pfix will no longer auto-activate.[/]")
            console.print("[dim]To re-enable: pfix enable[/]")
            return 0
        except Exception as e:
            console.print(f"[red]✗ Failed to disable: {e}[/]")
            return 1
    else:
        console.print("[yellow]⚠ pfix auto-activation was not enabled[/]")
        return 0


def cmd_status() -> int:
    """Show diagnostic status of pfix."""
    from pfix import __version__
    from pfix.config import get_config
    import site
    import sys

    config = get_config()
    warnings = config.validate()

    # Header
    console.print(f"\n[bold cyan]pfix {__version__}[/bold cyan]")
    console.print("[dim]Self-healing Python — fix code & deps via LLM + MCP[/]\n")

    # Installation Status
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

    console.print(table)

    # Configuration Status
    console.print()
    cfg_table = Table(title="Configuration", show_header=False)
    cfg_table.add_column("Setting", style="cyan")
    cfg_table.add_column("Value")

    cfg_table.add_row("Model", config.llm_model)
    cfg_table.add_row("API Key", "[green]✓ set[/]" if config.llm_api_key else "[red]✗ missing[/]")
    cfg_table.add_row("API Base", config.llm_api_base)
    cfg_table.add_row("Pkg Manager", config.pkg_manager)
    cfg_table.add_row("Python", sys.version.split()[0])
    cfg_table.add_row("Working Directory", str(Path.cwd()))

    console.print(cfg_table)

    # Warnings and issues
    if warnings:
        console.print()
        for w in warnings:
            console.print(f"[yellow]⚠ {w}[/]")

    # Summary
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


def cmd_deps(args) -> int:
    if not hasattr(args, "deps_command") or args.deps_command is None:
        console.print("Usage: pfix deps [scan|install|generate]")
        return 1

    from pfix.dependency import scan_project_deps, install_packages, generate_requirements

    if args.deps_command == "generate":
        generate_requirements()
        return 0

    result = scan_project_deps()

    if not result["missing"]:
        console.print(f"[green]✓ All dependencies satisfied ({len(result['installed'])} packages)[/]")
        return 0

    table = Table(title=f"Missing Dependencies ({len(result['missing'])})")
    table.add_column("Package", style="yellow")
    for pkg in result["missing"]:
        table.add_row(pkg)
    console.print(table)

    if args.deps_command == "install":
        install_packages(result["missing"])

    return 0


def cmd_server(args) -> int:
    try:
        from pfix.mcp_server import start_server

        if args.http:
            start_server(transport="http", host=args.host, port=args.http)
        else:
            start_server(transport="stdio")
        return 0
    except ImportError as e:
        console.print(f"[red]MCP server requires: pip install pfix[mcp][/]\n{e}")
        return 1


def _install_excepthook():
    from pfix.analyzer import analyze_exception
    from pfix.llm import request_fix
    from pfix.fixer import apply_fix
    from pfix.config import get_config
    from pathlib import Path

    original = sys.excepthook
    config = get_config()

    def _clear_pycache(source_file: Path):
        """Clear __pycache__ entries for a source file to prevent stale bytecode."""
        try:
            pycache_dir = source_file.parent / "__pycache__"
            if pycache_dir.exists():
                stem = source_file.stem
                for pyc_file in pycache_dir.glob(f"{stem}.*.pyc"):
                    try:
                        pyc_file.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

    def hook(exc_type, exc_value, exc_tb):
        if exc_type in (KeyboardInterrupt, SystemExit):
            original(exc_type, exc_value, exc_tb)
            return

        console.print(f"\n[red]💥 pfix hook: {exc_type.__name__}: {exc_value}[/]")
        exc_value.__traceback__ = exc_tb
        ctx = analyze_exception(exc_value)
        proposal = request_fix(ctx)

        if proposal.confidence > 0.1:
            fixed = apply_fix(ctx, proposal, confirm=True)
            
            # Restart process if fix applied and auto_restart enabled
            if fixed and config.auto_restart:
                if ctx.source_file:
                    _clear_pycache(Path(ctx.source_file))
                console.print("[green]🔄 Restarting...[/]")
                os.execv(sys.executable, [sys.executable] + sys.argv)

        original(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


if __name__ == "__main__":
    sys.exit(main())
