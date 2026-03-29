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
    llm_model: str = "openrouter/qwen/qwen3-coder-next"
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

    # Internal cache for pyproject.toml data
    _pyproject_data: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls, dotenv_path: Optional[str] = None) -> "PfixConfig":
        """Load config from .env + environment + pyproject.toml."""
        _find_and_load_dotenv(dotenv_path)

        # Load initial config from environment
        env = _load_env_values()
        cfg = cls(**env)

        # Normalize and merge
        _sanitize_model_name(cfg)
        _merge_pyproject_config(cfg)

        return cfg

    @staticmethod
    def _read_pyproject_full(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                return {}
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def validate(self) -> list[str]:
        warnings = []
        if not self.llm_api_key:
            warnings.append("No API key. Set OPENROUTER_API_KEY in .env")
        return warnings


def _find_and_load_dotenv(dotenv_path: Optional[str]):
    """Find and load .env from specified path or parent directories."""
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        for parent in [Path.cwd(), *Path.cwd().parents]:
            env_file = parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                break


def _sanitize_model_name(cfg: "PfixConfig"):
    """Ensure OpenRouter models have the proper prefix."""
    if cfg.llm_api_base and "openrouter" in cfg.llm_api_base:
        if "/" in cfg.llm_model and not cfg.llm_model.startswith("openrouter/"):
            cfg.llm_model = f"openrouter/{cfg.llm_model}"


def _merge_pyproject_config(cfg: "PfixConfig"):
    """Merge tool.pfix settings from pyproject.toml."""
    pyproject_full = PfixConfig._read_pyproject_full(cfg.project_root / "pyproject.toml")
    cfg._pyproject_data = pyproject_full
    
    pyproject = pyproject_full.get("tool", {}).get("pfix", {})
    for key, val in pyproject.items():
        # Only set if not already overridden by PFIX_* env var
        env_key = f"PFIX_{key.upper()}"
        if hasattr(cfg, key) and not os.getenv(env_key):
            setattr(cfg, key, val)


def _load_env_values() -> dict:
    """Load and convert environment variables into dict for PfixConfig. CC≤3."""
    env = {}
    env.update(_load_llm_env())
    env.update(_load_behavior_env())
    env.update(_load_mcp_env())
    env.update(_load_git_env())
    env.update(_load_paths_env())
    return env


def _load_llm_env() -> dict:
    def _env_float(key: str, default: float) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _env_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    return {
        "llm_model": os.getenv("PFIX_MODEL", os.getenv("LIBFIX_MODEL", PfixConfig.llm_model)),
        "llm_api_key": os.getenv("OPENROUTER_API_KEY", os.getenv("PFIX_API_KEY", "")),
        "llm_api_base": os.getenv("PFIX_API_BASE", PfixConfig.llm_api_base),
        "llm_temperature": _env_float("PFIX_TEMPERATURE", PfixConfig.llm_temperature),
        "llm_max_tokens": _env_int("PFIX_MAX_TOKENS", PfixConfig.llm_max_tokens),
    }


def _load_behavior_env() -> dict:
    def _env_bool(key: str, default: bool) -> bool:
        val = os.getenv(key, str(default).lower())
        return val.lower() in ("true", "1", "yes")

    def _env_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    pkg_manager = "uv" if shutil.which("uv") else "pip"
    return {
        "auto_apply": _env_bool("PFIX_AUTO_APPLY", False),
        "auto_install_deps": _env_bool("PFIX_AUTO_INSTALL_DEPS", True),
        "auto_restart": _env_bool("PFIX_AUTO_RESTART", False),
        "max_retries": _env_int("PFIX_MAX_RETRIES", 3),
        "enabled": _env_bool("PFIX_ENABLED", True),
        "dry_run": _env_bool("PFIX_DRY_RUN", False),
        "pkg_manager": os.getenv("PFIX_PKG_MANAGER", pkg_manager),
        "create_backups": _env_bool("PFIX_CREATE_BACKUPS", True),
    }


def _load_mcp_env() -> dict:
    def _env_bool(key: str, default: bool) -> bool:
        val = os.getenv(key, str(default).lower())
        return val.lower() in ("true", "1", "yes")

    return {
        "mcp_enabled": _env_bool("PFIX_MCP_ENABLED", False),
        "mcp_server_url": os.getenv("PFIX_MCP_SERVER_URL", PfixConfig.mcp_server_url),
        "mcp_transport": os.getenv("PFIX_MCP_TRANSPORT", PfixConfig.mcp_transport),
    }


def _load_git_env() -> dict:
    def _env_bool(key: str, default: bool) -> bool:
        val = os.getenv(key, str(default).lower())
        return val.lower() in ("true", "1", "yes")

    return {
        "git_auto_commit": _env_bool("PFIX_GIT_COMMIT", False),
        "git_commit_prefix": os.getenv("PFIX_GIT_PREFIX", PfixConfig.git_commit_prefix),
    }


def _load_paths_env() -> dict:
    return {
        "project_root": Path(os.getenv("PFIX_PROJECT_ROOT", str(Path.cwd()))),
        "log_file": os.getenv("PFIX_LOG_FILE"),
    }


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
