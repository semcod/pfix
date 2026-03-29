#!/usr/bin/env python3
"""Memory errors — RecursionError, large allocations, unbounded growth."""

from pfix import pfix


@pfix(hint="Infinite recursion — missing base case")
def factorial(n: int) -> int:
    return n * factorial(n - 1)  # RecursionError: no base case for n <= 1


@pfix(hint="Fibonacci without memoization — exponential memory/time")
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)  # Too slow for large n


@pfix(hint="Unbounded list growth — appending in infinite loop")
def accumulate_data() -> list:
    data = []
    i = 0
    while True:  # No exit condition
        data.append("x" * 1000)
        i += 1
        if i > 100_000:  # Safety valve for testing
            break
    return data


@pfix(hint="Creating a string that's too large by repeated concatenation")
def build_huge_string(n: int) -> str:
    result = ""
    for i in range(n):
        result = result + f"line {i}: {'x' * 100}\n"  # O(n²) string concat
    return result


if __name__ == "__main__":
    import sys
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(200)  # Lower limit for faster failure

    tests = [
        ("1. Infinite recursion (factorial)", lambda: factorial(5)),
        ("2. Exponential recursion (fib)", lambda: fibonacci(35)),
        ("3. Unbounded list growth", lambda: accumulate_data()),
        ("4. O(n²) string concat", lambda: build_huge_string(50_000)),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            result = fn()
            print(f"   OK: {type(result).__name__}, len={len(result) if hasattr(result, '__len__') else result}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {str(e)[:80]}")

    sys.setrecursionlimit(old_limit)
