# Import Examples — Module & Import Errors

Demonstrates common import issues: missing modules, circular imports, shadowing, wrong names.

## Files

- `circular.py` — Circular import simulation and NameError from typos
- `missing_module.py` — ModuleNotFoundError, auto-install demonstration
- `platform_specific.py` — Platform/version conditional import failures
- `shadowing.py` — Local names shadowing stdlib modules
- `wrong_names.py` — Import typos and wrong package names

## Usage

```bash
# Run all import tests
python main.py

# Or run individual files
python missing_module.py
python circular.py
python shadowing.py
python wrong_names.py
python platform_specific.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing httpx | `ModuleNotFoundError` | Third-party not installed |
| Missing yaml | `ModuleNotFoundError` | PyYAML not installed |
| Circular import | `ImportError` | Module A imports B, B imports A |
| `list` shadowed | `TypeError` | Variable shadows builtin |
| `json` shadowed | `AttributeError` | String shadows module |
| Typo: colections | `ModuleNotFoundError` | Missing 'l' in collections |
| Typo: dateime | `ModuleNotFoundError` | Missing 't' in datetime |
| Wrong attr: b64_encode | `ImportError` | Should be b64encode |
