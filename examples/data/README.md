# Data Processing Examples — Parsing & Numeric Errors

Demonstrates common data processing errors: parsing failures, numeric errors, and data validation issues.

## Files

- `numeric_errors.py` — Division by zero, float precision, NaN propagation, overflow
- `parse_errors.py` — KeyError, IndexError, ValueError, JSON/CSV parsing

## Usage

```bash
# Run all data processing tests
python main.py

# Or run individual files
python numeric_errors.py
python parse_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Average of empty list | `ZeroDivisionError` | Division by zero |
| Float precision | `AssertionError` | 0.1 + 0.2 != 0.3 |
| NaN propagation | Logic error | NaN corrupts all calculations |
| Missing dict key | `KeyError` | Accessing non-existent key |
| List index out of range | `IndexError` | Accessing index beyond length |
| Invalid int() | `ValueError` | Non-numeric string |
| JSON with trailing comma | `JSONDecodeError` | Invalid JSON syntax |
| CSV missing column | `KeyError` | Inconsistent column count |
