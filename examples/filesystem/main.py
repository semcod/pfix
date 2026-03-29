"""
pfix Filesystem Examples — Main Entry Point

Demonstrates file and path errors.
"""

import pfix


def main():
    print("=== pfix Filesystem Examples ===\n")

    print("Running file_errors.py tests:")
    print("-" * 40)
    exec(open("file_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All filesystem tests complete ===")


if __name__ == "__main__":
    main()
