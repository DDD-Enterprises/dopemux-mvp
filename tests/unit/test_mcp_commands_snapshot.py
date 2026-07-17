"""CLI-wiring tests for `dopemux mcp snapshot-tools` (mcp_commands.mcp_snapshot_tools_cmd).

Pure-logic coverage (seed ingestion, merge, serialization, SSE-frame parsing)
lives in tests/unit/test_mcp_tool_snapshot.py. These tests only check that the
CLI wires load -> seed-merge -> live-merge -> write correctly and reports
per-server output, using monkeypatched tool_snapshot functions — no network,
no real fleet.
"""

from __future__ import annotations

import json

from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp import tool_snapshot


def _catalog():
    return {
        "version": 1,
        "servers": {
            "serena": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3006/mcp",
            },
        },
    }


def test_snapshot_tools_offline_seed_only_writes_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "serena.json").write_text(
        json.dumps(
            {
                "server": "serena",
                "url": "http://127.0.0.1:3006/mcp",
                "transport": "http",
                "tool_names": ["read_file"],
                "verdict": "OK",
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "mcp_tool_surfaces.json"

    live_calls = []
    monkeypatch.setattr(
        tool_snapshot,
        "snapshot_from_live",
        lambda catalog, timeout: live_calls.append(1) or {"servers": {}},
    )

    result = CliRunner().invoke(
        mcp_commands.mcp_snapshot_tools_cmd,
        ["--seed-from", str(seed_dir), "--output", str(output_path), "--offline"],
    )

    assert result.exit_code == 0, result.output
    assert live_calls == []  # --offline must skip live probing entirely
    assert "serena" in result.output
    assert "source=seed" in result.output

    written = json.loads(output_path.read_text())
    assert written["servers"]["serena"]["source"] == "seed"
    assert written["servers"]["serena"]["tool_count"] == 1


def test_snapshot_tools_live_run_merges_over_existing_seed_base(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())

    output_path = tmp_path / "mcp_tool_surfaces.json"
    output_path.write_text(
        tool_snapshot.dump_snapshot(
            {
                "schema_version": 1,
                "generated_at": "2026-07-16T00:00:00Z",
                "generator": "dopemux mcp snapshot-tools",
                "servers": {
                    "serena": {
                        "transport": "http",
                        "endpoint": "http://localhost:3006/mcp",
                        "source": "seed",
                        "captured_at": "2026-07-16T00:00:00Z",
                        "tool_count": 1,
                        "tools": {"read_file": ""},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_live(catalog, timeout):
        assert timeout == 9.5
        return {
            "servers": {
                "serena": {
                    "transport": "http",
                    "endpoint": "http://localhost:3006/mcp",
                    "source": "live",
                    "captured_at": "2026-07-16T02:00:00Z",
                    "tool_count": 27,
                    "tools": {f"tool_{i}": "" for i in range(27)},
                }
            }
        }

    monkeypatch.setattr(tool_snapshot, "snapshot_from_live", fake_live)

    result = CliRunner().invoke(
        mcp_commands.mcp_snapshot_tools_cmd,
        ["--output", str(output_path), "--timeout", "9.5"],
    )

    assert result.exit_code == 0, result.output
    written = json.loads(output_path.read_text())
    assert written["servers"]["serena"]["source"] == "live"
    assert written["servers"]["serena"]["tool_count"] == 27


def test_snapshot_tools_refuses_to_write_empty_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mcp_commands, "_load_catalog", lambda: {"version": 1, "servers": {}}
    )
    monkeypatch.setattr(
        tool_snapshot, "snapshot_from_live", lambda catalog, timeout: {"servers": {}}
    )
    output_path = tmp_path / "mcp_tool_surfaces.json"

    result = CliRunner().invoke(
        mcp_commands.mcp_snapshot_tools_cmd,
        ["--output", str(output_path)],
    )

    assert result.exit_code != 0
    assert "empty snapshot" in result.output
    assert not output_path.exists()


def test_snapshot_tools_reports_write_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(
        tool_snapshot,
        "snapshot_from_live",
        lambda catalog, timeout: {
            "servers": {
                "serena": {
                    "transport": "http",
                    "endpoint": "http://localhost:3006/mcp",
                    "source": "live",
                    "captured_at": "2026-07-16T00:00:00Z",
                    "tool_count": 1,
                    "tools": {"read_file": ""},
                }
            }
        },
    )

    # Point --output at a path whose parent directory does not exist so the
    # write raises OSError, exercising the write-failure exit path.
    bad_output = tmp_path / "does-not-exist" / "mcp_tool_surfaces.json"

    result = CliRunner().invoke(
        mcp_commands.mcp_snapshot_tools_cmd,
        ["--output", str(bad_output)],
    )

    assert result.exit_code != 0
    assert "Failed to write" in result.output


def test_snapshot_tools_default_output_path_uses_repo_root(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path)
    )
    monkeypatch.setattr(
        tool_snapshot,
        "snapshot_from_live",
        lambda catalog, timeout: {
            "servers": {
                "serena": {
                    "transport": "http",
                    "endpoint": "http://localhost:3006/mcp",
                    "source": "live",
                    "captured_at": "2026-07-16T00:00:00Z",
                    "tool_count": 1,
                    "tools": {"read_file": ""},
                }
            }
        },
    )

    result = CliRunner().invoke(mcp_commands.mcp_snapshot_tools_cmd, [])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "mcp_tool_surfaces.json").exists()


def test_snapshot_tools_no_repo_root_and_no_output_raises(monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: None)

    result = CliRunner().invoke(mcp_commands.mcp_snapshot_tools_cmd, ["--offline"])

    assert result.exit_code != 0
    assert "Not inside a git repository" in result.output
