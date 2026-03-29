# Type Examples — Type Errors & Attribute Errors

Demonstrates common type-related errors: type mismatches, attribute errors, None propagation.

## Files

- `attribute_errors.py` — Wrong method names, None.attr access, typos
- `pattern_errors.py` — f-string formatting, sorting, unpacking, dict merge
- `type_errors.py` — String/concat errors, calling None, unhashable types

## Usage

```bash
# Run all type tests
python main.py

# Or run individual files
python attribute_errors.py
python pattern_errors.py
python type_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| dict.append() | `AttributeError` | Dict has no append method |
| list.strip() | `AttributeError` | List has no strip method |
| None subscript | `TypeError` | Accessing dict on None |
| .lenght typo | `AttributeError` | Should be len() |
| str + int | `TypeError` | Can't concatenate str and int |
| str to range() | `TypeError` | range() needs int |
| Calling None | `TypeError` | None is not callable |
| Unhashable key | `TypeError` | List can't be dict key |
| f-string format | `TypeError` | Object has no __format__ |
| sorted() with None | `TypeError` | Can't compare None and int |
