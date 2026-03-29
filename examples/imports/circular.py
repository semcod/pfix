#!/usr/bin/env python3
"""Circular import — module A imports B, B imports A at top level."""

from pfix import pfix

# Simulate circular import by defining mutually dependent functions
# that reference each other's modules incorrectly

REGISTRY = {}


@pfix(hint="This function references 'processor' which references back to 'registry'")
def register_handler(name: str, func):
    """Register a handler — but tries to import processor which imports this module."""
    # This simulates: from examples.imports.circular_b import process
    # where circular_b does: from examples.imports.circular_a import register
    from examples.imports._circular_helper import get_processor

    REGISTRY[name] = func
    processor = get_processor()
    return processor.validate(func)


@pfix(hint="NameError from unresolved circular dependency")
def process_all():
    """Process all registered handlers."""
    for name, handler in REGISTY.items():  # typo: REGISTY → REGISTRY
        handler()


if __name__ == "__main__":
    print("1. Circular import simulation:")
    try:
        register_handler("test", lambda: print("hello"))
    except Exception as e:
        print(f"   FAIL: {type(e).__name__}: {e}")

    print("\n2. NameError from typo in global name:")
    try:
        process_all()
    except Exception as e:
        print(f"   FAIL: {type(e).__name__}: {e}")
