"""Tests for the cockpit's Start / Finish write path to the Task Orchestrator.

Every test uses fakes; nothing here talks to port 7890. The orchestrator shapes come from its
source at tag v3.8.0 (the deployed jar reports 3.8.0, and the live tools/list description of
``advance_item`` captured on 2026-11-16 equals the description in that source):

- ``advance_item`` returns ``structuredContent = {results: [...], summary, allUnblockedItems}``.
  An applied result carries ``previousRole``, ``newRole``, ``applied: true`` and
  ``expectedNotes``; a refused one carries ``applied: false``, ``error`` and, for a gate refusal,
  ``missingNotes: [{key, description, guidance?}]``.
- ``query_items`` ``get`` returns the full item, including ``id`` and ``role``.
- A validation or internal error is ``isError: true`` with text that can include the session id.
"""
import asyncio
import json
import uuid

import pytest

import orchestrator_tasks as ot
import orchestrator_transitions as tr

EXPECTED = ot.ExpectedProject(project_id="alpha", project_root="/synthetic/alpha")
OK = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha", container_id="c-alpha-1")
OK_RECREATED = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha", container_id="c-alpha-2")
OK_NO_ID = ot.OwnerCheck(verdict="OK", project_id="alpha", name="alpha", detail="to-alpha")
WRONG = ot.OwnerCheck(verdict="WRONG_PROJECT", project_id="beta", name="beta", detail="to-beta")
UNKNOWN = ot.OwnerCheck(verdict="UNKNOWN", project_id=None, name=None, detail="docker ps timed out")

ITEM = "3f2a9c4e-1b7d-4e8a-9c21-5d6f7a8b9c0d"
REQUEST = "0b9f6c1e-7a2d-4c3b-8e5f-112233445566"
KEY = "synthetic-dashboard-key"

CONTRACT_KEYS = {
    "source", "endpoint", "status", "reason", "item_id", "trigger", "request_id", "actor",
    "previous_role", "new_role", "missing_notes", "project",
}


# --- fakes -------------------------------------------------------------------------------


def _owner_sequence(*checks):
    remaining = list(checks)
    seen = []

    def check_owner(expected):
        seen.append(expected)
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    check_owner.seen = seen
    return check_owner


def _role_reader(role="queue", error=None):
    calls = []

    async def get_role(item_id):
        calls.append(item_id)
        if error:
            raise error
        return role

    get_role.calls = calls
    return get_role


def _advancer(payload=None, error=None):
    calls = []

    async def advance(item_id, trigger, request_id):
        calls.append((item_id, trigger, request_id))
        if error:
            raise error
        return payload

    advance.calls = calls
    return advance


def _applied(previous="queue", new="work", trigger="start", item_id=ITEM):
    return {
        "results": [
            {
                "itemId": item_id,
                "previousRole": previous,
                "newRole": new,
                "trigger": trigger,
                "applied": True,
                "actor": {"id": "operator:cockpit", "kind": "user"},
                "verification": {"status": "unverified", "verifier": "noop"},
                "cascadeEvents": [],
                "unblockedItems": [],
                "expectedNotes": [],
            }
        ],
        "summary": {"total": 1, "succeeded": 1, "failed": 0},
        "allUnblockedItems": [],
    }


def _refused(error, missing=None, item_id=ITEM, trigger="complete"):
    result = {"itemId": item_id, "trigger": trigger, "applied": False, "error": error}
    if missing is not None:
        result["missingNotes"] = missing
    return {"results": [result], "summary": {"total": 1, "succeeded": 0, "failed": 1}, "allUnblockedItems": []}


def _run(trigger="start", item_id=ITEM, request_id=REQUEST, **overrides):
    kwargs = {
        "resolve_expected": lambda _checkout: EXPECTED,
        "check_owner": _owner_sequence(OK),
        "get_role": _role_reader("queue" if trigger == "start" else "work"),
        "advance": _advancer(_applied() if trigger == "start" else _applied("work", "terminal", "complete")),
    }
    kwargs.update(overrides)
    result = asyncio.run(tr.transition_item("/synthetic/alpha", item_id, trigger, request_id, **kwargs))
    return result, kwargs


# --- the allow-list ----------------------------------------------------------------------


class TestAllowList:
    def test_only_start_and_finish_are_exposed(self):
        assert tr.ALLOWED_TRIGGERS == {"start": "queue", "complete": "work"}
        assert tr.WRITE_TOOL == "advance_item"

    @pytest.mark.parametrize("trigger", ["cancel", "block", "hold", "resume", "reopen", "skip", "START", ""])
    def test_any_other_trigger_is_refused_before_any_check(self, trigger):
        result, kwargs = _run(trigger=trigger)
        assert result["status"] == "refused"
        assert "start" in result["reason"] and "complete" in result["reason"]
        assert kwargs["check_owner"].seen == []
        assert kwargs["get_role"].calls == [] and kwargs["advance"].calls == []

    def test_the_sender_refuses_a_trigger_outside_the_allow_list(self):
        with pytest.raises(ValueError):
            asyncio.run(tr.send_transition(ITEM, "cancel", REQUEST, session_factory=_fake_session([], [])))

    def test_the_sender_refuses_any_tool_but_the_two_it_names(self):
        with pytest.raises(ValueError):
            asyncio.run(tr._call_tool("manage_items", {}, session_factory=_fake_session([], [])))

    def test_the_read_module_still_names_no_write_tool(self):
        source = open(ot.__file__, encoding="utf-8").read()
        assert "advance_item" not in source


# --- input validation ---------------------------------------------------------------------


class TestInput:
    @pytest.mark.parametrize("item_id", ["3f2a", "3f2a9c4e", "not-a-uuid", "", ITEM.upper(), ITEM + "0", "{" + ITEM + "}"])
    def test_item_id_must_be_a_full_lowercase_uuid(self, item_id):
        result, kwargs = _run(item_id=item_id)
        assert result["status"] == "refused"
        assert "item id" in result["reason"]
        assert kwargs["check_owner"].seen == [] and kwargs["advance"].calls == []

    @pytest.mark.parametrize("request_id", ["", "1", "click-1", None])
    def test_request_id_must_be_a_uuid(self, request_id):
        result, kwargs = _run(request_id=request_id)
        assert result["status"] == "refused"
        assert "request_id" in result["reason"]
        assert kwargs["advance"].calls == []


# --- ownership ----------------------------------------------------------------------------


class TestOwnership:
    def test_no_provable_identity_refuses_without_reading(self):
        result, kwargs = _run(resolve_expected=lambda _c: None)
        assert result["status"] == "unavailable"
        assert kwargs["get_role"].calls == [] and kwargs["advance"].calls == []

    def test_wrong_project_refuses_without_reading(self):
        result, kwargs = _run(check_owner=_owner_sequence(WRONG))
        assert result["status"] == "wrong_project"
        assert "beta" in result["reason"] and "nothing was written" in result["reason"]
        assert kwargs["get_role"].calls == [] and kwargs["advance"].calls == []

    def test_unknown_owner_refuses_without_reading(self):
        result, kwargs = _run(check_owner=_owner_sequence(UNKNOWN))
        assert result["status"] == "unavailable"
        assert kwargs["get_role"].calls == [] and kwargs["advance"].calls == []

    def test_owner_without_container_id_refuses(self):
        result, kwargs = _run(check_owner=_owner_sequence(OK_NO_ID))
        assert result["status"] == "unavailable"
        assert kwargs["advance"].calls == []

    def test_owner_is_rechecked_after_the_role_read_and_before_the_write(self):
        result, kwargs = _run(check_owner=_owner_sequence(OK, WRONG))
        assert result["status"] == "wrong_project"
        assert kwargs["get_role"].calls == [ITEM]
        assert kwargs["advance"].calls == []
        assert len(kwargs["check_owner"].seen) == 2

    def test_a_replaced_container_between_read_and_write_refuses(self):
        result, kwargs = _run(check_owner=_owner_sequence(OK, OK_RECREATED))
        assert result["status"] == "unavailable"
        assert "replaced" in result["reason"] and "nothing was written" in result["reason"]
        assert kwargs["advance"].calls == []

    def test_container_id_never_reaches_the_response(self):
        result, _ = _run()
        assert "c-alpha-1" not in json.dumps(result)


# --- the role precondition ----------------------------------------------------------------


class TestRolePrecondition:
    @pytest.mark.parametrize("role", ["work", "review", "blocked", "terminal"])
    def test_start_only_from_queue(self, role):
        result, kwargs = _run(get_role=_role_reader(role))
        assert result["status"] == "refused"
        assert result["previous_role"] == role
        assert "queue" in result["reason"]
        assert kwargs["advance"].calls == []

    @pytest.mark.parametrize("role", ["queue", "review", "blocked", "terminal"])
    def test_finish_only_from_work(self, role):
        result, kwargs = _run(trigger="complete", get_role=_role_reader(role))
        assert result["status"] == "refused"
        assert "work" in result["reason"]
        assert kwargs["advance"].calls == []

    def test_role_read_failure_writes_nothing(self):
        result, kwargs = _run(get_role=_role_reader(error=ot.McpReadError("timed out after 5 s")))
        assert result["status"] == "unavailable"
        assert "nothing was written" in result["reason"]
        assert kwargs["advance"].calls == []


# --- the write and its result -------------------------------------------------------------


class TestWrite:
    def test_start_from_queue_applies(self):
        result, kwargs = _run()
        assert set(result) == CONTRACT_KEYS
        assert result["status"] == "applied"
        assert result["previous_role"] == "queue" and result["new_role"] == "work"
        assert result["reason"] is None
        assert result["missing_notes"] is None
        assert kwargs["advance"].calls == [(ITEM, "start", REQUEST)]

    def test_actor_is_named_and_marked_unverified(self):
        result, _ = _run()
        assert result["actor"]["id"] == "operator:cockpit"
        assert result["actor"]["kind"] == "user"
        assert "unverified" in result["actor"]["verification"]

    def test_finish_from_work_applies(self):
        result, kwargs = _run(trigger="complete")
        assert result["status"] == "applied"
        assert result["new_role"] == "terminal"
        assert kwargs["advance"].calls == [(ITEM, "complete", REQUEST)]

    def test_an_unexpected_move_is_reported_not_hidden(self):
        # Another writer started the item between the role read and the write.
        result, _ = _run(advance=_advancer(_applied("work", "review")))
        assert result["status"] == "applied"
        assert result["previous_role"] == "work" and result["new_role"] == "review"
        assert "not queue to work" in result["reason"]

    def test_gate_refusal_returns_the_missing_notes(self):
        payload = _refused(
            "Gate check failed: required notes not filled: proof-bundle",
            missing=[{"key": "proof-bundle", "description": "AGENTS.md section 9 proof", "guidance": "fill it"}],
        )
        result, _ = _run(trigger="complete", advance=_advancer(payload))
        assert result["status"] == "refused"
        assert result["reason"].startswith("orchestrator refused: Gate check failed")
        assert result["missing_notes"] == [{"key": "proof-bundle", "description": "AGENTS.md section 9 proof"}]
        assert result["previous_role"] == "work" and result["new_role"] is None

    def test_refusal_without_notes_has_unknown_missing_notes(self):
        result, _ = _run(advance=_advancer(_refused("not the claim holder", trigger="start")))
        assert result["status"] == "refused"
        assert result["missing_notes"] is None

    def test_expected_notes_are_a_fallback_for_missing_notes(self):
        payload = _refused("Gate check failed")
        payload["results"][0]["expectedNotes"] = [
            {"key": "a", "required": True, "exists": False, "description": "needed"},
            {"key": "b", "required": True, "exists": True, "description": "done"},
            {"key": "c", "required": False, "exists": False, "description": "optional"},
        ]
        result, _ = _run(trigger="complete", advance=_advancer(payload))
        assert result["missing_notes"] == [{"key": "a", "description": "needed"}]

    def test_long_or_multiline_refusal_text_is_bounded(self):
        result, _ = _run(advance=_advancer(_refused("line1\nline2\t" + "x" * 2000, trigger="start")))
        assert "\n" not in result["reason"] and "\t" not in result["reason"]
        assert len(result["reason"]) <= len("orchestrator refused: ") + tr.REASON_MAX

    @pytest.mark.parametrize(
        "payload",
        [
            None,
            {},
            {"results": []},
            {"results": "no"},
            {"results": [_applied()["results"][0], _applied()["results"][0]]},
            _applied(item_id="99999999-1b7d-4e8a-9c21-5d6f7a8b9c0d"),
            {"results": [{"itemId": ITEM, "applied": "yes"}]},
            {"results": [{"itemId": ITEM, "applied": True, "previousRole": "queue"}]},
            {"results": [{"itemId": ITEM, "applied": True, "previousRole": "queue", "newRole": "elsewhere"}]},
        ],
    )
    def test_an_unreadable_reply_means_the_outcome_is_unknown(self, payload):
        result, _ = _run(advance=_advancer(payload))
        assert result["status"] == "unavailable"
        assert "outcome is unknown" in result["reason"]

    def test_a_failure_after_sending_means_the_outcome_is_unknown(self):
        error = tr.TransitionOutcomeUnknown("timed out after 5 s")
        result, _ = _run(advance=_advancer(error=error))
        assert result["status"] == "unavailable"
        assert "outcome is unknown" in result["reason"]

    def test_a_failure_before_sending_writes_nothing(self):
        result, _ = _run(advance=_advancer(error=ot.McpReadError("initialize returned HTTP 500")))
        assert result["status"] == "unavailable"
        assert "nothing was written" in result["reason"]

    def test_writes_never_overlap(self):
        """Read role, re-check owner and write run under one lock, so two clicks cannot both see queue."""
        state = {"role": "queue", "active": 0, "max_active": 0}

        async def get_role(_item_id):
            state["active"] += 1
            state["max_active"] = max(state["max_active"], state["active"])
            await asyncio.sleep(0)
            return state["role"]

        async def advance(item_id, trigger, request_id):
            await asyncio.sleep(0)
            state["role"] = "work"
            state["active"] -= 1
            return _applied()

        async def both():
            kwargs = {
                "resolve_expected": lambda _c: EXPECTED,
                "check_owner": _owner_sequence(OK),
                "get_role": get_role,
                "advance": advance,
            }
            return await asyncio.gather(
                tr.transition_item("/x", ITEM, "start", REQUEST, **kwargs),
                tr.transition_item("/x", ITEM, "start", str(uuid.uuid4()), **kwargs),
            )

        first, second = asyncio.run(both())
        assert state["max_active"] == 1
        assert sorted([first["status"], second["status"]]) == ["applied", "refused"]


# --- the MCP client -----------------------------------------------------------------------


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
            response = responses.pop(0)
            if isinstance(response, BaseException):
                raise response
            return response

    return FakeSession


def _handshake():
    return [
        _FakeResponse(200, json.dumps({"result": {"serverInfo": {"name": "synthetic"}}}), {"Mcp-Session-Id": "s-1"}),
        _FakeResponse(202, ""),
    ]


def _tool_reply(structured, is_error=False, text="ok"):
    result = {"content": [{"type": "text", "text": text}], "isError": is_error}
    if structured is not None:
        result["structuredContent"] = structured
    return _FakeResponse(200, json.dumps({"jsonrpc": "2.0", "id": 2, "result": result}))


class TestMcpClient:
    def test_send_transition_builds_one_allow_listed_call_with_the_actor(self):
        log = []
        responses = _handshake() + [_tool_reply(_applied())]
        payload = asyncio.run(tr.send_transition(ITEM, "start", REQUEST, session_factory=_fake_session(responses, log)))

        posts = [entry for entry in log if entry[0] == "post"]
        assert [p[2]["method"] for p in posts] == ["initialize", "notifications/initialized", "tools/call"]
        assert all(p[1] == ot.MCP_URL for p in posts)
        assert posts[2][2]["params"] == {
            "name": "advance_item",
            "arguments": {
                "transitions": [{"itemId": ITEM, "trigger": "start", "actor": {"id": "operator:cockpit", "kind": "user"}}],
                "requestId": REQUEST,
            },
        }
        assert posts[2][3]["Mcp-Session-Id"] == "s-1"
        assert payload["results"][0]["applied"] is True

    def test_read_item_role_uses_get_and_checks_the_id(self):
        log = []
        responses = _handshake() + [_tool_reply({"id": ITEM, "title": "T", "role": "queue"})]
        role = asyncio.run(tr.read_item_role(ITEM, session_factory=_fake_session(responses, log)))
        assert role == "queue"
        call = [entry for entry in log if entry[0] == "post"][2][2]
        assert call["params"] == {"name": "query_items", "arguments": {"operation": "get", "itemId": ITEM}}

    @pytest.mark.parametrize(
        "structured",
        [
            {"id": "99999999-1b7d-4e8a-9c21-5d6f7a8b9c0d", "role": "queue"},
            {"id": ITEM},
            {"id": ITEM, "role": "somewhere"},
            {"id": ITEM, "role": 3},
        ],
    )
    def test_read_item_role_rejects_another_item_or_an_unknown_role(self, structured):
        responses = _handshake() + [_tool_reply(structured)]
        with pytest.raises(ot.McpReadError):
            asyncio.run(tr.read_item_role(ITEM, session_factory=_fake_session(responses, [])))

    def test_tool_error_text_is_not_forwarded(self):
        responses = _handshake() + [_tool_reply(None, is_error=True, text="Internal error (session s-secret): boom")]
        with pytest.raises(ot.McpReadError) as caught:
            asyncio.run(tr.read_item_role(ITEM, session_factory=_fake_session(responses, [])))
        assert "s-secret" not in str(caught.value)

    def test_failure_before_the_write_call_is_not_outcome_unknown(self):
        responses = [_FakeResponse(500, "")]
        with pytest.raises(ot.McpReadError) as caught:
            asyncio.run(tr.send_transition(ITEM, "start", REQUEST, session_factory=_fake_session(responses, [])))
        assert not isinstance(caught.value, tr.TransitionOutcomeUnknown)

    @pytest.mark.parametrize(
        "last",
        [
            asyncio.TimeoutError(),
            ConnectionResetError("peer reset"),
            _FakeResponse(502, ""),
            _FakeResponse(200, "not json"),
        ],
    )
    def test_failure_at_or_after_the_write_call_is_outcome_unknown(self, last):
        responses = _handshake() + [last]
        with pytest.raises(tr.TransitionOutcomeUnknown):
            asyncio.run(tr.send_transition(ITEM, "start", REQUEST, session_factory=_fake_session(responses, [])))

    def test_tool_error_on_the_write_call_is_outcome_unknown(self):
        responses = _handshake() + [_tool_reply(None, is_error=True, text="Internal error in 'advance_item'")]
        with pytest.raises(tr.TransitionOutcomeUnknown) as caught:
            asyncio.run(tr.send_transition(ITEM, "start", REQUEST, session_factory=_fake_session(responses, [])))
        assert "Internal error" not in str(caught.value)


# --- the request handler: auth and body ---------------------------------------------------


def _handle(body, *, api_key=KEY, configured=KEY, item_id=ITEM, transition=None):
    calls = []

    async def fake_transition(checkout, item_id, trigger, request_id):
        calls.append((checkout, item_id, trigger, request_id))
        return tr.build_response("applied", item_id=item_id, trigger=trigger, request_id=request_id,
                                 previous_role="queue", new_role="work")

    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    status, payload = asyncio.run(
        tr.handle_transition_request(
            item_id=item_id,
            api_key=api_key,
            configured_key=configured,
            body=raw,
            checkout="/synthetic/alpha",
            transition=transition or fake_transition,
        )
    )
    return status, payload, calls


class TestHandler:
    def test_writes_are_refused_when_no_key_is_configured(self):
        status, payload, calls = _handle({"trigger": "start", "request_id": REQUEST}, configured=None)
        assert status == 403
        assert set(payload) == CONTRACT_KEYS
        assert payload["status"] == "refused" and "DASHBOARD_API_KEY" in payload["reason"]
        assert calls == []

    @pytest.mark.parametrize("api_key", [None, "", "wrong", KEY + "x"])
    def test_a_missing_or_wrong_key_is_refused(self, api_key):
        status, payload, calls = _handle({"trigger": "start", "request_id": REQUEST}, api_key=api_key)
        assert status == 401
        assert set(payload) == CONTRACT_KEYS
        assert payload["status"] == "refused" and "X-API-Key" in payload["reason"]
        assert calls == []

    @pytest.mark.parametrize(
        "body",
        [b"", b"not json", b"[]", {"trigger": "start"}, {"request_id": REQUEST}, {"trigger": 1, "request_id": REQUEST},
         {"trigger": "start", "request_id": 7}],
    )
    def test_a_malformed_body_is_refused_in_the_contract_shape(self, body):
        status, payload, calls = _handle(body)
        assert status == 400
        assert set(payload) == CONTRACT_KEYS
        assert payload["status"] == "refused"
        assert calls == []

    def test_a_good_request_reaches_the_transition(self):
        status, payload, calls = _handle({"trigger": "start", "request_id": REQUEST})
        assert status == 200 and payload["status"] == "applied"
        assert calls == [("/synthetic/alpha", ITEM, "start", REQUEST)]

    @pytest.mark.parametrize(
        "outcome,code",
        [("applied", 200), ("refused", 409), ("wrong_project", 409), ("unavailable", 503)],
    )
    def test_http_status_follows_the_outcome(self, outcome, code):
        async def transition(checkout, item_id, trigger, request_id):
            return tr.build_response(outcome, item_id=item_id, trigger=trigger, request_id=request_id, reason="r")

        status, payload, _ = _handle({"trigger": "start", "request_id": REQUEST}, transition=transition)
        assert status == code and payload["status"] == outcome

    def test_an_unexpected_exception_becomes_a_contract_body(self):
        async def transition(checkout, item_id, trigger, request_id):
            raise RuntimeError("secret detail /Users/someone")

        status, payload, _ = _handle({"trigger": "start", "request_id": REQUEST}, transition=transition)
        assert status == 500
        assert set(payload) == CONTRACT_KEYS
        assert payload["status"] == "unavailable"
        assert "outcome is unknown" in payload["reason"]
        assert "secret" not in json.dumps(payload)


# --- the route ----------------------------------------------------------------------------


def test_transition_route_is_wired_and_never_a_bare_500(monkeypatch):
    import backend
    from fastapi.testclient import TestClient

    async def explode(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(backend, "handle_transition_request", explode)
    client = TestClient(backend.app)  # no context manager: the lifespan (Redis) does not run
    response = client.post(f"/api/tasks/{ITEM}/transition", json={"trigger": "start", "request_id": REQUEST},
                           headers={"X-API-Key": KEY})
    assert response.status_code == 500
    body = response.json()
    assert set(body) == CONTRACT_KEYS and body["status"] == "unavailable"


def test_transition_route_passes_key_body_and_checkout(monkeypatch):
    import backend
    from fastapi.testclient import TestClient

    seen = {}

    async def fake(**kwargs):
        seen.update(kwargs)
        return 409, tr.build_response("refused", item_id=kwargs["item_id"], reason="r")

    monkeypatch.setattr(backend, "handle_transition_request", fake)
    monkeypatch.setattr(backend, "API_KEY", KEY)
    response = TestClient(backend.app).post(
        f"/api/tasks/{ITEM}/transition", content=b'{"trigger": "start"}', headers={"X-API-Key": "given"}
    )
    assert response.status_code == 409 and response.json()["status"] == "refused"
    assert seen["item_id"] == ITEM and seen["api_key"] == "given" and seen["configured_key"] == KEY
    assert seen["body"] == b'{"trigger": "start"}' and seen["checkout"] == backend.REPO_ROOT


def test_read_routes_keep_their_open_key_behaviour(monkeypatch):
    import backend

    monkeypatch.setattr(backend, "API_KEY", None)
    assert asyncio.run(backend.verify_api_key(api_key=None)) is None


def test_transition_route_is_listed_on_the_root_endpoint():
    import backend

    assert "/api/tasks/{item_id}/transition" in asyncio.run(backend.root())["endpoints"]
