#!/usr/bin/env python3
"""Missing third-party module — pfix should auto-install via pip/uv."""

from pfix import pfix


@pfix(hint="Fetches JSON from HTTP API")
def fetch_api_data(url: str) -> dict:
    import httpx  # not installed by default

    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


@pfix(hint="Parses YAML configuration file")
def load_yaml_config(path: str) -> dict:
    import yaml  # PyYAML — module name != package name

    with open(path) as f:
        return yaml.safe_load(f)


@pfix(hint="Generates a UUID-based filename")
def generate_filename(prefix: str) -> str:
    import shortuuid  # niche package, unlikely to be installed

    return f"{prefix}_{shortuuid.uuid()}.txt"


if __name__ == "__main__":
    # Each call triggers ModuleNotFoundError → pfix installs → retries
    print("1. httpx (direct name match):")
    try:
        print(f"   {fetch_api_data('https://httpbin.org/json')}")
    except Exception as e:
        print(f"   FAIL: {e}")

    print("\n2. PyYAML (module='yaml', package='pyyaml'):")
    try:
        print(f"   {load_yaml_config('/dev/null')}")
    except Exception as e:
        print(f"   FAIL: {e}")

    print("\n3. shortuuid (niche package):")
    try:
        print(f"   {generate_filename('report')}")
    except Exception as e:
        print(f"   FAIL: {e}")
