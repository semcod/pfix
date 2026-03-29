"""
pfix Memory Examples — Main Entry Point

Demonstrates recursion, leaks, and large allocation errors.
"""

import pfix


def main():
    print("=== pfix Memory Examples ===\n")

    print("Running recursion_and_alloc.py tests:")
    print("-" * 40)
    exec(open("recursion_and_alloc.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning resource_leaks.py tests:")
    print("-" * 40)
    exec(open("resource_leaks.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All memory tests complete ===")


if __name__ == "__main__":
    main()
