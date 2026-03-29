"""
pfix Import Examples — Main Entry Point

Demonstrates module and import errors.
"""

import pfix


def main():
    print("=== pfix Import Examples ===\n")

    print("Running missing_module.py tests:")
    print("-" * 40)
    exec(open("missing_module.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning circular.py tests:")
    print("-" * 40)
    exec(open("circular.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning shadowing.py tests:")
    print("-" * 40)
    exec(open("shadowing.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning wrong_names.py tests:")
    print("-" * 40)
    exec(open("wrong_names.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning platform_specific.py tests:")
    print("-" * 40)
    exec(open("platform_specific.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All import tests complete ===")


if __name__ == "__main__":
    main()
