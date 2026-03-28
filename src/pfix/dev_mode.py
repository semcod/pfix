"""
pfix Dependency Development Mode

Automatically catch and fix errors in installed dependencies during development.

Usage:
    1. Create .env in your project:
       PFIX_DEV_MODE=true
       PFIX_AUTO_APPLY=true
       OPENROUTER_API_KEY=sk-or-v1-...
    
    2. Run your code normally:
       python your_script.py
    
    3. Any error in site-packages will be caught and fixed!

How it works:
    - Hooks into Python's import system (sys.meta_path)
    - Wraps all imports from site-packages with error handling
    - Automatically applies fixes to dependency source code
    - Creates backups before modifying
"""

import sys
import os
from pathlib import Path
from types import ModuleType
from typing import Any


def is_site_package(module: ModuleType) -> bool:
    """Check if module is from site-packages (third-party)."""
    try:
        module_file = getattr(module, '__file__', None)
        if not module_file:
            return False
        return 'site-packages' in module_file or 'dist-packages' in module_file
    except Exception:
        return False


def wrap_module_functions(module: ModuleType):
    """Wrap all callable attributes of a module with error handling."""
    for attr_name in dir(module):
        if attr_name.startswith('_'):
            continue
        
        try:
            attr = getattr(module, attr_name)
            if callable(attr) and not isinstance(attr, (type, ModuleType)):
                setattr(module, attr_name, _create_wrapper(attr, module.__name__))
        except Exception:
            pass


def _create_wrapper(func, module_name: str):
    """Create a wrapper that catches errors and triggers pfix."""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Only handle if pfix is available and dev mode enabled
            if os.getenv('PFIX_DEV_MODE', '').lower() != 'true':
                raise
            
            try:
                import pfix
                from pfix.analyzer import analyze_exception
                from pfix.llm import request_fix
                from pfix.fixer import apply_fix
                
                print(f"\n[dev-mode] 💥 Caught error in {module_name}.{func.__name__}: {e}")
                print(f"[dev-mode] Attempting auto-fix...")
                
                # Build context for fix
                ctx = analyze_exception(e, hints={
                    'module': module_name,
                    'function': func.__name__,
                    'is_dependency': True,
                })
                
                proposal = request_fix(ctx)
                if proposal.confidence > 0.1:
                    from pfix.config import get_config
                    config = get_config()
                    old_auto = config.auto_apply
                    config.auto_apply = True
                    
                    fixed = apply_fix(ctx, proposal, confirm=False)
                    config.auto_apply = old_auto
                    
                    if fixed:
                        print(f"[dev-mode] ✓ Fix applied! Retrying...")
                        # Retry the function call with fixed code
                        return func(*args, **kwargs)
                    else:
                        print(f"[dev-mode] ⚠ Fix not applied")
                else:
                    print(f"[dev-mode] ⚠ Confidence too low ({proposal.confidence:.0%})")
                
            except ImportError:
                pass  # pfix not installed
            except Exception as fix_error:
                print(f"[dev-mode] ⚠ Fix failed: {fix_error}")
            
            raise  # Re-raise original error
    
    return wrapper


def install_dev_mode_hook():
    """Install the development mode import hook."""
    if os.getenv('PFIX_DEV_MODE', '').lower() != 'true':
        return
    
    try:
        import pfix
    except ImportError:
        print("[dev-mode] ⚠ pfix not installed, run: pip install pfix")
        return
    
    class DevModeFinder:
        """Meta path finder that wraps modules from site-packages."""
        
        def find_module(self, fullname: str, path=None):
            return None  # We don't find modules, just wrap them
        
        def find_spec(self, fullname: str, path, target=None):
            return None
    
    class DevModeLoader:
        """Loader that wraps loaded modules."""
        pass
    
    # Install post-import hook
    original_import = __builtins__.__import__
    
    def dev_mode_import(name, *args, **kwargs):
        module = original_import(name, *args, **kwargs)
        
        # Only wrap site-packages modules
        if isinstance(module, ModuleType) and is_site_package(module):
            wrap_module_functions(module)
        
        return module
    
    __builtins__.__import__ = dev_mode_import
    
    print("[dev-mode] ✓ pfix development mode active")
    print("[dev-mode]   Errors in dependencies will be auto-fixed")


# Auto-install if env var is set
if os.getenv('PFIX_DEV_MODE', '').lower() == 'true':
    install_dev_mode_hook()
