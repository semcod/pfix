from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from rich.console import Console

console = Console()


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


def _install_excepthook():
    """Install global exception hook with pfix auto-fix."""
    from pfix.config import get_config
    config = get_config()
    hook = _create_excepthook(sys.excepthook, config)
    sys.excepthook = hook


def _create_excepthook(original_hook, config):
    """Create exception hook closure."""
    from pathlib import Path

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
        from pfix.analyzer import analyze_exception
        from pfix.llm import request_fix
        from pfix.fixer import apply_fix

        if exc_type in (KeyboardInterrupt, SystemExit):
            original_hook(exc_type, exc_value, exc_tb)
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

        original_hook(exc_type, exc_value, exc_tb)

    return hook
