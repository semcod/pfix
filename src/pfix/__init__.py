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

from importlib import import_module
from typing import Any

__version__ = "0.1.79"
__all__ = [
    "pfix",
    "apfix",
    "auto_pfix",
    "pfix_session",
    "pfix_guard",
    "configure",
    "get_config",
    "PfixConfig",
    "reset_config",
]

_LAZY_EXPORTS = {
    "pfix": ("pfix.decorator", "pfix"),
    "apfix": ("pfix.decorator", "apfix"),
    "auto_pfix": ("pfix.session", "auto_pfix"),
    "pfix_session": ("pfix.session", "pfix_session"),
    "pfix_guard": ("pfix.session", "pfix_guard"),
    "configure": ("pfix.config", "configure"),
    "get_config": ("pfix.config", "get_config"),
    "PfixConfig": ("pfix.config", "PfixConfig"),
    "reset_config": ("pfix.config", "reset_config"),
}


def __getattr__(name: str) -> Any:
    """Load public runtime integrations only when they are requested."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute = target
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value

# ── Auto-activation on import ─────────────────────────────────────
# If PFIX_AUTO_APPLY=true in .env, automatically install global exception hook
# This allows: `import pfix` to just work with zero code changes


def _auto_activate():
    """Check .env and auto-enable pfix if context allows."""
    import os

    _load_env()

    activation = os.getenv("PFIX_AUTO_ACTIVATE", "").lower()
    if activation in ("false", "0", "no"):
        return

    # Preserve the documented PFIX_AUTO_APPLY opt-in while keeping plain
    # metadata imports free from implicit runtime hooks.
    if os.getenv("PFIX_AUTO_APPLY", "false").lower() in ("true", "1", "yes"):
        from .session import install_pfix_hook

        caller_file = _get_caller_file()
        install_pfix_hook(caller_file, auto_apply=True)

    # Runtime TODO hooks are broader than auto-apply and require an explicit
    # activation flag even when pyproject.toml enables their configuration.
    if activation in ("true", "1", "yes"):
        _setup_runtime_todo()


def _load_env():
    """Load .env file from current or parent directories."""
    from pathlib import Path
    from dotenv import load_dotenv

    for parent in [Path.cwd(), *Path.cwd().parents]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break


def _get_caller_file() -> str | None:
    """Get the file path of the script that imported pfix."""
    import inspect

    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        # Walk back: _auto_activate -> <module> -> caller
        caller_globals = frame.f_back.f_back.f_globals
        return caller_globals.get("__file__")
    return None


def _setup_runtime_todo():
    """Configure and install runtime_todo excepthook if enabled."""
    import os
    from .config import get_config

    config = get_config()
    pyproject = getattr(config, "_pyproject_data", {})
    rt_config = pyproject.get("tool", {}).get("pfix", {}).get("runtime_todo", {})

    rt_enabled = os.getenv("PFIX_RUNTIME_TODO", str(rt_config.get("enabled", "false"))).lower() in ("true", "1", "yes")
    if rt_enabled:
        try:
            from .runtime_todo import RuntimeCollector, TodoFile

            todo_path = os.getenv("PFIX_TODO_FILE", rt_config.get("todo_file", "TODO.md"))
            collector = RuntimeCollector(
                TodoFile(todo_path),
                enabled=True,
                min_severity=rt_config.get("min_severity", "low"),
                deduplicate=rt_config.get("deduplicate", True),
            )
            collector.install_excepthook()
        except Exception:
            pass


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
