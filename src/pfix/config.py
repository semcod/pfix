"""
pfix.config — Configuration management.

Loads from .env → environment → pyproject.toml [tool.pfix].
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class PfixConfig:
    """Central configuration."""

    # LLM
    llm_model: str = "openrouter/anthropic/claude-sonnet-4"
    llm_api_key: str = ""
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    # Behavior
    auto_apply: bool = False
    auto_install_deps: bool = True
    auto_restart: bool = False          # os.execv restart after fix
    max_retries: int = 3
    enabled: bool = True
    dry_run: bool = False

    # Dependency manager: "pip" | "uv" (auto-detected)
    pkg_manager: str = "pip"

    # MCP
    mcp_enabled: bool = False
    mcp_server_url: str = "http://localhost:3001"
    mcp_transport: str = "stdio"        # "stdio" | "http"

    # Git integration
    git_auto_commit: bool = False
    git_commit_prefix: str = "pfix: "

    # Backup
    create_backups: bool = True  # Set to false to disable .pfix_backups/

    # Paths
    project_root: Path = field(default_factory=lambda: Path.cwd())
    log_file: Optional[str] = None

    # Extra context for LLM
    extra_context: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, dotenv_path: Optional[str] = None) -> "PfixConfig":
        """Load config from .env + environment + pyproject.toml."""
        # Find and load .env
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            for parent in [Path.cwd(), *Path.cwd().parents]:
                env_file = parent / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                    break

        # Detect uv
        pkg_manager = "uv" if shutil.which("uv") else "pip"

        cfg = cls(
            llm_model=os.getenv("PFIX_MODEL", os.getenv("LIBFIX_MODEL", cls.llm_model)),
            llm_api_key=os.getenv("OPENROUTER_API_KEY", os.getenv("PFIX_API_KEY", "")),
            llm_api_base=os.getenv("PFIX_API_BASE", cls.llm_api_base),
            llm_temperature=float(os.getenv("PFIX_TEMPERATURE", str(cls.llm_temperature))),
            llm_max_tokens=int(os.getenv("PFIX_MAX_TOKENS", str(cls.llm_max_tokens))),
            auto_apply=os.getenv("PFIX_AUTO_APPLY", "false").lower() in ("true", "1", "yes"),
            auto_install_deps=os.getenv("PFIX_AUTO_INSTALL_DEPS", "true").lower() in ("true", "1", "yes"),
            auto_restart=os.getenv("PFIX_AUTO_RESTART", "false").lower() in ("true", "1", "yes"),
            max_retries=int(os.getenv("PFIX_MAX_RETRIES", "3")),
            enabled=os.getenv("PFIX_ENABLED", "true").lower() in ("true", "1", "yes"),
            dry_run=os.getenv("PFIX_DRY_RUN", "false").lower() in ("true", "1", "yes"),
            pkg_manager=os.getenv("PFIX_PKG_MANAGER", pkg_manager),
            mcp_enabled=os.getenv("PFIX_MCP_ENABLED", "false").lower() in ("true", "1", "yes"),
            mcp_server_url=os.getenv("PFIX_MCP_SERVER_URL", cls.mcp_server_url),
            mcp_transport=os.getenv("PFIX_MCP_TRANSPORT", cls.mcp_transport),
            git_auto_commit=os.getenv("PFIX_GIT_COMMIT", "false").lower() in ("true", "1", "yes"),
            git_commit_prefix=os.getenv("PFIX_GIT_PREFIX", cls.git_commit_prefix),
            create_backups=os.getenv("PFIX_CREATE_BACKUPS", "true").lower() in ("true", "1", "yes"),
            project_root=Path(os.getenv("PFIX_PROJECT_ROOT", str(Path.cwd()))),
            log_file=os.getenv("PFIX_LOG_FILE"),
        )

        # Auto-fix model name: ensure openrouter/ prefix for OpenRouter models
        if cfg.llm_api_base and "openrouter" in cfg.llm_api_base:
            if "/" in cfg.llm_model and not cfg.llm_model.startswith("openrouter/"):
                cfg.llm_model = f"openrouter/{cfg.llm_model}"

        # Merge pyproject.toml [tool.pfix]
        pyproject = cls._read_pyproject(cfg.project_root / "pyproject.toml")
        for key, val in pyproject.items():
            if hasattr(cfg, key) and not os.getenv(f"PFIX_{key.upper()}"):
                setattr(cfg, key, val)

        return cfg

    @staticmethod
    def _read_pyproject(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                return {}
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("pfix", {})

    def validate(self) -> list[str]:
        warnings = []
        if not self.llm_api_key:
            warnings.append("No API key. Set OPENROUTER_API_KEY in .env")
        return warnings


# ── Global singleton ────────────────────────────────────────────────

_config: Optional[PfixConfig] = None


def get_config() -> PfixConfig:
    global _config
    if _config is None:
        _config = PfixConfig.from_env()
    return _config


def configure(**kwargs) -> PfixConfig:
    """Override global config programmatically."""
    global _config
    _config = PfixConfig.from_env()
    for k, v in kwargs.items():
        if hasattr(_config, k):
            setattr(_config, k, v)
        else:
            _config.extra_context[k] = v
    return _config


def reset_config():
    """Reset global config (useful in tests)."""
    global _config
    _config = None
