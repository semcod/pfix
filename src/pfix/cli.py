"""
pfix.cli — Command-line interface.

    pfix run script.py          # Run with global exception hook
    pfix run script.py --auto   # Auto-apply fixes
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

    # version
    sub.add_parser("version", help="Show version")

    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "check":
        return cmd_check()
    elif args.command == "deps":
        return cmd_deps(args)
    elif args.command == "server":
        return cmd_server(args)
    elif args.command == "version":
        from pfix import __version__
        console.print(f"pfix {__version__}")
        return 0
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

    original = sys.excepthook

    def hook(exc_type, exc_value, exc_tb):
        if exc_type in (KeyboardInterrupt, SystemExit):
            original(exc_type, exc_value, exc_tb)
            return

        console.print(f"\n[red]💥 pfix hook: {exc_type.__name__}: {exc_value}[/]")
        exc_value.__traceback__ = exc_tb
        ctx = analyze_exception(exc_value)
        proposal = request_fix(ctx)

        if proposal.confidence > 0.1:
            apply_fix(ctx, proposal, confirm=True)

        original(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


if __name__ == "__main__":
    sys.exit(main())
