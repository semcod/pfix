"""
pfix Data Processing Examples — Main Entry Point

Demonstrates parsing and numeric errors.
"""

import pfix


def main():
    print("=== pfix Data Processing Examples ===\n")

    print("Running numeric_errors.py tests:")
    print("-" * 40)
    exec(open("numeric_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning parse_errors.py tests:")
    print("-" * 40)
    exec(open("parse_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All data processing tests complete ===")


if __name__ == "__main__":
    main()
