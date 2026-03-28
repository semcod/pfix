"""
pfix.integrations.pytest_plugin — pytest plugin for auto-fixing failing tests.

Usage:
    pytest --pfix-auto-fix    # Auto-fix failing tests
    pytest --pfix-diagnose    # Show diagnosis without fixing

# conftest.py
pytest_plugins = ["pfix.integrations.pytest_plugin"]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from pfix.analyzer import analyze_exception
from pfix.fixer import apply_fix
from pfix.llm import request_fix


# pytest hooks
def pytest_addoption(parser: pytest.Parser) -> None:
    """Add pfix options to pytest."""
    group = parser.getgroup("pfix", "Self-healing Python tests")
    group.addoption(
        "--pfix-auto-fix",
        action="store_true",
        default=False,
        help="Automatically fix failing tests with LLM",
    )
    group.addoption(
        "--pfix-diagnose",
        action="store_true",
        default=False,
        help="Show pfix diagnosis for failures without fixing",
    )
    group.addoption(
        "--pfix-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold for auto-fix (default: 0.5)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pfix plugin."""
    config._pfix_auto_fix = config.getoption("--pfix-auto-fix")
    config._pfix_diagnose = config.getoption("--pfix-diagnose")
    config._pfix_confidence = config.getoption("--pfix-confidence")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Any:
    """Hook to analyze and fix test failures."""
    outcome = yield
    report = outcome.get_result()

    if not report.failed:
        return

    # Get pytest config
    config = item.config
    auto_fix = getattr(config, "_pfix_auto_fix", False)
    diagnose = getattr(config, "_pfix_diagnose", False)
    min_confidence = getattr(config, "_pfix_confidence", 0.5)

    if not auto_fix and not diagnose:
        return

    # Get the exception
    excinfo = call.excinfo
    if excinfo is None:
        return

    exc = excinfo.value
    exc_type = excinfo.type

    # Get the test function
    test_func = item.obj

    try:
        # Analyze with pfix
        ctx = analyze_exception(exc, func=test_func)
        proposal = request_fix(ctx)

        # Add to report
        if diagnose or auto_fix:
            report._pfix_diagnosis = proposal.diagnosis
            report._pfix_fix_description = proposal.fix_description
            report._pfix_confidence = proposal.confidence

        # Apply fix if requested and confidence is high enough
        if auto_fix and proposal.confidence >= min_confidence:
            if proposal.has_code_fix or proposal.has_dependency_fix:
                applied = apply_fix(ctx, proposal, confirm=False)
                report._pfix_applied = applied

                # Re-run the test to see if it passes now
                if applied:
                    # Mark for re-run
                    item._pfix_retry = True

    except Exception:
        # Silently ignore pfix errors
        pass


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Print pfix summary after tests."""
    config = terminalreporter.config
    auto_fix = getattr(config, "_pfix_auto_fix", False)
    diagnose = getattr(config, "_pfix_diagnose", False)

    if not auto_fix and not diagnose:
        return

    lines = []
    lines.append("")
    lines.append("=" * 50)
    lines.append("pfix Analysis Summary")
    lines.append("=" * 50)

    failures = terminalreporter.stats.get("failed", [])
    pfix_count = 0
    fixed_count = 0

    for report in failures:
        if hasattr(report, "_pfix_diagnosis"):
            pfix_count += 1
            lines.append(f"")
            lines.append(f"Test: {report.nodeid}")
            lines.append(f"Confidence: {report._pfix_confidence:.0%}")
            lines.append(f"Diagnosis: {report._pfix_diagnosis}")

            if hasattr(report, "_pfix_fix_description"):
                lines.append(f"Proposed fix: {report._pfix_fix_description}")

            if hasattr(report, "_pfix_applied"):
                if report._pfix_applied:
                    lines.append("✓ Fix applied!")
                    fixed_count += 1
                else:
                    lines.append("✗ Fix not applied")

    if pfix_count == 0:
        lines.append("No failures analyzed by pfix")
    else:
        lines.append("")
        lines.append(f"Analyzed: {pfix_count}, Fixed: {fixed_count}")

    terminalreporter.write_lines(lines)


# Hook to retry tests after fix
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item) -> bool:
    """Retry tests that were fixed by pfix."""
    if not hasattr(item, "_pfix_retry"):
        return False  # Let pytest handle normally

    # Re-run the test
    from _pytest.runner import runtestprotocol

    reports = runtestprotocol(item, log=False, nextitem=nextitem)

    # Check if it passed now
    for report in reports:
        if report.when == "call":
            if report.passed:
                # Add a note that it was fixed
                report._pfix_was_fixed = True

    return True
