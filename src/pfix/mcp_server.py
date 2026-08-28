"""
pfix.mcp_server — MCP Server using FastMCP from the official SDK.

Exposes pfix tools via MCP protocol for IDE integration
(Claude Code, VS Code, Cursor, Windsurf, etc.)

Start:
    pfix server                  # stdio transport (for IDE)
    pfix server --http 3001      # HTTP transport (for remote)
    python -m pfix.mcp_server    # direct

Tools:
    pfix_analyze    — analyze error, return diagnosis
    pfix_fix        — analyze + apply fix to file
    pfix_diagnose   — run environment diagnostics
    pfix_deps_scan  — scan project for missing deps
    pfix_deps_install — install a package
    pfix_deps_generate — generate requirements.txt via pipreqs
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

_MCP_WRITE_ENV = "PFIX_MCP_ALLOW_WRITE"


def _write_enabled() -> bool:
    return os.getenv(_MCP_WRITE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _approval_hash(action: str, payload: dict[str, Any]) -> str:
    """Return a stable digest that binds approval to one exact mutation."""
    encoded = json.dumps(
        {"action": action, "payload": payload},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _approval_required(
    action: str,
    payload: dict[str, Any],
    *,
    actor: str,
    approval_hash: str,
) -> tuple[bool, str]:
    expected = _approval_hash(action, {**payload, "actor": actor.strip()})
    approved = _write_enabled() and bool(actor.strip()) and approval_hash.strip() == expected
    return not approved, expected


def _resolve_workspace_path(path: str, workspace_root: str = ".") -> Path:
    """Resolve a writable path and reject escapes outside the workspace root."""
    root = Path(workspace_root).expanduser().resolve()
    candidate = Path(path).expanduser()
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes workspace root: {path}") from exc
    return target


def create_mcp_server():
    """Create FastMCP server with pfix tools.

    Returns the server instance (requires `pip install pfix[mcp]`).
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError("MCP server requires the mcp package. Install with: pip install pfix[mcp]")

    mcp = FastMCP(
        "pfix",
        dependencies=["litellm", "pipreqs", "python-dotenv", "rich", "pathspec"],
    )

    _register_analyze_tool(mcp)
    _register_fix_tool(mcp)
    _register_deps_tools(mcp)
    _register_diagnose_tool(mcp)
    _register_edit_tool(mcp)

    return mcp


def _register_analyze_tool(mcp):
    """Register pfix_analyze tool."""

    @mcp.tool()
    def pfix_analyze(
        exception_type: str,
        exception_message: str,
        source_file: str,
        traceback: str = "",
        function_name: str = "",
        line_number: int = 0,
        hint: str = "",
    ) -> str:
        """Analyze a Python error and return diagnosis + fix proposal (no changes applied)."""
        from .llm import request_fix

        ctx = _build_ctx(
            exception_type,
            exception_message,
            source_file,
            traceback,
            function_name,
            line_number,
            hint,
        )
        proposal = request_fix(ctx)

        return json.dumps(
            {
                "diagnosis": proposal.diagnosis,
                "error_category": proposal.error_category,
                "fix_description": proposal.fix_description,
                "confidence": proposal.confidence,
                "dependencies": proposal.dependencies,
                "has_code_fix": proposal.has_code_fix,
            },
            indent=2,
        )


def _register_fix_tool(mcp):
    """Register pfix_fix tool."""

    @mcp.tool()
    def pfix_fix(
        exception_type: str,
        exception_message: str,
        source_file: str,
        traceback: str = "",
        function_name: str = "",
        line_number: int = 0,
        hint: str = "",
        auto_apply: bool = False,
        workspace_root: str = ".",
        actor: str = "",
        approval_hash: str = "",
    ) -> str:
        """Propose a fix; applying it requires actor-bound approval of the returned hash."""
        from .config import configure
        from .fixer import apply_fix, _make_diff
        from .llm import request_fix

        try:
            target = _resolve_workspace_path(source_file, workspace_root)
        except ValueError as exc:
            return json.dumps({"applied": False, "error": str(exc)}, indent=2)

        ctx = _build_ctx(
            exception_type,
            exception_message,
            str(target),
            traceback,
            function_name,
            line_number,
            hint,
        )

        proposal = request_fix(ctx)

        if proposal.confidence < 0.1:
            return json.dumps(
                {
                    "applied": False,
                    "reason": "Confidence too low",
                    "confidence": proposal.confidence,
                    "diagnosis": proposal.diagnosis,
                },
                indent=2,
            )

        # Compute diff
        diff = ""
        if proposal.has_code_fix and target.is_file():
            original = target.read_text(encoding="utf-8")
            new = proposal.fixed_file_content or original
            diff = _make_diff(original, new, str(target))

        approval_payload = {
            "source_file": str(target),
            "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
            "dependencies": sorted(proposal.dependencies),
        }
        requires_approval, expected_hash = _approval_required(
            "pfix_fix",
            approval_payload,
            actor=actor,
            approval_hash=approval_hash,
        )

        if not auto_apply or requires_approval:
            return json.dumps(
                {
                    "applied": False,
                    "requires_approval": True,
                    "approval_hash": expected_hash,
                    "approval_payload": approval_payload,
                    "required_env": _MCP_WRITE_ENV,
                    "diagnosis": proposal.diagnosis,
                    "fix_description": proposal.fix_description,
                    "confidence": proposal.confidence,
                    "diff": diff[:3000],
                    "diff_truncated": len(diff) > 3000,
                    "reason": (
                        "Set auto_apply=true and provide actor plus the exact approval_hash"
                        if not auto_apply
                        else (
                            f"Enable {_MCP_WRITE_ENV}=1 and provide actor plus the exact "
                            "approval_hash"
                        )
                    ),
                },
                indent=2,
            )

        configure(auto_apply=True)
        applied = apply_fix(ctx, proposal, confirm=False)

        return json.dumps(
            {
                "applied": applied,
                "diagnosis": proposal.diagnosis,
                "fix_description": proposal.fix_description,
                "confidence": proposal.confidence,
                "diff": diff[:3000],
                "diff_truncated": len(diff) > 3000,
                "approval_hash": expected_hash,
                "approved_by": actor.strip(),
                "dependencies_installed": proposal.dependencies if applied else [],
            },
            indent=2,
        )


def _register_deps_tools(mcp):
    """Register dependency-related tools."""

    @mcp.tool()
    def pfix_deps_scan(path: str) -> str:
        """Scan Python files for missing third-party dependencies."""
        from .dependency import scan_project_deps

        target = Path(path)
        if not target.exists():
            return json.dumps({"error": f"Path not found: {path}"})

        result = scan_project_deps(target if target.is_dir() else target.parent)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def pfix_deps_install(
        package: str,
        apply: bool = False,
        actor: str = "",
        approval_hash: str = "",
    ) -> str:
        """Plan a package installation; execution requires actor-bound approval."""
        from .dependency import install_packages

        payload = {"package": package.strip()}
        requires_approval, expected_hash = _approval_required(
            "pfix_deps_install", payload, actor=actor, approval_hash=approval_hash
        )
        if not apply or requires_approval:
            return json.dumps(
                {
                    **payload,
                    "installed": False,
                    "requires_approval": True,
                    "approval_hash": expected_hash,
                    "required_env": _MCP_WRITE_ENV,
                },
                indent=2,
            )

        results = install_packages([package])
        return json.dumps(
            {
                "package": package,
                "installed": results.get(package, False),
                "approved_by": actor.strip(),
            },
            indent=2,
        )

    @mcp.tool()
    def pfix_deps_generate(
        project_dir: str = ".",
        apply: bool = False,
        actor: str = "",
        approval_hash: str = "",
    ) -> str:
        """Plan requirements generation; writing requires actor-bound approval."""
        from .dependency import generate_requirements

        project = Path(project_dir).expanduser().resolve()
        payload = {"project_dir": str(project), "output": str(project / "requirements.txt")}
        requires_approval, expected_hash = _approval_required(
            "pfix_deps_generate", payload, actor=actor, approval_hash=approval_hash
        )
        if not apply or requires_approval:
            return json.dumps(
                {
                    **payload,
                    "written": False,
                    "requires_approval": True,
                    "approval_hash": expected_hash,
                    "required_env": _MCP_WRITE_ENV,
                },
                indent=2,
            )

        output = generate_requirements(project)
        if output.exists():
            content = output.read_text()
            return json.dumps(
                {
                    "path": str(output),
                    "content": content[:20_000],
                    "content_truncated": len(content) > 20_000,
                    "approved_by": actor.strip(),
                },
                indent=2,
            )
        return json.dumps({"error": "Failed to generate requirements.txt"})


def _register_diagnose_tool(mcp):
    """Register pfix_diagnose tool."""

    @mcp.tool()
    def pfix_diagnose(
        project_path: str = ".",
        categories: str = "",
        max_issues: int = 100,
    ) -> str:
        """Run environment diagnostics on project.

        Args:
            project_path: Path to project directory
            categories: Comma-separated list of categories to check
                       (imports,filesystem,venv,memory,network,etc.)
        """
        from .env_diagnostics import EnvDiagnostics

        target = Path(project_path)
        if not target.exists():
            return json.dumps({"error": f"Path not found: {project_path}"})

        diag = EnvDiagnostics(target)

        # Parse categories if provided
        cat_list = None
        if categories:
            cat_list = [c.strip() for c in categories.split(",") if c.strip()]

        results = diag.check_all(categories=cat_list)
        issue_limit = max(1, min(int(max_issues), 500))

        # Count by status
        critical = sum(1 for r in results if r.status == "critical")
        errors = sum(1 for r in results if r.status == "error")
        warnings = sum(1 for r in results if r.status == "warning")

        return json.dumps(
            {
                "project": str(target),
                "categories_checked": cat_list or "all",
                "total_issues": len(results),
                "critical": critical,
                "errors": errors,
                "warnings": warnings,
                "issues": [
                    {
                        "category": r.category,
                        "check": r.check_name,
                        "status": r.status,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "auto_fixable": r.auto_fixable,
                        "path": r.abs_path,
                        "line": r.line_number,
                    }
                    for r in results
                    if r.status != "ok"
                ][:issue_limit],
                "issues_truncated": sum(1 for r in results if r.status != "ok") > issue_limit,
            },
            indent=2,
        )


def _register_edit_tool(mcp):
    """Register pfix_edit_file tool."""

    @mcp.tool()
    def pfix_edit_file(
        path: str,
        content: str,
        workspace_root: str = ".",
        actor: str = "",
        approval_hash: str = "",
    ) -> str:
        """Write within a workspace after actor-bound approval of exact content."""
        try:
            target = _resolve_workspace_path(path, workspace_root)
            payload = {
                "path": str(target),
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
            requires_approval, expected_hash = _approval_required(
                "pfix_edit_file", payload, actor=actor, approval_hash=approval_hash
            )
            if requires_approval:
                return json.dumps(
                    {
                        "status": "approval_required",
                        "path": str(target),
                        "approval_hash": expected_hash,
                        "content_sha256": payload["content_sha256"],
                        "required_env": _MCP_WRITE_ENV,
                    },
                    indent=2,
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return json.dumps(
                {"status": "ok", "path": str(target), "approved_by": actor.strip()}, indent=2
            )
        except Exception as e:
            return json.dumps({"error": str(e)})


def _build_ctx(
    exception_type,
    exception_message,
    source_file,
    traceback_text,
    function_name,
    line_number,
    hint,
):
    """Build ErrorContext from MCP tool arguments."""
    from .types import ErrorContext

    source_code = ""
    if source_file and Path(source_file).is_file():
        try:
            source_code = Path(source_file).read_text(encoding="utf-8")
        except Exception:
            pass

    return ErrorContext(
        exception_type=exception_type,
        exception_message=exception_message,
        traceback_text=traceback_text,
        source_file=source_file,
        source_code=source_code,
        function_name=function_name,
        line_number=line_number,
        hints={"hint": hint} if hint else {},
        python_version=f"{sys.version.split()[0]}",
    )


def start_server(transport: str = "stdio", host: str = "127.0.0.1", port: int = 3001):
    """Start the MCP server."""
    mcp = create_mcp_server()

    if transport == "stdio":
        print("🔧 pfix MCP server (stdio transport)", file=sys.stderr, flush=True)
        mcp.run(transport="stdio")
    else:
        print(f"🔧 pfix MCP server on http://{host}:{port}", file=sys.stderr, flush=True)
        mcp.run(transport="sse", host=host, port=port)


# Also support: python -m pfix.mcp_server
if __name__ == "__main__":
    start_server()
