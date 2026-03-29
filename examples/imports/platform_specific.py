#!/usr/bin/env python3
"""Platform & version conditional imports — wrong guards, missing fallbacks."""

from pfix import pfix


@pfix(hint="Using Python 3.11+ tomllib without fallback for 3.10")
def load_toml(path: str) -> dict:
    import tomllib  # ModuleNotFoundError on Python < 3.11

    with open(path, "rb") as f:
        return tomllib.load(f)


@pfix(hint="Linux-only module on any platform — no OS check")
def get_inotify_events():
    import inotify.adapters  # Only exists on Linux, not macOS/Windows

    i = inotify.adapters.Inotify()
    i.add_watch("/tmp")
    return list(i.event_gen(timeout_s=1))


@pfix(hint="Using typing.Self (3.11+) without future import or fallback")
def test_self_type():
    from typing import Self  # ImportError on Python < 3.11

    class Builder:
        def set_name(self, name: str) -> Self:
            self.name = name
            return self

    return Builder().set_name("test")


@pfix(hint="Forgot to install optional extras — needs pfix[mcp]")
def test_optional_extra():
    from mcp.server.fastmcp import FastMCP  # ImportError without mcp extra

    server = FastMCP("test")
    return server


if __name__ == "__main__":
    import sys
    print(f"Python {sys.version}\n")

    tests = [
        ("1. tomllib (3.11+ only)", lambda: load_toml("pyproject.toml")),
        ("2. inotify (Linux only)", lambda: get_inotify_events()),
        ("3. typing.Self (3.11+)", lambda: test_self_type()),
        ("4. Optional extra (mcp)", lambda: test_optional_extra()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
