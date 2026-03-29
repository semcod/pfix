#!/usr/bin/env python3
"""Network errors — connection refused, timeout, DNS, bad URL."""

from pfix import pfix


@pfix(hint="Connection refused — service not running on this port")
def connect_to_database():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    sock.connect(("127.0.0.1", 54321))  # ConnectionRefusedError
    return sock


@pfix(hint="DNS resolution fails — misspelled hostname")
def fetch_from_typo_domain():
    import urllib.request
    url = "https://api.exmaple.com/data"  # typo: exmaple → example
    return urllib.request.urlopen(url, timeout=3).read()


@pfix(hint="Timeout on slow endpoint — should increase timeout or retry")
def call_slow_api():
    import urllib.request
    url = "https://httpbin.org/delay/30"
    return urllib.request.urlopen(url, timeout=1).read()  # TimeoutError


@pfix(hint="HTTP error 404 not handled — should check status code")
def download_missing_file():
    import urllib.request, urllib.error
    url = "https://httpbin.org/status/404"
    return urllib.request.urlopen(url).read()  # HTTPError 404


if __name__ == "__main__":
    tests = [
        ("1. Connection refused (port 54321)", lambda: connect_to_database()),
        ("2. DNS fail (typo domain)", lambda: fetch_from_typo_domain()),
        ("3. Timeout (1s on 30s endpoint)", lambda: call_slow_api()),
        ("4. HTTP 404 not handled", lambda: download_missing_file()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
