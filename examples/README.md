# pfix Examples — Test Suite for Self-Healing

Each subdirectory contains scripts that deliberately trigger specific error categories.
Run any script with pfix to test auto-repair:

```bash
pfix run examples/imports/missing_module.py --auto --dry-run
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
