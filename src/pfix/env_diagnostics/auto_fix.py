"""
pfix.env_diagnostics.auto_fix — Auto-fix handlers for environment issues.

Provides automatic fixes for issues marked as auto_fixable=True.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..types import DiagnosticResult


def can_auto_fix(result: "DiagnosticResult") -> bool:
    """Check if this result can be auto-fixed."""
    if not result.auto_fixable:
        return False
    return result.check_name in _FIX_HANDLERS


def apply_auto_fix(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Apply auto-fix for a diagnostic result.

    Returns:
        (success, message)
    """
    handler = _FIX_HANDLERS.get(result.check_name)
    if not handler:
        return False, f"No auto-fix handler for {result.check_name}"

    try:
        return handler(result, project_root)
    except Exception as e:
        return False, f"Fix failed: {e}"


def _fix_stale_bytecode(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Remove stale .pyc files."""
    removed = 0
    for pyc in project_root.rglob("*.pyc"):
        py = pyc.with_suffix(".py")
        if py.exists() and pyc.stat().st_mtime > py.stat().st_mtime:
            pyc.unlink()
            removed += 1

    # Also clear __pycache__
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)
            removed += 1

    return True, f"Removed {removed} stale bytecode items"


def _fix_missing_requirement(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Install missing requirement."""
    from ..dependency import install_packages

    pkg = result.details.get("package", "")
    if not pkg:
        return False, "No package specified"

    results = install_packages([pkg])
    success = results.get(pkg, False)

    return success, f"Installed {pkg}: {'OK' if success else 'FAILED'}"


def _fix_utf8_bom(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Remove UTF-8 BOM from file."""
    path = result.abs_path
    if not path or not Path(path).exists():
        return False, "File not found"

    file_path = Path(path)
    content = file_path.read_bytes()

    if content.startswith(b"\xef\xbb\xbf"):
        file_path.write_bytes(content[3:])
        return True, f"Removed BOM from {file_path.name}"

    return False, "File had no BOM"


def _fix_mixed_line_endings(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Convert line endings to LF."""
    path = result.abs_path
    if not path or not Path(path).exists():
        return False, "File not found"

    file_path = Path(path)
    content = file_path.read_bytes()

    # Convert CRLF to LF
    new_content = content.replace(b"\r\n", b"\n")

    if new_content != content:
        file_path.write_bytes(new_content)
        return True, f"Converted line endings to LF in {file_path.name}"

    return False, "No line ending changes needed"


def _fix_large_log_file(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Truncate large log file."""
    path = result.abs_path
    if not path or not Path(path).exists():
        return False, "File not found"

    file_path = Path(path)

    # Keep last 1000 lines
    try:
        with open(file_path, "rb") as f:
            lines = f.readlines()

        if len(lines) > 1000:
            with open(file_path, "wb") as f:
                f.writelines(lines[-1000:])
            return True, f"Truncated {file_path.name} to last 1000 lines"

        return False, "File is small, no truncation needed"

    except Exception as e:
        return False, f"Failed to truncate: {e}"


def _fix_api_key_placeholder(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Guide user to set proper API key."""
    var = result.details.get("variable", "API_KEY")
    return False, f"Please set a real value for {var} in .env file"


def _fix_missing_dotenv(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Copy .env.example to .env."""
    example = project_root / ".env.example"
    env_file = project_root / ".env"

    if not example.exists():
        return False, ".env.example not found"

    if env_file.exists():
        return False, ".env already exists"

    shutil.copy2(example, env_file)
    return True, f"Created .env from .env.example"


def _fix_env_not_gitignored(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Add .env to .gitignore."""
    gitignore = project_root / ".gitignore"

    if not gitignore.exists():
        gitignore.write_text(".env\n")
        return True, "Created .gitignore with .env"

    content = gitignore.read_text()
    if ".env" in content:
        return False, ".env already in .gitignore"

    with open(gitignore, "a") as f:
        f.write("\n.env\n")

    return True, "Added .env to .gitignore"


def _fix_missing_init(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Create missing __init__.py file."""
    path = result.abs_path
    if not path:
        return False, "No path specified"
    
    file_path = Path(path)
    if file_path.exists():
        return False, f"{file_path.name} already exists"
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()
    return True, f"Created {file_path}"

def _fix_hidden_pollution(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Remove hidden pollution files."""
    path = result.abs_path
    if not path or not Path(path).exists():
        return False, "File not found"
    
    Path(path).unlink()
    return True, f"Removed {Path(path).name}"

def _fix_no_manifest(result: "DiagnosticResult", project_root: Path) -> tuple[bool, str]:
    """Generate requirements.txt."""
    from ..dependency import generate_requirements
    try:
        generate_requirements()
        return True, "Generated requirements.txt"
    except Exception as e:
        return False, f"Failed to generate: {e}"

# Registry of auto-fix handlers
_FIX_HANDLERS: dict[str, callable] = {
    "stale_bytecode": _fix_stale_bytecode,
    "missing_requirement": _fix_missing_requirement,
    "utf8_bom": _fix_utf8_bom,
    "mixed_line_endings": _fix_mixed_line_endings,
    "large_log_file": _fix_large_log_file,
    "api_key_placeholder": _fix_api_key_placeholder,
    "missing_dotenv": _fix_missing_dotenv,
    "env_not_gitignored": _fix_env_not_gitignored,
    "missing_init": _fix_missing_init,
    "hidden_pollution": _fix_hidden_pollution,
    "no_manifest": _fix_no_manifest,
}
