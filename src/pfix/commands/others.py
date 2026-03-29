from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


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


def cmd_rollback(args) -> int:
    from pfix.rollback import rollback_command, show_history
    if args.history:
        show_history()
        return 0
    success = rollback_command(
        last=args.last,
        filepath=args.file,
        before=args.before,
    )
    return 0 if success else 1


def cmd_audit(args) -> int:
    from pfix.audit import print_audit_report, read_audit_log
    if args.report:
        print_audit_report(days=args.days)
    else:
        entries = read_audit_log(limit=10)
        if not entries:
            console.print("[yellow]No audit entries found[/]")
            return 0
        console.print(f"[bold]Recent Audit Entries ({len(entries)} shown):[/]")
        for e in entries:
            status = "[green]✓[/]" if e.fix_applied else "[red]✗[/]"
            console.print(f"{status} {e.timestamp[:16]} {e.file.split('/')[-1]} - {e.error_type}")
    return 0


def cmd_init(args=None) -> int:
    from pfix.init_wizard import init_wizard
    init_wizard()
    return 0


def cmd_dashboard(args=None) -> int:
    from pfix.dashboard import run_dashboard
    run_dashboard()
    return 0


def cmd_explain(args) -> int:
    from pfix.explain import explain
    explain(what=args.what, file=args.file)
    return 0
