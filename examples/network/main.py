"""
pfix Network Examples — Main Entry Point

Demonstrates connection and network errors.
"""

import pfix


def main():
    print("=== pfix Network Examples ===\n")

    print("Running connection_errors.py tests:")
    print("-" * 40)
    exec(open("connection_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All network tests complete ===")


if __name__ == "__main__":
    main()
