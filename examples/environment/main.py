"""
pfix Environment Examples — Main Entry Point

Demonstrates env var and venv issues.
"""

import pfix


def main():
    print("=== pfix Environment Examples ===\n")

    print("Running env_var_errors.py tests:")
    print("-" * 40)
    exec(open("env_var_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning venv_issues.py tests:")
    print("-" * 40)
    exec(open("venv_issues.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All environment tests complete ===")


if __name__ == "__main__":
    main()
