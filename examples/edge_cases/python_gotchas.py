#!/usr/bin/env python3
"""Context manager, property, and descriptor errors."""

from pfix import pfix


@pfix(hint="Using context manager without 'with' — resource leak and wrong return")
def test_no_with_statement():
    path = "/etc/hostname"
    f = open(path)  # No 'with' — resource leak
    content = f.read()
    # forgot f.close() — and if exception happens before, never closed
    return content.strip()


@pfix(hint="@property used but called with parentheses")
def test_property_called():
    class User:
        def __init__(self, first, last):
            self.first = first
            self.last = last

        @property
        def full_name(self):
            return f"{self.first} {self.last}"

    u = User("Alice", "Smith")
    return u.full_name()  # TypeError: 'str' object is not callable


@pfix(hint="@staticmethod accessing self — should be regular method")
def test_staticmethod_self():
    class Calculator:
        def __init__(self, base=0):
            self.base = base

        @staticmethod
        def add(value):
            return self.base + value  # NameError: 'self' not defined in static

    calc = Calculator(10)
    return calc.add(5)


@pfix(hint="Generator function used as regular function — returns generator, not value")
def test_generator_confusion():
    def get_items():
        yield 1
        yield 2
        yield 3

    result = get_items()
    return result + [4, 5]  # TypeError: can't add generator and list


@pfix(hint="contextmanager decorator but forgot to yield")
def test_bad_context_manager():
    from contextlib import contextmanager

    @contextmanager
    def timer():
        import time
        start = time.time()
        # Missing yield! — RuntimeError: generator didn't yield
        elapsed = time.time() - start
        print(f"Took {elapsed:.2f}s")

    with timer():
        pass


if __name__ == "__main__":
    tests = [
        ("1. open() without 'with'", lambda: test_no_with_statement()),
        ("2. property called with ()", lambda: test_property_called()),
        ("3. self in @staticmethod", lambda: test_staticmethod_self()),
        ("4. Generator + list concat", lambda: test_generator_confusion()),
        ("5. contextmanager no yield", lambda: test_bad_context_manager()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
