"""
pfix.fixer — Apply code fixes: diff, backup, validate, git commit.
"""

from __future__ import annotations

import ast
import difflib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .analyzer import ErrorContext
from .config import get_config
from .dependency import install_packages, update_requirements_file
from .llm import FixProposal

console = Console(stderr=True)


def apply_fix(
    ctx: ErrorContext,
    proposal: FixProposal,
    confirm: bool = True,
) -> bool:
    """Apply a FixProposal. Returns True if anything was applied."""
    config = get_config()
    applied_any = False

    # 1. Dependencies
    if proposal.has_dependency_fix:
        console.print(
            Panel(
                "\n".join(f"  {config.pkg_manager} install {d}" for d in proposal.dependencies),
                title="[cyan]📦 Dependencies[/]",
                border_style="cyan",
            )
        )
        if not config.dry_run:
            results = install_packages(proposal.dependencies)
            if any(results.values()):
                applied_any = True
                update_requirements_file(proposal.dependencies)

    # 2. Code fix
    if proposal.has_code_fix:
        source_file = Path(ctx.source_file)
        if not source_file.is_file():
            console.print(f"[red]✗ File not found: {source_file}[/]")
            return applied_any

        original = source_file.read_text(encoding="utf-8")

        if proposal.fixed_file_content:
            new_content = proposal.fixed_file_content
        elif proposal.fixed_function:
            new_content = _replace_function(original, ctx.function_name, proposal.fixed_function)
            if new_content is None:
                console.print("[yellow]⚠ Could not locate function — skipping[/]")
                return applied_any
        else:
            return applied_any

        # Diff
        diff = _make_diff(original, new_content, str(source_file))
        if not diff.strip():
            console.print("[yellow]⚠ No changes in fix[/]")
            return applied_any

        console.print(
            Panel(
                Syntax(diff, "diff", theme="monokai"),
                title=f"[green]🔧 {proposal.fix_description}[/]",
                subtitle=f"confidence: {proposal.confidence:.0%}",
                border_style="green",
            )
        )

        if config.dry_run:
            console.print("[dim]  DRY RUN — not applying[/]")
            return applied_any

        # Confirm
        should_apply = config.auto_apply
        if not should_apply and confirm:
            try:
                answer = input("\n  Apply this fix? [y/N] ").strip().lower()
                should_apply = answer in ("y", "yes")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]  Skipped[/]")
                return applied_any

        if should_apply:
            if not _validate_syntax(new_content):
                console.print("[red]✗ Fixed code has syntax errors — aborting[/]")
                return applied_any

            backup = _backup(source_file)
            console.print(f"[dim]  Backup: {backup}[/]")

            source_file.write_text(new_content, encoding="utf-8")
            console.print(f"[green]✓ Fix applied to {source_file}[/]")
            applied_any = True

            # Git auto-commit
            if config.git_auto_commit:
                _git_commit(source_file, proposal.fix_description)
        else:
            console.print("[yellow]  Fix skipped[/]")

    # 3. Diagnosis
    if proposal.diagnosis:
        console.print(
            Panel(proposal.diagnosis, title="[blue]🔍 Diagnosis[/]", border_style="blue")
        )

    return applied_any


def _replace_function(source: str, func_name: str, new_func: str) -> Optional[str]:
    """Replace a function definition in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    simple_name = func_name.split(".")[-1]
    lines = source.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == simple_name:
                start = node.lineno - 1
                end = node.end_lineno

                indent = len(lines[start]) - len(lines[start].lstrip())
                indent_str = " " * indent

                new_lines = new_func.splitlines(keepends=True)
                if new_lines:
                    first_indent = len(new_lines[0]) - len(new_lines[0].lstrip())
                    reindented = []
                    for line in new_lines:
                        if line.strip():
                            rel = len(line) - len(line.lstrip()) - first_indent
                            reindented.append(indent_str + " " * max(0, rel) + line.lstrip())
                        else:
                            reindented.append("\n")

                    result = lines[:start] + reindented
                    if end is not None and end < len(lines):
                        result += lines[end:]
                    return "".join(result)
    return None


def _make_diff(old: str, new: str, filename: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))


def _validate_syntax(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _backup(filepath: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = filepath.parent / ".pfix_backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f"{filepath.name}.{ts}.bak"
    shutil.copy2(filepath, backup)
    return backup


def _git_commit(filepath: Path, message: str):
    """Auto-commit the fix via git."""
    config = get_config()
    try:
        import git
        repo = git.Repo(filepath.parent, search_parent_directories=True)
        repo.index.add([str(filepath)])
        repo.index.commit(f"{config.git_commit_prefix}{message}")
        console.print(f"[green]  📝 Git commit: {config.git_commit_prefix}{message}[/]")
    except ImportError:
        console.print("[dim]  git commit skipped (install gitpython)[/]")
    except Exception as e:
        console.print(f"[yellow]  git commit failed: {e}[/]")
