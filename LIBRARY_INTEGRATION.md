# Integrating pfix with Your Python Library

This guide shows how to add pfix auto-healing capabilities to your own Python libraries.

## Quick Setup (One Command)

**Install pfix and enable auto-activation:**

```bash
# 1. Install pfix
pip install pfix

# 2. Enable auto-activation for your venv
pfix enable

# 3. Add config to pyproject.toml
echo '
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
' >> pyproject.toml

# 4. Done! Now ALL Python scripts auto-fix errors
python your_script.py  # No import needed!
```

## How It Works

After `pfix enable`, a `.pth` file is installed in your venv's site-packages. This file:
- Runs automatically when Python starts
- Detects `pyproject.toml` or `.env` configuration
- Installs pfix hooks if configured
- Works for ALL scripts without `import pfix`

## Configuration Files

**pyproject.toml** (behavior settings, committed to git):
```toml
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
max_retries = 3
create_backups = false
git_auto_commit = false
```

**.env** (API keys, NOT committed):
```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

## Disabling Auto-Activation

```bash
# Temporary (per session)
export PFIX_DISABLE_AUTO=true
python your_script.py

# Permanent (uninstall)
rm $(python -c "import site; print(site.getsitepackages()[0])")/pfix_auto.pth
```

## Recommended: Full Setup

### 1. Add pfix as Optional Dependency

**pyproject.toml:**
```toml
[project]
name = "your-library"
version = "1.0.0"
dependencies = []

[project.optional-dependencies]
dev = [
    "pfix>=0.1.19",
    # ... other dev deps
]
all = ["your-library[pfix]"]
```

### 2. Create Configuration Files

**pyproject.toml** (behavior settings, committed to git):
```toml
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = false       # Ask before fixing in production
auto_install_deps = true
auto_restart = false     # Don't restart library code
max_retries = 3
create_backups = true
git_auto_commit = false
```

**.env.example** (API keys template, committed):
```bash
# Copy to .env and fill in your key
OPENROUTER_API_KEY=sk-or-v1-...
# Or for local models:
# PFIX_MODEL=ollama/codellama:7b
# PFIX_API_BASE=http://localhost:11434
```

**.gitignore**:
```gitignore
.env
.pfix_backups/
```

### 3. Add Development Entry Point

**your_library/__init__.py:**
```python
"""Your library with optional pfix integration."""

__version__ = "1.0.0"

# Auto-activate pfix if installed and configured
try:
    import pfix
except ImportError:
    pass  # pfix not installed, that's fine
```

### 4. Create Development Scripts

**scripts/dev-mode.py:**
```python
#!/usr/bin/env python3
"""Run your library with pfix auto-healing enabled."""

import os
import sys

# Ensure pfix is installed
try:
    import pfix
except ImportError:
    print("Installing pfix...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pfix"])
    import pfix

# Configure for development
from pfix import configure
configure(
    auto_apply=True,
    auto_restart=False,  # Libraries shouldn't restart
    create_backups=True,
)

# Run your code
from your_library import main
main()
```

**scripts/pfix-cli:**
```bash
#!/bin/bash
# CLI wrapper for running code with pfix

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate venv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Install pfix if needed
python -c "import pfix" 2>/dev/null || pip install pfix

# Run with pfix enabled
export PFIX_ENABLED=true
export PFIX_AUTO_APPLY=true
python "$@"
```

Make it executable:
```bash
chmod +x scripts/pfix-cli
```

## Usage Patterns

### For Library Users (No Changes to Their Code)

User installs your library with pfix:
```bash
pip install your-library[pfix]
```

User creates `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_AUTO_APPLY=true
```

User's code just works:
```python
import your_library  # pfix auto-activates

your_library.do_something_risky()  # Auto-fixed on error!
```

### For Library Development (Testing)

```bash
# Run tests with auto-healing
pfix-cli -m pytest tests/

# Or use the dev script
python scripts/dev-mode.py
```

## Best Practices

### 1. Don't Force pfix on Users

Make it optional:
```toml
[project.optional-dependencies]
pfix = ["pfix>=0.1.19"]
```

Not required:
```toml
[project.dependencies]  # Don't put it here!
```

### 2. Respect User's Choice

In your library code:
```python
try:
    import pfix
    # pfix will only auto-activate if user has PFIX_AUTO_APPLY=true
except ImportError:
    pass  # User doesn't want pfix, respect that
```

### 3. Provide Clear Documentation

Add to your README:

```markdown
## Auto-Healing Mode (Optional)

Install with pfix support:
```bash
pip install your-library[pfix]
```

Create `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_AUTO_APPLY=true
```

Now any errors are automatically diagnosed and fixed!
```

### 4. CI/CD Integration

Add to your CI config:

**.github/workflows/test.yml:**
```yaml
- name: Test with pfix
  run: |
    pip install your-library[pfix]
    # Run with dry-run to catch issues
    PFIX_DRY_RUN=true python -m your_library.tests
```

## Configuration Templates

### Template 1: Research/Experimentation (Aggressive)

```toml
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
max_retries = 5
create_backups = true
```

### Template 2: Production Library (Conservative)

```toml
[tool.pfix]
model = "openrouter/anthropic/claude-haiku-4"  # Cheaper
auto_apply = false      # Ask before fixing
auto_install_deps = false  # Don't auto-install in prod
auto_restart = false
create_backups = true
max_retries = 1
```

### Template 3: Local Development (Free)

```toml
[tool.pfix]
model = "ollama/codellama:7b"
auto_apply = true
auto_install_deps = true
auto_restart = false
create_backups = true
```

## Testing Your Integration

Create `tests/test_pfix_integration.py`:

```python
"""Test pfix integration works correctly."""

import pytest


def test_pfix_imports():
    """Ensure pfix can be imported."""
    try:
        import pfix
        assert hasattr(pfix, 'pfix')
    except ImportError:
        pytest.skip("pfix not installed")


def test_auto_healing_disabled_by_default():
    """Ensure pfix doesn't auto-activate without user config."""
    import os
    # PFIX_ENABLED should not be set by library
    assert os.getenv('PFIX_ENABLED') is None or os.getenv('PFIX_AUTO_APPLY') is None


def test_user_can_enable():
    """Ensure user can enable pfix via environment."""
    import os
    os.environ['PFIX_ENABLED'] = 'true'
    os.environ['PFIX_AUTO_APPLY'] = 'true'
    
    try:
        import pfix
        config = pfix.get_config()
        assert config.enabled is True
    finally:
        del os.environ['PFIX_ENABLED']
        del os.environ['PFIX_AUTO_APPLY']
```

## Common Issues

### Issue: "pfix activates when I don't want it"

**Solution:** Only import pfix in development entry points, not in `__init__.py`:

```python
# your_library/__init__.py
# DON'T: import pfix here

# your_library/__main__.py
if __name__ == "__main__":
    import pfix  # Only for CLI usage
    from your_library import cli
    cli.main()
```

### Issue: "Backups filling up disk"

**Solution:** Add cleanup to your .env or pyproject.toml:

```toml
[tool.pfix]
create_backups = false  # Or clean periodically
```

Or add to your CI:
```bash
rm -rf .pfix_backups/
```

### Issue: "Tests fail because pfix modifies code"

**Solution:** Disable pfix in test config:

```toml
# pyproject.toml
[tool.pfix]
enabled = false
```

Or use pytest fixture:
```python
@pytest.fixture(autouse=True)
def disable_pfix(monkeypatch):
    monkeypatch.setenv('PFIX_ENABLED', 'false')
```

## Summary Checklist

- [ ] Add `pfix` to `[project.optional-dependencies]`
- [ ] Create `[tool.pfix]` section in `pyproject.toml`
- [ ] Create `.env.example` template
- [ ] Add `.pfix_backups/` to `.gitignore`
- [ ] Add optional `import pfix` in entry points
- [ ] Document in README how to enable
- [ ] Test integration works
- [ ] Consider providing `pfix-cli` wrapper script

## Example: Complete Library Setup

See `examples/complex_demo/` in pfix repository for a working example with:
- `pyproject.toml` configuration
- `.env.example` for API keys
- `pfix-python` wrapper script
- Zero-import usage pattern

## Dependency Development Mode (Fix Errors in Libraries)

Enable auto-fixing of errors in your dependencies (site-packages):

### Quick Setup

**.env:**
```bash
PFIX_DEV_MODE=true
PFIX_AUTO_APPLY=true
OPENROUTER_API_KEY=sk-or-v1-...
```

**In your code:**
```python
from pfix.dev_mode import install_dev_mode_hook
install_dev_mode_hook()

# Now any error in pandas, requests, numpy, etc. will be auto-fixed!
import pandas as pd
df = pd.read_csv("data.csv")  # If this fails, pandas code will be fixed!
```

### Global venv Hook (Recommended)

Create `venv/lib/python3.x/site-packages/sitecustomize.py`:
```python
"""Auto-enable pfix dev mode for entire virtual environment."""
import os
os.environ['PFIX_DEV_MODE'] = 'true'
os.environ['PFIX_AUTO_APPLY'] = 'true'

try:
    from pfix.dev_mode import install_dev_mode_hook
    install_dev_mode_hook()
    print("[pfix-dev] Development mode active - dependencies will be auto-fixed")
except ImportError:
    pass
```

Now ALL Python scripts in this venv automatically fix dependency errors!

### How It Works

1. Hooks into Python's import system (`sys.meta_path`)
2. Wraps all functions from site-packages with error handlers
3. Catches exceptions and applies LLM fixes to dependency source code
4. Creates backups before modifying installed packages
5. Retries the function call with fixed code

### Use Cases

- **Patching buggy libraries** until upstream fixes them
- **Testing fixes** before submitting PRs to open source projects  
- **Development speed** - don't get blocked by dependency issues
- **Legacy code** - fix old unmaintained packages

### Warning

⚠️ **Only use in development!** Never use in production as it modifies installed packages.
