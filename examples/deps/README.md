# Dependency Examples — Version Conflicts & Package Traps

Demonstrates common dependency issues: version conflicts, wrong package names, and missing extras.

## Files

- `package_traps.py` — Wrong package names, namespace conflicts, extras needed
- `version_conflicts.py` — Deprecated APIs, removed modules, version mismatches

## Usage

```bash
# Run all dependency tests
python main.py

# Or run individual files
python package_traps.py
python version_conflicts.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Wrong package name | Various | PyPI packages with confusing names |
| Missing extras | `ImportError` | Needs `requests[security]` for SNI |
| Deprecated API | `AttributeError` | `collections.MutableMapping` removed in 3.10+ |
| Renamed function | `AttributeError` | `json.read` → `json.loads` |
| Optional dependency | `ImportError` | Missing `pfix[mcp]` extra |
