"""
pfix.session — File-level auto-healing context manager.

Usage:
    from pfix import pfix_session, configure
    
    configure(auto_apply=True)
    
    with pfix_session(__file__):
        # Your entire script runs here
        # Any exception triggers pfix auto-repair
        def buggy_function():
            return 1 / 0  # Will be auto-fixed
        
        buggy_function()

Or as a decorator replacement:
    from pfix import auto_pfix
    
    @auto_pfix  # Wraps ALL functions in the module
    def main():
        ...
"""

from __future__ import annotations

import contextlib
import functools
import inspect
import os
import sys
import types
from pathlib import Path
from typing import Any, Callable, Iterator, Optional, TypeVar

from rich.console import Console

from .analyzer import analyze_exception, classify_error
from .config import get_config
from .dependency import detect_missing_from_error, install_packages, resolve_package_name
from .fixer import apply_fix
from .llm import request_fix

console = Console(stderr=True)
F = TypeVar("F", bound=Callable)


@contextlib.contextmanager
def pfix_session(
    target_file: Optional[str] = None,
    *,
    auto_apply: Optional[bool] = None,
    retries: Optional[int] = None,
    restart: Optional[bool] = None,
) -> Iterator[None]:
    """Context manager that enables pfix auto-repair for the entire code block.
    
    Args:
        target_file: Path to the file being fixed (auto-detected if None)
        auto_apply: Auto-apply fixes without confirmation
        retries: Max fix attempts per error
        restart: Restart process after applying fix
        
    Example:
        with pfix_session(__file__, auto_apply=True):
            main()  # Any exception here triggers auto-fix
    """
    config = get_config()
    
    # Auto-detect target file from caller if not provided
    if target_file is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = frame.f_back.f_globals.get('__file__')
            target_file = caller_module
    
    target_path = Path(target_file).resolve() if target_file else None
    
    max_retries = retries if retries is not None else config.max_retries
    should_auto = auto_apply if auto_apply is not None else config.auto_apply
    should_restart = restart if restart is not None else config.auto_restart
    
    original_excepthook = sys.excepthook
    
    def pfix_excepthook(exc_type, exc_value, exc_tb):
        if exc_type in (KeyboardInterrupt, SystemExit):
            original_excepthook(exc_type, exc_value, exc_tb)
            return
        
        console.print(f"\n[red]💥 pfix session caught: {exc_type.__name__}: {exc_value}[/]")
        
        # Try quick dep fix first
        if isinstance(exc_value, (ModuleNotFoundError, ImportError)):
            module = detect_missing_from_error(str(exc_value))
            if module:
                pkg = resolve_package_name(module)
                console.print(f"[cyan]📦 Installing missing dependency: {pkg}[/]")
                results = install_packages([pkg])
                if results.get(pkg, False):
                    console.print(f"[green]✓ {pkg} installed, retry...[/]")
                    return  # Don't propagate, let caller retry
        
        # Full LLM analysis
        exc_value.__traceback__ = exc_tb
        ctx = analyze_exception(exc_value, source_file=target_path)
        error_class = classify_error(ctx)
        console.print(f"[blue]🔍 Analyzing ({error_class})...[/]")
        
        proposal = request_fix(ctx)
        
        if proposal.confidence < 0.1:
            console.print("[yellow]⚠ LLM confidence too low — skipping[/]")
            original_excepthook(exc_type, exc_value, exc_tb)
            return
        
        # Apply fix
        old_auto = config.auto_apply
        if should_auto:
            config.auto_apply = True
        
        fixed = apply_fix(ctx, proposal, confirm=not should_auto)
        config.auto_apply = old_auto
        
        if fixed:
            if should_restart:
                console.print("[green]🔄 Restarting process...[/]")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                console.print("[green]✓ Fix applied — restart script to use fixed code[/]")
        else:
            console.print("[yellow]Fix not applied[/]")
        
        # Still show original error
        original_excepthook(exc_type, exc_value, exc_tb)
    
    sys.excepthook = pfix_excepthook
    
    try:
        yield
    finally:
        sys.excepthook = original_excepthook


def auto_pfix(
    func: Optional[F] = None,
    *,
    auto_apply: Optional[bool] = None,
    retries: Optional[int] = None,
    restart: Optional[bool] = None,
) -> Any:
    """Decorator that wraps the entire function with file-level pfix.
    
    Unlike @pfix which wraps individual functions, this uses pfix_session
    internally to catch and fix errors anywhere in the call stack.
    
    Example:
        @auto_pfix(auto_apply=True)
        def main():
            # All code here is protected
            buggy()  # Auto-fixed on error
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get source file of the wrapped function
            source_file = inspect.getfile(fn)
            
            with pfix_session(
                source_file,
                auto_apply=auto_apply,
                retries=retries,
                restart=restart,
            ):
                return fn(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    if func is not None:
        return decorator(func)
    return decorator


@contextlib.contextmanager
def pfix_guard(
    source_file: Optional[str] = None,
    auto_apply: bool = True,
) -> Iterator[None]:
    """Lightweight guard for main blocks — just install excepthook.
    
    This is the simplest way to use pfix:
        from pfix import pfix_guard
        
        with pfix_guard(__file__):
            main()
    """
    import sys
    
    # Determine target file
    if source_file is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            source_file = frame.f_back.f_globals.get('__file__')
    
    target_path = Path(source_file).resolve() if source_file else None
    original_hook = sys.excepthook
    
    def hook(exc_type, exc_value, exc_tb):
        if exc_type in (KeyboardInterrupt, SystemExit):
            original_hook(exc_type, exc_value, exc_tb)
            return
            
        console.print(f"\n[red]💥 pfix guard: {exc_type.__name__}: {exc_value}[/]")
        
        exc_value.__traceback__ = exc_tb
        ctx = analyze_exception(exc_value, source_file=target_path)
        proposal = request_fix(ctx)
        
        if proposal.confidence > 0.1:
            config = get_config()
            old_auto = config.auto_apply
            config.auto_apply = auto_apply
            apply_fix(ctx, proposal, confirm=not auto_apply)
            config.auto_apply = old_auto
        
        original_hook(exc_type, exc_value, exc_tb)
    
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = original_hook
