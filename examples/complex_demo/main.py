"""
pfix Complex Demo — Data Processing Library

Zero-config example: just `import pfix`, configuration is in pyproject.toml
"""

import pfix


def load_and_process_data(filepath: str) -> dict:
    """Load CSV, process it, return statistics."""
    import pandas as pd  # Will auto-install if missing

    # Bug 1: FileNotFoundError if file doesn't exist
    df = pd.read_csv(filepath)

    # Bug 2: Type error - column name as integer instead of string
    result = {
        "mean_age": df[age].mean(),  # 'age' should be "age"
        "count": len(df),
        "columns": list(df.columns),
    }

    # Bug 3: Logic error - divide by zero if DataFrame is empty
    avg_salary = df["salary"].sum() / len(df)

    result["avg_salary"] = avg_salary
    return result


def analyze_users(users: list[dict]) -> dict:
    """Analyze user data with multiple bugs."""
    import json

    # Bug 4: TypeError - can't add int to str
    total_score = 0
    for user in users:
        total_score += user["score"]  # score might be string

    # Bug 5: KeyError - field might not exist
    names = [user["name"] for user in users]

    # Bug 6: AttributeError - wrong method name
    result = {
        "total": len(users),
        "avg_score": total_score / len(users),
        "names": names.sort(),  # .sort() returns None
    }

    return result


def main():
    print("=== pfix Complex Demo (pyproject.toml config) ===\n")

    print("1. Processing CSV file:")
    stats = load_and_process_data("data/users.csv")
    print(f"   ✓ Stats: {stats}")

    print("\n2. Analyzing user list:")
    test_users = [
        {"name": "Alice", "score": 100},
        {"name": "Bob", "score": "85"},  # String score - will cause TypeError
        {"name": "Charlie"},  # Missing score - will cause KeyError
    ]
    result = analyze_users(test_users)
    print(f"   ✓ Result: {result}")

    print("\n3. Final check:")
    print("   ✓ Demo complete!")


if __name__ == "__main__":
    main()
