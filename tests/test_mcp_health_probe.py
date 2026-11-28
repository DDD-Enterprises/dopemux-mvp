"""
Tests for .claude/hooks/mcp_health_probe.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from mcp_health_probe import (  # noqa: E402
    _extract_port,
    _format_health,
    emit_mcp_health,
)

# ---------------------------------------------------------------------------
# Port extraction
# ---------------------------------------------------------------------------

def test_extract_port_default(monkeypatch):
    monkeypatch.delenv("CONPORT_MCP_PORT", raising=False)
    assert _extract_port("http://localhost:${CONPORT_MCP_PORT:-3005}/mcp") == 3005


def test_extract_port_env_override(monkeypatch):
    monkeypatch.setenv("CONPORT_MCP_PORT", "4444")
    assert _extract_port("http://localhost:${CONPORT_MCP_PORT:-3005}/mcp") == 4444


def test_extract_port_literal():
    assert _extract_port("http://localhost:3020/mcp") == 3020


def test_extract_port_no_port():
    assert _extract_port("http://localhost/mcp") is None


# ---------------------------------------------------------------------------
# format_health output policy
# ---------------------------------------------------------------------------

def test_all_healthy_one_line():
    health = {
        "servers": {
            "conport": {"up": True, "port": 3005},
            "dope-memory": {"up": True, "port": 3020},
        },
        "leaked_containers": 1,
    }
    result = _format_health(health)
    assert result is not None
    assert "✅" in result
    assert "⚠️" not in result
    assert "\n" not in result  # single line when healthy


def test_down_server_emits_problem_line():
    health = {
        "servers": {"conport": {"up": False, "port": 3005}},
        "leaked_containers": 0,
    }
    result = _format_health(health)
    assert result is not None
    lines = result.splitlines()
    assert len(lines) >= 2
    assert "dopemux mcp start --services conport" in result


def test_down_server_shell_quotes_repo_path():
    health = {
        "servers": {"conport": {"up": False, "port": 3005}},
        "leaked_containers": 0,
    }
    project_root = Path("/some/repo with spaces;echo unsafe")

    result = _format_health(health, project_root)

    assert result is not None
    assert (
        "dopemux mcp start --repo '/some/repo with spaces;echo unsafe' "
        "--services conport"
    ) in result


def test_task_orchestrator_down_points_to_http_singleton_wrapper():
    health = {
        "servers": {"task-orchestrator": {"up": False, "port": 7890}},
        "leaked_containers": 0,
    }
    result = _format_health(health)
    assert result is not None
    assert "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh" in result
    assert "dopemux mcp start --services task-orchestrator" not in result


def test_stdio_server_shown_as_gear():
    health = {
        "servers": {"task-orchestrator": {"up": None}},
        "leaked_containers": 0,
    }
    result = _format_health(health)
    assert result is not None
    assert "⚙️" in result


def test_many_leaked_containers_warns():
    health = {"servers": {}, "leaked_containers": 4}
    result = _format_health(health)
    assert result is not None
    assert "SQLite-contention" in result
    assert "/mcp:doctor --prune" in result


def test_two_leaked_containers_warn():
    health = {"servers": {}, "leaked_containers": 2}
    result = _format_health(health)
    assert result is not None
    assert "2 task-orchestrator containers" in result


def test_one_leaked_container_no_warn():
    health = {"servers": {}, "leaked_containers": 1}
    result = _format_health(health)
    # No problem if only 1 container — that's normal
    assert result is None or "⚠️" not in result


def test_repo_aware_remediation_includes_repo_flag():
    """A project_root should surface --repo <path> before --services in the
    generic remediation line (PR1150-B1: the --repo emission branch was
    implemented but never exercised by tests)."""
    health = {
        "servers": {"conport": {"up": False, "port": 3005}},
        "leaked_containers": 0,
    }
    result = _format_health(health, project_root=Path("/some/repo"))
    assert result is not None
    assert "dopemux mcp start --repo /some/repo --services conport" in result


def test_no_project_root_omits_repo_flag():
    """Without a project_root, the generic remediation must fall back to the
    bare (no --repo) form — never silently insert a stale/None path."""
    health = {
        "servers": {"conport": {"up": False, "port": 3005}},
        "leaked_containers": 0,
    }
    result = _format_health(health, project_root=None)
    assert result is not None
    assert "dopemux mcp start --services conport" in result
    assert "--repo" not in result


def test_task_orchestrator_down_keeps_dedicated_remediation_even_with_repo():
    """task-orchestrator is an intentional exception to --repo emission: it
    always gets its dedicated wrapper-script remediation, never the generic
    `dopemux mcp start --repo ... --services task-orchestrator` line, even
    when a project_root is supplied."""
    health = {
        "servers": {"task-orchestrator": {"up": False, "port": 7890}},
        "leaked_containers": 0,
    }
    result = _format_health(health, project_root=Path("/some/repo"))
    assert result is not None
    assert "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh" in result
    assert "--repo" not in result
    assert "dopemux mcp start --services task-orchestrator" not in result


def test_emit_mcp_health_passes_project_root_into_repo_flag(tmp_path):
    """Integration-style: emit_mcp_health's public entrypoint must forward its
    project_root argument through to _format_health so the injected
    SessionStart line carries --repo <project_root>."""
    _make_mcp_json(tmp_path, port=3005)
    with patch("mcp_health_probe._probe_port", return_value=False), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert result is not None
    assert f"--repo {tmp_path} --services conport" in result


def test_max_3_problems_shown():
    """ADHD: at most 3 problem lines (+ truncation line)."""
    health = {
        "servers": {
            f"srv{i}": {"up": False, "port": 3000 + i} for i in range(5)
        },
        "leaked_containers": 4,
    }
    result = _format_health(health)
    assert result is not None
    lines = result.splitlines()
    # summary line + ≤3 problems + 1 "more" line
    problem_lines = [l for l in lines if l.startswith("⚠️")]
    assert len(problem_lines) <= 3
    assert any("more" in l for l in lines)


# ---------------------------------------------------------------------------
# emit_mcp_health — socket probing
# ---------------------------------------------------------------------------

def _make_mcp_json(tmp_path: Path, transport: str = "sse", port: int = 3005) -> None:
    cfg = {
        "mcpServers": {
            "conport": {
                "type": transport,
                "url": f"http://localhost:{port}/mcp",
            }
        }
    }
    (tmp_path / ".mcp.json").write_text(json.dumps(cfg))


def test_port_open_emits_checkmark(tmp_path):
    _make_mcp_json(tmp_path, port=3005)
    with patch("mcp_health_probe._probe_port", return_value=True), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert result is not None
    assert "✅" in result


def test_port_closed_emits_warning(tmp_path):
    _make_mcp_json(tmp_path, port=3005)
    with patch("mcp_health_probe._probe_port", return_value=False), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert result is not None
    assert "dopemux mcp start" in result


def test_docker_timeout_omits_container_line(tmp_path):
    _make_mcp_json(tmp_path, port=3005)
    with patch("mcp_health_probe._probe_port", return_value=True), \
         patch("mcp_health_probe._count_leaked_containers", return_value=None):
        result = emit_mcp_health(tmp_path)
    # Should not raise, container line simply absent
    assert result is not None
    assert "SQLite" not in (result or "")


def test_mcp_json_missing_returns_none(tmp_path):
    # No .mcp.json in tmp_path
    with patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert result is None


def test_cache_fresh_skips_probe(tmp_path):
    """Fresh cache → probe functions not called."""
    _make_mcp_json(tmp_path, port=3005)
    # Pre-warm through the public entrypoint so the cache binds its inputs.
    with patch("mcp_health_probe._probe_port", return_value=True), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        emit_mcp_health(tmp_path)

    with patch("mcp_health_probe._probe_port") as mock_probe, \
         patch("mcp_health_probe._count_leaked_containers") as mock_docker:
        result = emit_mcp_health(tmp_path)
    mock_probe.assert_not_called()
    mock_docker.assert_not_called()
    assert result is not None


def test_exception_in_probe_returns_none(tmp_path):
    _make_mcp_json(tmp_path, port=3005)
    with patch("mcp_health_probe._probe_port", side_effect=Exception("boom")):
        result = emit_mcp_health(tmp_path)
    assert result is None


_TEMPLATE = "http://localhost:${CONPORT_MCP_PORT:-3005}/mcp"


def _write_template_config(root):
    (root / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "conport": {"type": "sse", "url": _TEMPLATE},
        "dope-memory": {"type": "http", "url":
            "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp"},
    }}))


def test_target_envrc_ports_override_ambient_without_mutation(tmp_path, monkeypatch):
    _write_template_config(tmp_path)
    (tmp_path / ".envrc.dopemux-mcp").write_text(
        "export CONPORT_MCP_PORT='3007' # checkout port\n"
        'export DOPE_MEMORY_PORT="3054"\n')
    monkeypatch.setenv("CONPORT_MCP_PORT", "9999")
    monkeypatch.setenv("DOPE_MEMORY_PORT", "9998")
    before = dict(os.environ)
    with patch("mcp_health_probe._probe_port", return_value=True) as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        emit_mcp_health(tmp_path)
    assert probe.call_args_list == [call(3007), call(3054)]
    assert dict(os.environ) == before


@pytest.mark.parametrize("body", [None, "", "export CONPORT_MCP_PORT=oops\n",
    "export CONPORT_MCP_PORT=0\n", "export CONPORT_MCP_PORT=65536\n",
    "export CONPORT_MCP_PORT=3007\nexport CONPORT_MCP_PORT=3008\n",
    "export CONPORT_MCP_PORT 3007\n"])
def test_bad_target_config_is_visible_and_never_probed(tmp_path, monkeypatch, body):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "conport": {"type": "sse", "url": _TEMPLATE}}}))
    if body is not None:
        (tmp_path / ".envrc.dopemux-mcp").write_text(body)
    monkeypatch.setenv("CONPORT_MCP_PORT", "4444")
    with patch("mcp_health_probe._probe_port") as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    probe.assert_not_called()
    assert "configuration" in result
    assert "not listening" not in result


def test_shell_text_is_not_executed_or_echoed(tmp_path):
    marker = tmp_path / "executed"
    _write_template_config(tmp_path)
    (tmp_path / ".envrc.dopemux-mcp").write_text(
        f"export CONPORT_MCP_PORT=$(touch {marker})\n"
        "export DOPE_MEMORY_PORT=3054\n"
        f"touch {marker}\n")
    with patch("mcp_health_probe._probe_port", return_value=True) as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert not marker.exists()
    assert "touch" not in result
    assert probe.call_args_list == [call(3054)]


def test_literal_port_ignores_invalid_envrc(tmp_path):
    _make_mcp_json(tmp_path, port=7890)
    (tmp_path / ".envrc.dopemux-mcp").write_text("CONPORT_MCP_PORT=bad\n")
    with patch("mcp_health_probe._probe_port", return_value=True) as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        emit_mcp_health(tmp_path)
    probe.assert_called_once_with(7890)


def test_legacy_cache_is_invalidated(tmp_path):
    _write_template_config(tmp_path)
    (tmp_path / ".envrc.dopemux-mcp").write_text(
        "CONPORT_MCP_PORT=3007\nDOPE_MEMORY_PORT=3054\n")
    from datetime import datetime, timezone
    cache = tmp_path / ".claude" / ".mcp-health-cache.json"
    cache.parent.mkdir()
    cache.write_text(json.dumps({"written_at": datetime.now(timezone.utc).isoformat(),
        "servers": {"conport": {"up": False, "port": 3005}}}))
    with patch("mcp_health_probe._probe_port", return_value=True) as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert probe.call_args_list == [call(3007), call(3054)]
    assert "not listening" not in result


@pytest.mark.parametrize("change", ["envrc", "mcp"])
def test_config_change_invalidates_fresh_cache(tmp_path, change):
    _write_template_config(tmp_path)
    envrc = tmp_path / ".envrc.dopemux-mcp"
    envrc.write_text("CONPORT_MCP_PORT=3007\nDOPE_MEMORY_PORT=3054\n")
    with patch("mcp_health_probe._probe_port", return_value=True), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        emit_mcp_health(tmp_path)
    if change == "envrc":
        envrc.write_text("CONPORT_MCP_PORT=3008\nDOPE_MEMORY_PORT=3054\n")
    else:
        _make_mcp_json(tmp_path, port=7777)
    with patch("mcp_health_probe._probe_port", return_value=False) as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    assert probe.called
    assert "not listening" in result
    assert probe.call_args_list == ([call(3008), call(3054)] if change == "envrc"
                                    else [call(7777)])


@pytest.mark.parametrize("value", ["0", "65536", "invalid"])
def test_extract_port_invalid_ambient_does_not_fall_back(monkeypatch, value):
    monkeypatch.setenv("CONPORT_MCP_PORT", value)
    assert _extract_port(_TEMPLATE) is None


@pytest.mark.parametrize("url", ["http://remote.example:3007/mcp",
                                "http://[::1]:3007/mcp"])
def test_unsupported_host_is_not_probed_as_ipv4_localhost(tmp_path, url):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "conport": {"type": "sse", "url": url}}}))
    with patch("mcp_health_probe._probe_port") as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    probe.assert_not_called()
    assert "not probed" in result
    assert "✅" not in result


def test_malformed_reassignment_invalidates_prior_value(tmp_path):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "conport": {"type": "sse", "url": _TEMPLATE}}}))
    (tmp_path / ".envrc.dopemux-mcp").write_text(
        "CONPORT_MCP_PORT=3007\nexport CONPORT_MCP_PORT 3008\n")
    with patch("mcp_health_probe._probe_port") as probe, \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        result = emit_mcp_health(tmp_path)
    probe.assert_not_called()
    assert "configuration" in result


def test_unrelated_envrc_values_do_not_invalidate_or_enter_cache(tmp_path):
    _write_template_config(tmp_path)
    envrc = tmp_path / ".envrc.dopemux-mcp"
    envrc.write_text("CONPORT_MCP_PORT=3007\nDOPE_MEMORY_PORT=3054\n"
                     "UNRELATED_VALUE=synthetic-before\n")
    with patch("mcp_health_probe._probe_port", return_value=True), \
         patch("mcp_health_probe._count_leaked_containers", return_value=0):
        emit_mcp_health(tmp_path)
    envrc.write_text(envrc.read_text().replace("synthetic-before", "synthetic-after"))
    with patch("mcp_health_probe._probe_port") as probe, \
         patch("mcp_health_probe._count_leaked_containers") as docker:
        emit_mcp_health(tmp_path)
    probe.assert_not_called()
    docker.assert_not_called()
    assert "synthetic" not in (tmp_path / ".claude" / ".mcp-health-cache.json").read_text()
