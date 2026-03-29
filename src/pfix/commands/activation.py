from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_enable() -> int:
    """Enable pfix auto-activation and add config to pyproject.toml."""
    import site

    # Find pfix package location
    import pfix
    pfix_pkg = Path(pfix.__file__).parent

    # Find site-packages directory
    site_packages = Path(site.getsitepackages()[0]) if site.getsitepackages() else None
    if not site_packages:
        site_packages = Path(site.getusersitepackages())

    if not site_packages or not site_packages.exists():
        console.print("[red]✗ Cannot find site-packages directory[/]")
        return 1

    # Install .pth file for auto-activation
    source_file = pfix_pkg / "auto_activate.pth"
    dest_file = site_packages / "pfix_auto.pth"

    if source_file.exists():
        try:
            shutil.copy2(source_file, dest_file)
            console.print(f"[green]✓ pfix auto-activation enabled[/]")
            console.print(f"[dim]  Installed: {dest_file}[/]")
        except Exception as e:
            console.print(f"[red]✗ Failed to install .pth file: {e}[/]")
            return 1
    else:
        console.print(f"[yellow]⚠ Source file not found: {source_file}[/]")
    
    # 2. Add config to pyproject.toml if it exists
    pyproject = Path.cwd() / "pyproject.toml"
    config_added = False
    
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.pfix]" not in content:
                # Append config to existing pyproject.toml
                config_block = '''\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'''
                with open(pyproject, "a") as f:
                    f.write(config_block)
                console.print(f"[green]✓ Added [tool.pfix] to {pyproject}[/]")
                config_added = True
            else:
                console.print(f"[dim]  [tool.pfix] already exists in {pyproject}[/]")
        except Exception as e:
            console.print(f"[yellow]⚠ Could not update {pyproject}: {e}[/]")
    else:
        # Create new pyproject.toml
        try:
            config_block = '''[build-system]\nrequires = ["setuptools>=61"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "my-project"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n\n[tool.pfix]\nmodel = "openrouter/qwen/qwen3-coder-next"\nauto_apply = true\nauto_install_deps = true\nauto_restart = true\nmax_retries = 3\ncreate_backups = false\n'''
            pyproject.write_text(config_block)
            console.print(f"[green]✓ Created {pyproject} with pfix config[/]")
            config_added = True
        except Exception as e:
            console.print(f"[yellow]⚠ Could not create {pyproject}: {e}[/]")
    
    # Summary
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
    return 0


def cmd_disable() -> int:
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
