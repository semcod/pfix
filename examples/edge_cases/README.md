# Edge Cases — Class Errors, Python Gotchas & Tricky Errors

Demonstrates advanced edge cases: class inheritance, closures, decorators, and dynamic code.

## Files

- `class_errors.py` — MRO conflicts, `__slots__`, dataclass mutable defaults, missing `super()`
- `python_gotchas.py` — Context managers, properties, staticmethod issues, generators
- `tricky_errors.py` — Lambda errors, closures, stacked decorators, `__getattr__`

## Usage

```bash
# Run all edge case tests
python main.py

# Or run individual files
python class_errors.py
python python_gotchas.py
python tricky_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing `super().__init__()` | `AttributeError` | Parent state not initialized |
| `__slots__` violation | `AttributeError` | Dynamic attribute blocked |
| Mutable dataclass default | Logic error | Shared list across instances |
| MRO conflict | `TypeError` | Inconsistent inheritance order |
| `open()` without `with` | Resource leak | File never closed |
| Property called with `()` | `TypeError` | Property is not callable |
| `self` in `@staticmethod` | `NameError` | No self in static context |
| Late binding closure | Logic error | All lambdas capture same value |
| Stacked decorator | `ValueError` | Inner decorator raises |
| `__getattr__` typo chain | `AttributeError` | Typo in chained access |
