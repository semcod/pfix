"""
pfix Production Examples — Main Entry Point

Demonstrates real-world error patterns.
"""

import pfix


def main():
    print("=== pfix Production Examples ===\n")

    print("Running api_patterns.py tests:")
    print("-" * 40)
    exec(open("api_patterns.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning cascading_errors.py tests:")
    print("-" * 40)
    exec(open("cascading_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning degradation.py tests:")
    print("-" * 40)
    exec(open("degradation.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All production tests complete ===")


if __name__ == "__main__":
    main()
