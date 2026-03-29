#!/usr/bin/env python3
"""Production scenarios — error chains, partial failures, cascading errors."""

from pfix import pfix


# --- 1. Error chain: one failure causes cascade ---
@pfix(hint="Config load fails → DB init fails → API fails. Fix root cause.")
def start_application():
    config = load_db_config()
    db = connect_database(config)
    return serve_api(db)

def load_db_config() -> dict:
    import json
    # Root cause: config file missing
    with open("/etc/myapp/database.json") as f:
        return json.load(f)

def connect_database(config: dict):
    return {"connection": f"postgres://{config['host']}:{config['port']}"}

def serve_api(db):
    return f"API running with {db}"


# --- 2. Partial failure in batch processing ---
@pfix(hint="Some items fail, some succeed. Should collect errors, not abort all.")
def process_batch(items: list) -> dict:
    results = {"success": [], "errors": []}
    for item in items:
        processed = transform_item(item)  # May raise for some items
        results["success"].append(processed)
    return results

def transform_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "value": int(item["value"]),        # ValueError if not numeric
        "ratio": item["value"] / item["count"],  # ZeroDivisionError if count=0
    }


# --- 3. Retry-worthy transient error ---
@pfix(hint="Simulated transient failure — succeeds on 3rd try")
def fetch_with_transient_failure():
    import random
    if not hasattr(fetch_with_transient_failure, "_attempts"):
        fetch_with_transient_failure._attempts = 0
    fetch_with_transient_failure._attempts += 1

    if fetch_with_transient_failure._attempts < 3:
        raise ConnectionError(f"Attempt {fetch_with_transient_failure._attempts}: server busy")
    return {"status": "ok", "attempt": fetch_with_transient_failure._attempts}


# --- 4. Resource cleanup failure ---
@pfix(hint="Exception during cleanup masks the original error")
def process_with_cleanup():
    resource = acquire_resource()
    try:
        result = do_work(resource)
        return result
    finally:
        release_resource(resource)  # This also raises!

def acquire_resource():
    return {"handle": 42, "name": "temp_file"}

def do_work(resource):
    raise ValueError("Processing failed: corrupt data")

def release_resource(resource):
    raise OSError("Cannot release: file already deleted")


if __name__ == "__main__":
    tests = [
        ("1. Error chain (config → DB → API)",
         lambda: start_application()),

        ("2. Partial batch failure",
         lambda: process_batch([
             {"id": 1, "value": "100", "count": 5},
             {"id": 2, "value": "abc", "count": 3},  # ValueError
             {"id": 3, "value": "200", "count": 0},   # ZeroDivisionError
         ])),

        ("3. Transient failure (retry-worthy)",
         lambda: fetch_with_transient_failure()),

        ("4. Exception in cleanup (finally)",
         lambda: process_with_cleanup()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
