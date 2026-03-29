from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_diagnose(args) -> int:
    """Run environment diagnostics."""
    from pfix.env_diagnostics import EnvDiagnostics

    # Parse categories filter
    categories = None
    if args.category:
        categories = [c.strip() for c in args.category.split(",")]

    # Run diagnostics
    diag = EnvDiagnostics()
    results = diag.check_all(categories=categories)

    # Output format
    output = _format_diagnostic_results(results, diag, args.json)

    # Output to file or console
    _output_diagnostic_results(output, args.output)

    # Auto-fix if requested
    if args.fix:
        _apply_diagnostic_fixes(results, diag.project_root)

    # Determine exit code
    return _get_diagnose_exit_code(results, args.check)


def _format_diagnostic_results(results, diag, json_output: bool) -> str:
    """Format diagnostic results for output (JSON or text)."""
    if json_output:
        import json
        return json.dumps([
            {
                "category": r.category,
                "check_name": r.check_name,
                "status": r.status,
                "message": r.message,
                "details": r.details,
                "suggestion": r.suggestion,
                "auto_fixable": r.auto_fixable,
                "abs_path": r.abs_path,
                "line_number": r.line_number,
            }
            for r in results
        ], indent=2)
    else:
        return diag.generate_report(results)


def _output_diagnostic_results(output: str, output_path: str | None) -> None:
    """Output results to file or console."""
    if output_path:
        Path(output_path).write_text(output)
        console.print(f"[green]✓ Report written to {output_path}[/]")
    else:
        console.print(output)


def _apply_diagnostic_fixes(results, project_root) -> tuple[int, int]:
    """Apply auto-fixes to diagnostic results. Returns (fixed_count, failed_count)."""
    from ..env_diagnostics.auto_fix import can_auto_fix, apply_auto_fix

    fixable = [r for r in results if can_auto_fix(r)]
    if not fixable:
        console.print("\n[dim]No auto-fixable issues found[/]")
        return 0, 0

    console.print(f"\n[cyan]🔧 Attempting to fix {len(fixable)} issues...[/]")
    fixed = 0
    failed = 0

    for r in fixable:
        success, msg = apply_auto_fix(r, project_root)
        if success:
            console.print(f"  [green]✓[/] [{r.category}/{r.check_name}] {msg}")
            fixed += 1
        else:
            console.print(f"  [yellow]⚠[/] [{r.category}/{r.check_name}] {msg}")
            failed += 1

    console.print(f"\n[green]Fixed: {fixed}[/] | [yellow]Failed: {failed}[/]")
    return fixed, failed


def _get_diagnose_exit_code(results, check_mode: bool) -> int:
    """Determine exit code based on results and check mode."""
    if check_mode:
        critical_errors = [r for r in results if r.status in ("critical", "error")]
        if critical_errors:
            return 1
    return 0
