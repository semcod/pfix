"""
pfix.dependency — Dependency resolution with pip/uv + pipreqs scanning.

Features:
- Auto-detect uv for faster installs
- pipreqs-based project import scanning
- Module→PyPI name mapping (cv2→opencv-python etc.)
- requirements.txt / pyproject.toml updater
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from .config import get_config

console = Console(stderr=True)

# Module name → PyPI package name (when they differ)
MODULE_TO_PACKAGE: dict[str, str] = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "attr": "attrs",
    "dotenv": "python-dotenv",
    "gi": "PyGObject",
    "serial": "pyserial",
    "usb": "pyusb",
    "Crypto": "pycryptodome",
    "jose": "python-jose",
    "jwt": "PyJWT",
    "magic": "python-magic",
    "dateutil": "python-dateutil",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "lxml": "lxml",
    "wx": "wxPython",
    "tomli": "tomli",
    "git": "gitpython",
    "mcp": "mcp",
    "httpx": "httpx",
    "uvicorn": "uvicorn",
}


def resolve_package_name(module_name: str) -> str:
    """Map Python module name → PyPI package name."""
    top_level = module_name.split(".")[0]
    return MODULE_TO_PACKAGE.get(top_level, top_level)


def is_module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def install_packages(packages: list[str], dry_run: bool = False) -> dict[str, bool]:
    """Install packages via pip or uv. Returns {package: success}."""
    config = get_config()
    results = {}

    if not config.auto_install_deps and not dry_run:
        console.print("[yellow]⚠ Auto-install disabled. Set PFIX_AUTO_INSTALL_DEPS=true[/]")
        return {pkg: False for pkg in packages}

    for pkg in packages:
        if dry_run:
            console.print(f"[dim]  DRY RUN: would install {pkg}[/]")
            results[pkg] = True
            continue

        console.print(f"[cyan]📦 Installing {pkg} (via {config.pkg_manager})...[/]")
        try:
            if config.pkg_manager == "uv":
                cmd = ["uv", "pip", "install", pkg]
            else:
                cmd = [sys.executable, "-m", "pip", "install", pkg, "--quiet"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                console.print(f"[green]  ✓ Installed {pkg}[/]")
                results[pkg] = True
            else:
                console.print(f"[red]  ✗ Failed: {result.stderr.strip()[:200]}[/]")
                results[pkg] = False
        except subprocess.TimeoutExpired:
            console.print(f"[red]  ✗ Timeout installing {pkg}[/]")
            results[pkg] = False
        except FileNotFoundError:
            # uv not found, fallback to pip
            if config.pkg_manager == "uv":
                console.print("[yellow]  uv not found, falling back to pip[/]")
                config.pkg_manager = "pip"
                return install_packages([pkg], dry_run)
            results[pkg] = False
        except Exception as e:
            console.print(f"[red]  ✗ Error: {e}[/]")
            results[pkg] = False

    return results


def scan_project_deps(project_dir: Optional[Path] = None) -> dict:
    """Use pipreqs to scan project for all imports and find missing ones.

    Returns: {"all_imports": [...], "missing": [...], "installed": [...]}
    """
    if project_dir is None:
        project_dir = get_config().project_root

    result = {"all_imports": [], "missing": [], "installed": []}

    try:
        from pipreqs import pipreqs

        all_imports = pipreqs.get_all_imports(str(project_dir))
        result["all_imports"] = list(all_imports)

        # Check which are installed
        stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()
        for imp in all_imports:
            top = imp.split(".")[0]
            if top in stdlib or top in sys.builtin_module_names:
                continue
            if is_module_available(top):
                result["installed"].append(top)
            else:
                result["missing"].append(resolve_package_name(top))
    except Exception:
        pass

    return result


def update_requirements_file(
    packages: list[str],
    requirements_path: Optional[Path] = None,
) -> bool:
    """Append packages to requirements.txt."""
    if requirements_path is None:
        requirements_path = get_config().project_root / "requirements.txt"

    existing: set[str] = set()
    if requirements_path.exists():
        for line in requirements_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                name = re.split(r"[=<>~!]", line)[0].strip()
                existing.add(name.lower())

    new = [p for p in packages if re.split(r"[=<>~!]", p)[0].lower() not in existing]
    if not new:
        return False

    with open(requirements_path, "a") as f:
        f.write("\n# Added by pfix\n")
        for pkg in new:
            f.write(f"{pkg}\n")

    console.print(f"[green]📝 Updated {requirements_path}: {', '.join(new)}[/]")
    return True


def generate_requirements(project_dir: Optional[Path] = None) -> Path:
    """Generate requirements.txt via pipreqs for the project."""
    if project_dir is None:
        project_dir = get_config().project_root

    output = project_dir / "requirements.txt"
    try:
        from pipreqs import pipreqs

        imports = pipreqs.get_all_imports(str(project_dir))
        pkg_names = pipreqs.get_pkg_names(imports)
        pipreqs.generate_requirements_file(output, pkg_names)
        console.print(f"[green]📝 Generated {output}[/]")
    except Exception as e:
        console.print(f"[yellow]⚠ pipreqs failed: {e}[/]")

    return output


def detect_missing_from_error(exception_message: str) -> Optional[str]:
    """Extract module name from ModuleNotFoundError/ImportError."""
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", exception_message)
    if match:
        return match.group(1)
    match = re.search(r"cannot import name .+ from ['\"]([^'\"]+)['\"]", exception_message)
    if match:
        return match.group(1)
    return None
