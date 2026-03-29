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
    """Find files related to the error through imports."""
    related = set()
    to_process = [(source_file, 0)]
    processed = set()
    project_root = source_file.parent

    while to_process:
        current, depth = to_process.pop(0)

        if current in processed or depth > max_depth or not current.exists():
            continue
        processed.add(current)

        for module_name, is_relative in _extract_imports_from_file(current):
            candidate = _resolve_import_path(module_name, current, project_root, is_relative)
            if candidate and candidate.exists():
                related.add(candidate)
                to_process.append((candidate, depth + 1))

    return sorted(related)


def _extract_imports_from_file(filepath: Path) -> list[tuple[str, bool]]:
    """Extract list of (module_name, is_relative) from a Python file."""
    imports = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module, node.level > 0 or node.module.startswith(".")))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name.split(".")[0], False))
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


def _resolve_import_path(module_name: str, current_file: Path, project_root: Path, is_relative: bool) -> Optional[Path]:
    """Resolve a module name to a filesystem path."""
    if is_relative:
        base = current_file.parent
    else:
        base = project_root

    parts = module_name.split(".")
    candidate = base / "/".join(parts)
    
    # Try .py and /__init__.py
    py_file = candidate.with_suffix(".py")
    if py_file.exists():
        return py_file
    
    init_file = candidate / "__init__.py"
    if init_file.exists():
        return init_file
        
    return None


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
