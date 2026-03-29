#!/usr/bin/env python3
"""FileNotFoundError — missing files, wrong paths, relative vs absolute."""

from pfix import pfix


@pfix(hint="File path is relative but CWD is different from expected")
def load_config() -> dict:
    import json
    with open("config.json") as f:  # FileNotFoundError: config.json doesn't exist
        return json.load(f)


@pfix(hint="Typo in extension: .ymal instead of .yaml")
def load_settings() -> dict:
    import json
    with open("settings.ymal") as f:  # typo: .ymal → .yaml
        return json.load(f)


@pfix(hint="Missing parent directory — should create it first")
def save_report(data: str):
    output_dir = "/tmp/pfix_test/reports/2026/q1"
    filepath = f"{output_dir}/report.txt"
    with open(filepath, "w") as f:  # FileNotFoundError: parent dir doesn't exist
        f.write(data)


@pfix(hint="Using ~ without expanduser()")
def read_ssh_key() -> str:
    with open("~/.ssh/id_rsa.pub") as f:  # ~ not expanded
        return f.read()


@pfix(hint="Path separator wrong for OS")
def read_cross_platform(filename: str) -> str:
    path = "data\\files\\" + filename  # backslash on Linux
    with open(path) as f:
        return f.read()


if __name__ == "__main__":
    tests = [
        ("1. Missing config.json", lambda: load_config()),
        ("2. Typo in extension", lambda: load_settings()),
        ("3. Missing parent directory", lambda: save_report("Q1 Results")),
        ("4. Unexpanded ~", lambda: read_ssh_key()),
        ("5. Wrong path separator", lambda: read_cross_platform("test.txt")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
