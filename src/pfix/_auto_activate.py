"""
pfix Auto-Activation module.

This module contains the auto-activation logic that is triggered
via pfix_auto.pth during Python startup.
"""

import sys
import os
from pathlib import Path


def _auto_activate_pfix():
    """Auto-activate pfix if configured in pyproject.toml or .env."""
    try:
        from pfix.config import get_config
        config = get_config()

        if not _should_auto_activate(config):
            return

        # Auto-activate based on configuration
        if config.auto_apply or os.getenv('PFIX_AUTO_APPLY', '').lower() in ('true', '1', 'yes'):
            _install_hooks(config)

    except ImportError:
        pass  # pfix not installed, skip silently
    except Exception:
        pass  # Never break user code


def _should_auto_activate(config) -> bool:
    """Check if auto-activation should proceed."""
    if hasattr(config, 'enabled') and not config.enabled:
        return False

    if os.getenv('PFIX_DISABLE_AUTO', '').lower() in ('true', '1', 'yes'):
        return False

    project_root = Path.cwd()
    has_config = (
        (project_root / "pyproject.toml").exists() or
        any((p / ".env").exists() for p in [project_root] + list(project_root.parents))
    )
    return has_config


def _install_hooks(config):
    """Install core pfix hooks."""
    from pfix.session import install_pfix_hook
    install_pfix_hook(auto_apply=config.auto_apply)

    _install_syntax_error_handler()

    if os.getenv('PFIX_DEV_MODE', '').lower() == 'true':
        from pfix.dev_mode import install_dev_mode_hook
        install_dev_mode_hook()


def _install_syntax_error_handler():
    """Install import hook to catch SyntaxError during module loading."""
    try:
        def _pfix_import(name, *args, **kwargs):
            try:
                import builtins
                return builtins.__import__(name, *args, **kwargs)
            except SyntaxError as e:
                _handle_syntax_error(e)
                raise

        import builtins
        builtins.__import__ = _pfix_import

    except Exception:
        pass


def _handle_syntax_error(exc: SyntaxError):
    """Handle SyntaxError by calling pfix to fix it."""
    try:
        from pfix.config import get_config
        config = get_config()

        if not config.auto_apply:
            return

        from rich.console import Console
        console = Console(stderr=True)
        console.print(f"\n[red]💥 pfix: SyntaxError detected: {exc}[/]")

        ctx = _build_error_context(exc)
        _attempt_fix_and_restart(ctx, config, console)

    except Exception:
        pass


def _build_error_context(exc: SyntaxError) -> "ErrorContext":
    """Build ErrorContext from SyntaxError."""
    from pfix.types import ErrorContext
    ctx = ErrorContext(
        exception_type="SyntaxError",
        exception_message=str(exc),
        source_file=exc.filename or "",
        line_number=exc.lineno or 0,
        failing_line=exc.text or "",
        python_version=sys.version.split()[0]
    )

    if ctx.source_file:
        try:
            source_path = Path(ctx.source_file)
            if source_path.exists():
                ctx.source_code = source_path.read_text(encoding="utf-8")
        except Exception:
            pass
    return ctx


def _attempt_fix_and_restart(ctx: "ErrorContext", config, console: "Console"):
    """Attempt to apply LLM fix and restart if successful."""
    from pfix.llm import request_fix
    from pfix.fixer import apply_fix
    from pfix.session import _clear_pycache

    proposal = request_fix(ctx)
    if proposal.confidence > 0.1 and proposal.has_code_fix:
        console.print(f"[blue]🔍 Confidence OK ({proposal.confidence:.0%}), applying fix...[/]")
        if apply_fix(ctx, proposal, confirm=False):
            console.print(f"[green]✓ Fix applied to {ctx.source_file}[/]")
            if config.auto_restart and ctx.source_file:
                _clear_pycache(Path(ctx.source_file))
                console.print("[green]🔄 Restarting process...[/]")
                os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        console.print(f"[yellow]⚠ Confidence too low ({proposal.confidence:.0%}), skipping[/]")


_auto_activate_pfix()


# Execute immediately when module is loaded (during Python startup via .pth)
_auto_activate_pfix()
