#!/usr/bin/env python3
"""Type mismatch in real patterns — f-strings, unpacking, sort, comparison."""

from pfix import pfix


@pfix(hint="f-string with object that has no __format__ — needs __str__")
def format_report(items: list) -> str:
    class Metric:
        def __init__(self, name, value):
            self.name = name
            self.value = value
        # Missing __str__ and __format__

    m = Metric("cpu", 92.5)
    return f"Report: {m:.2f}"  # TypeError: unsupported format character


@pfix(hint="sorted() with key returning None for some items")
def sort_users(users: list[dict]) -> list[dict]:
    return sorted(users, key=lambda u: u.get("age"))
    # TypeError: '<' not supported between 'NoneType' and 'int'


@pfix(hint="Chained comparison with incompatible types")
def check_range(value) -> bool:
    low = 0
    high = "100"  # Bug: string instead of int
    return low <= value <= high  # TypeError: '<=' str and int


@pfix(hint="Starred unpacking with too few values")
def parse_header(line: str) -> tuple:
    first, *middle, last = line.split()
    # ValueError if line has only 1 word (need at least 2 for first+last)
    return first, middle, last


@pfix(hint="Dict merge operator | with non-dict — needs Python 3.9+")
def merge_configs(base: dict, override: dict) -> dict:
    return base | override | "extra"  # TypeError: unsupported operand type(s)


@pfix(hint="Walrus operator in wrong context")
def find_first_match(items: list, predicate) -> str:
    if result := [x for x in items if predicate(x)]:
        return result[0]
    raise ValueError("No match found")


if __name__ == "__main__":
    tests = [
        ("1. f-string format on custom object",
         lambda: format_report([])),
        ("2. sorted() with None keys",
         lambda: sort_users([
             {"name": "Alice", "age": 30},
             {"name": "Bob"},  # no 'age' key → None
             {"name": "Carol", "age": 25},
         ])),
        ("3. Chained comparison str vs int",
         lambda: check_range(50)),
        ("4. Starred unpacking too few",
         lambda: parse_header("solo")),
        ("5. Dict merge with non-dict",
         lambda: merge_configs({"a": 1}, {"b": 2})),
        ("6. find_first_match — no match",
         lambda: find_first_match([1, 2, 3], lambda x: x > 10)),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
