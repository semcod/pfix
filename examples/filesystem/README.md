# Filesystem Examples — File & Path Errors

Demonstrates common filesystem errors: missing files, wrong paths, relative vs absolute path confusion.

## Files

- `file_errors.py` — FileNotFoundError, wrong extensions, unexpanded paths

## Usage

```bash
# Run all filesystem tests
python main.py

# Or run individual files
python file_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Missing config.json | `FileNotFoundError` | Relative path from wrong CWD |
| Typo in extension | `FileNotFoundError` | `.ymal` instead of `.yaml` |
| Missing parent directory | `FileNotFoundError` | Directory doesn't exist |
| Unexpanded `~` | `FileNotFoundError` | Home path not expanded |
| Wrong path separator | `FileNotFoundError` | Backslash on Linux |
