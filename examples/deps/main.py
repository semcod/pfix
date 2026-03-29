"""
pfix Dependency Examples — Main Entry Point

Demonstrates version conflicts and package traps.
"""

import pfix


def main():
    print("=== pfix Dependency Examples ===\n")

    print("Running package_traps.py tests:")
    print("-" * 40)
    exec(open("package_traps.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning version_conflicts.py tests:")
    print("-" * 40)
    exec(open("version_conflicts.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All dependency tests complete ===")


if __name__ == "__main__":
    main()
