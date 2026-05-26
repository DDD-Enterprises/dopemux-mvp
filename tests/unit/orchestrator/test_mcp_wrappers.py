import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.orchestrator.policy import classify_capability


class _Result(SimpleNamespace):
    def model_dump(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }


def _queue_result():
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "priority_queue",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        queue_items=[{"id": "TP-1", "title": "Ready"}],
        next_action={"id": "TP-1", "title": "Ready"},
        error=None,
    )


def _blockers_result():
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "blockers",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        active_blockers=[{"id": "TP-0", "title": "Blocked"}],
        error=None,
    )


def _workflow_result():
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "workflow_state",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        state={"status": "active"},
        allowed_transitions=["start"],
        error=None,
    )


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _packet_payload() -> dict:
    return {
        "id": "TP-DMX-ORCH-005",
        "project": "dopemux-mvp",
        "target": "Add read-only MCP wrappers",
        "repo_binding": {
            "project_id": "DDD-Enterprises/dopemux-mvp",
            "repo_marker": ".dopetaskroot",
            "require_identity_match": True,
        },
        "series": {
            "id": "DMX-ORCH-INTEGRATION",
            "base_branch": "main",
            "parent_tp_id": "TP-DMX-ORCH-004",
            "final_packet": False,
        },
        "commit": {
            "message": "feat(orchestrator): add read-only MCP wrappers",
            "allowlist": ["src/dopemux/orchestrator/mcp_wrappers.py"],
        },
        "pr": {
            "title": "feat(orchestrator): add read-only MCP wrappers",
            "body": "Add read-only MCP wrappers",
            "base": "main",
        },
        "steps": [
            {
                "id": "validate",
                "task": "Validate wrappers",
                "validation": ["pytest exits 0"],
            }
        ],
    }


def _proof_payload() -> dict:
    return {
        "bundle_id": "TP-DMX-ORCH-005-PROOF",
        "run_id": "tp-dmx-orch-005-local",
        "skill": "codex",
        "status": "READY_FOR_REVIEW",
        "validation_state": "PASSED",
        "created_at": "2026-05-26T00:00:00Z",
        "manifest": {
            "bundle_id": "TP-DMX-ORCH-005-PROOF",
            "packet_id": "TP-DMX-ORCH-005",
            "generated_artifacts": [
                "task-packets/generated/TP-DMX-ORCH-005.json",
                "proof/dmx-orch-integration/TP-DMX-ORCH-005/PROOF.json",
            ],
        },
        "authoritative_artifacts": [
            "task-packets/generated/TP-DMX-ORCH-005.json",
            "proof/dmx-orch-integration/TP-DMX-ORCH-005/PROOF.json",
        ],
        "supporting_artifacts": ["tests/unit/orchestrator/test_mcp_wrappers.py"],
        "chain_of_custody": {
            "documented": True,
            "source_version": "TP-DMX-ORCH-005",
            "created_at": "2026-05-26T00:00:00Z",
            "parent_bundle_ids": ["TP-DMX-ORCH-004"],
        },
        "warnings": [],
        "blockers": [],
    }


def test_orchestrator_mcp_tool_descriptors_are_policy_registered_read_only():
    from dopemux.orchestrator.mcp_wrappers import ORCHESTRATOR_MCP_TOOLS

    tool_names = [tool["name"] for tool in ORCHESTRATOR_MCP_TOOLS]

    assert tool_names == [
        "orchestrator.status.queue",
        "orchestrator.status.blockers",
        "orchestrator.status.state",
        "orchestrator.daily.summary",
        "orchestrator.packet.validate",
        "orchestrator.proof.validate",
    ]
    for tool_name in tool_names:
        decision = classify_capability(tool_name)
        assert decision.tier in {"T0", "T1"}
        assert decision.allowed is True
        assert decision.decision == "allow"
        assert not any(
            forbidden in tool_name
            for forbidden in {
                "apply",
                "comment",
                "delete",
                "index",
                "merge",
                "record",
                "refresh",
                "transition",
                "write",
            }
        )


@pytest.mark.asyncio
async def test_queue_wrapper_dispatches_read_helper_with_policy_metadata(monkeypatch):
    from dopemux.orchestrator import mcp_wrappers

    async def fake_queue(project_id: str):
        assert project_id == "dopemux-mvp"
        return _queue_result()

    monkeypatch.setattr(mcp_wrappers, "pm_get_priority_queue", fake_queue)

    payload = await mcp_wrappers.handle_orchestrator_tool_call(
        "orchestrator.status.queue",
        {"project_id": "dopemux-mvp"},
    )

    assert payload["tool"] == "orchestrator.status.queue"
    assert payload["read_only"] is True
    assert payload["policy"]["tier"] == "T0"
    assert payload["policy"]["allowed"] is True
    assert payload["result"]["queue_items"] == [{"id": "TP-1", "title": "Ready"}]


@pytest.mark.asyncio
async def test_daily_wrapper_combines_read_only_status_surfaces(monkeypatch):
    from dopemux.orchestrator import mcp_wrappers

    async def fake_queue(project_id: str):
        return _queue_result()

    async def fake_blockers(project_id: str):
        return _blockers_result()

    async def fake_state(project_id: str):
        return _workflow_result()

    monkeypatch.setattr(mcp_wrappers, "pm_get_priority_queue", fake_queue)
    monkeypatch.setattr(mcp_wrappers, "pm_get_blockers", fake_blockers)
    monkeypatch.setattr(mcp_wrappers, "pm_get_workflow_state", fake_state)

    payload = await mcp_wrappers.handle_orchestrator_tool_call(
        "orchestrator.daily.summary",
        {"project_id": "dopemux-mvp"},
    )

    assert payload["read_only"] is True
    assert payload["policy"]["tier"] == "T1"
    assert payload["result"]["queue"]["queue_items"][0]["id"] == "TP-1"
    assert payload["result"]["blockers"]["active_blockers"][0]["id"] == "TP-0"
    assert payload["result"]["workflow_state"]["state"] == {"status": "active"}


@pytest.mark.asyncio
async def test_validator_wrappers_return_validation_reports(tmp_path: Path):
    from dopemux.orchestrator.mcp_wrappers import handle_orchestrator_tool_call

    packet_path = _write_json(tmp_path / "packet.json", _packet_payload())
    proof_path = _write_json(tmp_path / "proof.json", _proof_payload())

    packet_payload = await handle_orchestrator_tool_call(
        "orchestrator.packet.validate",
        {"packet_path": str(packet_path)},
    )
    proof_payload = await handle_orchestrator_tool_call(
        "orchestrator.proof.validate",
        {"proof_path": str(proof_path)},
    )

    assert packet_payload["read_only"] is True
    assert packet_payload["policy"]["tier"] == "T1"
    assert packet_payload["validation"]["kind"] == "task_packet"
    assert packet_payload["validation"]["status"] == "PASS"
    assert proof_payload["validation"]["kind"] == "proof_bundle"
    assert proof_payload["validation"]["status"] == "PASS"


@pytest.mark.asyncio
async def test_unknown_wrapper_tool_fails_closed():
    from dopemux.orchestrator.mcp_wrappers import handle_orchestrator_tool_call

    payload = await handle_orchestrator_tool_call(
        "orchestrator.transition.apply",
        {"item_id": "TP-1"},
    )

    assert payload["read_only"] is True
    assert payload["error"] == "Unknown read-only orchestrator MCP tool"
    assert payload["policy"]["allowed"] is False
