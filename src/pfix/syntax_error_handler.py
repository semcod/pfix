"""
SyntaxError handling for pfix CLI.

This module provides special handling for SyntaxError exceptions,
which occur during module import/parsing rather than runtime.
"""

import sys
from pathlib import Path
from rich.console import Console

console = Console(stderr=True)


def handle_syntax_error(exc: SyntaxError, auto_apply: bool = True) -> bool:
    """
    Handle SyntaxError by calling pfix to fix it.
    
    Args:
        exc: The SyntaxError exception
        auto_apply: Whether to auto-apply fixes without confirmation
        
    Returns:
        True if fix was applied, False otherwise
    """
    try:
        from pfix.types import ErrorContext
        from pfix.llm import request_fix
        from pfix.fixer import apply_fix
        from pfix.config import get_config
        from pfix.session import _clear_pycache
        
        config = get_config()
        
        console.print(f"[red]💥 pfix: SyntaxError detected: {exc}[/]")
        
        # Build context from SyntaxError
        ctx = ErrorContext()
        ctx.exception_type = "SyntaxError"
        ctx.exception_message = str(exc)
        ctx.source_file = exc.filename or ""
        ctx.line_number = exc.lineno or 0
        ctx.failing_line = exc.text or ""
        ctx.python_version = sys.version.split()[0]
        
        # Read source file
        if ctx.source_file:
            try:
                source_path = Path(ctx.source_file)
                if source_path.exists():
                    ctx.source_code = source_path.read_text(encoding="utf-8")
            except Exception:
                pass
        
        console.print(f"[dim]Debug: SyntaxError in {ctx.source_file}:{ctx.line_number}[/]")
        
        # Request fix from LLM
        proposal = request_fix(ctx)
        console.print(f"[dim]Debug: confidence={proposal.confidence}, has_fix={proposal.has_code_fix}[/]")
        
        if proposal.confidence > 0.1 and proposal.has_code_fix:
            console.print(f"[blue]🔍 Confidence OK ({proposal.confidence:.0%}), applying fix...[/]")
            fixed = apply_fix(ctx, proposal, confirm=not auto_apply)
            
            if fixed:
                console.print(f"[green]✓ Fix applied to {ctx.source_file}[/]")
                if config.auto_restart and ctx.source_file:
                    _clear_pycache(Path(ctx.source_file))
                    console.print("[green]🔄 Restarting process...[/]")
                    import os
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                return True
        else:
            console.print(f"[yellow]⚠ Confidence too low ({proposal.confidence:.0%}), skipping[/]")
            if proposal.diagnosis:
                console.print(f"[dim]Diagnosis: {proposal.diagnosis[:200]}[/]")
            if proposal.raw_response:
                console.print(f"[dim]Raw: {proposal.raw_response[:200]}[/]")
                
    except Exception as e:
        console.print(f"[red]Error handling SyntaxError: {e}[/]")
    
    return False
