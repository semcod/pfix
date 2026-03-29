#!/usr/bin/env python3
"""Dependency traps — wrong package with same name, extras needed, version pinning."""

from pfix import pfix


@pfix(hint="PyPI has malicious/wrong package with similar name")
def test_wrong_package():
    # 'python-json' is NOT the stdlib json — it's a different PyPI package
    # People sometimes pip install json and get confused
    import json
    data = json.loads('{"key": "value"}')
    return data


@pfix(hint="Need 'requests[security]' extras for SNI support")
def fetch_sni_url():
    import requests
    # Some older systems need pyOpenSSL for SNI
    return requests.get("https://example.com", verify=True).status_code


@pfix(hint="Installed 'Pillow' but importing 'PIL.Image' fails on some installs")
def resize_image():
    from PIL import Image  # ImportError if Pillow not installed correctly

    img = Image.new("RGB", (100, 100), color="red")
    img = img.resize((50, 50))
    return f"Image: {img.size}"


@pfix(hint="Multiple packages provide same module — conflict")
def test_namespace_conflict():
    # Both 'google-cloud-storage' and 'google-auth' provide 'google' namespace
    # Installing one without the other can break imports
    from google.cloud import storage  # ImportError: various reasons
    return storage


if __name__ == "__main__":
    tests = [
        ("1. stdlib json (should just work)", lambda: test_wrong_package()),
        ("2. requests SNI support", lambda: fetch_sni_url()),
        ("3. PIL/Pillow import", lambda: resize_image()),
        ("4. Google namespace conflict", lambda: test_namespace_conflict()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")
