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
"""

from .config import PfixConfig, configure, get_config
from .decorator import apfix, pfix
from .session import auto_pfix, pfix_guard, pfix_session

__version__ = "0.1.3"
__all__ = ["pfix", "apfix", "auto_pfix", "pfix_session", "pfix_guard", "configure", "get_config", "PfixConfig"]
