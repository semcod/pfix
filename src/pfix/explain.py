"""
pfix.explain — Educational mode: explain errors and fixes.

Usage:
    pfix explain last        # Explain the last error/fix
    pfix explain TypeError   # General lesson about TypeError
    pfix explain --file src/x.py:42  # Explain specific line
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .config import get_config
from .llm import SYSTEM_PROMPT

console = Console()


EXPLAIN_PROMPT = """\
You are pfix — an educational Python assistant.

Explain the error or concept in a way that teaches the developer:
1. What caused the error (root cause)
2. Why it's a problem
3. How to prevent it in the future
4. Best practices related to this issue

Use simple language but be technically accurate. Include code examples.
"""


def explain_last() -> str:
    """Explain the most recent error from logs."""
    log_dir = Path(".pfix_logs")

    # Find most recent log file
    if not log_dir.exists():
        return "No error logs found. Run some code with pfix first."

    log_files = sorted(log_dir.glob("pfix_*.jsonl"), reverse=True)
    if not log_files:
        return "No error logs found."

    # Read last entry from most recent file
    latest = log_files[0]
    lines = latest.read_text().strip().split("\n")
    if not lines:
        return "Log file is empty."

    try:
        last_entry = json.loads(lines[-1])
    except json.JSONDecodeError:
        return "Could not parse log file."

    # Extract error info
    exc_type = last_entry.get("exception_type", "Unknown")
    exc_msg = last_entry.get("exception_message", "No message")
    diagnosis = last_entry.get("diagnosis", "No diagnosis available")

    return _generate_explanation(exc_type, exc_msg, diagnosis)


def explain_exception_type(exc_type: str) -> str:
    """Generate general educational content about an exception type."""
    explanations = {
        "TypeError": """
## TypeError: Type Mismatch

**What it means:** You tried to perform an operation on incompatible types.

**Common causes:**
- Adding string + number: `"5" + 3`
- Calling a method that doesn't exist for the type
- Passing wrong type to function

**How to prevent:**
- Use type hints
- Validate inputs with `isinstance()`
- Convert types explicitly: `int("5")` or `str(3)`

**Example fix:**
```python
# Bad
age = input("Age: ")  # Returns string
next_year = age + 1   # TypeError!

# Good
age = int(input("Age: "))
next_year = age + 1
```
""",
        "KeyError": """
## KeyError: Missing Dictionary Key

**What it means:** You tried to access a key that doesn't exist in a dict.

**Common causes:**
- Typo in key name
- Key was never added
- Key was deleted

**How to prevent:**
- Use `.get()` with default: `d.get("key", "default")`
- Check first: `if "key" in d:`
- Use `collections.defaultdict`

**Example fix:**
```python
# Bad
value = my_dict["missing_key"]  # KeyError!

# Good
value = my_dict.get("missing_key", "default_value")
```
""",
        "IndexError": """
## IndexError: List Index Out of Range

**What it means:** You tried to access an index that doesn't exist.

**Common causes:**
- Empty list
- Index >= length
- Off-by-one errors

**How to prevent:**
- Check length: `if i < len(lst):`
- Use slicing: `lst[:5]` (won't error)
- Handle empty lists

**Example fix:**
```python
# Bad
first = my_list[0]  # IndexError if empty!

# Good
first = my_list[0] if my_list else None
```
""",
        "AttributeError": """
## AttributeError: Missing Attribute

**What it means:** You tried to access an attribute/method that doesn't exist.

**Common causes:**
- Typo in attribute name
- Wrong object type
- None value

**How to prevent:**
- Use `hasattr()` to check
- Use `getattr()` with default
- Validate objects before use

**Example fix:**
```python
# Bad
result = obj.nme  # Typo: AttributeError!

# Good
result = getattr(obj, "name", "default")
```
""",
        "ModuleNotFoundError": """
## ModuleNotFoundError: Import Failed

**What it means:** Python couldn't find the module you're importing.

**Common causes:**
- Package not installed
- Wrong Python environment
- Typo in module name

**How to prevent:**
- Use virtual environments
- Keep requirements.txt updated
- Use absolute imports

**Example fix:**
```bash
# Install missing package
pip install package_name
```
""",
    }

    if exc_type in explanations:
        return explanations[exc_type]

    # Generate generic explanation for other types
    return f"""
## {exc_type}

**What it means:** This is a standard Python exception.

**To learn more:**
- Check Python docs: https://docs.python.org/3/library/exceptions.html
- Search Stack Overflow for "{exc_type} python"
- Look at the full traceback to find where it occurred

**General debugging tips:**
1. Read the error message carefully
2. Check the line number in the traceback
3. Look at the types of values involved
4. Add print() statements to inspect state
"""


def _generate_explanation(exc_type: str, exc_msg: str, diagnosis: str) -> str:
    """Generate explanation text."""
    parts = []

    # Header
    parts.append(f"# Understanding: {exc_type}")
    parts.append("")

    # The error
    parts.append("## The Error")
    parts.append(f"```")
    parts.append(f"{exc_type}: {exc_msg}")
    parts.append(f"```")
    parts.append("")

    # Diagnosis if available
    if diagnosis:
        parts.append("## Diagnosis")
        parts.append(diagnosis)
        parts.append("")

    # Educational content
    parts.append(explain_exception_type(exc_type))

    return "\n".join(parts)


def explain(
    what: str = "last",
    file: Optional[str] = None,
) -> None:
    """
    Main entry point for explain command.

    Args:
        what: "last" or exception type name
        file: Optional file:line reference
    """
    if file:
        # Explain specific file location
        console.print(Panel(f"Explaining: {file}", title="pfix explain"))
        console.print("[yellow]File-specific explanations coming soon![/]")
        return

    if what == "last":
        explanation = explain_last()
    else:
        # Explain exception type
        explanation = explain_exception_type(what)

    # Display with rich
    console.print(Markdown(explanation))
