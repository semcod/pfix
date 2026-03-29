#!/usr/bin/env python3
"""Realistic production patterns — API handler errors, data pipeline, config boot."""

from pfix import pfix


# --- 1. API handler with multiple failure points ---
@pfix(hint="Simulates a REST API handler with auth, validation, DB, serialization")
def handle_request(request: dict) -> dict:
    user = authenticate(request)
    payload = validate_payload(request)
    result = query_database(user, payload)
    return serialize_response(result)

def authenticate(request: dict) -> dict:
    token = request["headers"]["Authorization"]  # KeyError if no headers
    if not token.startswith("Bearer "):
        raise PermissionError("Invalid token format")
    return {"id": 1, "role": "user"}

def validate_payload(request: dict) -> dict:
    body = request["body"]
    if "query" not in body:
        raise ValueError("Missing required field: query")
    limit = int(body.get("limit", "10"))  # ValueError if non-numeric
    return {"query": body["query"], "limit": limit}

def query_database(user: dict, payload: dict) -> list:
    # Simulated DB results — some rows have missing fields
    return [
        {"id": 1, "name": "Item A", "price": 10.0},
        {"id": 2, "name": "Item B"},  # Missing 'price'
        {"id": 3, "name": "Item C", "price": None},  # price is None
    ]

def serialize_response(results: list) -> dict:
    total = sum(r["price"] for r in results)  # KeyError + TypeError (None)
    return {"items": results, "total": total, "count": len(results)}


# --- 2. ETL pipeline with schema mismatch ---
@pfix(hint="ETL: extract → transform → load — schema changed upstream")
def run_etl_pipeline():
    raw_data = extract_from_api()
    transformed = transform_records(raw_data)
    return load_to_output(transformed)

def extract_from_api() -> list[dict]:
    # Upstream API changed: 'user_name' → 'username'
    return [
        {"username": "alice", "email": "alice@example.com", "score": 95},
        {"username": "bob", "email": "bob@example.com", "score": 87},
    ]

def transform_records(records: list[dict]) -> list[dict]:
    return [
        {
            "name": r["user_name"].upper(),  # KeyError: 'user_name' (now 'username')
            "contact": r["email"],
            "grade": "A" if r["score"] >= 90 else "B",
        }
        for r in records
    ]

def load_to_output(records: list[dict]) -> str:
    import json
    return json.dumps(records, indent=2)


# --- 3. Config bootstrapping with env fallback chain ---
@pfix(hint="Config loaded from file → env → defaults. Multiple failure points.")
def bootstrap_config() -> dict:
    import json, os

    # Try file first
    config_path = os.getenv("APP_CONFIG", "/etc/myapp/config.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    # Merge with env vars — but env vars are strings, not typed
    config["port"] = int(os.getenv("PORT", config.get("port", "oops")))  # ValueError
    config["debug"] = os.getenv("DEBUG", config.get("debug", False))
    config["workers"] = int(os.getenv("WORKERS", config.get("workers", 4)))

    return config


if __name__ == "__main__":
    tests = [
        ("1. API handler — missing headers",
         lambda: handle_request({"body": {"query": "test"}})),

        ("1b. API handler — bad limit",
         lambda: handle_request({
             "headers": {"Authorization": "Bearer xyz"},
             "body": {"query": "test", "limit": "abc"},
         })),

        ("1c. API handler — None price in serialization",
         lambda: handle_request({
             "headers": {"Authorization": "Bearer xyz"},
             "body": {"query": "test"},
         })),

        ("2. ETL — schema changed (user_name → username)",
         lambda: run_etl_pipeline()),

        ("3. Config bootstrap — bad port default",
         lambda: bootstrap_config()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
