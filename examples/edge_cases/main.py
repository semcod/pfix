"""
pfix Edge Cases Examples — Main Entry Point

Demonstrates class errors, python gotchas, and tricky errors.
"""

import pfix


def main():
    print("=== pfix Edge Cases Examples ===\n")

    print("Running class_errors.py tests:")
    print("-" * 40)
    exec(open("class_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning python_gotchas.py tests:")
    print("-" * 40)
    exec(open("python_gotchas.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning tricky_errors.py tests:")
    print("-" * 40)
    exec(open("tricky_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All edge case tests complete ===")


if __name__ == "__main__":
    main()
