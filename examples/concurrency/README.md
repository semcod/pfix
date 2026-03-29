# Concurrency Examples — Async & Threading Errors

Demonstrates common concurrency errors: race conditions, async/await mistakes, and thread safety issues.

## Files

- `async_mistakes.py` — Missing `await`, sync calls in async, wrong event loop usage
- `race_conditions.py` — Dict/list modification during iteration, thread-unsafe counters

## Usage

```bash
# Run all concurrency tests
python main.py

# Or run individual files
python async_mistakes.py
python race_conditions.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing await | `TypeError` | Coroutine never executed |
| Blocking in async | Runtime issue | `time.sleep()` blocks event loop |
| Dict modification | `RuntimeError` | Changing dict size during iteration |
| Thread-unsafe counter | Race condition | Non-atomic increment |
