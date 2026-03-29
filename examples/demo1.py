#!/usr/bin/env python3
"""pfix demo — file-level auto-healing with pfix_session

Run with: python examples/demo.py
"""

from pfix import configure, pfix_session

from shared import fetch_json, average, greet

configure(auto_apply=True, dry_run=False)


def main():
    print("=== pfix Demo (file-level healing) ===\n")

    print("1. fetch_json (dep management):")
    result = fetch_json('https://httpbin.org/json')
    print(f"   ✓ Success: {type(result).__name__}")

    print("\n2. average([]) (ZeroDivisionError):")
    result = average([])
    print(f"   ✓ Result: {result}")

    print("\n3. greet('Alice', 30) (TypeError):")
    result = greet('Alice', 30)
    print(f"   ✓ Result: {result}")


if __name__ == "__main__":
    # Wrap entire execution in pfix session
    # Any exception triggers LLM auto-repair for this file
    with pfix_session(__file__, auto_apply=True):
        main()
