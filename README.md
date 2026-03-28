# 🔧 pfix

**Self-healing Python** — catches runtime errors and fixes source code + dependencies via LLM + MCP.

## Features

- **`@pfix` decorator** — wrap any function; errors trigger automatic repair
- **Fast dep fix** — `ModuleNotFoundError` → instant `pip`/`uv install` (no LLM call)
- **pipreqs scanning** — project-wide import analysis for missing dependencies
- **LLM code repair** — sends error context to LLM (OpenRouter/LiteLLM) for intelligent fixes
- **pip + uv** — auto-detects `uv` for faster installs, falls back to `pip`
- **MCP server** — `@mcp.tool()` via FastMCP for IDE integration (Claude Code, Cursor, VS Code)
- **Git auto-commit** — optional auto-commit of fixes with configurable prefix
- **Auto-restart** — `os.execv` process restart after fix applied
- **Interactive diff** — unified diff with confirmation before applying
- **Backup system** — timestamped backups in `.pfix_backups/`
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

## Quick Start

```bash
# 1. Configure
cp .env.example .env
# Set OPENROUTER_API_KEY=sk-or-v1-...

# 2. Use in your code
```

```python
from pfix import pfix

@pfix
def process_data(path):
    import pandas as pd                    # auto-installed if missing
    df = pd.read_csv(path)
    return df.groupby("category").sum()    # LLM fixes column errors

@pfix(retries=3, hint="Parses ISO dates from API", deps=["requests", "python-dateutil"])
def fetch_events(url: str):
    import requests
    from dateutil.parser import parse
    return [parse(e["ts"]) for e in requests.get(url).json()["events"]]
```

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
| `OPENROUTER_API_KEY` | — | Required |
| `PFIX_MODEL` | `openrouter/anthropic/claude-sonnet-4` | LLM model |
| `PFIX_AUTO_APPLY` | `false` | Auto-apply fixes |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | Auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | Restart after fix |
| `PFIX_PKG_MANAGER` | auto | `pip` or `uv` |
| `PFIX_MAX_RETRIES` | `3` | Max attempts |
| `PFIX_DRY_RUN` | `false` | Show only |
| `PFIX_GIT_COMMIT` | `false` | Auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix: ` | Commit prefix |

### pyproject.toml

```toml
[tool.pfix]
model = "openrouter/anthropic/claude-sonnet-4"
auto_apply = false
max_retries = 3
```

### Programmatic

```python
from pfix import configure

configure(
    auto_apply=True,
    pkg_manager="uv",
    git_auto_commit=True,
)
```

## How It Works

```
@pfix decorated function
        │
        ▼
   Exception caught
        │
        ├── ModuleNotFoundError? → pip/uv install → retry
        │
        ▼
   ErrorContext built (traceback, source, vars, imports, pipreqs scan)
        │
        ▼
   LLM analysis (LiteLLM → OpenRouter)
        │
        ▼
   FixProposal (diagnosis, code, deps, confidence)
        │
        ├── Show diff → confirm (or auto-apply)
        ├── Create .pfix_backups/ backup
        ├── Apply fix to source
        ├── Git commit (optional)
        ▼
   Reload module → retry (or os.execv restart)
```

## Dependencies

| Package | Role |
|---|---|
| `litellm` | LLM proxy — OpenRouter, OpenAI, Anthropic, Ollama |
| `python-dotenv` | Load .env config |
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


Licensed under Apache-2.0.


Licensed under Apache-2.0.


Licensed under Apache-2.0.


Apache 2.0 — Tom Sapletta / Softreck
