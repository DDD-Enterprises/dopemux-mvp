"""Release-one safe adapter gate tests (TP-DCP-MCP-RO-0015)."""

from __future__ import annotations

from dcp_facade.http_client import HttpResponse, ReadOnlyHttpClient, ReadOnlyHttpError
from dcp_facade.ownership import OwnershipEvidence, OwnershipVerdict, verify_ownership
from dcp_facade import safe_adapters as SA
from dcp_facade.route_manifest import (
    RELEASE_ONE_DENIED_OPERATIONS,
    RELEASE_ONE_OPERATIONS,
    is_release_one_operation,
)


class _FakeTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, *, method, url, params, json, timeout):
        self.calls.append(
            {"method": method, "url": url, "params": params, "json": json}
        )
        return HttpResponse(status=200, json={"ok": True, "url": url}, ok=True)


def _verified(family: str = "conport") -> OwnershipVerdict:
    service = "conport" if family == "conport" else "dope-memory"
    return verify_ownership(
        OwnershipEvidence(
            family=family,
            expected_project_id="proj-a",
            expected_project_root="/tmp/proj-a",
            expected_worktree_root="/tmp/proj-a/wt",
            runtime_project_id="proj-a",
            runtime_project_root="/tmp/proj-a",
            runtime_worktree_root="/tmp/proj-a/wt",
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": service,
                "dopemux.worktree_root": "/tmp/proj-a/wt",
            },
            mounts=("/tmp/proj-a/wt",),
            protocol_ok=True,
            candidate_count=1,
        )
    )


def _blocked() -> OwnershipVerdict:
    return OwnershipVerdict(
        family="conport", state="BLOCKED", reason="wrong project identity", evidence_codes=("wrong_project",)
    )


def test_release_one_operation_table():
    assert is_release_one_operation("conport", "list_decisions")
    assert is_release_one_operation("conport", "get_decision")
    assert not is_release_one_operation("conport", "get_progress")
    assert is_release_one_operation("dope_memory", "memory_search")
    assert "get_progress" in RELEASE_ONE_DENIED_OPERATIONS
    assert SA.release_one_operations()["conport"] == RELEASE_ONE_OPERATIONS["conport"]


def test_list_decisions_requires_ownership():
    transport = _FakeTransport()
    client = ReadOnlyHttpClient(transport=transport)
    denied = SA.list_decisions(
        ownership=_blocked(),
        client=client,
        base_url="http://127.0.0.1:3004",
        workspace_id="ws",
    )
    assert denied.allowed is False
    assert transport.calls == []

    allowed = SA.list_decisions(
        ownership=_verified("conport"),
        client=client,
        base_url="http://127.0.0.1:3004",
        workspace_id="ws",
        limit=5,
    )
    assert allowed.allowed is True
    assert allowed.response is not None and allowed.response.ok
    assert transport.calls and transport.calls[0]["method"] == "GET"
    assert "/api/decisions" in transport.calls[0]["url"]


def test_get_decision_by_id():
    transport = _FakeTransport()
    client = ReadOnlyHttpClient(transport=transport)
    result = SA.get_decision(
        ownership=_verified("conport"),
        client=client,
        base_url="http://127.0.0.1:3004",
        workspace_id="ws",
        decision_id="dec-1",
    )
    assert result.allowed is True
    assert "/api/decisions/dec-1" in transport.calls[0]["url"]


def test_progress_explicitly_blocked():
    result = SA.deny_blocked_operation("get_progress", "conport")
    assert result.allowed is False
    assert "blocked" in result.reason


def test_memory_search_and_replay_release_one():
    transport = _FakeTransport()
    client = ReadOnlyHttpClient(transport=transport)
    own = _verified("dope_memory")
    search = SA.memory_search(
        ownership=own,
        client=client,
        base_url="http://127.0.0.1:3020",
        workspace_id="ws",
        query="q",
    )
    replay = SA.memory_replay_session(
        ownership=own,
        client=client,
        base_url="http://127.0.0.1:3020",
        workspace_id="ws",
        session_id="s1",
    )
    assert search.allowed and replay.allowed
    paths = [c["url"] for c in transport.calls]
    assert any("memory_search" in u for u in paths)
    assert any("memory_replay_session" in u for u in paths)


def test_memory_write_not_release_one():
    assert not is_release_one_operation("dope_memory", "memory_store")
    denied = SA.deny_blocked_operation("memory_store", "dope_memory")
    assert denied.allowed is False


def test_adapter_error_fail_closed():
    def boom(**kwargs):
        raise ReadOnlyHttpError("base_url host is not loopback")

    client = ReadOnlyHttpClient(transport=boom)
    result = SA.list_decisions(
        ownership=_verified("conport"),
        client=client,
        base_url="http://127.0.0.1:3004",
        workspace_id="ws",
    )
    assert result.allowed is False
    assert "adapter error" in result.reason


def test_public_dict_never_marks_callable():
    transport = _FakeTransport()
    client = ReadOnlyHttpClient(transport=transport)
    result = SA.list_decisions(
        ownership=_verified("conport"),
        client=client,
        base_url="http://127.0.0.1:3004",
        workspace_id="ws",
    )
    pub = result.to_public_dict()
    assert pub["callable"] is False
    assert pub["allowed"] is True
