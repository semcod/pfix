#!/usr/bin/env python3
"""Types — demonstrates fixing various TypeErrors and AttributeErrors."""

import pfix

def attribute_error_test():
    """Accessing non-existent attribute."""
    d = {"name": "Alice"}
    # Bug: accessing dict as object
    print(f"Name: {d.name}")


def type_error_test():
    """Type mismatch in operations."""
    x = "100"
    y = 50
    # Bug: adding string to integer
    result = x + y
    print(f"Result: {result}")


def pattern_error_test():
    """Common pattern mismatch."""
    data = None
    # Bug: missing check for None
    print(f"Data length: {len(data)}")


if __name__ == "__main__":
    print("=== pfix Types Examples ===")
    
    tests = [
        ("1. AttributeError (dict as object)", attribute_error_test),
        ("2. TypeError (str + int)", type_error_test),
        ("3. Pattern Error (None check)", pattern_error_test),
    ]
    
    for label, fn in tests:
        print(f"\n{label}:")
        try:
            fn()
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {e}")
