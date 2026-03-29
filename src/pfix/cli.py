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
    parser = _build_parser()
    args = parser.parse_args(argv)
    return _dispatch(args)


def _build_parser() -> argparse.ArgumentParser:
    """Build and configure ArgumentParser for pfix CLI."""
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

    # diagnose
    diag_p = sub.add_parser("diagnose", help="Run environment diagnostics")
    diag_p.add_argument("--category", type=str, help="Filter by category (comma-separated)")
    diag_p.add_argument("--output", type=str, help="Output file for results")
    diag_p.add_argument("--fix", action="store_true", help="Auto-fix what can be fixed")
    diag_p.add_argument("--json", action="store_true", help="Output JSON format")
    diag_p.add_argument("--check", action="store_true", help="Exit with error if critical/error found")

    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """Dispatch to command handler based on parsed args."""
    from pfix.commands.run import cmd_run, cmd_dev
    from pfix.commands.config import cmd_check, cmd_status
    from pfix.commands.activation import cmd_enable, cmd_disable
    from pfix.commands.diagnose import cmd_diagnose
    from pfix.commands.others import (
        cmd_deps, cmd_server, cmd_rollback, cmd_audit, 
        cmd_init, cmd_dashboard, cmd_explain
    )

    commands: dict[str, Callable] = {
        "run": cmd_run,
        "dev": cmd_dev,
        "check": cmd_check,
        "enable": cmd_enable,
        "disable": cmd_disable,
        "deps": cmd_deps,
        "server": cmd_server,
        "status": cmd_status,
        "rollback": cmd_rollback,
        "audit": cmd_audit,
        "init": cmd_init,
        "dashboard": cmd_dashboard,
        "explain": cmd_explain,
        "diagnose": cmd_diagnose,
    }

    if args.command == "version":
        from pfix import __version__
        console.print(f"pfix {__version__}")
        return 0

    handler = commands.get(args.command)
    if handler:
        if args.command in ("enable", "disable", "init", "dashboard", "status"):
            return handler()  # No args
        return handler(args)

    _build_parser().print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
