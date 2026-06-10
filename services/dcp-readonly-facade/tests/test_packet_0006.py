"""TP-DCP-MCP-RO-0006: dope-context and task-orchestrator adapter tests.

Coverage:
  - Happy path (dope-context tools return BLOCKED with transport limitation)
  - Happy path (task-orchestrator tools return OK with data)
  - Missing profile → BLOCKED
  - Backend unavailable → BLOCKED
  - Sub-call partial failure → PARTIAL (task-orchestrator only)
  - Redaction applied to task-orchestrator response
  - Denial assertions (source inspection):
      - dope_context.py never references search_all, index_workspace, index_docs,
        clear_index, sync_workspace, sync_docs, start_autonomous, stop_autonomous
      - task_orchestrator.py never constructs a "transition" path
      - tools.py new functions never reference forbidden PM/bridge routes
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from dcp_facade import envelope as E
from dcp_facade import dope_context as dc_adapter
from dcp_facade import task_orchestrator as to_adapter
from dcp_facade import tools
from dcp_facade.http_client import ReadOnlyHttpError

_SRC = Path(__file__).resolve().parents[1] / "src" / "dcp_facade"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reg_with_profiles(build_registry, project_entry, ws, profiles):
    return build_registry(
        [project_entry(ws, project_id="p", service_profiles=profiles)],
        approved_roots=[str(ws.parent)],
    )


def _dc_profiles():
    return {"dope_context": {"base_url": "http://127.0.0.1:3010"}}


def _to_profiles():
    return {"task_orchestrator": {"base_url": "http://127.0.0.1:8000"}}


def _full_profiles():
    return {
        "dope_context": {"base_url": "http://127.0.0.1:3010"},
        "task_orchestrator": {"base_url": "http://127.0.0.1:8000"},
    }


def _to_profiles_with_pid(pid: str):
    return {"task_orchestrator": {"base_url": "http://127.0.0.1:8000", "task_orchestrator_project_id": pid}}


# ---------------------------------------------------------------------------
# dope-context: search_code_docs
# ---------------------------------------------------------------------------

class TestSearchCodeDocs:
    def test_blocked_with_transport_limitation(self, make_workspace, build_registry, project_entry, make_client):
        """Phase 1: search_code_docs always returns BLOCKED (transport not bridged)."""
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _dc_profiles())
        client, ft = make_client(json_body={"results": []})
        env = tools.search_code_docs(reg, "p", query="oauth", client=client)
        assert env["status"] == E.BLOCKED
        assert env["source_system"] == E.SOURCE_DOPE_CONTEXT
        assert env["authority_label"] == E.AUTHORITY_DERIVED
        assert any("MCP transport not yet bridged" in r for r in env["blocked_reasons"])
        assert any("MCP JSON-RPC" in lim for lim in env["limitations"])
        # Client was never called (fail-closed before any HTTP request succeeds)
        assert ft.calls == []

    def test_blocked_with_docs_kind(self, make_workspace, build_registry, project_entry, make_client):
        """docs kind also returns BLOCKED."""
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _dc_profiles())
        client, _ = make_client()
        env = tools.search_code_docs(reg, "p", query="architecture", kind="docs", client=client)
        assert env["status"] == E.BLOCKED
        assert env["source_system"] == E.SOURCE_DOPE_CONTEXT

    def test_unknown_project_blocked(self, build_registry, make_client):
        reg = build_registry([])
        client, _ = make_client()
        env = tools.search_code_docs(reg, "ghost", query="foo", client=client)
        assert env["status"] == E.BLOCKED

    def test_missing_dope_context_profile_blocked(self, make_workspace, build_registry, project_entry, make_client):
        ws = make_workspace()["path"]
        # only task_orchestrator profile, no dope_context
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        client, _ = make_client()
        env = tools.search_code_docs(reg, "p", query="foo", client=client)
        assert env["status"] == E.BLOCKED
        assert any("dope_context not configured" in r for r in env["blocked_reasons"])

    def test_data_is_none(self, make_workspace, build_registry, project_entry, make_client):
        """Blocked envelope carries no fabricated data."""
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _dc_profiles())
        client, _ = make_client()
        env = tools.search_code_docs(reg, "p", query="anything", client=client)
        assert env["data"] is None


# ---------------------------------------------------------------------------
# dope-context: get_index_status
# ---------------------------------------------------------------------------

class TestGetIndexStatus:
    def test_blocked_with_transport_and_inventory_limitation(self, make_workspace, build_registry, project_entry, make_client):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _dc_profiles())
        client, ft = make_client(json_body={})
        env = tools.get_index_status(reg, "p", client=client)
        assert env["status"] == E.BLOCKED
        assert env["source_system"] == E.SOURCE_DOPE_CONTEXT
        assert env["authority_label"] == E.AUTHORITY_DERIVED
        assert any("MCP transport not yet bridged" in r for r in env["blocked_reasons"])
        assert any("PROPOSED-only" in lim for lim in env["limitations"])
        # Client was never called
        assert ft.calls == []

    def test_unknown_project_blocked(self, build_registry, make_client):
        reg = build_registry([])
        client, _ = make_client()
        env = tools.get_index_status(reg, "ghost", client=client)
        assert env["status"] == E.BLOCKED

    def test_missing_dope_context_profile_blocked(self, make_workspace, build_registry, project_entry, make_client):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        client, _ = make_client()
        env = tools.get_index_status(reg, "p", client=client)
        assert env["status"] == E.BLOCKED
        assert any("dope_context not configured" in r for r in env["blocked_reasons"])


# ---------------------------------------------------------------------------
# task-orchestrator: get_workflow_status_snapshot
# ---------------------------------------------------------------------------

_TO_QUEUE_RESP = {"items": [{"id": "task-1", "title": "Do something"}], "count": 1}
_TO_BLOCKERS_RESP = {"blockers": [], "count": 0}
_TO_STATE_RESP = {"project_id": "p", "phases": [], "allowed_transitions": []}


class FanOutTransport:
    """Fake transport that returns different responses per URL path."""

    def __init__(self, routes: dict, default_status=200):
        self.routes = routes  # path-suffix -> {"json": ..., "status": ...}
        self.default_status = default_status
        self.calls: list[dict] = []

    def __call__(self, *, method, url, params, json, timeout):
        self.calls.append({"method": method, "url": url, "params": params})
        from dcp_facade.http_client import HttpResponse
        for suffix, resp in self.routes.items():
            if url.endswith(suffix):
                status = resp.get("status", 200)
                return HttpResponse(status=status, json=resp.get("json"), ok=(200 <= status < 300))
        return HttpResponse(status=404, json=None, ok=False)


class TestGetWorkflowStatusSnapshot:
    def test_ok_all_three_subcalls(self, make_workspace, build_registry, project_entry):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        ft = FanOutTransport({
            "/workflow/queue": {"json": _TO_QUEUE_RESP},
            "/workflow/blockers": {"json": _TO_BLOCKERS_RESP},
            "/workflow/state": {"json": _TO_STATE_RESP},
        })
        from dcp_facade.http_client import ReadOnlyHttpClient
        client = ReadOnlyHttpClient(transport=ft)
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        assert env["status"] == E.OK
        assert env["source_system"] == E.SOURCE_TASK_ORCHESTRATOR
        assert env["authority_label"] == E.AUTHORITY_CANONICAL
        assert env["data"]["queue"] is not None
        assert env["data"]["blockers"] is not None
        assert env["data"]["state"] is not None
        # Permanent workflow-view-only limitation always present
        assert any("workflow-view" in lim for lim in env["limitations"])
        # Three GET calls made
        assert len(ft.calls) == 3
        assert all(c["method"] == "GET" for c in ft.calls)

    def test_partial_when_state_fails(self, make_workspace, build_registry, project_entry):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        ft = FanOutTransport({
            "/workflow/queue": {"json": _TO_QUEUE_RESP},
            "/workflow/blockers": {"json": _TO_BLOCKERS_RESP},
            "/workflow/state": {"json": None, "status": 503},
        })
        from dcp_facade.http_client import ReadOnlyHttpClient
        client = ReadOnlyHttpClient(transport=ft)
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        assert env["status"] == E.PARTIAL
        assert env["data"]["queue"] is not None
        assert env["data"]["blockers"] is not None
        assert env["data"]["state"] is None
        assert any("state unavailable" in lim for lim in env["limitations"])

    def test_blocked_when_all_subcalls_fail(self, make_workspace, build_registry, project_entry, make_client):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        client, _ = make_client(raise_exc=TimeoutError("down"))
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        assert env["status"] == E.BLOCKED
        assert any("all task-orchestrator sub-reads failed" in r for r in env["blocked_reasons"])

    def test_missing_task_orchestrator_profile_blocked(self, make_workspace, build_registry, project_entry, make_client):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _dc_profiles())
        client, _ = make_client()
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        assert env["status"] == E.BLOCKED
        assert any("task_orchestrator not configured" in r for r in env["blocked_reasons"])

    def test_unknown_project_blocked(self, build_registry, make_client):
        reg = build_registry([])
        client, _ = make_client()
        env = tools.get_workflow_status_snapshot(reg, "ghost", client=client)
        assert env["status"] == E.BLOCKED

    def test_redaction_applied(self, make_workspace, build_registry, project_entry):
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        leaky = {
            "items": [{"id": "t1", "claimedBy": "user@example.com", "path": str(ws / "secret.txt")}],
        }
        ft = FanOutTransport({
            "/workflow/queue": {"json": leaky},
            "/workflow/blockers": {"json": _TO_BLOCKERS_RESP},
            "/workflow/state": {"json": _TO_STATE_RESP},
        })
        from dcp_facade.http_client import ReadOnlyHttpClient
        client = ReadOnlyHttpClient(transport=ft)
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        blob = str(env["data"])
        assert str(ws) not in blob
        assert env["redactions"]

    def test_workflow_view_limitation_always_present(self, make_workspace, build_registry, project_entry, make_client):
        """Permanent limitation note is present even when backend is unavailable."""
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws, _to_profiles())
        client, _ = make_client(raise_exc=TimeoutError("down"))
        env = tools.get_workflow_status_snapshot(reg, "p", client=client)
        assert any("workflow-view" in lim for lim in env["limitations"])

    def test_registry_bound_project_id_not_caller_supplied(self, make_workspace, build_registry, project_entry):
        """task_orchestrator_project_id comes from registry profile, not caller."""
        ws = make_workspace()["path"]
        reg = _reg_with_profiles(build_registry, project_entry, ws,
                                  _to_profiles_with_pid("registry-bound-pid"))
        captured = []
        ft = FanOutTransport({
            "/workflow/queue": {"json": _TO_QUEUE_RESP},
            "/workflow/blockers": {"json": _TO_BLOCKERS_RESP},
            "/workflow/state": {"json": _TO_STATE_RESP},
        })
        from dcp_facade.http_client import ReadOnlyHttpClient
        client = ReadOnlyHttpClient(transport=ft)
        tools.get_workflow_status_snapshot(reg, "p", client=client)
        # All calls use registry-bound project_id in URL
        for call in ft.calls:
            assert "registry-bound-pid" in call["url"]


# ---------------------------------------------------------------------------
# Denial assertion tests (source inspection)
# ---------------------------------------------------------------------------

class TestDenialAssertions:
    def _src(self, filename: str) -> str:
        return (_SRC / filename).read_text(encoding="utf-8")

    def test_dope_context_adapter_has_no_search_all(self):
        src = self._src("dope_context.py")
        # search_all may appear in comments (denial documentation), but must not
        # appear as a callable or route string outside comments.
        # We check the actual function call tokens, not prose.
        # The denial is documented in module docstring — acceptable in comments.
        # Key check: no HTTP route or function invocation for search_all.
        assert "search_all(" not in src
        assert '"/search_all"' not in src
        assert "'/search_all'" not in src

    def test_dope_context_adapter_has_no_index_mutation_routes(self):
        src = self._src("dope_context.py")
        for forbidden in (
            "index_workspace",
            "index_docs",
            "clear_index",
            "sync_workspace",
            "sync_docs",
            "start_autonomous",
            "stop_autonomous",
        ):
            # These may appear in denial docstrings (DENIED routes section) but
            # must never appear as callable invocations.
            # Check: not called as a function (followed by open-paren or '(').
            assert f"{forbidden}(" not in src, f"forbidden callable {forbidden!r} in dope_context.py"

    def test_task_orchestrator_adapter_has_no_transition_route(self):
        src = self._src("task_orchestrator.py")
        # "transition" must not appear as a URL path component.
        assert "/transition" not in src
        assert '"transition"' not in src
        assert "'transition'" not in src

    def test_task_orchestrator_adapter_has_no_pm_write_routes(self):
        src = self._src("task_orchestrator.py")
        for forbidden in ("/api/pm", "/api/workflow/ideas", "/api/workflow/epics", "promote"):
            assert forbidden not in src, f"forbidden token {forbidden!r} in task_orchestrator.py"

    def test_tools_new_functions_have_no_search_all(self):
        src = self._src("tools.py")
        # search_all should not appear in any executable context.
        assert "search_all(" not in src
        assert '"/search_all"' not in src

    def test_tools_new_functions_have_no_bridge_proxy_routes(self):
        src = self._src("tools.py")
        for forbidden in ("/kg/", "/ddg/", "/route/pm"):
            assert forbidden not in src, f"forbidden token {forbidden!r} in tools.py"

    def test_dope_context_adapter_only_raises_not_calls_http(self):
        """The Phase 1 adapter raises without constructing any HTTP URL."""
        src = self._src("dope_context.py")
        # The adapter must NOT call client.get() or client.post_read() with real paths.
        # It may import ReadOnlyHttpClient for type hints only.
        assert 'client.get(' not in src
        assert 'client.post_read(' not in src

    def test_task_orchestrator_adapter_uses_only_get(self):
        """task_orchestrator adapter only uses client.get(), never post_read."""
        src = self._src("task_orchestrator.py")
        assert 'client.post_read(' not in src
        # Confirm no mutating verbs
        for verb in ("PUT", "PATCH", "DELETE", ".put(", ".patch(", ".delete("):
            assert verb not in src

    def test_no_pm_routes_in_tools_new_sections(self):
        """New tool functions in tools.py must not reference PM write routes."""
        src = self._src("tools.py")
        for forbidden in ("/api/pm", "/api/workflow/ideas", "/api/workflow/epics", "promote"):
            assert forbidden not in src, f"forbidden token {forbidden!r} in tools.py"
