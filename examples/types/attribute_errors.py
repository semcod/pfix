#!/usr/bin/env python3
"""AttributeError & None propagation — wrong method names, None.attr access."""

from pfix import pfix


@pfix(hint="Dict has no .append(), should use list or dict[key]=val")
def collect_results(items):
    results = {}
    for item in items:
        results.append(item)  # AttributeError: dict has no .append()
    return results


@pfix(hint="String .split() returns list, not calling .strip() on list")
def clean_csv_line(line: str) -> list:
    parts = line.split(",")
    return parts.strip()  # AttributeError: list has no .strip()


@pfix(hint="Function returns None implicitly, caller accesses .data on None")
def get_user(user_id: int):
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    if user_id in users:
        return users[user_id]
    # implicit return None

def show_user_name(user_id: int) -> str:
    user = get_user(user_id)
    return user["name"]  # TypeError: NoneType is not subscriptable


@pfix(hint="Using .lenght instead of len()")
def check_size(items: list) -> bool:
    return items.lenght > 0  # AttributeError: typo .lenght → len(items)


@pfix(hint="Chained attribute access on possibly-None intermediate")
def parse_config(data: dict) -> str:
    return data.get("database").get("host")  # AttributeError if first .get returns None


@pfix(hint="Wrong method name on file object")
def read_first_line(path: str) -> str:
    with open(path) as f:
        return f.readLine()  # AttributeError: readLine → readline


if __name__ == "__main__":
    tests = [
        ("1. dict.append()", lambda: collect_results([1, 2, 3])),
        ("2. list.strip()", lambda: clean_csv_line("a, b, c")),
        ("3. None subscript", lambda: show_user_name(999)),
        ("4. .lenght typo", lambda: check_size([1, 2])),
        ("5. Chained None.get()", lambda: parse_config({"database": None})),
        ("6. .readLine() typo", lambda: read_first_line("/etc/hostname")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
