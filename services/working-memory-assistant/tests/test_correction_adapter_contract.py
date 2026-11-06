import json

import pytest
from chronicle.store import ChronicleStore
from dope_memory_main import DopeMemoryMCPServer, MemoryCorrectRequest


def test_main_adapter_applies_supported_fields_and_preserves_omitted_summary(
    tmp_path, monkeypatch
):
    store = ChronicleStore(tmp_path / "ledger.sqlite")
    store.initialize_schema()
    try:
        source = store.insert_work_log_entry(
            "ws",
            "A",
            "planning",
            "decision",
            "Keep summary",
            source_event_id="e",
            source_event_type="test",
            source_adapter="test",
            source_event_ts_utc="2026-11-04T10:00:00Z",
            promotion_rule="test",
        )
        server = DopeMemoryMCPServer("ws")
        monkeypatch.setattr(server, "_get_store", lambda workspace: store)
        result = server.memory_correct(
            "ws",
            "A",
            source,
            "update",
            corrected_tags=["fixed"],
            corrected_category="implementation",
            corrected_entry_type="milestone",
            write_principal="runner:codex",
        )
        assert result.success, result.error
        row = store.get_entry_by_id("ws", "A", result.data["new_entry_id"])
        assert row["summary"] == "Keep summary"
        assert json.loads(row["tags_json"]) == ["fixed"]
        assert row["category"] == "implementation"
        assert row["entry_type"] == "milestone"
        assert row["write_principal"] == "runner:codex"
    finally:
        store.close()


@pytest.mark.parametrize(
    "kind", ["update", "summary", "tags", "category", "outcome", "retraction"]
)
def test_rest_accepts_shared_supported_vocabulary(kind):
    assert (
        MemoryCorrectRequest(entry_id="a", correction_type=kind).correction_type == kind
    )


@pytest.mark.asyncio
async def test_mcp_correction_round_trip_uses_the_same_writer(tmp_path, monkeypatch):
    pytest.importorskip("fastmcp")
    from fastmcp import Client
    from fastmcp.exceptions import ToolError
    from auth_identity import AuthGate
    from mcp_http import build_mcp_server

    store = ChronicleStore(tmp_path / "ledger.sqlite")
    store.initialize_schema()
    try:
        source = store.insert_work_log_entry(
            "ws",
            "A",
            "planning",
            "decision",
            "Keep summary",
            source_event_id="e",
            source_event_type="test",
            source_adapter="test",
            source_event_ts_utc="2026-11-04T10:00:00Z",
            promotion_rule="test",
            tags=["old"],
            details={"preserved": True},
        )
        backend = DopeMemoryMCPServer("ws")
        monkeypatch.setattr(backend, "_get_store", lambda workspace: store)
        server = build_mcp_server(
            lambda: backend,
            bound_workspace_id="ws",
            read_default_instance_id="A",
            gate=AuthGate(mode="log", auth_dir=tmp_path / "auth"),
        )
        async with Client(server) as client:
            result = await client.call_tool(
                "memory_correct",
                {
                    "entry_id": source,
                    "correction_type": "tags",
                    "corrected_tags": [],
                    "idempotency_key": "mcp-key",
                },
            )
            entry_id = result.data["new_entry_id"]
            row = store.get_entry_by_id("ws", "A", entry_id)
            assert row["summary"] == "Keep summary"
            assert json.loads(row["tags_json"]) == []
            assert json.loads(row["details_json"]) == {"preserved": True}
            assert row["write_principal"] == "unverified"
            retry = await client.call_tool(
                "memory_correct",
                {
                    "entry_id": source,
                    "correction_type": "tags",
                    "corrected_tags": ["changed"],
                    "idempotency_key": "mcp-key",
                },
            )
            assert retry.data["new_entry_id"] == entry_id
            with pytest.raises(ToolError, match="correction_type"):
                await client.call_tool(
                    "memory_correct", {"entry_id": entry_id, "correction_type": "typo"}
                )
    finally:
        store.close()
