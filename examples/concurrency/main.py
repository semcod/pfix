"""
pfix Concurrency Examples — Main Entry Point

Demonstrates async/await mistakes and race conditions.
"""

import pfix


def main():
    print("=== pfix Concurrency Examples ===\n")

    print("Running async_mistakes.py tests:")
    print("-" * 40)
    exec(open("async_mistakes.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning race_conditions.py tests:")
    print("-" * 40)
    exec(open("race_conditions.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All concurrency tests complete ===")


if __name__ == "__main__":
    main()
