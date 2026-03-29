#!/usr/bin/env python3
"""Edge cases — lambda errors, closures, stacked decorators, eval, dynamic code."""

from pfix import pfix


# --- 1. Lambda with error ---
@pfix(hint="Lambda has a division by zero — pfix must find the lambda source")
def apply_to_all(items: list, func=lambda x: x / 0) -> list:
    return [func(item) for item in items]  # ZeroDivisionError inside lambda


# --- 2. Closure capturing wrong variable ---
@pfix(hint="Late binding closure — all lambdas capture i=4 (last value)")
def make_multipliers() -> list:
    multipliers = []
    for i in range(5):
        multipliers.append(lambda x: x * i)  # Bug: all capture i=4
    # Expected: [0, 5, 10, 15, 20]. Actual: [20, 20, 20, 20, 20]
    results = [m(5) for m in multipliers]
    if results != [0, 5, 10, 15, 20]:
        raise ValueError(f"Late binding bug: {results} (expected [0,5,10,15,20])")
    return results


# --- 3. Stacked decorators — error in inner decorator ---
def validate_positive(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result < 0:
            raise ValueError(f"Result must be positive, got {result}")
        return result
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper

@pfix(hint="Inner decorator validate_positive raises ValueError for negative result")
@validate_positive
def subtract(a: int, b: int) -> int:
    return a - b  # Returns negative if b > a


# --- 4. Dynamic attribute / __getattr__ ---
@pfix(hint="Dynamic object with __getattr__ — AttributeError from typo in chain")
def use_dynamic_config():
    class Config:
        def __init__(self):
            self.database = type("DB", (), {"host": "localhost", "port": 5432})()

    cfg = Config()
    return cfg.databse.host  # typo: databse → database


# --- 5. Generator that raises mid-iteration ---
@pfix(hint="Generator raises StopIteration prematurely via next() without default")
def consume_generator():
    def limited_gen():
        yield 1
        yield 2
        # No more items

    gen = limited_gen()
    results = []
    for _ in range(5):
        results.append(next(gen))  # StopIteration on 3rd call
    return results


if __name__ == "__main__":
    tests = [
        ("1. Lambda with div/0", lambda: apply_to_all([1, 2, 3])),
        ("2. Late binding closure", lambda: make_multipliers()),
        ("3. Stacked decorator error", lambda: subtract(3, 10)),
        ("4. __getattr__ typo chain", lambda: use_dynamic_config()),
        ("5. Generator exhaustion", lambda: consume_generator()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
