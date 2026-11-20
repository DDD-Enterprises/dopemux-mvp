"""Tests for the cockpit's read-only Task Orchestrator queue reader.

Fixtures are synthetic. The result envelope (``structuredContent`` holding
``{items, total, returned, limit, offset}``, with a prose summary in ``content``) and the tool
error shape were observed on the live orchestrator on 2026-11-16 with a filter that matches
nothing. The fields of an item follow the list-mode description in its tools list; no real item
has been read.
"""
import asyncio
import json
import subprocess

import pytest

import orchestrator_tasks as ot
from dopemux.mcp.docker_inspect import DockerContainerInfo, DockerInspectResult

EXPECTED = ot.ExpectedProject(project_id="alpha", project_root="/synthetic/alpha")
MCP_URL = ot.MCP_URL


def _container(name, project_id, project_root, ports=(7890,)):
    return DockerContainerInfo(
        id=f"id-{name}",
        name=name,
        labels={"dopemux.project_id": project_id, "dopemux.project_root": project_root},
        published_ports=list(ports),
    )


def _inspect(*containers, available=True, error=None):
    calls = []

    def inspect(*, timeout):
        calls.append(timeout)
        return DockerInspectResult(available=available, error=error, containers=list(containers))

    inspect.calls = calls
    return inspect


def _wrapper(*items, total=None):
    return {
        "items": list(items),
        "total": len(items) if total is None else total,
        "returned": len(items),
        "limit": 20,
        "offset": 0,
    }


def _rpc(wrapper, summary="Found some item(s)"):
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [{"type": "text", "text": summary}],
            "isError": False,
            "structuredContent": wrapper,
        },
    }


WORK_ITEM = {"id": "11111111-aaaa", "parentId": None, "title": "Wire the queue", "role": "work",
             "priority": "high", "depth": 0, "tags": "cockpit,backend"}
QUEUE_ITEM = {"id": "22222222-bbbb", "parentId": "11111111-aaaa", "title": "Write the tests", "role": "queue",
              "priority": "medium", "depth": 1, "tags": ["cockpit"], "complexity": 3}


# --- strict parsing ------------------------------------------------------------------------


class TestParsing:
    def test_structured_content_wrapper(self):
        items, total = ot.parse_item_list(ot.extract_tool_payload(_rpc(_wrapper(WORK_ITEM))), "work")

        assert total == 1
        assert items == [
            {
                "id": "11111111-aaaa",
                "title": "Wire the queue",
                "role": "work",
                "priority": "high",
                "parent_id": None,
                "depth": 0,
                "tags": ["cockpit", "backend"],
                "complexity": None,
            }
        ]

    def test_observed_empty_result(self):
        rpc = _rpc(_wrapper(), summary="Found 0 item(s)")
        assert ot.parse_item_list(ot.extract_tool_payload(rpc), "queue") == ([], 0)

    def test_supplied_complexity_and_parent_pass_through(self):
        items, _ = ot.parse_item_list(_wrapper(QUEUE_ITEM), "queue")
        assert items[0]["complexity"] == 3
        assert items[0]["parent_id"] == "11111111-aaaa"
        assert items[0]["tags"] == ["cockpit"]

    def test_fields_the_orchestrator_omits_become_null(self):
        items, total = ot.parse_item_list({"items": [{"id": "x1", "title": "Bare"}]}, "queue")
        assert total is None
        assert items[0] == {"id": "x1", "title": "Bare", "role": "queue", "priority": None,
                            "parent_id": None, "depth": None, "tags": None, "complexity": None}

    def test_wrongly_typed_optional_fields_become_null(self):
        raw = {"id": "x1", "title": "Odd", "priority": 5, "depth": "deep", "tags": 7, "complexity": True}
        items, _ = ot.parse_item_list({"items": [raw], "total": "many"}, "queue")
        assert items[0]["priority"] is None
        assert items[0]["depth"] is None
        assert items[0]["tags"] is None
        assert items[0]["complexity"] is None

    @pytest.mark.parametrize(
        "rpc",
        [
            None,
            [],
            {},
            {"result": "nope"},
            {"result": {"content": [{"type": "text", "text": "Found 3 item(s)"}], "isError": False}},
            {"result": {"structuredContent": ["not", "an", "object"]}},
        ],
    )
    def test_unexpected_envelopes_are_errors(self, rpc):
        with pytest.raises(ot.McpReadError):
            ot.extract_tool_payload(rpc)

    def test_jsonrpc_error_and_tool_error_are_errors(self):
        with pytest.raises(ot.McpReadError) as rpc_error:
            ot.extract_tool_payload({"error": {"code": -32000, "message": "boom at /synthetic/home/db"}})
        assert str(rpc_error.value) == "orchestrator returned a JSON-RPC error"
        assert rpc_error.value.detail == "boom at /synthetic/home/db"

        tool_error = {"result": {"isError": True, "content": [{"type": "text", "text": "Query failed: Invalid role"}]}}
        with pytest.raises(ot.McpReadError) as reported:
            ot.extract_tool_payload(tool_error)
        assert str(reported.value) == "orchestrator tool reported an error"
        assert reported.value.detail == "Query failed: Invalid role"

    def test_role_text_from_the_server_is_not_forwarded(self):
        payload = {"items": [{"id": "x1", "title": "Odd", "role": "/synthetic/home/role"}]}
        with pytest.raises(ot.McpReadError) as mismatch:
            ot.parse_item_list(payload, "queue")
        assert str(mismatch.value) == "asked for role queue, got an item in another role"
        assert "/synthetic" in mismatch.value.detail

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"items": "many"},
            {"items": [["not", "an", "object"]]},
            {"items": [{"title": "No id"}]},
            {"items": [{"id": "x1"}]},
            {"items": [{"id": "", "title": "Empty id"}]},
            {"items": [{"id": "x1", "title": "Wrong role", "role": "terminal"}]},
        ],
    )
    def test_unexpected_item_lists_are_errors(self, payload):
        with pytest.raises(ot.McpReadError):
            ot.parse_item_list(payload, "queue")


# --- port ownership ------------------------------------------------------------------------


class TestPortOwner:
    def test_this_projects_container_is_ok(self):
        inspect = _inspect(_container("to-alpha", "alpha", "/synthetic/alpha"))
        check = ot.check_port_owner(EXPECTED, inspect=inspect)
        assert check.verdict == "OK"
        assert (check.project_id, check.name) == ("alpha", "alpha")
        assert check.container_id == "id-to-alpha"
        assert inspect.calls == [ot.OWNER_CHECK_TIMEOUT_S]
        assert ot.OWNER_CHECK_TIMEOUT_S <= 5.0

    def test_another_projects_container_is_wrong_project(self):
        inspect = _inspect(_container("to-beta", "beta", "/synthetic/elsewhere/beta"))
        check = ot.check_port_owner(EXPECTED, inspect=inspect)
        assert check.verdict == "WRONG_PROJECT"
        assert (check.project_id, check.name) == ("beta", "beta")
        assert "/synthetic" not in json.dumps(check.__dict__)

    def test_container_on_another_port_does_not_count(self):
        inspect = _inspect(_container("to-alpha", "alpha", "/synthetic/alpha", ports=(8000,)))
        check = ot.check_port_owner(EXPECTED, inspect=inspect)
        assert check.verdict == "UNKNOWN"
        assert "no container publishes port 7890" in check.detail

    def test_two_publishers_are_unknown(self):
        inspect = _inspect(
            _container("to-alpha", "alpha", "/synthetic/alpha"),
            _container("to-beta", "beta", "/synthetic/beta"),
        )
        assert ot.check_port_owner(EXPECTED, inspect=inspect).verdict == "UNKNOWN"

    @pytest.mark.parametrize(
        "docker_error, public",
        [
            ("docker ps timed out", "docker ps timed out"),
            ("docker binary not found on PATH", "docker binary not found"),
            ("docker binary not found", "docker binary not found"),
            ("Cannot connect to the Docker daemon at unix:///synthetic/home/.docker/run/docker.sock.", "docker is not reachable"),
            ("docker ps failed: [Errno 13] Permission denied: '/synthetic/home/bin/docker'", "docker is not reachable"),
            (None, "docker is not reachable"),
        ],
    )
    def test_docker_failures_map_to_fixed_messages(self, docker_error, public):
        check = ot.check_port_owner(EXPECTED, inspect=_inspect(available=False, error=docker_error))
        assert check.verdict == "UNKNOWN"
        assert check.detail == f"docker ps unavailable: {public}"
        assert check.container_id is None

    def test_a_path_in_the_project_id_label_is_not_passed_on(self):
        odd = _container("to-odd", "/synthetic/home/code/beta", "/synthetic/home/code/beta")
        check = ot.check_port_owner(EXPECTED, inspect=_inspect(odd))
        assert check.verdict == "WRONG_PROJECT"
        assert check.project_id is None and check.name == "beta"
        assert "/synthetic" not in json.dumps(check.__dict__)

    def test_owner_without_a_container_id_is_unknown(self):
        nameless = DockerContainerInfo(
            id="", name="to-alpha", published_ports=[7890],
            labels={"dopemux.project_id": "alpha", "dopemux.project_root": "/synthetic/alpha"},
        )
        check = ot.check_port_owner(EXPECTED, inspect=_inspect(nameless))
        assert check.verdict == "UNKNOWN"
        assert "no container id" in check.detail

    def test_unlabelled_container_is_unknown(self):
        bare = DockerContainerInfo(id="id", name="mystery", labels={}, published_ports=[7890])
        assert ot.check_port_owner(EXPECTED, inspect=_inspect(bare)).verdict == "UNKNOWN"

    def test_matching_root_with_another_id_is_never_ok(self):
        inspect = _inspect(_container("to-odd", "beta", "/synthetic/alpha"))
        assert ot.check_port_owner(EXPECTED, inspect=inspect).verdict == "CONFLICT"


def test_expected_project_is_unknown_outside_a_git_checkout(tmp_path):
    assert ot.resolve_expected_project(tmp_path) is None


def _git_fails_with(monkeypatch, error):
    """Make every git call of the identity resolver fail the way a host without git does."""
    from dopemux.mcp import project_identity

    def run(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(project_identity.subprocess, "run", run)


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError(2, "No such file or directory", "git"),
        PermissionError(13, "Permission denied", "git"),
        subprocess.TimeoutExpired(cmd=["git", "rev-parse"], timeout=5),
    ],
)
def test_expected_project_is_unknown_when_git_cannot_run(monkeypatch, tmp_path, error):
    _git_fails_with(monkeypatch, error)
    assert ot.resolve_expected_project(tmp_path) is None


def test_missing_git_is_unavailable_not_an_exception(monkeypatch, tmp_path):
    """The slim service image has no git: /api/tasks must still answer, with unavailable."""
    _git_fails_with(monkeypatch, FileNotFoundError(2, "No such file or directory", "git"))
    owner_checks = []
    lister = _lister()

    result = asyncio.run(
        ot.read_task_queue(tmp_path, check_owner=lambda expected: owner_checks.append(expected), list_role=lister)
    )

    assert result["status"] == "unavailable"
    assert result["project"] == {"expected": None, "owner": None, "verdict": "NOT_CHECKED"}
    assert result["items"] == []
    assert owner_checks == [] and lister.calls == []


# --- the gate ------------------------------------------------------------------------------


OK = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha", container_id="c-alpha-1")
OK_RECREATED = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha", container_id="c-alpha-2")
OK_NO_ID = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha")
WRONG = ot.OwnerCheck(verdict="WRONG_PROJECT", project_id="beta", name="beta", detail="to-beta")
UNKNOWN = ot.OwnerCheck(verdict="UNKNOWN", project_id=None, name=None, detail="docker ps timed out")
CONFLICT = ot.OwnerCheck(verdict="CONFLICT", project_id="beta", name="alpha", detail="to-odd")


def _owner_sequence(*checks):
    remaining = list(checks)
    seen = []

    def check_owner(expected):
        seen.append(expected)
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    check_owner.seen = seen
    return check_owner


def _lister(by_role=None, error=None):
    calls = []

    async def list_role(role):
        calls.append(role)
        if error:
            raise error
        return (by_role or {}).get(role, ([], 0))

    list_role.calls = calls
    return list_role


def _read(**overrides):
    kwargs = {
        "resolve_expected": lambda _checkout: EXPECTED,
        "check_owner": _owner_sequence(OK),
        "list_role": _lister(),
    }
    kwargs.update(overrides)
    return asyncio.run(ot.read_task_queue("/synthetic/alpha", **kwargs)), kwargs


def _item(item_id, role):
    return {"id": item_id, "title": item_id.upper(), "role": role, "priority": None, "parent_id": None,
            "depth": None, "tags": None, "complexity": None}


class TestReadTaskQueue:
    def test_unknown_expected_project_serves_nothing_and_asks_nobody(self):
        result, used = _read(resolve_expected=lambda _checkout: None)

        assert result["status"] == "unavailable"
        assert result["project"] == {"expected": None, "owner": None, "verdict": "NOT_CHECKED"}
        assert result["items"] == [] and result["total"] is None
        assert "git checkout" in result["reason"]
        assert used["check_owner"].seen == []
        assert used["list_role"].calls == []

    def test_wrong_project_names_the_owner_and_never_reads(self):
        result, used = _read(check_owner=_owner_sequence(WRONG))

        assert result["status"] == "wrong_project"
        assert result["project"]["owner"] == {"project_id": "beta", "name": "beta"}
        assert result["project"]["expected"] == {"project_id": "alpha", "name": "alpha"}
        assert "beta" in result["reason"] and "7890" in result["reason"]
        assert result["items"] == [] and result["total"] is None
        assert used["list_role"].calls == []

    @pytest.mark.parametrize("check", [UNKNOWN, CONFLICT])
    def test_undetermined_owner_is_unavailable_and_never_reads(self, check):
        result, used = _read(check_owner=_owner_sequence(check))

        assert result["status"] == "unavailable"
        assert result["project"]["verdict"] == check.verdict
        assert check.detail in result["reason"]
        assert result["items"] == []
        assert used["list_role"].calls == []

    def test_ok_lists_work_before_queue(self):
        lister = _lister({"work": ([_item("w1", "work")], 1), "queue": ([_item("q1", "queue"), _item("q2", "queue")], 7)})
        result, _ = _read(list_role=lister)

        assert result["status"] == "ok"
        assert result["source"] == "task-orchestrator-mcp"
        assert result["endpoint"] == MCP_URL
        assert result["roles"] == ["work", "queue"]
        assert lister.calls == ["work", "queue"]
        assert [item["id"] for item in result["items"]] == ["w1", "q1", "q2"]
        assert result["total"] == 8
        assert result["reason"] is None
        assert result["project"]["verdict"] == "OK"
        assert result["fetched_at"].endswith("+00:00")

    def test_ok_with_no_items_is_empty_not_unavailable(self):
        result, _ = _read()
        assert result["status"] == "empty"
        assert result["items"] == [] and result["total"] == 0

    def test_unknown_total_stays_null(self):
        lister = _lister({"work": ([_item("w1", "work")], None), "queue": ([], 0)})
        result, _ = _read(list_role=lister)
        assert result["status"] == "ok" and result["total"] is None

    def test_read_failure_is_unavailable_and_names_the_endpoint(self):
        result, _ = _read(list_role=_lister(error=ot.McpReadError("initialize timed out")))

        assert result["status"] == "unavailable"
        assert MCP_URL in result["reason"] and "initialize timed out" in result["reason"]
        assert result["items"] == [] and result["total"] is None

    def test_owner_change_during_the_read_discards_the_items(self):
        lister = _lister({"work": ([_item("w1", "work")], 1)})
        result, _ = _read(check_owner=_owner_sequence(OK, WRONG), list_role=lister)

        assert lister.calls == ["work", "queue"]
        assert result["status"] == "wrong_project"
        assert result["items"] == [] and result["total"] is None
        assert "changed" in result["reason"]

    def test_owner_lost_during_the_read_discards_the_items(self):
        lister = _lister({"work": ([_item("w1", "work")], 1)})
        result, _ = _read(check_owner=_owner_sequence(OK, UNKNOWN), list_role=lister)

        assert result["status"] == "unavailable"
        assert result["items"] == []

    def test_owner_recreated_during_the_read_discards_the_items(self):
        """A -> B -> A: both proofs say OK, but the container that answered may not be the first one."""
        lister = _lister({"work": ([_item("w1", "work")], 1)})
        result, _ = _read(check_owner=_owner_sequence(OK, OK_RECREATED), list_role=lister)

        assert lister.calls == ["work", "queue"]
        assert result["status"] == "unavailable"
        assert result["items"] == [] and result["total"] is None
        assert "replaced during the read" in result["reason"]
        assert result["project"]["verdict"] == "OK"

    def test_same_container_before_and_after_is_served(self):
        lister = _lister({"work": ([_item("w1", "work")], 1)})
        result, _ = _read(check_owner=_owner_sequence(OK, OK), list_role=lister)
        assert result["status"] == "ok" and [item["id"] for item in result["items"]] == ["w1"]

    def test_ok_without_a_container_id_is_never_read(self):
        result, used = _read(check_owner=_owner_sequence(OK_NO_ID))
        assert result["status"] == "unavailable"
        assert used["list_role"].calls == []

    def test_container_ids_never_leave_the_reader(self):
        for sequence in ((OK,), (OK, OK_RECREATED), (WRONG,)):
            result, _ = _read(check_owner=_owner_sequence(*sequence))
            assert "c-alpha" not in json.dumps(result)

    def test_docker_stderr_never_reaches_the_response(self):
        stderr = "Cannot connect to the Docker daemon at unix:///synthetic/home/.docker/run/docker.sock."
        inspect = _inspect(available=False, error=stderr)
        result, _ = _read(check_owner=lambda expected: ot.check_port_owner(expected, inspect=inspect))

        assert result["status"] == "unavailable"
        assert result["reason"] == "port 7890 owner could not be proven (UNKNOWN): docker ps unavailable: docker is not reachable"
        assert "/synthetic" not in json.dumps(result) and "docker.sock" not in json.dumps(result)

    def test_read_error_detail_never_reaches_the_response(self):
        error = ot.McpReadError("orchestrator tool reported an error", detail="failed at /synthetic/home/data.db")
        result, _ = _read(list_role=_lister(error=error))

        assert result["reason"] == f"{MCP_URL} read failed: orchestrator tool reported an error"
        assert "/synthetic" not in json.dumps(result)

    def test_no_host_paths_leave_the_reader(self):
        for check in (OK, WRONG, UNKNOWN):
            result, _ = _read(check_owner=_owner_sequence(check))
            assert "/synthetic" not in json.dumps(result)


# --- the MCP client ------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def text(self):
        return self._body


def _fake_session(responses, log):
    class FakeSession:
        def __init__(self, **kwargs):
            log.append(("session", kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        def post(self, url, *, json, headers):  # noqa: A002 - mirrors aiohttp's keyword
            log.append(("post", url, json, dict(headers)))
            return responses.pop(0)

    return FakeSession


class TestMcpClient:
    def test_handshake_then_one_read_only_tool_call(self):
        log = []
        responses = [
            _FakeResponse(200, json.dumps({"result": {"serverInfo": {"name": "synthetic"}}}), {"Mcp-Session-Id": "s-1"}),
            _FakeResponse(202, ""),
            _FakeResponse(200, json.dumps(_rpc(_wrapper(QUEUE_ITEM, total=4)))),
        ]

        items, total = asyncio.run(ot.list_role_items("queue", session_factory=_fake_session(responses, log)))

        posts = [entry for entry in log if entry[0] == "post"]
        assert [post[2]["method"] for post in posts] == ["initialize", "notifications/initialized", "tools/call"]
        assert all(post[1] == MCP_URL for post in posts)
        assert "Mcp-Session-Id" not in posts[0][3]
        assert posts[1][3]["Mcp-Session-Id"] == "s-1" and posts[2][3]["Mcp-Session-Id"] == "s-1"
        assert posts[2][2]["params"] == {
            "name": "query_items",
            "arguments": {"operation": "search", "role": "queue", "limit": 20},
        }
        assert total == 4 and items[0]["id"] == "22222222-bbbb"

    def test_sse_framed_reply_is_read(self):
        framed = "event: message\ndata: " + json.dumps(_rpc(_wrapper(WORK_ITEM))) + "\n\n"
        responses = [_FakeResponse(200, "{}"), _FakeResponse(202, ""), _FakeResponse(200, framed)]

        items, _ = asyncio.run(ot.list_role_items("work", session_factory=_fake_session(responses, [])))
        assert items[0]["title"] == "Wire the queue"

    @pytest.mark.parametrize("failing_call, expected", [(0, "initialize returned HTTP 503"), (2, "tools/call returned HTTP 503")])
    def test_http_errors_name_the_step(self, failing_call, expected):
        responses = [_FakeResponse(200, "{}"), _FakeResponse(202, ""), _FakeResponse(200, "{}")]
        responses[failing_call] = _FakeResponse(503, "nope")

        with pytest.raises(ot.McpReadError, match=expected):
            asyncio.run(ot.list_role_items("queue", session_factory=_fake_session(responses, [])))

    def test_unparseable_reply_is_a_read_error(self):
        responses = [_FakeResponse(200, "{}"), _FakeResponse(202, ""), _FakeResponse(200, "<html>")]
        with pytest.raises(ot.McpReadError):
            asyncio.run(ot.list_role_items("queue", session_factory=_fake_session(responses, [])))

    def test_transport_failure_is_a_read_error(self):
        class Exploding:
            def __init__(self, **_kwargs):
                pass

            async def __aenter__(self):
                raise OSError("connection refused")

            async def __aexit__(self, exc_type, exc, tb):
                return None

        with pytest.raises(ot.McpReadError) as failure:
            asyncio.run(ot.list_role_items("queue", session_factory=Exploding))
        assert str(failure.value) == "connection failed (OSError)"
        assert failure.value.detail == "connection refused"

    def test_timeout_is_a_read_error(self):
        class Slow:
            def __init__(self, **_kwargs):
                pass

            async def __aenter__(self):
                raise asyncio.TimeoutError()

            async def __aexit__(self, exc_type, exc, tb):
                return None

        with pytest.raises(ot.McpReadError, match="timed out"):
            asyncio.run(ot.list_role_items("queue", session_factory=Slow))

    def test_only_listed_roles_can_be_read(self):
        with pytest.raises(ValueError):
            asyncio.run(ot.list_role_items("terminal", session_factory=_fake_session([], [])))

    def test_the_module_names_no_write_tool(self):
        source = open(ot.__file__, encoding="utf-8").read()
        for write_tool in ("advance_item", "manage_items", "manage_notes", "manage_dependencies",
                           "claim_item", "complete_tree", "create_work_tree"):
            assert write_tool not in source


# --- the route -----------------------------------------------------------------------------


def test_api_tasks_route_returns_the_reader_payload(monkeypatch):
    import backend

    seen = {}

    async def fake_read(checkout):
        seen["checkout"] = checkout
        return {"status": "wrong_project", "items": []}

    monkeypatch.setattr(backend, "read_task_queue", fake_read)

    payload = asyncio.run(backend.get_tasks(api_key=None))

    assert payload == {"status": "wrong_project", "items": []}
    assert seen["checkout"] == backend.REPO_ROOT


def test_api_tasks_is_listed_on_the_root_endpoint():
    import backend

    assert "/api/tasks" in asyncio.run(backend.root())["endpoints"]
