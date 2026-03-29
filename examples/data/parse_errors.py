#!/usr/bin/env python3
"""Data processing errors — KeyError, IndexError, ValueError, JSON/CSV parse."""

from pfix import pfix


@pfix(hint="Dict key 'email' missing — should use .get() with default")
def extract_email(user: dict) -> str:
    return user["email"]  # KeyError if key missing


@pfix(hint="List index out of range — empty list or wrong index")
def get_third_element(items: list):
    return items[2]  # IndexError if < 3 elements


@pfix(hint="int() with non-numeric string")
def parse_user_age(age_str: str) -> int:
    return int(age_str)  # ValueError: invalid literal for int()


@pfix(hint="JSON with trailing comma — invalid JSON")
def parse_json_response(raw: str) -> dict:
    import json
    return json.loads(raw)  # json.JSONDecodeError


@pfix(hint="CSV with inconsistent column count")
def parse_csv_data(csv_text: str) -> list[dict]:
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(csv_text))
    rows = []
    for row in reader:
        # Force access to column that might not exist in all rows
        rows.append({
            "name": row["name"],
            "score": int(row["score"]),  # ValueError if empty or missing
            "grade": row["grade"],       # KeyError if column missing in some rows
        })
    return rows


@pfix(hint="Unpacking wrong number of values")
def parse_coordinate(coord_str: str) -> tuple:
    x, y, z = coord_str.split(",")  # ValueError if not exactly 3 parts
    return float(x), float(y), float(z)


if __name__ == "__main__":
    tests = [
        ("1. KeyError: missing dict key",
         lambda: extract_email({"name": "Alice", "age": 30})),

        ("2. IndexError: list too short",
         lambda: get_third_element([10, 20])),

        ("3. ValueError: non-numeric string",
         lambda: parse_user_age("twenty-five")),

        ("4. JSONDecodeError: trailing comma",
         lambda: parse_json_response('{"name": "Bob", "age": 25,}')),

        ("5. CSV: missing column",
         lambda: parse_csv_data("name,score\nAlice,95\nBob,")),

        ("6. ValueError: wrong unpack count",
         lambda: parse_coordinate("1.0,2.0")),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
