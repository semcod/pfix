#!/usr/bin/env python3
"""Async/await mistakes — missing await, sync in async, wrong event loop."""

from pfix import pfix


@pfix(hint="Missing await — coroutine never executed, just returns coroutine object")
def test_missing_await():
    import asyncio

    async def fetch_data():
        return {"status": "ok"}

    async def process():
        result = fetch_data()  # Missing 'await' — gets coroutine, not dict
        return result["status"]  # TypeError: coroutine not subscriptable

    return asyncio.run(process())


@pfix(hint="Blocking call inside async function — blocks entire event loop")
def test_sync_in_async():
    import asyncio
    import time

    async def handler():
        time.sleep(2)  # WRONG: blocks event loop. Should use asyncio.sleep()
        return "done"

    return asyncio.run(asyncio.wait_for(handler(), timeout=0.5))


@pfix(hint="Trying to await a non-coroutine")
def test_await_non_coroutine():
    import asyncio

    def sync_function():
        return 42

    async def process():
        result = await sync_function()  # TypeError: object int can't be used in await
        return result

    return asyncio.run(process())


@pfix(hint="Generator used where async generator expected")
def test_sync_generator_in_async():
    import asyncio

    def sync_gen():
        yield 1
        yield 2
        yield 3

    async def consume():
        results = []
        async for item in sync_gen():  # TypeError: 'generator' not async iterable
            results.append(item)
        return results

    return asyncio.run(consume())


if __name__ == "__main__":
    tests = [
        ("1. Missing await", lambda: test_missing_await()),
        ("2. Blocking sleep in async", lambda: test_sync_in_async()),
        ("3. await non-coroutine", lambda: test_await_non_coroutine()),
        ("4. sync gen in async for", lambda: test_sync_generator_in_async()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
