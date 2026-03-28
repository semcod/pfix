"""
pfix.multi_fix — Multi-file fix analysis.

For errors spanning multiple files (imports, inheritance, cross-file dependencies).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rich.console import Console

from .analyzer import ErrorContext
from .types import FixProposal

console = Console(stderr=True)


@dataclass
class MultiFileFixProposal:
    """Fix proposal affecting multiple files."""

    files: dict[str, str]  # {path: new_content}
    dependencies: list[str]
    diagnosis: str
    confidence: float
    primary_file: str = ""  # The file where error originated


def find_related_files(
    source_file: Path,
    error_ctx: ErrorContext,
    max_depth: int = 2,
) -> list[Path]:
    """
    Find files related to the error through imports.

    Args:
        source_file: File where error occurred
        error_ctx: Error context
        max_depth: How many levels of imports to follow

    Returns:
        List of related file paths
    """
    related = set()
    to_process = [(source_file, 0)]
    processed = set()

    project_root = source_file.parent

    while to_process:
        current, depth = to_process.pop(0)

        if current in processed or depth > max_depth:
            continue
        processed.add(current)

        if not current.exists():
            continue

        try:
            content = current.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    # Try to resolve relative imports
                    if module.startswith("."):
                        # Relative import
                        base = current.parent
                    else:
                        # Absolute import - look in project
                        base = project_root

                    parts = module.split(".")
                    candidate = base / "/".join(parts) + ".py"

                    if candidate.exists():
                        related.add(candidate)
                        to_process.append((candidate, depth + 1))

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        # Look for local module
                        candidate = project_root / f"{name}.py"
                        if candidate.exists():
                            related.add(candidate)
                            to_process.append((candidate, depth + 1))

        except (SyntaxError, UnicodeDecodeError):
            continue

    return sorted(related)


def build_multi_file_context(
    error_ctx: ErrorContext,
    related_files: list[Path],
) -> str:
    """
    Build LLM prompt with multiple files.

    Returns prompt text including all relevant files.
    """
    parts = [
        "## Error Report (Multi-file Analysis)",
        f"**Exception**: `{error_ctx.exception_type}: {error_ctx.exception_message}`",
        f"**Primary File**: `{error_ctx.source_file}` line {error_ctx.line_number}",
        f"**Function**: `{error_ctx.function_name}`",
        "",
        "### Traceback",
        f"```\n{error_ctx.traceback_text}\n```",
    ]

    # Add primary file
    if error_ctx.source_code:
        parts += [
            "",
            f"### Primary File: {error_ctx.source_file}",
            f"```python\n{error_ctx.source_code[:3000]}\n```",
        ]

    # Add related files
    for i, file_path in enumerate(related_files[:3], 1):  # Max 3 related files
        try:
            content = file_path.read_text(encoding="utf-8")
            # Truncate large files
            if len(content) > 2000:
                content = content[:2000] + "\n# ... (truncated)"

            parts += [
                "",
                f"### Related File {i}: {file_path}",
                f"```python\n{content}\n```",
            ]
        except Exception:
            continue

    # Add instructions for multi-file fix
    parts += [
        "",
        "### Multi-File Fix Instructions",
        "Return JSON with 'files' object mapping file paths to new content:",
        '{',
        '  "files": {',
        f'    "{error_ctx.source_file}": "new content here",',
        '    "other/file.py": "other content"',
        '  },',
        '  "dependencies": ["package>=1.0"],',
        '  "diagnosis": "explanation",',
        '  "confidence": 0.85',
        '}',
    ]

    return "\n".join(parts)


def parse_multi_file_response(raw: str) -> Optional[MultiFileFixProposal]:
    """
    Parse LLM response for multi-file fix.

    Args:
        raw: Raw LLM response text

    Returns:
        MultiFileFixProposal or None if parsing fails
    """
    import json
    import re

    # Extract JSON from response
    text = raw.strip()

    # Look for JSON block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    elif not text.startswith("{"):
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            text = text[s : e + 1]

    try:
        data = json.loads(text)

        return MultiFileFixProposal(
            files=data.get("files", {}),
            dependencies=data.get("dependencies", []),
            diagnosis=data.get("diagnosis", ""),
            confidence=float(data.get("confidence", 0.0)),
            primary_file=list(data.get("files", {}).keys())[0] if data.get("files") else "",
        )
    except (json.JSONDecodeError, KeyError) as e:
        console.print(f"[yellow]⚠ Failed to parse multi-file response: {e}[/]")
        return None


def apply_multi_file_fix(
    proposal: MultiFileFixProposal,
    project_root: Path,
    create_backups: bool = True,
) -> dict[str, bool]:
    """
    Apply multi-file fix proposal.

    Args:
        proposal: Multi-file fix proposal
        project_root: Root directory of project
        create_backups: Whether to create .bak files

    Returns:
        Dict of {filepath: success}
    """
    results = {}

    for relative_path, new_content in proposal.files.items():
        filepath = project_root / relative_path

        if not filepath.exists():
            console.print(f"[yellow]⚠ File not found: {filepath}[/]")
            results[relative_path] = False
            continue

        try:
            # Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                console.print(f"[red]✗ Syntax error in {relative_path}: {e}[/]")
                results[relative_path] = False
                continue

            # Backup
            if create_backups:
                backup = filepath.with_suffix(filepath.suffix + ".bak")
                backup.write_text(filepath.read_text(encoding="utf-8"), encoding="utf-8")

            # Write
            filepath.write_text(new_content, encoding="utf-8")
            console.print(f"[green]✓ Applied fix to {relative_path}[/]")
            results[relative_path] = True

        except Exception as e:
            console.print(f"[red]✗ Failed to apply fix to {relative_path}: {e}[/]")
            results[relative_path] = False

    return results
