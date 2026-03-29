#!/usr/bin/env python3
"""Environment — venv detection, Python version guards, sys.path problems."""

from pfix import pfix


@pfix(hint="Code uses match/case (3.10+) but might run on 3.9")
def classify_status(code: int) -> str:
    # SyntaxError on Python < 3.10 — but pfix can only catch this at import time
    # Simulating with if/elif that's missing a branch:
    if code == 200:
        return "ok"
    elif code == 404:
        return "not_found"
    elif code == 500:
        return "server_error"
    # Missing: what if code is 301, 403, etc.?
    # No else clause — returns None implicitly
    return None  # Bug: should raise or have default


@pfix(hint="sys.path pollution — importing from wrong location")
def test_sys_path_issue():
    import sys

    # Simulating: someone added '' to sys.path, causing local module to shadow stdlib
    # Check if current dir is in sys.path (it usually is, but can cause issues)
    if "" in sys.path or "." in sys.path:
        # This is normal for scripts but dangerous for packages
        pass

    # Check if site-packages is accessible
    import site
    sp = site.getsitepackages()
    if not sp:
        raise EnvironmentError("No site-packages found — broken venv?")

    return f"sys.path has {len(sys.path)} entries, site-packages at {sp[0]}"


@pfix(hint="Running without venv — packages installed globally")
def check_venv_active() -> dict:
    import sys, os

    in_venv = sys.prefix != sys.base_prefix
    venv_path = os.environ.get("VIRTUAL_ENV", None)

    if not in_venv:
        raise EnvironmentError(
            "Not running in a virtual environment! "
            "Global pip install can break system Python. "
            "Run: python -m venv .venv && source .venv/bin/activate"
        )

    return {
        "venv": True,
        "prefix": sys.prefix,
        "venv_path": venv_path,
        "python": sys.executable,
    }


@pfix(hint="Wrong Python version for type syntax")
def test_version_features() -> dict:
    import sys
    v = sys.version_info

    features = {}

    # Check which features are available
    if v >= (3, 10):
        features["match_case"] = True
        features["union_type_x_or_y"] = True
    if v >= (3, 11):
        features["tomllib"] = True
        features["exception_groups"] = True
    if v >= (3, 12):
        features["type_statement"] = True

    # Simulate using a feature that requires newer Python
    if "tomllib" not in features:
        raise RuntimeError(
            f"Python {v.major}.{v.minor} detected. "
            f"This code requires Python 3.11+ for tomllib. "
            f"Fallback: pip install tomli"
        )

    return features


if __name__ == "__main__":
    tests = [
        ("1. Missing else in status classify", lambda: classify_status(301)),
        ("2. sys.path inspection", lambda: test_sys_path_issue()),
        ("3. Venv activation check", lambda: check_venv_active()),
        ("4. Python version features", lambda: test_version_features()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            result = fn()
            print(f"   OK: {result}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
