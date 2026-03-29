"""Shared demo functions for pfix examples.

This module contains common demo functions used across multiple example files
to eliminate code duplication.
"""

from pfix import pfix


@pfix(deps=["requests"])
def fetch_json(url: str) -> dict:
    """Fetch JSON from URL — dependencies auto-installed on first run."""
    import requests
    return requests.get(url).json()


@pfix(retries=2)
def average(numbers: list[float]) -> float:
    """Calculate average — ZeroDivisionError will be auto-fixed."""
    if len(numbers) == 0:
        return float('nan')
    return sum(numbers) / len(numbers)


@pfix(retries=2)
def greet(name: str, age: int) -> str:
    """Greet user — TypeError will be auto-fixed."""
    return "Hello " + name + "! Age: " + age  # Bug: str + int
