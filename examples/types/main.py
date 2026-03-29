"""
pfix Type Examples — Main Entry Point

Demonstrates type errors, attribute errors, and pattern errors.
"""

import pfix


def main():
    print("=== pfix Type Examples ===\n")

    print("Running type_errors.py tests:")
    print("-" * 40)
    exec(open("type_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning attribute_errors.py tests:")
    print("-" * 40)
    exec(open("attribute_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning pattern_errors.py tests:")
    print("-" * 40)
    exec(open("pattern_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All type tests complete ===")


if __name__ == "__main__":
    main()
