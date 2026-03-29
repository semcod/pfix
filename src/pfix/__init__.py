"""
pfix — Self-healing Python for development.

Catches runtime errors and fixes source code + dependencies via LLM + MCP.

    from pfix import pfix

    @pfix
    def my_function():
        ...

    # Configure
    from pfix import configure
    configure(auto_apply=True, llm_model="openrouter/qwen/qwen3-coder-next")

Auto-activation via .env:
    Set PFIX_AUTO_APPLY=true in .env to enable auto-fixing on any exception
    without any code changes (just import pfix).
"""

from .config import PfixConfig, configure, get_config, reset_config
from .decorator import apfix, pfix
from .session import auto_pfix, pfix_guard, pfix_session

__version__ = "0.1.47"
__all__ = ["pfix", "apfix", "auto_pfix", "pfix_session", "pfix_guard", "configure", "get_config", "PfixConfig", "reset_config"]

# ── Auto-activation on import ─────────────────────────────────────
# If PFIX_AUTO_APPLY=true in .env, automatically install global exception hook
# This allows: `import pfix` to just work with zero code changes

def _auto_activate():
    """Check .env and auto-enable pfix if PFIX_AUTO_APPLY=true."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Load .env file first
    for parent in [Path.cwd(), *Path.cwd().parents]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
    
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

    # Check for runtime_todo auto-activation (via env or pyproject)
    from .config import get_config
    config = get_config()
    pyproject = getattr(config, "_pyproject_data", {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})
    
    runtime_todo_enabled = os.getenv("PFIX_RUNTIME_TODO", str(rt_config.get("enabled", "false"))).lower() in ("true", "1", "yes")
    if runtime_todo_enabled:
        try:
            from .runtime_todo import RuntimeCollector, TodoFile
            todo_path = os.getenv("PFIX_TODO_FILE", rt_config.get("todo_file", "TODO.md"))
            todo = TodoFile(todo_path)
            collector = RuntimeCollector(
                todo, 
                enabled=True,
                min_severity=rt_config.get("min_severity", "low"),
                deduplicate=rt_config.get("deduplicate", True),
            )
            collector.install_excepthook()
        except Exception:
            pass  # Never break user code

# Run auto-activation
try:
    _auto_activate()
except Exception as e:
    # Never break user code if auto-activation fails
    import sys
    print(f"[pfix-debug] Auto-activation failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    pass
