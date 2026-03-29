#!/usr/bin/env python3
"""Environment errors — missing env vars, wrong types, venv issues."""

from pfix import pfix


@pfix(hint="Env var not set — os.environ[] raises KeyError, should use os.getenv()")
def get_database_url() -> str:
    import os
    return os.environ["DATABASE_URL"]  # KeyError if not set


@pfix(hint="Env var is string '0' but treated as falsy int")
def get_port() -> int:
    import os
    port = os.getenv("PORT")  # Returns None if not set
    return int(port)  # TypeError: int() argument must be a string, not NoneType


@pfix(hint="Boolean env var compared as string, not parsed")
def is_debug_mode() -> bool:
    import os
    debug = os.getenv("DEBUG", "false")
    if debug:  # Always True! Non-empty string "false" is truthy
        return True
    return False


@pfix(hint="HOME dir different in Docker/CI — hardcoded path fails")
def read_user_config() -> dict:
    import json
    config_path = "/home/tom/.config/myapp/config.json"  # Hardcoded user path
    with open(config_path) as f:
        return json.load(f)


if __name__ == "__main__":
    tests = [
        ("1. Missing DATABASE_URL", lambda: get_database_url()),
        ("2. None to int()", lambda: get_port()),
        ("3. 'false' is truthy", lambda: is_debug_mode()),
        ("4. Hardcoded /home/tom/", lambda: read_user_config()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            result = fn()
            print(f"   OK: {result}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
