"""
pfix.permissions — RBAC permissions for pfix.

Configuration in pyproject.toml:
    [tool.pfix.permissions]
    auto_apply_allowed = ["dev", "staging"]  # Environments where auto-apply is OK
    require_approval_above_cc = 10             # Require approval for complex code
    block_patterns = ["**/migrations/**", "**/settings.py"]  # Never modify these
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from .config import get_config


def get_environment() -> str:
    """Detect current environment."""
    import os

    # Check environment variables
    env_vars = ["ENV", "ENVIRONMENT", "STAGE", "DEPLOY_ENV"]
    for var in env_vars:
        if value := os.getenv(var):
            return value.lower()

    # Default
    return "dev"


def check_auto_apply_allowed() -> tuple[bool, str]:
    """
    Check if auto-apply is permitted in current environment.

    Returns:
        (allowed, reason)
    """
    config = get_config()
    env = get_environment()

    allowed_envs = getattr(config, "auto_apply_allowed", ["dev", "staging"])

    if env in allowed_envs:
        return True, ""

    if "production" in env or "prod" in env:
        return False, f"Auto-apply blocked in production environment '{env}'"

    return False, f"Auto-apply not allowed in environment '{env}' (allowed: {allowed_envs})"


def check_complexity_approval(cc: int) -> tuple[bool, str]:
    """
    Check if high-complexity fix requires manual approval.

    Args:
        cc: Cyclomatic complexity of code being modified

    Returns:
        (approved, reason)
    """
    config = get_config()
    threshold = getattr(config, "require_approval_above_cc", 10)

    if cc <= threshold:
        return True, ""

    return False, f"Fix in complex code (CC={cc}) requires manual approval (threshold: {threshold})"


def check_blocked_path(filepath: Path) -> tuple[bool, str]:
    """
    Check if file path is blocked from modification.

    Args:
        filepath: Path to file

    Returns:
        (allowed, reason)
    """
    config = get_config()
    patterns = getattr(config, "block_patterns", [])

    str_path = str(filepath)

    for pattern in patterns:
        if fnmatch(str_path, pattern):
            return False, f"Path blocked by pattern '{pattern}'"

    # Default blocked paths
    default_blocked = [
        "**/migrations/**",
        "**/alembic/versions/**",
        "**/settings.py",
        "**/config.py",
        "**/secrets.py",
        "**/.env*",
    ]

    for pattern in default_blocked:
        if fnmatch(str_path, pattern):
            return False, f"Path blocked by default pattern '{pattern}'"

    return True, ""


def check_all_permissions(
    filepath: Path,
    cc: int = 0,
    auto_apply: bool = False,
) -> tuple[bool, str]:
    """
    Check all permissions for a fix operation.

    Args:
        filepath: Target file path
        cc: Cyclomatic complexity
        auto_apply: Whether auto-apply is requested

    Returns:
        (permitted, reason)
    """
    # Check path blocked
    allowed, reason = check_blocked_path(filepath)
    if not allowed:
        return False, reason

    # Check auto-apply permissions
    if auto_apply:
        allowed, reason = check_auto_apply_allowed()
        if not allowed:
            return False, reason

    # Check complexity
    if cc > 0:
        allowed, reason = check_complexity_approval(cc)
        if not allowed:
            return False, reason

    return True, ""


def get_permissions_summary() -> dict:
    """Get summary of current permissions."""
    config = get_config()
    env = get_environment()

    auto_apply_ok, auto_apply_reason = check_auto_apply_allowed()

    return {
        "environment": env,
        "auto_apply_allowed": auto_apply_ok,
        "auto_apply_reason": auto_apply_reason,
        "blocked_patterns": getattr(config, "block_patterns", []),
        "complexity_threshold": getattr(config, "require_approval_above_cc", 10),
        "allowed_environments": getattr(config, "auto_apply_allowed", ["dev", "staging"]),
    }
