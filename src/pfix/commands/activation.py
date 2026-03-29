from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_enable(args=None) -> int:
    """Enable pfix auto-activation and add config to pyproject.toml. CC≤5."""
    site_packages = _find_site_packages()
    if not site_packages:
        console.print("[red]✗ Cannot find site-packages directory[/]")
        return 1

    # Install .pth file
    import pfix
    pfix_pkg = Path(pfix.__file__).parent
    _install_pth_file(pfix_pkg, site_packages)
    
    # Configure pyproject.toml
    pyproject_path = Path.cwd() / "pyproject.toml"
    config_added = _ensure_project_config(pyproject_path)
    
    _print_enable_summary(config_added)
    return 0


def _find_site_packages() -> Optional[Path]:
    """Locate the active site-packages directory."""
    import site
    packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not packages or not packages.exists():
        packages = Path(site.getusersitepackages())
    return packages if packages and packages.exists() else None


def _install_pth_file(pfix_pkg: Path, site_packages: Path):
    """Copy the auto_activate.pth to site-packages."""
    source = pfix_pkg / "auto_activate.pth"
    dest = site_packages / "pfix_auto.pth"

    if not source.exists():
        console.print(f"[yellow]⚠ Source file not found: {source}[/]")
        return

    try:
        shutil.copy2(source, dest)
        console.print(f"[green]✓ pfix auto-activation enabled[/]")
        console.print(f"[dim]  Installed: {dest}[/]")
    except Exception as e:
        console.print(f"[red]✗ Failed to install .pth file: {e}[/]")


def _ensure_project_config(path: Path) -> bool:
    """Ensure pfix configuration exists in pyproject.toml."""
    if path.exists():
        return _update_existing_pyproject(path)
    return _create_new_pyproject(path)


def _update_existing_pyproject(path: Path) -> bool:
    """Add [tool.pfix] to existing pyproject.toml if missing."""
    try:
        content = path.read_text()
        if "[tool.pfix]" in content:
            console.print(f"[dim]  [tool.pfix] already exists in {path}[/]")
            return False

        config_block = '\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'
        with open(path, "a") as f:
            f.write(config_block)
        console.print(f"[green]✓ Added [tool.pfix] to {path}[/]")
        return True
    except Exception as e:
        console.print(f"[yellow]⚠ Could not update {path}: {e}[/]")
        return False


def _create_new_pyproject(path: Path) -> bool:
    """Create a minimal pyproject.toml with pfix config."""
    try:
        config_block = '[build-system]\nrequires = ["setuptools>=61"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "my-project"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'
        path.write_text(config_block)
        console.print(f"[green]✓ Created {path} with pfix config[/]")
        return True
    except Exception as e:
        console.print(f"[yellow]⚠ Could not create {path}: {e}[/]")
        return False


def _print_enable_summary(config_added: bool):
    """Print success message and next steps."""
    console.print()
    console.print("[cyan]✓ pfix is now enabled![/]")
    console.print()
    if config_added:
        console.print("[dim]Configuration added to pyproject.toml.[/]")
        console.print("[dim]Add your API key:[/]")
        console.print('  echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env')
    else:
        console.print("[dim]Edit pyproject.toml to customize settings.[/]")
    console.print()
    console.print("[dim]Run: python your_script.py (no import needed!)[/]")
    console.print()
    console.print("[dim]To disable: pfix disable[/]")


def cmd_disable(args=None) -> int:
    """Disable pfix auto-activation."""
    import site

    # Find site-packages directory
    site_packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not site_packages:
        site_packages = Path(site.getusersitepackages())

    if not site_packages or not site_packages.exists():
        console.print("[red]✗ Cannot find site-packages directory[/]")
        return 1

    # Remove .pth file
    dest_file = site_packages / "pfix_auto.pth"

    if dest_file.exists():
        try:
            dest_file.unlink()
            console.print(f"[green]✓ pfix auto-activation disabled[/]")
            console.print(f"[dim]  Removed: {dest_file}[/]")
            console.print()
            console.print("[dim]pfix will no longer auto-activate.[/]")
            console.print("[dim]To re-enable: pfix enable[/]")
            return 0
        except Exception as e:
            console.print(f"[red]✗ Failed to disable: {e}[/]")
            return 1
    else:
        console.print("[yellow]⚠ pfix auto-activation was not enabled[/]")
        return 0
