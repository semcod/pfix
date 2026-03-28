# pfix Complex Demo — pyproject.toml Configuration

This example demonstrates pfix working with **zero Python code configuration**. All settings are in `pyproject.toml`.

## What's Different

Unlike other examples that use `.env` or `configure()`, this example uses **only pyproject.toml** `[tool.pfix]` section:

```python
# main.py - just import, no config needed
import pfix
```

```toml
# pyproject.toml - all config here
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
```

## Configuration

### pyproject.toml (behavior settings)

Non-sensitive pfix behavior configuration:

```toml
[tool.pfix]
model = "openrouter/qwen/qwen3-coder-next"
auto_apply = true
auto_install_deps = true
auto_restart = true
```

### .env (API keys)

Sensitive credentials - **never commit to git**:

```bash
# Copy template to .env and fill in your actual key
cp .env.example .env

# Edit .env:
OPENROUTER_API_KEY=sk-or-v1-...
```

The `.env` file is automatically loaded by pfix and is gitignored by default.

## Files

```
complex_demo/
├── pyproject.toml      # pfix behavior configuration (committed)
├── .env.example        # API key template (committed)
├── .env                # Your actual API key (NOT committed - add to .gitignore!)
├── main.py             # Zero-config code
├── data/
│   └── users.csv       # Sample data
└── README.md
```

## Prerequisites

1. Activate the virtual environment:
```bash
source /home/tom/github/semcod/pfix/examples/venv/bin/activate
```

2. Install pfix in editable mode from project root:
```bash
cd /home/tom/github/semcod/pfix
pip install -e .
```

## Quick Development Usage (No import needed!)

Use `pfix-python` wrapper - works like normal `python` but with pfix auto-activated:

```bash
# Instead of:
python main.py

# Use:
pfix-python main.py
```

**Benefit:** No `import pfix` needed in your code files!

The wrapper is in `venv/bin/pfix-python` when you activate the virtual environment.

## Standard Usage (With import)

```bash
cd /home/tom/github/semcod/pfix/examples/complex_demo
python main.py
```

Or with the wrapper (no import needed in code):
```bash
pfix-python main.py
```

1. First run: pfix installs pandas (if missing), detects and fixes bugs one by one
2. With `auto_restart=true`, process restarts after each fix automatically
3. Eventually all bugs are fixed and script completes successfully

## Bugs Demonstrated

1. **Missing library** — `import pandas` triggers auto-install
2. **Type error** — column name as variable instead of string
3. **FileNotFoundError** — missing data file
4. **Logic error** — divide by zero with empty DataFrame
5. **TypeError** — adding int to string
6. **KeyError** — missing dictionary key
7. **AttributeError** — using `.sort()` which returns None

## Why pyproject.toml?

- **Version controlled** — config stays with your code
- **No extra files** — single `pyproject.toml` for all project settings
- **IDE friendly** — editors understand TOML structure
- **Reproducible** — same config across all environments
