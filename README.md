# 🔧 pfix

[![PyPI version](https://badge.fury.io/py/pfix.svg)](https://pypi.org/project/pfix/)
[![PyPI downloads](https://img.shields.io/pypi/dm/pfix.svg)](https://pypi.org/project/pfix/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linter-ruff-purple.svg)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen.svg)](https://pre-commit.com/)
[![Tests: 56 examples](https://img.shields.io/badge/tests-56%20examples-blue)](examples/)
[![Docs](https://img.shields.io/badge/docs-available-brightgreen.svg)](docs/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.70-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$14.53-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-17.1h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $14.5287 (75 commits)
- 👤 **Human dev:** ~$1712 (17.1h @ $100/h, 30min dedup)

Generated on 2026-03-29 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



**Self-healing Python** — catches runtime errors and fixes source code + dependencies via LLM + MCP.

The strategy of using a small tool for detecting errors in a single library or file enables quick bug fixes before writing a prompt, since all context is contained in the error file. This offloads large and expensive models that should be used where smaller ones are insufficient—allowing them to plan and create strategy for the entire library instead of handling individual errors, like in test files.

This automation can also be leveraged via CI/GitOps with provided API keys to the LLM provider for fixing encountered errors during testing across the entire ecosystem.


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

### From PyPI (Users)

```bash
pip install pfix

# With MCP server support
pip install pfix[mcp]

# With git auto-commit
pip install pfix[git]

# Everything
pip install pfix[all]
```

### From Source (Developers)

Clone and install in editable mode:

```bash
git clone https://github.com/softreck/pfix.git
cd pfix
pip install -e .

# Or with all optional dependencies
pip install -e ".[all]"
```

**Editable mode** (`-e`) allows you to modify source code without reinstalling. Changes take effect immediately.

### Running Examples

After installation, examples can be run from any directory:

```bash
# From project root
cd /path/to/pfix/examples

# Run all examples with auto-reset (recommended for testing)
python run_all.py

# Run a single example category
cd types && python main.py
cd data && python main.py

# Reset all examples to original buggy state
python reset.py

# The .env file in project root is automatically found
```

**Example workflow:**
```bash
cd examples
python run_all.py              # Run all 12 categories, auto-reset at end
python run_all.py --dry-run      # Preview what would run
python run_all.py --no-reset     # Keep fixed versions for inspection
python reset.py                  # Manual reset when needed
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
pfix diagnose                   # Run environment diagnostics
pfix diagnose --category memory,filesystem  # Filter categories
pfix diagnose --fix             # Auto-fix what can be fixed
pfix diagnose --output TODO.md # Save to file
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
| `pfix_diagnose` | Run environment diagnostics |
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

pfix supports multiple configuration methods (in order of priority):
1. Environment variables (override everything)
2. `.env` file in project root
3. `pyproject.toml` `[tool.pfix]` section
4. `setup.cfg` `[pfix]` section
5. `setup.py` keyword arguments
6. Programmatic `configure()`

### Configuration Priority

Higher numbers win (environment variables have highest priority):

```
[6] Environment variables (PFIX_*)
[5] .env file
[4] pyproject.toml [tool.pfix]
[3] setup.cfg [pfix]
[2] setup.py setup()
[1] configure() programmatic
```

### Method 1: .env (Recommended for Development)

Create a `.env` file in your project root:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Behavior
PFIX_AUTO_APPLY=true              # Auto-apply fixes without confirmation
PFIX_AUTO_INSTALL_DEPS=true       # Auto-install missing dependencies
PFIX_AUTO_RESTART=true              # Restart process after fix
PFIX_MAX_RETRIES=3
PFIX_CREATE_BACKUPS=false           # Disable backups

# Optional
PFIX_MODEL=openrouter/qwen/qwen3-coder-next
PFIX_PKG_MANAGER=uv               # pip or uv
PFIX_GIT_COMMIT=false             # Auto-commit fixes
PFIX_GIT_PREFIX="pfix: "
```

**Note:** `.env` is searched from current working directory upward, so it works from any subdirectory (e.g., `examples/`).

### Method 2: pyproject.toml (Recommended for Projects)

Add to your `pyproject.toml`:

```toml
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
max_retries = 3
create_backups = false
git_auto_commit = false
git_commit_prefix = "pfix: "
enabled = true
dry_run = false
pkg_manager = "uv"  # auto, pip, or uv
mcp_enabled = false
mcp_transport = "stdio"
mcp_server_url = "http://localhost:3001"
```

**Benefits:**
- Version controlled with your project
- Works with any Python packaging tool
- No external files needed

### Method 3: setup.cfg (Legacy Projects)

For projects using `setup.cfg`:

```ini
[metadata]
name = myproject
version = 1.0.0
...

[pfix]
model = openrouter/qwen/qwen3-coder-next
auto_apply = true
auto_install_deps = true
auto_restart = false
max_retries = 3
create_backups = true
```

### Method 4: setup.py (Legacy Projects)

For projects using `setup.py`:

```python
from setuptools import setup

setup(
    name="myproject",
    version="1.0.0",
    # ... other setup args
    
    # pfix configuration
    pfix_model="openrouter/qwen/qwen3-coder-next",
    pfix_auto_apply=True,
    pfix_auto_install_deps=True,
    pfix_auto_restart=False,
    pfix_max_retries=3,
    pfix_create_backups=True,
    pfix_enabled=True,
)
```

**Note:** `setup.py` config requires pfix to be installed in the same environment.

### Method 5: Programmatic Configuration

Configure at runtime in your Python code:

```python
from pfix import configure

# Before importing pfix or using the hook
configure(
    # LLM settings
    llm_model="openrouter/qwen/qwen3-coder-next",
    llm_api_key="sk-or-v1-...",
    llm_temperature=0.2,
    llm_max_tokens=4096,
    
    # Behavior
    auto_apply=True,
    auto_install_deps=True,
    auto_restart=True,
    max_retries=3,
    enabled=True,
    dry_run=False,
    
    # Project
    pkg_manager="uv",
    create_backups=False,
    project_root="/path/to/project",
    
    # Git
    git_auto_commit=False,
    git_commit_prefix="pfix: ",
    
    # MCP
    mcp_enabled=False,
    mcp_transport="stdio",
)

# Now import pfix to activate with these settings
import pfix
```

### Configuration Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENROUTER_API_KEY` | `str` | — | **Required** — OpenRouter API key |
| `PFIX_MODEL` | `str` | `openrouter/qwen/qwen3-coder-next` | LLM model to use |
| `PFIX_API_BASE` | `str` | `https://openrouter.ai/api/v1` | API base URL |
| `PFIX_AUTO_APPLY` | `bool` | `false` | Auto-apply fixes without confirmation |
| `PFIX_AUTO_INSTALL_DEPS` | `bool` | `true` | Auto-install missing dependencies |
| `PFIX_AUTO_RESTART` | `bool` | `false` | Restart process after fix applied |
| `PFIX_MAX_RETRIES` | `int` | `3` | Max fix attempts per error |
| `PFIX_DRY_RUN` | `bool` | `false` | Show proposed fixes without applying |
| `PFIX_CREATE_BACKUPS` | `bool` | `true` | Create `.pfix_backups/` before fixing |
| `PFIX_ENABLED` | `bool` | `true` | Master switch to disable pfix |
| `PFIX_PKG_MANAGER` | `str` | auto | `pip`, `uv`, or auto-detected |
| `PFIX_GIT_COMMIT` | `bool` | `false` | Auto-commit fixes to git |
| `PFIX_GIT_PREFIX` | `str` | `pfix: ` | Git commit message prefix |
| `PFIX_MCP_ENABLED` | `bool` | `false` | Enable MCP server |
| `PFIX_MCP_TRANSPORT` | `str` | `stdio` | `stdio` or `http` |
| `PFIX_PROJECT_ROOT` | `str` | `.` | Project root for relative paths |

## LLM Models & Providers

pfix uses [LiteLLM](https://litellm.ai) to support multiple LLM providers. You can use cloud APIs or run models locally.

### OpenRouter (Cloud - Recommended)

OpenRouter provides access to multiple models with a single API key.

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_MODEL=openrouter/qwen/qwen3-coder-next
```

**Recommended models:**
| Model | Description | Best For |
|-------|-------------|----------|
| `openrouter/qwen/qwen3-coder-next` | Claude 4 Sonnet | Balanced quality/speed |
| `openrouter/anthropic/claude-opus-4` | Claude 4 Opus | Complex fixes |
| `openrouter/anthropic/claude-haiku-4` | Claude 4 Haiku | Fast, cheap fixes |
| `openrouter/qwen/qwen3-235b-a22b-2507` | Qwen3 235B | Code-heavy tasks |
| `openrouter/qwen/qwen3.5-flash-02-23` | Qwen3.5 Flash | Fast responses |
| `openrouter/nvidia/nemotron-3-super-120b-a12b:free` | Nemotron 3 Super | Free tier |
| `openrouter/deepseek/deepseek-coder-v2` | DeepSeek Coder | Code-specific |

### Ollama (Local - Free, Private)

Run models locally for zero cost and complete privacy.

**Setup:**
```bash
# Install Ollama: https://ollama.ai

# Pull a code-capable model
ollama pull codellama:7b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder:6.7b
```

**Configure pfix:**
```bash
# .env
PFIX_MODEL=ollama/codellama:7b
PFIX_API_BASE=http://localhost:11434
# No API key needed for local models
```

**Recommended local models:**
| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `ollama/codellama:7b` | 7B | Fast | Good |
| `ollama/qwen2.5-coder:7b` | 7B | Fast | Very Good |
| `ollama/deepseek-coder:6.7b` | 6.7B | Fast | Very Good |
| `ollama/codellama:13b` | 13B | Medium | Excellent |
| `ollama/qwen2.5-coder:14b` | 14B | Medium | Excellent |

### OpenAI

```bash
# .env
PFIX_MODEL=gpt-4o
PFIX_API_KEY=sk-...
PFIX_API_BASE=https://api.openai.com/v1
```

**Models:** `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Anthropic (Direct)

```bash
# .env
PFIX_MODEL=anthropic/claude-3-sonnet-20241022
PFIX_API_KEY=sk-ant-...
```

**Models:** `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`

### Azure OpenAI

```bash
# .env
PFIX_MODEL=azure/<your-deployment-name>
PFIX_API_KEY=...
PFIX_API_BASE=https://<resource>.openai.azure.com
```

### Google Vertex AI / Gemini

```bash
# .env
PFIX_MODEL=vertex_ai/gemini-1.5-pro
# or
PFIX_MODEL=gemini/gemini-1.5-pro
```

### Choosing a Model

**For beginners:** Start with `openrouter/qwen/qwen3-coder-next` (good balance)

**For cost savings:** Use Ollama locally or OpenRouter free models (`:free` suffix)

**For complex fixes:** Use larger models (Claude Opus, GPT-4, Qwen 235B)

**For speed:** Use smaller models (Haiku, GPT-4o-mini, local 7B models)

## Runtime Error Tracking

pfix can automatically capture runtime errors to `TODO.md` for production monitoring:

```toml
[tool.pfix.runtime_todo]
enabled = true
todo_file = "TODO.md"
min_severity = "medium"
max_entries = 500
deduplicate = true
include_local_vars = false
include_traceback_depth = 5
```

**Features:**
- **Absolute paths** — errors tracked with full file paths
- **Deduplication** — same error 1000x = one entry with counter
- **Full traceback** — complete call stack, not just last frame
- **Environment context** — Python version, hostname, PID, venv path
- **Thread-safe** — file locking for multi-worker setups (gunicorn/uvicorn)
- **Append-only** — never loses history

**Enable via environment:**
```bash
PFIX_RUNTIME_TODO=true
PFIX_TODO_FILE=TODO.md
```

## Environment Diagnostics

Comprehensive environment checking with 14 diagnostic categories:

```bash
pfix diagnose                    # Run all diagnostics
pfix diagnose --category venv,memory,network
pfix diagnose --json --check     # CI mode (exit 1 on errors)
pfix diagnose --fix              # Auto-fix what can be fixed
```

**Categories:**
| Category | Checks |
|----------|--------|
| `import_dependency` | Missing imports, circular deps, version conflicts, stdlib shadowing |
| `filesystem` | Disk space, permissions, broken symlinks, large files |
| `venv` | Activation, integrity, global leaks, requirements sync |
| `python_version` | pyproject.toml requires-python, deprecated features |
| `memory` | Available RAM, swap, recursion limit, GC pressure |
| `network` | DNS, connectivity, SSL certs, proxy config |
| `process` | ulimits, signals, zombie processes |
| `encoding` | UTF-8 BOM, line endings, locale |
| `paths` | sys.path issues, PYTHONPATH, long paths |
| `config_env` | .env security, required vars, gitignore |
| `concurrency` | Thread count, asyncio loop issues |
| `serialization` | Pickle protocol, corrupt cache files |
| `hardware` | GPU availability, CPU count, Docker limits |
| `third_party` | API rate limits, auth expiration, schema changes |

**Auto-fixable issues:**
- Stale `.pyc` files → `find . -name '*.pyc' -delete`
- UTF-8 BOM → remove BOM markers
- Mixed line endings → convert to LF
- Missing `.env` → copy from `.env.example`
- `.env` not gitignored → add to `.gitignore`
- Large log files → truncate to last N lines

**Usage in CI/CD:**
```yaml
- run: pfix diagnose --check --json
  continue-on-error: true
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
