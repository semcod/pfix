#!/usr/bin/env python3
"""Import typos and wrong names — pfix should suggest corrections."""

from pfix import pfix


@pfix(hint="Should import 'collections' not 'colections'")
def count_words(text: str) -> dict:
    from colections import Counter  # typo: colections → collections

    words = text.lower().split()
    return dict(Counter(words))


@pfix(hint="Should use 'from datetime import datetime'")
def get_timestamp() -> str:
    from dateime import datetime  # typo: dateime → datetime

    return datetime.now().isoformat()


@pfix(hint="Uses wrong submodule path")
def encode_base64(data: bytes) -> str:
    from base64 import b64_encode  # wrong: b64_encode → b64encode

    return b64_encode(data).decode()


@pfix(hint="Confuses package name with module name")
def parse_html(html: str) -> str:
    from beautifulsoup4 import BeautifulSoup  # wrong: should be 'bs4'

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


@pfix(hint="Uses old removed module")
def find_files(pattern: str) -> list:
    import glob2  # might not exist, should use stdlib glob

    return glob2.glob(pattern, recursive=True)


if __name__ == "__main__":
    tests = [
        ("1. Typo: colections", lambda: count_words("hello world hello")),
        ("2. Typo: dateime", lambda: get_timestamp()),
        ("3. Wrong attr: b64_encode", lambda: encode_base64(b"hello")),
        ("4. Wrong package: beautifulsoup4", lambda: parse_html("<p>Hi</p>")),
        ("5. Non-existent: glob2", lambda: find_files("*.py")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
