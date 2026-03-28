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
    pfix_deps_scan  — scan project for missing deps
    pfix_deps_install — install a package
    pfix_deps_generate — generate requirements.txt via pipreqs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def create_mcp_server():
    """Create FastMCP server with pfix tools.

    Returns the server instance (requires `pip install pfix[mcp]`).
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP server requires the mcp package. Install with: pip install pfix[mcp]"
        )

    mcp = FastMCP(
        "pfix",
        dependencies=["litellm", "pipreqs", "python-dotenv", "rich", "pathspec"],
    )

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
        from .types import ErrorContext
        from .llm import request_fix

        ctx = _build_ctx(
            exception_type, exception_message, source_file,
            traceback, function_name, line_number, hint,
        )
        proposal = request_fix(ctx)

        return json.dumps({
            "diagnosis": proposal.diagnosis,
            "error_category": proposal.error_category,
            "fix_description": proposal.fix_description,
            "confidence": proposal.confidence,
            "dependencies": proposal.dependencies,
            "has_code_fix": proposal.has_code_fix,
        }, indent=2)

    @mcp.tool()
    def pfix_fix(
        exception_type: str,
        exception_message: str,
        source_file: str,
        traceback: str = "",
        function_name: str = "",
        line_number: int = 0,
        hint: str = "",
        auto_apply: bool = True,
    ) -> str:
        """Analyze error AND apply fix to the source file (creates backup)."""
        from .config import configure
        from .fixer import apply_fix, _make_diff
        from .llm import request_fix

        ctx = _build_ctx(
            exception_type, exception_message, source_file,
            traceback, function_name, line_number, hint,
        )

        if auto_apply:
            configure(auto_apply=True)

        proposal = request_fix(ctx)

        if proposal.confidence < 0.1:
            return json.dumps({
                "applied": False,
                "reason": "Confidence too low",
                "confidence": proposal.confidence,
                "diagnosis": proposal.diagnosis,
            }, indent=2)

        # Compute diff
        diff = ""
        if proposal.has_code_fix and Path(source_file).is_file():
            original = Path(source_file).read_text(encoding="utf-8")
            new = proposal.fixed_file_content or original
            diff = _make_diff(original, new, source_file)

        applied = apply_fix(ctx, proposal, confirm=False)

        return json.dumps({
            "applied": applied,
            "diagnosis": proposal.diagnosis,
            "fix_description": proposal.fix_description,
            "confidence": proposal.confidence,
            "diff": diff[:3000],  # truncate for MCP response
            "dependencies_installed": proposal.dependencies if applied else [],
        }, indent=2)

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
    def pfix_deps_install(package: str) -> str:
        """Install a Python package via pip/uv."""
        from .dependency import install_packages

        results = install_packages([package])
        return json.dumps({
            "package": package,
            "installed": results.get(package, False),
        }, indent=2)

    @mcp.tool()
    def pfix_deps_generate(project_dir: str = ".") -> str:
        """Generate requirements.txt via pipreqs for a project directory."""
        from .dependency import generate_requirements

        output = generate_requirements(Path(project_dir))
        if output.exists():
            content = output.read_text()
            return json.dumps({
                "path": str(output),
                "content": content,
            }, indent=2)
        return json.dumps({"error": "Failed to generate requirements.txt"})

    @mcp.tool()
    def pfix_edit_file(path: str, content: str) -> str:
        """Write content to a file (used by LLM to apply fixes)."""
        try:
            Path(path).write_text(content, encoding="utf-8")
            return json.dumps({"status": "ok", "path": path})
        except Exception as e:
            return json.dumps({"error": str(e)})

    return mcp


def _build_ctx(
    exception_type, exception_message, source_file,
    traceback_text, function_name, line_number, hint,
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
        print("🔧 pfix MCP server (stdio transport)")
        mcp.run(transport="stdio")
    else:
        print(f"🔧 pfix MCP server on http://{host}:{port}")
        mcp.run(transport="sse", host=host, port=port)


# Also support: python -m pfix.mcp_server
if __name__ == "__main__":
    start_server()
