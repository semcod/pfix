# pfix Examples — Test Suite for Self-Healing

Each subdirectory contains scripts that deliberately trigger specific error categories.
Run any script with pfix to test auto-repair:

```bash
pfix run examples/imports/missing_module.py --auto --dry-run
```

## Quick Start: Run All Examples

### Run all tests and auto-reset

```bash
cd examples
python run_all.py
```

This will:
1. Run all 12 example categories sequentially
2. Display pfix auto-fixing errors in real-time
3. Automatically reset all files to original buggy state via `git checkout`

### Manual reset only

```bash
python reset.py
```

Restores all example files to their original buggy state using `git checkout`.

### Options

```bash
python run_all.py --dry-run    # Show what would be run
python run_all.py --no-reset   # Run tests but keep fixed versions
python run_all.py --reset      # Only reset, don't run tests
```

## Categories

| Directory | Errors Tested | Count |
|-----------|--------------|-------|
| `imports/` | ModuleNotFoundError, ImportError, circular, shadow | 6 |
| `types/` | TypeError, type coercion, generics, overloads | 6 |
| `filesystem/` | FileNotFoundError, PermissionError, paths | 5 |
| `deps/` | Version conflicts, missing extras, wrong package | 4 |
| `encoding/` | UnicodeError, BOM, mixed encodings, locale | 4 |
| `network/` | ConnectionError, Timeout, DNS, SSL | 4 |
| `memory/` | MemoryError, RecursionError, leaks, large alloc | 4 |
| `concurrency/` | Race conditions, deadlocks, async errors | 4 |
| `data/` | KeyError, IndexError, ValueError, JSON/CSV parse | 6 |
| `env/` | Missing env vars, wrong Python version, venv issues | 4 |
| `edge_cases/` | Nested decorators, lambdas, eval, metaclasses | 5 |
| `production/` | Multi-error chains, partial failures, graceful degrade | 4 |
| **Total** | | **56** |
