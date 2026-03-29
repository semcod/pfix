#!/usr/bin/env python3
"""Dependency issues — version conflicts, removed APIs, wrong extras."""

from pfix import pfix


@pfix(hint="Using removed API from old version of a package")
def use_deprecated_api():
    import collections
    # collections.MutableMapping removed in Python 3.10+
    # should use collections.abc.MutableMapping
    class MyDict(collections.MutableMapping):  # AttributeError in 3.10+
        pass


@pfix(hint="pkg_resources is deprecated in favor of importlib.metadata")
def get_package_version(name: str) -> str:
    import pkg_resources  # DeprecationWarning, removed in some envs
    return pkg_resources.get_distribution(name).version


@pfix(hint="Using function that was renamed in newer version")
def legacy_json_parse(data: str) -> dict:
    import json
    return json.read(data)  # AttributeError: json.read → json.loads


@pfix(hint="Missing optional dependency for feature — needs pfix[mcp]")
def start_mcp_server():
    from mcp.server.fastmcp import FastMCP  # ImportError if mcp not installed
    server = FastMCP("test")
    return server


if __name__ == "__main__":
    tests = [
        ("1. Removed API (MutableMapping)", lambda: use_deprecated_api()),
        ("2. Deprecated pkg_resources", lambda: get_package_version("pip")),
        ("3. Renamed function json.read", lambda: legacy_json_parse('{"a":1}')),
        ("4. Missing optional dep (mcp)", lambda: start_mcp_server()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
