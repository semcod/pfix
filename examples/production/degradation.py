#!/usr/bin/env python3
"""Graceful degradation — missing fallbacks, uncaught edge cases in production."""

from pfix import pfix


@pfix(hint="Cache lookup fails but no fallback to primary source")
def get_user_cached(user_id: int) -> dict:
    cache = {}  # Empty cache
    return cache[user_id]  # KeyError — should fallback to DB lookup


@pfix(hint="Feature flag check fails — entire feature crashes instead of degrading")
def render_dashboard(features: dict) -> str:
    sections = []
    sections.append(render_header())
    if features["analytics_v2"]:  # KeyError if flag not defined
        sections.append(render_analytics_v2())
    sections.append(render_footer())
    return "\n".join(sections)

def render_header(): return "<header>Dashboard</header>"
def render_footer(): return "<footer>© 2026</footer>"
def render_analytics_v2(): return "<div>Analytics V2</div>"


@pfix(hint="Retry without backoff or max attempts — infinite retry storm")
def fetch_with_bad_retry(url: str) -> dict:
    import time
    attempts = 0
    while True:
        attempts += 1
        try:
            raise ConnectionError(f"Attempt {attempts}: refused")
        except ConnectionError:
            if attempts > 5:
                raise  # Safety valve
            time.sleep(0)  # No backoff! Should be exponential
            continue


@pfix(hint="JSON response changed structure — 'data' key moved to 'results'")
def parse_api_v2_response() -> list:
    response = {
        "status": "ok",
        "results": [1, 2, 3],  # Was "data" in v1
        "meta": {"page": 1},
    }
    return response["data"]  # KeyError: 'data' (now 'results')


if __name__ == "__main__":
    tests = [
        ("1. Cache miss without fallback", lambda: get_user_cached(42)),
        ("2. Missing feature flag", lambda: render_dashboard({"dark_mode": True})),
        ("3. Retry storm (no backoff)", lambda: fetch_with_bad_retry("http://localhost")),
        ("4. API response schema change", lambda: parse_api_v2_response()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
