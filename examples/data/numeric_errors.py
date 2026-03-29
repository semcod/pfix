#!/usr/bin/env python3
"""Numeric & math errors — ZeroDivision, overflow, NaN propagation, precision."""

from pfix import pfix


@pfix(hint="Division by zero — denominator can be zero from user input")
def calculate_average(values: list[float]) -> float:
    return sum(values) / len(values)  # ZeroDivisionError if empty list


@pfix(hint="Float precision — 0.1 + 0.2 != 0.3 causes assertion failure")
def validate_total(items: list[dict]) -> bool:
    total = sum(item["price"] for item in items)
    expected = 0.3
    if total != expected:  # False! 0.1 + 0.2 = 0.30000000000000004
        raise AssertionError(f"Total {total} != expected {expected}")
    return True


@pfix(hint="NaN propagation — NaN in data silently corrupts all calculations")
def compute_statistics(data: list[float]) -> dict:
    n = len(data)
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n

    # NaN makes all comparisons False
    if mean > 100:
        category = "high"
    elif mean > 50:
        category = "medium"
    else:
        category = "low"  # NaN falls here — wrong!

    return {"mean": mean, "variance": variance, "category": category}


@pfix(hint="Integer overflow in timestamp math — seconds vs milliseconds confusion")
def time_ago(timestamp_ms: int) -> str:
    import time
    now = int(time.time())  # seconds
    diff = now - timestamp_ms  # Bug: mixing seconds and milliseconds
    if diff < 0:
        raise ValueError(f"Timestamp is {abs(diff)} seconds in the future — likely ms vs s confusion")
    return f"{diff} seconds ago"


@pfix(hint="Modulo by zero")
def distribute_evenly(total: int, groups: int) -> tuple:
    per_group = total // groups      # ZeroDivisionError
    remainder = total % groups       # ZeroDivisionError
    return per_group, remainder


if __name__ == "__main__":
    tests = [
        ("1. Average of empty list",
         lambda: calculate_average([])),
        ("2. Float precision (0.1+0.2 != 0.3)",
         lambda: validate_total([{"price": 0.1}, {"price": 0.2}])),
        ("3. NaN propagation",
         lambda: compute_statistics([1.0, float("nan"), 3.0, 4.0])),
        ("4. Seconds vs milliseconds",
         lambda: time_ago(1711641600000)),  # ms timestamp
        ("5. Modulo by zero",
         lambda: distribute_evenly(100, 0)),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
