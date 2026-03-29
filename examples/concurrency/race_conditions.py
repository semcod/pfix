#!/usr/bin/env python3
"""Concurrency errors — race conditions, async mistakes, thread safety."""

from pfix import pfix


@pfix(hint="Modifying dict during iteration")
def filter_dict_inplace(data: dict) -> dict:
    for key in data:
        if data[key] is None:
            del data[key]  # RuntimeError: dictionary changed size during iteration
    return data


@pfix(hint="Modifying list during iteration")
def remove_negatives(numbers: list) -> list:
    for num in numbers:
        if num < 0:
            numbers.remove(num)  # Skips elements, wrong result
    return numbers


@pfix(hint="asyncio.run() inside already-running loop")
def fetch_async_in_sync():
    import asyncio

    async def fetch():
        return "data"

    # If called from Jupyter or another async context, this fails:
    # RuntimeError: cannot be called from a running event loop
    loop = asyncio.get_event_loop()
    if loop.is_running():
        raise RuntimeError("Cannot call asyncio.run() from running event loop")
    return asyncio.run(fetch())


@pfix(hint="Thread-unsafe counter without lock")
def parallel_count() -> int:
    import threading

    counter = {"value": 0}  # mutable shared state

    def increment():
        for _ in range(10_000):
            counter["value"] += 1  # Race condition: not atomic

    threads = [threading.Thread(target=increment) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Expected: 40_000. Actual: less due to race condition
    expected = 40_000
    actual = counter["value"]
    if actual != expected:
        raise ValueError(f"Race condition: expected {expected}, got {actual}")
    return actual


if __name__ == "__main__":
    tests = [
        ("1. Dict modified during iteration",
         lambda: filter_dict_inplace({"a": 1, "b": None, "c": 3, "d": None})),
        ("2. List modified during iteration",
         lambda: remove_negatives([1, -2, 3, -4, 5, -6])),
        ("3. asyncio.run() conflict",
         lambda: fetch_async_in_sync()),
        ("4. Thread-unsafe counter",
         lambda: parallel_count()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
