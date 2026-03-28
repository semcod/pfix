"""
pfix.mcp_client — MCP client for IDE file editing.

Connects to MCP servers (filesystem, editor) to apply fixes
in the developer's actual environment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .config import get_config

logger = logging.getLogger("pfix.mcp")


@dataclass
class MCPResult:
    success: bool
    content: Any = None
    error: Optional[str] = None


class MCPClient:
    """Client for MCP servers (filesystem, editor tools)."""

    def __init__(self, server_url: Optional[str] = None):
        config = get_config()
        self.server_url = server_url or config.mcp_server_url
        self._session = None

    async def connect(self) -> bool:
        try:
            import httpx
            self._session = httpx.AsyncClient(base_url=self.server_url, timeout=30.0)
            return True
        except Exception as e:
            logger.warning(f"MCP connect failed: {e}")
            return False

    async def disconnect(self):
        if self._session:
            await self._session.aclose()
            self._session = None

    async def call_tool(self, tool_name: str, arguments: dict) -> MCPResult:
        if not self._session:
            return MCPResult(success=False, error="Not connected")
        try:
            resp = await self._session.post("/mcp/v1/tools/call", json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
                "id": 1,
            })
            data = resp.json()
            if "error" in data:
                return MCPResult(success=False, error=str(data["error"]))
            result = data.get("result", {})
            return MCPResult(
                success=not result.get("isError", False),
                content=result.get("content", []),
            )
        except Exception as e:
            return MCPResult(success=False, error=str(e))

    async def edit_file(self, path: str, content: str) -> MCPResult:
        for tool in ["write_file", "create_or_update", "edit_file", "pfix_edit_file"]:
            result = await self.call_tool(tool, {"path": path, "content": content})
            if result.success:
                return result
        return MCPResult(success=False, error="No file editing tool found")

    async def run_command(self, command: str) -> MCPResult:
        for tool in ["run_command", "execute_command", "bash", "shell"]:
            result = await self.call_tool(tool, {"command": command})
            if result.success:
                return result
        return MCPResult(success=False, error="No command tool found")
