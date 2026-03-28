# pfix Complex Demo — pyproject.toml Configuration

This example demonstrates pfix working with complex library integration (pandas) using **only pyproject.toml configuration** (no `.env` file).

## What's Different

Unlike `demo_auto.py` which uses `.env` for configuration, this example uses **pyproject.toml** `[tool.pfix]` section for all settings.

## Files

```
complex_demo/
├── main.py          # Demo script with multiple bugs
├── data/
│   └── users.csv    # Sample data file
└── README.md        # This file
```

## Configuration (pyproject.toml)

The main project `pyproject.toml` contains:

```toml
[tool.pfix]
model = "openrouter/anthropic/claude-sonnet-4"
auto_apply = true
auto_install_deps = true
auto_restart = true
max_retries = 3
create_backups = false
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

## Running

```bash
cd /home/tom/github/semcod/pfix/examples/complex_demo
python main.py
```

## Expected Flow

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
