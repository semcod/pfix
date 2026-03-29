#!/usr/bin/env python3
"""Import shadowing — local names shadow stdlib modules."""

from pfix import pfix

# This variable shadows the builtin 'list'
list = [1, 2, 3]

# This shadows 'json' module
json = "not a module"


@pfix(hint="'list' is shadowed by a variable assignment above")
def make_list_from_range(n: int):
    return list(range(n))  # TypeError: 'list' object is not callable


@pfix(hint="'json' is shadowed by string variable above")
def parse_json_string(data: str) -> dict:
    return json.loads(data)  # AttributeError: 'str' has no attribute 'loads'


@pfix(hint="Local variable 'os' shadows the import")
def get_home_dir():
    os = "not the module"  # shadows import
    import os  # SyntaxWarning in some versions, or uses local 'os'
    return os.path.expanduser("~")


@pfix(hint="Function parameter shadows builtin 'type'")
def create_instance(type: str, value):
    """Parameter 'type' shadows builtin type()."""
    return type(value)  # TypeError: 'str' object is not callable


if __name__ == "__main__":
    tests = [
        ("1. 'list' shadowed by variable", lambda: make_list_from_range(5)),
        ("2. 'json' shadowed by string", lambda: parse_json_string('{"a":1}')),
        ("3. 'os' shadowed locally", lambda: get_home_dir()),
        ("4. 'type' shadowed by param", lambda: create_instance("int", "42")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
