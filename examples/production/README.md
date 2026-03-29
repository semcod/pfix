# Production Examples — Real-World Error Patterns

Demonstrates production scenarios: API patterns, cascading errors, graceful degradation.

## Files

- `api_patterns.py` — REST API handlers, ETL pipelines, config bootstrapping
- `cascading_errors.py` — Error chains, partial failures, retry logic
- `degradation.py` — Missing fallbacks, retry storms, schema changes

## Usage

```bash
# Run all production tests
python main.py

# Or run individual files
python api_patterns.py
python cascading_errors.py
python degradation.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing auth header | `KeyError` | Request without headers |
| Bad limit param | `ValueError` | Non-numeric string to int |
| Schema changed | `KeyError` | `user_name` → `username` |
| Config not found | `FileNotFoundError` | Missing config file |
| Partial batch failure | Various | Some items fail, others succeed |
| Cleanup exception | Various | Exception in finally masks original |
| Cache miss | `KeyError` | No fallback to primary source |
| Missing feature flag | `KeyError` | Flag not defined |
| Retry storm | Various | No backoff, no max attempts |
| API schema change | `KeyError` | `data` → `results` |
