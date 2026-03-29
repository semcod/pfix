"""
pfix Encoding Examples — Main Entry Point

Demonstrates Unicode and codec errors.
"""

import pfix


def main():
    print("=== pfix Encoding Examples ===\n")

    print("Running codec_errors.py tests:")
    print("-" * 40)
    exec(open("codec_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\nRunning unicode_errors.py tests:")
    print("-" * 40)
    exec(open("unicode_errors.py").read(), {"__name__": "__main__", "pfix": pfix})

    print("\n\n=== All encoding tests complete ===")


if __name__ == "__main__":
    main()
