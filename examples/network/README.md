# Network Examples — Connection & Timeout Errors

Demonstrates network-related errors: connection refused, DNS failures, timeouts, HTTP errors.

## Files

- `connection_errors.py` — Connection refused, DNS failures, timeouts, bad URLs

## Usage

```bash
# Run all network tests
python main.py

# Or run individual files
python connection_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Connection refused | `ConnectionRefusedError` | Service not running on port |
| DNS typo | Various | Misspelled hostname |
| Timeout | `TimeoutError` | 1s timeout on 30s endpoint |
| HTTP 404 | `HTTPError` | Not handling error status |
