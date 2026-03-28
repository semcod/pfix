"""
pfix.session — File-level auto-healing execution wrapper.

Usage:
    from pfix import pfix_session, configure
    
    configure(auto_apply=True)
    
    # Run code with auto-healing
    pfix_session(__file__, lambda: main())
    
    # Or with context manager (catches exceptions within block)
    with pfix_session(__file__) as session:
        main()  # Any exception triggers auto-fix

Or as a decorator:
    from pfix import auto_pfix
    
    @auto_pfix(auto_apply=True)
    def main():
        # All code here is protected
        buggy()  # Auto-fixed on error
"""

from __future__ import annotations

import functools
import inspect
import os
import sys
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Optional, TypeVar

from rich.console import Console

from .analyzer import analyze_exception, classify_error
from .config import get_config
from .dependency import detect_missing_from_error, install_packages, resolve_package_name
from .fixer import apply_fix
from .llm import request_fix

console = Console(stderr=True)
F = TypeVar("F", bound=Callable)


class PFixSession:
    """Session context that catches and auto-fixes exceptions."""
    
    def __init__(
        self,
        target_file: Optional[str] = None,
        *,
        auto_apply: Optional[bool] = None,
        retries: Optional[int] = None,
        restart: Optional[bool] = None,
    ):
        self.config = get_config()
        
        if target_file is None:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_module = frame.f_back.f_globals.get('__file__')
                target_file = caller_module
        
        self.target_file = Path(target_file).resolve() if target_file else None
        self.max_retries = retries if retries is not None else self.config.max_retries
        self.auto_apply = auto_apply if auto_apply is not None else self.config.auto_apply
        self.restart = restart if restart is not None else self.config.auto_restart
    
    def __enter__(self) -> "PFixSession":
        return self
    
    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Handle exception if one occurred. Returns True if handled."""
        if exc_type and exc_val and exc_tb:
            return self._handle_exception(exc_type, exc_val, exc_tb)
        return False
    
    def __call__(self, func: Callable[[], Any]) -> Any:
        """Run function with exception handling."""
        with self:
            return func()
    
    def _handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Handle exception — analyze and fix. Returns True if fixed."""
        if exc_type in (KeyboardInterrupt, SystemExit):
            return False
            
        console.print(f"\n[red]💥 pfix caught: {exc_type.__name__}: {exc_value}[/]")
        
        if exc_tb:
            exc_value.__traceback__ = exc_tb
        
        # Quick dep fix
        if isinstance(exc_value, (ModuleNotFoundError, ImportError)):
            module = detect_missing_from_error(str(exc_value))
            if module:
                pkg = resolve_package_name(module)
                console.print(f"[cyan]📦 Installing: {pkg}[/]")
                results = install_packages([pkg])
                if results.get(pkg, False):
                    console.print(f"[green]✓ {pkg} installed[/]")
                    return True
        
        # LLM analysis
        hints = {"source_file": str(self.target_file)} if self.target_file else {}
        ctx = analyze_exception(exc_value, hints=hints)
        error_class = classify_error(ctx)
        console.print(f"[blue]🔍 Analyzing ({error_class})...[/]")
        
        proposal = request_fix(ctx)
        
        if proposal.confidence < 0.1:
            console.print("[yellow]⚠ LLM confidence too low — skipping[/]")
            return False
        
        old_auto = self.config.auto_apply
        self.config.auto_apply = self.auto_apply
        fixed = apply_fix(ctx, proposal, confirm=not self.auto_apply)
        self.config.auto_apply = old_auto
        
        if fixed:
            console.print("[green]✓ Fix applied[/]")
            if self.restart:
                console.print("[green]🔄 Restarting...[/]")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            return True
        else:
            console.print("[yellow]Fix not applied[/]")
            return False


def pfix_session(
    target_file: Optional[str] = None,
    *,
    auto_apply: Optional[bool] = None,
    retries: Optional[int] = None,
    restart: Optional[bool] = None,
) -> PFixSession:
    """Create pfix session for file-level auto-healing."""
    return PFixSession(
        target_file=target_file,
        auto_apply=auto_apply,
        retries=retries,
        restart=restart,
    )


def auto_pfix(
    func: Optional[F] = None,
    *,
    auto_apply: Optional[bool] = None,
    retries: Optional[int] = None,
    restart: Optional[bool] = None,
) -> Any:
    """Decorator that auto-fixes exceptions in wrapped function."""
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            source_file = inspect.getfile(fn)
            session = PFixSession(
                target_file=source_file,
                auto_apply=auto_apply,
                retries=retries,
                restart=restart,
            )
            with session:
                return fn(*args, **kwargs)
        return wrapper  # type: ignore
    
    if func is not None:
        return decorator(func)
    return decorator


def install_pfix_hook(
    target_file: Optional[str] = None,
    auto_apply: bool = True,
) -> None:
    """Install global pfix excepthook."""
    if target_file is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            target_file = frame.f_back.f_globals.get('__file__')
    
    target_path = Path(target_file).resolve() if target_file else None
    config = get_config()
    original_hook = sys.excepthook
    
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
            original_hook(exc_type, exc_value, exc_tb)
            return
        
        console.print(f"\n[red]💥 pfix: {exc_type.__name__}: {exc_value}[/]")
        
        if exc_tb:
            exc_value.__traceback__ = exc_tb
        
        if isinstance(exc_value, (ModuleNotFoundError, ImportError)):
            module = detect_missing_from_error(str(exc_value))
            if module:
                pkg = resolve_package_name(module)
                console.print(f"[cyan]📦 Installing: {pkg}[/]")
                results = install_packages([pkg])
                if results.get(pkg, False):
                    console.print(f"[green]✓ Installed {pkg}[/]")
                    return
        
        console.print("[dim]Debug: Analyzing exception...[/]")
        ctx = analyze_exception(exc_value)
        console.print(f"[dim]Debug: source_file={ctx.source_file}, func={ctx.function_name}[/]")
        
        console.print("[dim]Debug: Requesting fix from LLM...[/]")
        proposal = request_fix(ctx)
        console.print(f"[dim]Debug: confidence={proposal.confidence}, has_fix={proposal.has_code_fix}[/]")
        
        if proposal.confidence > 0.1:
            console.print(f"[blue]🔍 Confidence OK ({proposal.confidence:.0%}), applying fix...[/]")
            old_auto = config.auto_apply
            config.auto_apply = auto_apply
            fixed = apply_fix(ctx, proposal, confirm=not auto_apply)
            config.auto_apply = old_auto
            
            # Restart process if fix applied and auto_restart enabled
            if fixed and config.auto_restart:
                if ctx.source_file:
                    _clear_pycache(Path(ctx.source_file))
                console.print("[green]🔄 Restarting...[/]")
                os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            console.print(f"[yellow]⚠ Confidence too low ({proposal.confidence:.0%}), skipping[/]")
        
        original_hook(exc_type, exc_value, exc_tb)
    
    sys.excepthook = hook


# Alias for backward compatibility
pfix_guard = pfix_session
