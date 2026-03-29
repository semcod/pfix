# Environment Examples — Env Vars & Venv Issues

Demonstrates environment-related errors: missing env vars, venv detection, Python version guards.

## Files

- `env_var_errors.py` — Missing env vars, wrong types, boolean parsing
- `venv_issues.py` — Venv detection, sys.path problems, version checks

## Usage

```bash
# Run all environment tests
python main.py

# Or run individual files
python env_var_errors.py
python venv_issues.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing DATABASE_URL | `KeyError` | os.environ[] raises on missing |
| None to int() | `TypeError` | os.getenv() returns None |
| 'false' is truthy | Logic error | String "false" is truthy |
| Hardcoded home path | `FileNotFoundError` | Wrong path in Docker/CI |
| Missing else branch | Logic error | Function returns None |
| No venv active | `EnvironmentError` | Running without virtualenv |
| Wrong Python version | `RuntimeError` | Missing 3.11+ features |
