# Encoding Examples — Unicode & Codec Errors

Demonstrates encoding issues: UnicodeDecodeError, wrong codecs, BOM handling, bytes vs str.

## Files

- `codec_errors.py` — Subprocess encoding, binary/text mode mismatch, locale issues
- `unicode_errors.py` — Wrong file encoding, bytes/str confusion, Unicode in URLs

## Usage

```bash
# Run all encoding tests
python main.py

# Or run individual files
python codec_errors.py
python unicode_errors.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| ASCII for Unicode output | `UnicodeDecodeError` | Wrong encoding for subprocess |
| Bytes to text file | `TypeError` | Writing bytes to text mode |
| Latin-1 as UTF-8 | `UnicodeDecodeError` | Wrong file encoding |
| bytes + str concat | `TypeError` | Can't concatenate bytes and str |
| BOM in CSV | `KeyError` | Invisible BOM prefix on column name |
| Unicode in URL | Logic error | Non-ASCII not URL-encoded |
