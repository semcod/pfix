# 🔧 pfix

[![PyPI version](https://badge.fury.io/py/pfix.svg)](https://pypi.org/project/pfix/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

**Self-healing Python** — catches runtime errors and fixes source code + dependencies via LLM + MCP.

> 💡 **New in 0.1.5**: Zero-configuration mode! Just `import pfix` with `PFIX_AUTO_APPLY=true` in `.env` and any exception triggers automatic repair.

## Features

- **Zero-config mode** — `import pfix` + `.env` = auto-healing for entire project
- **`@pfix` decorator** — wrap any function; errors trigger automatic repair
- **Fast dep fix** — `ModuleNotFoundError` → instant `pip`/`uv install` (no LLM call)
- **pipreqs scanning** — project-wide import analysis for missing dependencies
- **LLM code repair** — sends error context to LLM (OpenRouter/LiteLLM) for intelligent fixes
- **pip + uv** — auto-detects `uv` for faster installs, falls back to `pip`
- **MCP server** — `@mcp.tool()` via FastMCP for IDE integration (Claude Code, Cursor, VS Code)
- **Git auto-commit** — optional auto-commit of fixes with configurable prefix
- **Auto-restart** — `os.execv` process restart after fix applied
- **Interactive diff** — unified diff with confirmation before applying
- **Backup system** — timestamped backups in `.pfix_backups/` (can be disabled)
- **Async support** — `@apfix` for async functions

## Installation

```bash
pip install pfix

# With MCP server support
pip install pfix[mcp]

# With git auto-commit
pip install pfix[git]

# Everything
pip install pfix[all]
```

## Quick Start (3 Ways)

### Option 1: Zero Configuration (Recommended)

Just `import pfix` with `PFIX_AUTO_APPLY=true` in your `.env`:

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_AUTO_APPLY=true
```

```python
# your_script.py
import pfix  # Auto-activates global exception hook

def buggy_function(x):
    return 1 / x  # Division by zero? Auto-fixed!

buggy_function(0)  # pfix catches, analyzes, fixes, and retries
```

**What happens:**
1. Exception is caught by global hook
2. LLM analyzes the error context
3. Fix is applied to source file
4. Process restarts (if `PFIX_AUTO_RESTART=true`)

### Option 2: Explicit Session Control

Use `pfix_session` for fine-grained control:

```python
from pfix import configure, pfix_session

configure(auto_apply=True, dry_run=False)

def process_data(data):
    return data[0] / data[1]  # Might fail

with pfix_session(__file__, auto_apply=True):
    result = process_data([1, 0])  # Auto-fixed on error
    print(f"Result: {result}")
```

### Option 3: Decorator (Per-Function)

Use `@pfix` for function-level control:

```python
from pfix import pfix

@pfix(retries=3, hint="Processes CSV files")
def analyze_csv(path):
    import pandas as pd  # Auto-installed if missing
    df = pd.read_csv(path)
    return df.groupby("category").sum()

@pfix(deps=["requests", "python-dateutil"])
def fetch_events(url: str):
    import requests
    from dateutil.parser import parse
    return [parse(e["ts"]) for e in requests.get(url).json()["events"]]
```

## Usage Patterns

### Pattern A: Development Mode (Interactive)

```python
from pfix import configure

# Ask before applying fixes
configure(auto_apply=False)

import pfix  # Hook installed

def risky_operation():
    return undefined_variable  # NameError

risky_operation()  # Shows diff, asks for confirmation
```

### Pattern B: CI/CD Mode (Non-Interactive)

```python
from pfix import configure

# Auto-apply everything, dry run for safety
configure(auto_apply=True, dry_run=True, create_backups=False)

import pfix
```

### Pattern C: Library Mode (Specific Functions)

```python
from pfix import pfix, pfix_session

# Only protect specific functions
@pfix(auto_apply=True)
def unstable_api_call():
    ...

# Or specific code blocks
with pfix_session(__file__):
    untrusted_code()
```

## Library Behavior

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Code                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐   │
│  │ Zero Config     │ or │ Session Block   │ or │ @pfix Decor │   │
│  │ import pfix     │    │ with pfix_session│   │ @pfix       │   │
│  └────────┬────────┘    └────────┬────────┘    └──────┬────┘   │
│           │                        │                    │        │
│           └────────────────────────┴────────────────────┘        │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Exception Occurs                                        │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │ 1. ModuleNotFoundError?                            │ │   │
│  │  │    → pip/uv install → retry                          │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                          │                             │   │
│  │                          ▼                             │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │ 2. Build ErrorContext                              │ │   │
│  │  │    - Traceback                                       │ │   │
│  │  │    - Source code                                     │ │   │
│  │  │    - Local variables                                 │ │   │
│  │  │    - File imports                                    │ │   │
│  │  │    - pipreqs scan                                    │ │   │
│  │  └────────────────┬───────────────────────────────────┘ │   │
│  │                   │                                       │   │
│  │                   ▼                                       │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ 3. LLM Analysis (LiteLLM → OpenRouter)            │   │   │
│  │  │    - Diagnosis                                     │   │   │
│  │  │    - Fix proposal                                  │   │   │
│  │  │    - Confidence score                              │   │   │
│  │  └────────────────┬───────────────────────────────────┘   │   │
│  │                   │                                       │   │
│  │                   ▼                                       │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ 4. Apply Fix (if confidence > 0.1)               │   │   │
│  │  │    - Show diff (or auto-apply)                     │   │   │
│  │  │    - Create backup (if create_backups=True)        │   │   │
│  │  │    - Write fixed code                              │   │   │
│  │  │    - Git commit (if git_auto_commit=True)          │   │   │
│  │  └────────────────┬───────────────────────────────────┘   │   │
│  │                   │                                       │   │
│  │                   ▼                                       │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ 5. Recovery                                        │   │   │
│  │  │    - Reload module → retry                         │   │   │
│  │  │    - or os.execv restart                           │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Error Types & Fixes

| Error Type | Auto-Fix Strategy | Example Fix |
|------------|-------------------|-------------|
| `ModuleNotFoundError` | pip/uv install | `pip install requests` |
| `NameError` | Add import | `import os` at top |
| `TypeError` | Type conversion | `str(age)` instead of `age` |
| `AttributeError` | Fix attribute access | `obj.get()` instead of `obj.attr` |
| `ZeroDivisionError` | Add guard clause | `if x == 0: return 0` |
| `IndexError` | Bounds checking | `if i < len(list):` |
| `KeyError` | Safe dict access | `dict.get(key, default)` |
| `ValueError` | Input validation | Try/except or validation |
| `FileNotFoundError` | Check path existence | `if os.path.exists():` |

### Confidence Thresholds

- **> 90%**: High confidence fixes (type conversions, simple guards)
- **50-90%**: Medium confidence (logic changes, API adjustments)
- **10-50%**: Low confidence (complex refactorings)
- **< 10%**: Skipped (manual review recommended)


## CLI

```bash
pfix run script.py              # Run with global exception hook
pfix run script.py --auto       # Auto-apply fixes
pfix run script.py --restart    # Restart process after fix
pfix check                      # Show config status
pfix deps scan                  # Scan for missing deps (pipreqs)
pfix deps install               # Install all missing deps
pfix deps generate              # Generate requirements.txt
pfix server                     # Start MCP server (stdio)
pfix server --http 3001         # Start MCP server (HTTP)
```

## MCP Integration

pfix exposes tools via FastMCP for IDE integration:

| Tool | Description |
|---|---|
| `pfix_analyze` | Analyze error → diagnosis + fix proposal |
| `pfix_fix` | Analyze + apply fix (with backup) |
| `pfix_deps_scan` | Scan for missing deps |
| `pfix_deps_install` | Install a package |
| `pfix_deps_generate` | Generate requirements.txt |
| `pfix_edit_file` | Write file content |

### Claude Code / VS Code setup

Add to your MCP config (`.claude/mcp.json` or VS Code settings):

```json
{
  "mcpServers": {
    "pfix": {
      "command": "python",
      "args": ["-m", "pfix.mcp_server"]
    }
  }
}
```

## Configuration

### .env

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | **Required** — OpenRouter API key |
| `PFIX_MODEL` | `openrouter/anthropic/claude-sonnet-4` | LLM model to use |
| `PFIX_AUTO_APPLY` | `false` | Auto-apply fixes without confirmation |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | Auto-install missing dependencies |
| `PFIX_AUTO_RESTART` | `false` | Restart process after fix applied |
| `PFIX_MAX_RETRIES` | `3` | Max fix attempts per error |
| `PFIX_DRY_RUN` | `false` | Show proposed fixes without applying |
| `PFIX_CREATE_BACKUPS` | `true` | Create `.pfix_backups/` before fixing |
| `PFIX_PKG_MANAGER` | auto | `pip` or `uv` (auto-detected) |
| `PFIX_GIT_COMMIT` | `false` | Auto-commit fixes to git |
| `PFIX_GIT_PREFIX` | `pfix: ` | Git commit message prefix |
| `PFIX_MCP_ENABLED` | `false` | Enable MCP server |
| `PFIX_MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `PFIX_ENABLED` | `true` | Master switch to disable pfix |

### pyproject.toml

```toml
[tool.pfix]
model = "openrouter/anthropic/claude-sonnet-4"
auto_apply = true
auto_install_deps = true
max_retries = 3
create_backups = false
git_auto_commit = true
git_prefix = "fix: "
```

### Programmatic

```python
from pfix import configure

configure(
    auto_apply=True,
    dry_run=False,
    pkg_manager="uv",
    create_backups=False,
    git_auto_commit=True,
    max_retries=5,
)
```

## Advanced Usage

### Custom Error Handlers

```python
from pfix import pfix

def log_error(exc):
    with open("errors.log", "a") as f:
        f.write(f"{type(exc).__name__}: {exc}\n")

@pfix(on_error=log_error, retries=3)
def risky_operation():
    ...
```

### Async Support

```python
from pfix import apfix

@apfix(auto_apply=True)
async def fetch_data(url):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Session with Custom Config

```python
from pfix import pfix_session, get_config

config = get_config()
config.llm_model = "openrouter/anthropic/claude-opus-4"
config.llm_temperature = 0.1

with pfix_session(__file__, auto_apply=True, restart=True):
    main()
```

## Examples

See [`examples/`](examples/) directory for working examples:

- [`demo_auto.py`](examples/demo_auto.py) — Zero-config auto-healing
- [`demo.py`](examples/demo.py) — Explicit session control
- [`README.md`](examples/README.md) — Examples documentation

## Best Practices

1. **Start with `PFIX_AUTO_APPLY=false`** to review fixes before applying
2. **Enable backups** (`PFIX_CREATE_BACKUPS=true`) in development
3. **Use dry-run mode** in CI/CD to preview fixes without applying
4. **Set `PFIX_AUTO_RESTART=true`** for long-running processes
5. **Add hints** to decorators for better LLM context: `@pfix(hint="Processes CSV files")`

## Troubleshooting

### "LLM confidence too low"
- Increase context with `@pfix(hint="...")`
- Check your API key is valid
- Try a different model in `PFIX_MODEL`

### "Could not locate function"
- Ensure the error is in a named function (not `lambda` or `exec`)
- Use `pfix_session` for module-level code

### Backups filling up disk
- Set `PFIX_CREATE_BACKUPS=false`
- Clean `.pfix_backups/` periodically: `rm -rf .pfix_backups/`

### Too many restarts
- Set `PFIX_MAX_RETRIES=1` to limit attempts
- Use `PFIX_AUTO_RESTART=false` to disable restarts

## Dependencies

| Package | Role |
|---------|------|
| `litellm` | LLM proxy — OpenRouter, OpenAI, Anthropic, Ollama |
| `python-dotenv` | Load `.env` configuration |
| `rich` | Terminal UI (diffs, panels, tables) |
| `pipreqs` | Project import scanning |
| `pathspec` | Gitignore-aware file filtering |
| `mcp` | FastMCP server (optional) |
| `gitpython` | Git auto-commit (optional) |
| `watchdog` | File change watching (optional) |

## License

Licensed under Apache-2.0.


Licensed under Apache-2.0.


Licensed under Apache-2.0.


Apache 2.0 — Tom Sapletta / Softreck
