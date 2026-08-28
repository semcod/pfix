from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("mcp")

from pfix.mcp_server import (
    _approval_hash,
    _approval_required,
    _resolve_workspace_path,
    create_mcp_server,
)


def test_mcp_mutating_tools_are_safe_by_default(tmp_path):
    mcp = create_mcp_server()
    tools = mcp._tool_manager._tools  # type: ignore[attr-defined]

    target = tmp_path / "example.py"
    edit = tools["pfix_edit_file"].fn
    response = json.loads(edit(str(target), "print('safe')", workspace_root=str(tmp_path)))

    assert response["status"] == "approval_required"
    assert not target.exists()


def test_mcp_fix_only_returns_proposal_by_default(tmp_path, monkeypatch):
    import pfix.fixer
    import pfix.llm

    source = tmp_path / "broken.py"
    source.write_text("value = 1\n")
    proposal = SimpleNamespace(
        confidence=0.9,
        diagnosis="test",
        fix_description="change value",
        dependencies=[],
        has_code_fix=True,
        fixed_file_content="value = 2\n",
    )
    monkeypatch.setattr(pfix.llm, "request_fix", lambda _ctx: proposal)
    monkeypatch.setattr(
        pfix.fixer,
        "apply_fix",
        lambda *_args, **_kwargs: pytest.fail("default MCP call must not apply a fix"),
    )

    mcp = create_mcp_server()
    fix = mcp._tool_manager._tools["pfix_fix"].fn  # type: ignore[attr-defined]
    response = json.loads(
        fix("ValueError", "broken", "broken.py", workspace_root=str(tmp_path))
    )

    assert response["applied"] is False
    assert response["requires_approval"] is True
    assert "approval_hash" in response
    assert source.read_text() == "value = 1\n"


def test_mcp_edit_requires_matching_actor_bound_hash(tmp_path, monkeypatch):
    mcp = create_mcp_server()
    edit = mcp._tool_manager._tools["pfix_edit_file"].fn  # type: ignore[attr-defined]
    target = _resolve_workspace_path("example.py", str(tmp_path))
    content = "print('approved')\n"
    payload = {
        "path": str(target),
        "content_sha256": __import__("hashlib").sha256(content.encode()).hexdigest(),
    }
    approval = _approval_hash("pfix_edit_file", {**payload, "actor": "tom"})
    monkeypatch.setenv("PFIX_MCP_ALLOW_WRITE", "1")

    response = json.loads(
        edit(
            "example.py",
            content,
            workspace_root=str(tmp_path),
            actor="tom",
            approval_hash=approval,
        )
    )

    assert response["status"] == "ok"
    assert target.read_text() == content


def test_workspace_path_rejects_escape(tmp_path):
    with pytest.raises(ValueError, match="escapes workspace"):
        _resolve_workspace_path("../outside.py", str(tmp_path))


def test_approval_requires_actor_capability_and_exact_digest(monkeypatch):
    required, expected = _approval_required("action", {"value": 1}, actor="", approval_hash="")
    assert required is True
    assert len(expected) == 64

    digest = _approval_hash("action", {"value": 1, "actor": "reviewer"})
    required, _ = _approval_required(
        "action", {"value": 1}, actor="reviewer", approval_hash=digest
    )
    assert required is True

    monkeypatch.setenv("PFIX_MCP_ALLOW_WRITE", "1")
    required, expected = _approval_required(
        "action", {"value": 1}, actor="reviewer", approval_hash=digest
    )
    assert required is False
    assert expected == digest


def test_unbuffered_stdio_emits_only_jsonrpc_on_stdout():
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "PFIX_AUTO_ACTIVATE": "0",
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(root / "src"),
    }
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    completed = subprocess.run(
        [sys.executable, "-m", "pfix.mcp_server"],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        cwd=root,
        env=env,
        timeout=10,
        check=False,
    )

    stdout_lines = completed.stdout.splitlines()
    assert completed.returncode == 0
    assert len(stdout_lines) == 1
    assert json.loads(stdout_lines[0])["id"] == 1
    assert "pfix MCP server" in completed.stderr
