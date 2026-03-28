"""
pfix — Self-healing Python for development.

Catches runtime errors and fixes source code + dependencies via LLM + MCP.

    from pfix import pfix

    @pfix
    def my_function():
        ...

    # Configure
    from pfix import configure
    configure(auto_apply=True, llm_model="openrouter/anthropic/claude-sonnet-4")

Auto-activation via .env:
    Set PFIX_AUTO_APPLY=true in .env to enable auto-fixing on any exception
    without any code changes (just import pfix).
"""

from .config import PfixConfig, configure, get_config
from .decorator import apfix, pfix
from .session import auto_pfix, pfix_guard, pfix_session

__version__ = "0.1.8"
__all__ = ["pfix", "apfix", "auto_pfix", "pfix_session", "pfix_guard", "configure", "get_config", "PfixConfig"]

# ── Auto-activation on import ─────────────────────────────────────
# If PFIX_AUTO_APPLY=true in .env, automatically install global exception hook
# This allows: `import pfix` to just work with zero code changes

def _auto_activate():
    """Check .env and auto-enable pfix if PFIX_AUTO_APPLY=true."""
    import os
    from pathlib import Path
    
    # Check if explicitly disabled
    if os.getenv("PFIX_AUTO_ACTIVATE", "true").lower() in ("false", "0", "no"):
        return
    
    # Check for auto_apply in environment (loaded from .env if present)
    auto_apply = os.getenv("PFIX_AUTO_APPLY", "false").lower() in ("true", "1", "yes")
    
    if auto_apply:
        # Import here to avoid circular imports
        from .session import install_pfix_hook
        
        # Get the caller's file (the script that imported pfix)
        import inspect
        frame = inspect.currentframe()
        caller_file = None
        if frame and frame.f_back and frame.f_back.f_back:
            # Walk back: _auto_activate -> <module> -> caller
            caller_globals = frame.f_back.f_back.f_globals
            caller_file = caller_globals.get("__file__")
        
        install_pfix_hook(caller_file, auto_apply=True)

# Run auto-activation
try:
    _auto_activate()
except Exception:
    # Never break user code if auto-activation fails
    pass
