#!/usr/bin/env python3
"""TypeError scenarios — wrong types, missing conversions, operator mismatches."""

from pfix import pfix


@pfix(hint="String concatenation with int — needs str() conversion")
def format_user_info(name: str, age: int) -> str:
    return "Name: " + name + ", Age: " + age  # TypeError: can only concatenate str


@pfix(hint="Passing string where int expected for range()")
def generate_sequence(count: str) -> list:
    return list(range(count))  # TypeError: 'str' not interpretable as int


@pfix(hint="Calling None — variable is None instead of function")
def apply_transform(data, transform=None):
    result = transform(data)  # TypeError: 'NoneType' not callable
    return result


@pfix(hint="Wrong number of arguments to function")
def calculate_area(width, height):
    return width * height

def test_wrong_args():
    return calculate_area(10)  # TypeError: missing 1 required positional argument


@pfix(hint="Unhashable type as dict key")
def build_index(items: list) -> dict:
    index = {}
    for item in items:
        index[[item]] = True  # TypeError: unhashable type: 'list'
    return index


@pfix(hint="Comparing incompatible types")
def find_minimum(values):
    return min(values)  # TypeError when mixing str and int


if __name__ == "__main__":
    tests = [
        ("1. str + int concat", lambda: format_user_info("Alice", 30)),
        ("2. str to range()", lambda: generate_sequence("5")),
        ("3. Calling None", lambda: apply_transform([1, 2, 3])),
        ("4. Missing argument", lambda: test_wrong_args()),
        ("5. Unhashable dict key", lambda: build_index(["a", "b"])),
        ("6. Mixed type comparison", lambda: find_minimum([3, "hello", 1])),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
