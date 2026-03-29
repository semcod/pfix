#!/usr/bin/env python3
"""Encoding errors — UnicodeDecodeError, BOM, wrong codec, bytes vs str."""

from pfix import pfix


@pfix(hint="File has latin-1 encoding but opened as utf-8")
def read_legacy_file() -> str:
    import tempfile, os
    # Create a file with latin-1 encoded content
    path = tempfile.mktemp(suffix=".txt")
    with open(path, "wb") as f:
        f.write("Café résumé naïve".encode("latin-1"))
    # Read it as UTF-8 — will fail
    with open(path, "r", encoding="utf-8") as f:  # UnicodeDecodeError
        content = f.read()
    os.unlink(path)
    return content


@pfix(hint="Bytes vs str confusion — .encode() on bytes or .decode() on str")
def process_api_response(data) -> str:
    raw = b'{"status": "ok"}'
    return raw + " processed"  # TypeError: can't concat bytes to str


@pfix(hint="String formatting with non-ASCII chars fails on bad locale")
def format_price(amount: float, currency: str = "€") -> str:
    return f"Total: {amount:.2f} {currency}"


@pfix(hint="URL with unicode chars not properly encoded")
def build_search_url(query: str) -> str:
    base = "https://api.example.com/search?q="
    return base + query  # Should use urllib.parse.quote for non-ASCII


@pfix(hint="CSV with BOM marker causes wrong first column name")
def read_bom_csv() -> list:
    import csv, tempfile, os
    from io import StringIO

    # Simulate BOM-prefixed CSV
    bom_csv = "\ufeffname,age\nAlice,30\nBob,25"
    reader = csv.DictReader(StringIO(bom_csv))
    rows = list(reader)
    # First column key has BOM prefix: '\ufeffname' instead of 'name'
    return [row["name"] for row in rows]  # KeyError: 'name'


if __name__ == "__main__":
    tests = [
        ("1. Latin-1 file read as UTF-8", lambda: read_legacy_file()),
        ("2. bytes + str concat", lambda: process_api_response(None)),
        ("3. Unicode in format string", lambda: format_price(49.99)),
        ("4. Unicode in URL", lambda: build_search_url("café noir")),
        ("5. BOM in CSV header", lambda: read_bom_csv()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
