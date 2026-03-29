#!/usr/bin/env python3
"""Encoding — locale mismatch, wrong codec for subprocess, path encoding."""

from pfix import pfix


@pfix(hint="subprocess output has non-UTF-8 bytes — locale dependent")
def run_system_command() -> str:
    import subprocess
    result = subprocess.run(
        ["echo", "Héllo wörld"],
        capture_output=True,
        text=True,
        encoding="ascii",  # Bug: should be utf-8 or locale default
    )
    return result.stdout.strip()


@pfix(hint="Writing bytes to text-mode file")
def write_binary_to_text():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".bin", delete=False) as f:
        f.write(b"\x89PNG\r\n")  # TypeError: write() str, not bytes
        return f.name


@pfix(hint="repr() vs str() confusion with non-ASCII")
def log_user_input(text: str) -> str:
    import logging
    # Accidentally using ascii() which escapes everything
    sanitized = ascii(text)  # 'caf\\xe9' instead of 'café'
    return f"User said: {sanitized}"


if __name__ == "__main__":
    tests = [
        ("1. ASCII encoding for Unicode output", lambda: run_system_command()),
        ("2. bytes to text-mode file", lambda: write_binary_to_text()),
        ("3. ascii() vs str() on Unicode", lambda: log_user_input("café résumé")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            result = fn()
            print(f"   OK: {result}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
