"""Unit tests for dopemux.mcp.tool_snapshot (seed ingestion, merge, serialization).

No network in these tests — live-transport probing (probe_streamable_http,
probe_classic_sse) is exercised against the real fleet manually, not here.
These tests cover the pure, injectable-free surface: seed ingestion from
capture fixtures, merge semantics, deterministic serialization, and the
SSE-frame body-parsing helper shared by both live transports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dopemux.mcp import tool_snapshot as ts

# --------------------------------------------------------------------------
# (a) Seed ingestion
# --------------------------------------------------------------------------


def _write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_snapshot_from_seed_ingests_ok_capture_with_full_tools_list(tmp_path):
    _write(
        tmp_path / "serena.json",
        {
            "server": "serena",
            "url": "http://127.0.0.1:3006/mcp",
            "transport": "http",
            "ts": "2026-07-16T11:23:51-0700",
            "tools_list": {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "read_file",
                            "description": "Reads the given file or a chunk of it.\nSecond line ignored.",
                        },
                        {"name": "list_dir", "description": "Lists a directory."},
                    ]
                },
            },
            "tool_names": ["list_dir", "read_file"],
            "tool_count": 2,
            "verdict": "OK",
        },
    )

    snapshot = ts.snapshot_from_seed(tmp_path)

    assert snapshot["schema_version"] == ts.SCHEMA_VERSION
    servers = snapshot["servers"]
    assert set(servers) == {"serena"}
    entry = servers["serena"]
    assert entry["source"] == "seed"
    assert entry["transport"] == "http"
    assert entry["endpoint"] == "http://127.0.0.1:3006/mcp"
    assert entry["tool_count"] == 2
    assert entry["tools"] == {
        "read_file": "Reads the given file or a chunk of it.",
        "list_dir": "Lists a directory.",
    }


def test_snapshot_from_seed_falls_back_to_bare_tool_names_when_no_tools_list(tmp_path):
    # Matches this fleet's SSE captures (conport, desktop-commander): only
    # tool_names were recorded, no tools_list.result.tools with descriptions.
    _write(
        tmp_path / "conport.json",
        {
            "server": "conport",
            "url": "http://127.0.0.1:3005/sse",
            "transport": "sse",
            "ts": "2026-07-16T11:23:52-0700",
            "tool_names": ["get_context", "log_decision"],
            "tool_count": 2,
            "verdict": "OK",
        },
    )

    snapshot = ts.snapshot_from_seed(tmp_path)

    entry = snapshot["servers"]["conport"]
    assert entry["tool_count"] == 2
    assert entry["tools"] == {"get_context": "", "log_decision": ""}


def test_snapshot_from_seed_skips_non_ok_verdicts(tmp_path):
    _write(
        tmp_path / "pal-http.json",
        {
            "server": "pal-http",
            "url": "http://127.0.0.1:3003/mcp",
            "transport": "http",
            "verdict": "UNREACHABLE: HTTPError: HTTP Error 404: Not Found",
        },
    )

    snapshot = ts.snapshot_from_seed(tmp_path)

    assert snapshot["servers"] == {}


def test_snapshot_from_seed_skips_summary_and_malformed_files(tmp_path):
    _write(
        tmp_path / "_summary.json", [{"server": "serena", "verdict": "OK", "tools": 27}]
    )
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")

    snapshot = ts.snapshot_from_seed(tmp_path)

    assert snapshot["servers"] == {}


def test_snapshot_from_seed_aliases_legacy_server_names_to_catalog_names(tmp_path):
    _write(
        tmp_path / "task-orchestrator-7890.json",
        {
            "server": "task-orchestrator-7890",
            "url": "http://127.0.0.1:7890/mcp",
            "transport": "http",
            "tool_names": ["get_context"],
            "tool_count": 1,
            "verdict": "OK",
        },
    )

    snapshot = ts.snapshot_from_seed(tmp_path)

    assert set(snapshot["servers"]) == {"task-orchestrator"}


def test_snapshot_from_seed_empty_dir_and_missing_dir(tmp_path):
    empty = ts.snapshot_from_seed(tmp_path)
    assert empty["servers"] == {}

    missing = ts.snapshot_from_seed(tmp_path / "does-not-exist")
    assert missing["servers"] == {}


# --------------------------------------------------------------------------
# (b) Merge semantics
# --------------------------------------------------------------------------


def _entry(source: str, tool_count: int = 1, **extra) -> dict:
    base = {
        "transport": "http",
        "endpoint": "http://example/mcp",
        "source": source,
        "captured_at": "2026-07-16T00:00:00Z",
        "tool_count": tool_count,
        "tools": {"a": ""} if tool_count else {},
    }
    base.update(extra)
    return base


def test_merge_live_over_seed_prefers_fresh_data_for_shared_server():
    base = {"servers": {"serena": _entry("seed", tool_count=27)}}
    overlay = {"servers": {"serena": _entry("live", tool_count=27)}}

    merged = ts.merge_snapshots(base, overlay)

    assert merged["servers"]["serena"]["source"] == "live"


def test_merge_keeps_base_when_overlay_is_unreachable_for_known_server():
    base = {"servers": {"conport": _entry("seed", tool_count=17)}}
    overlay = {
        "servers": {
            "conport": {
                "transport": "sse",
                "endpoint": "http://127.0.0.1:3005/sse",
                "source": "unreachable",
                "captured_at": "2026-07-16T01:00:00Z",
                "tool_count": 0,
                "tools": {},
                "reason": "connection refused",
            }
        }
    }

    merged = ts.merge_snapshots(base, overlay)

    assert merged["servers"]["conport"]["source"] == "seed"
    assert merged["servers"]["conport"]["tool_count"] == 17


def test_merge_adds_overlay_only_servers_including_unreachable_when_base_lacks_them():
    base = {"servers": {}}
    overlay = {
        "servers": {
            "pal": {
                "transport": "stdio",
                "endpoint": None,
                "source": "unreachable",
                "captured_at": "2026-07-16T01:00:00Z",
                "tool_count": 0,
                "tools": {},
                "reason": "stdio transport; capture via seed or session",
            }
        }
    }

    merged = ts.merge_snapshots(base, overlay)

    # Nothing better exists in base, so the unreachable overlay entry surfaces.
    assert merged["servers"]["pal"]["source"] == "unreachable"


def test_merge_preserves_base_only_servers_untouched():
    base = {"servers": {"dope-memory": _entry("seed", tool_count=10)}}
    overlay = {"servers": {}}

    merged = ts.merge_snapshots(base, overlay)

    assert merged["servers"] == base["servers"]


# --------------------------------------------------------------------------
# (c) Deterministic serialization
# --------------------------------------------------------------------------


def test_dump_snapshot_is_deterministic_regardless_of_key_insertion_order():
    servers_a = {}
    servers_a["zeta"] = _entry("live", tool_count=2)
    servers_a["alpha"] = _entry("seed", tool_count=1)
    snapshot_a = {
        "schema_version": 1,
        "generated_at": "2026-07-16T00:00:00Z",
        "generator": "dopemux mcp snapshot-tools",
        "servers": servers_a,
    }

    servers_b = {}
    servers_b["alpha"] = _entry("seed", tool_count=1)
    servers_b["zeta"] = _entry("live", tool_count=2)
    snapshot_b = {
        "schema_version": 1,
        "generated_at": "2026-07-16T00:00:00Z",
        "generator": "dopemux mcp snapshot-tools",
        "servers": servers_b,
    }

    dump_a = ts.dump_snapshot(snapshot_a)
    dump_b = ts.dump_snapshot(snapshot_b)

    assert dump_a == dump_b
    assert dump_a.endswith("\n")
    # Keys come out alphabetically sorted at every level.
    assert dump_a.index('"alpha"') < dump_a.index('"zeta"')


def test_dump_snapshot_round_trips_through_load_snapshot(tmp_path):
    snapshot = {
        "schema_version": 1,
        "generated_at": "2026-07-16T00:00:00Z",
        "generator": "dopemux mcp snapshot-tools",
        "servers": {"serena": _entry("live", tool_count=27)},
    }
    path = tmp_path / "mcp_tool_surfaces.json"
    path.write_text(ts.dump_snapshot(snapshot), encoding="utf-8")

    loaded = ts.load_snapshot(path)

    assert loaded == snapshot


def test_load_snapshot_missing_file_returns_empty_snapshot(tmp_path):
    loaded = ts.load_snapshot(tmp_path / "missing.json")

    assert loaded["servers"] == {}
    assert loaded["schema_version"] == ts.SCHEMA_VERSION


def test_load_snapshot_malformed_file_returns_empty_snapshot(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json at all", encoding="utf-8")

    loaded = ts.load_snapshot(path)

    assert loaded["servers"] == {}


# --------------------------------------------------------------------------
# (d) SSE-frame body parsing helper
# --------------------------------------------------------------------------


def test_parse_mcp_response_body_handles_raw_json():
    body = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}})

    parsed = ts.parse_mcp_response_body(body)

    assert parsed == {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}


def test_parse_mcp_response_body_handles_sse_framed_single_event():
    payload = {"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "foo"}]}}
    body = f"event: message\ndata: {json.dumps(payload)}\n\n"

    parsed = ts.parse_mcp_response_body(body)

    assert parsed == payload


def test_parse_mcp_response_body_picks_jsonrpc_result_among_multiple_frames():
    keepalive = {"type": "ping"}
    payload = {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}
    body = (
        f"data: {json.dumps(keepalive)}\n\n"
        f"event: message\ndata: {json.dumps(payload)}\n\n"
    )

    parsed = ts.parse_mcp_response_body(body)

    assert parsed == payload


def test_parse_mcp_response_body_handles_error_frame():
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "error": {"code": -32601, "message": "not found"},
    }
    body = f"data: {json.dumps(payload)}\n\n"

    parsed = ts.parse_mcp_response_body(body)

    assert parsed == payload


def test_parse_mcp_response_body_returns_none_for_empty_or_unparseable():
    assert ts.parse_mcp_response_body("") is None
    assert ts.parse_mcp_response_body("   \n  ") is None
    assert ts.parse_mcp_response_body("not json, not sse") is None


def test_parse_mcp_response_body_ignores_done_sentinel():
    assert ts.parse_mcp_response_body("data: [DONE]\n\n") is None


def test_extract_tools_reads_name_and_first_line_of_description():
    parsed = {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {"name": "a", "description": "Line one.\nLine two ignored."},
                {"name": "b"},
            ]
        },
    }

    tools = ts._extract_tools(parsed)

    assert tools == {"a": "Line one.", "b": ""}


def test_extract_tools_returns_none_for_non_tools_shape():
    assert ts._extract_tools({"jsonrpc": "2.0", "result": {}}) is None
    assert ts._extract_tools({"jsonrpc": "2.0", "error": {"code": -1}}) is None
    assert ts._extract_tools(None) is None


def test_first_line_truncates_to_120_chars_with_ellipsis():
    long_text = "x" * 200
    result = ts._first_line(long_text, limit=120)

    assert len(result) == 120
    assert result.endswith("…")


# --------------------------------------------------------------------------
# Endpoint resolution (used by snapshot_from_live)
# --------------------------------------------------------------------------


def test_resolve_endpoint_uses_url_for_singleton_servers():
    spec = {"transport": "http", "url": "http://localhost:3003/mcp"}

    endpoint = ts._resolve_endpoint(spec, {})

    assert endpoint == "http://localhost:3003/mcp"


def test_resolve_endpoint_expands_url_template_with_env_default():
    spec = {
        "transport": "sse",
        "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
    }

    assert ts._resolve_endpoint(spec, {}) == "http://localhost:3005/sse"
    assert (
        ts._resolve_endpoint(spec, {"CONPORT_MCP_PORT": "3141"})
        == "http://localhost:3141/sse"
    )


def test_resolve_endpoint_returns_none_for_stdio_transport():
    spec = {"transport": "stdio", "command": "docker"}

    assert ts._resolve_endpoint(spec, {}) is None


# --------------------------------------------------------------------------
# snapshot_from_live fail-open behavior (stdio + unsupported transports;
# no network needed since these branches never reach the wire)
# --------------------------------------------------------------------------


def test_snapshot_from_live_marks_stdio_servers_unreachable_with_reason():
    catalog = {
        "servers": {
            "pal-stdio": {"transport": "stdio", "command": "docker"},
        }
    }

    snapshot = ts.snapshot_from_live(catalog, timeout=0.01)

    entry = snapshot["servers"]["pal-stdio"]
    assert entry["source"] == "unreachable"
    assert entry["reason"] == "stdio transport; capture via seed or session"
    assert entry["tool_count"] == 0


def test_snapshot_from_live_one_bad_server_does_not_abort_others():
    catalog = {
        "servers": {
            "pal-stdio": {"transport": "stdio", "command": "docker"},
            "mystery": {"transport": "carrier-pigeon"},
        }
    }

    snapshot = ts.snapshot_from_live(catalog, timeout=0.01)

    assert set(snapshot["servers"]) == {"pal-stdio", "mystery"}
    assert snapshot["servers"]["mystery"]["source"] == "unreachable"
