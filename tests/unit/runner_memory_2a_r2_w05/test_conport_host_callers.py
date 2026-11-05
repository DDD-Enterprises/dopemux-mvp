"""Host-side ConPort REST writers: tools/conport_client, instance_state,
profile_analytics, decisions_commands, adhd/rte_adapter (all internal:cli,
except rte_adapter which is internal:adhd)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest
from click.testing import CliRunner

from dopemux import profile_analytics
from dopemux.adhd import rte_adapter
from dopemux.commands import decisions_commands
from dopemux.instance_state import InstanceState, InstanceStateManager
from dopemux.tools.conport_client import ConPortClient

from .conftest import FAKE_TOKEN, assert_no_secret

NO_TOKEN = ["token_missing", "token_keychain_down", "no_auth_package"]


# --------------------------------------------------------------------------
# src/dopemux/tools/conport_client.py  (internal:cli)
# --------------------------------------------------------------------------


async def _tools_client_writes(client: ConPortClient):
    context = {"focus": "x"}
    await client.update_active_context("ws-bound", context)
    await client.log_decision("ws-bound", "sum", "why", ["alt"])
    await client.log_progress("ws-bound", "IN_PROGRESS", "doing", 10)
    return context


async def test_should_send_cli_token_and_ids_on_every_tools_client_write(
    fake_server, token_ok, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")
    client = ConPortClient(base_url=fake_server.url)
    try:
        context = await _tools_client_writes(client)
    finally:
        await client.close()

    ctx, dec, prog = fake_server.requests
    assert [r.path for r in (ctx, dec, prog)] == [
        "/api/context/ws-bound",
        "/api/decisions",
        "/api/progress",
    ]
    for seen in (ctx, dec, prog):
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
        assert seen.headers["content-type"] == "application/json"
        assert seen.body["instance_id"] == "inst-a"
    assert dec.body["workspace_id"] == prog.body["workspace_id"] == "ws-bound"
    assert ctx.body["focus"] == "x"
    assert context == {"focus": "x"}, "the caller's dict must not be mutated"
    assert set(token_ok) == {"internal:cli"}


async def test_should_prefer_explicit_instance_id_on_tools_client(fake_server, token_ok, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "from-env")
    client = ConPortClient(base_url=fake_server.url, instance_id="from-ctor")
    try:
        await client.log_progress("ws-bound", "IN_PROGRESS", "doing", 0)
    finally:
        await client.close()

    assert fake_server.requests[0].body["instance_id"] == "from-ctor"


async def test_should_not_invent_an_instance_id_on_tools_client(fake_server, token_ok):
    client = ConPortClient(base_url=fake_server.url)
    try:
        await client.log_progress("ws-bound", "IN_PROGRESS", "doing", 0)
        await client.log_decision("ws-bound", "s", "r")
    finally:
        await client.close()

    assert all("instance_id" not in r.body for r in fake_server.requests)


async def test_should_not_fetch_a_token_for_tools_client_reads(fake_server, token_ok):
    client = ConPortClient(base_url=fake_server.url)
    try:
        await client.get_active_context("ws-bound")
        await client.get_decisions("ws-bound")
        await client.get_progress()
    finally:
        await client.close()

    assert all(r.authorization is None for r in fake_server.requests)
    assert token_ok == []


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_tools_client_has_no_token(
    fake_server, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)
    client = ConPortClient(base_url=fake_server.url)
    try:
        with caplog.at_level(logging.DEBUG):
            await _tools_client_writes(client)
    finally:
        await client.close()

    assert len(fake_server.requests) == 3
    assert all(r.authorization is None for r in fake_server.requests)
    assert_no_secret(caplog, capsys)


async def test_should_log_only_the_principal_name_when_tools_client_token_missing(
    fake_server, token_missing, caplog
):
    client = ConPortClient(base_url=fake_server.url)
    try:
        with caplog.at_level(logging.DEBUG):
            await client.log_progress("ws-bound", "IN_PROGRESS", "doing", 0)
    finally:
        await client.close()

    assert "internal:cli" in caplog.text


# --------------------------------------------------------------------------
# src/dopemux/instance_state.py  (internal:cli; custom_data has no instance_id)
# --------------------------------------------------------------------------


def _state() -> InstanceState:
    now = datetime.now(timezone.utc)
    return InstanceState(
        instance_id="inst-a",
        port_base=3000,
        worktree_path="/tmp/wt",
        git_branch="main",
        created_at=now,
        last_active=now,
        status="active",
    )


async def test_should_send_cli_token_on_instance_state_save_and_cleanup(
    fake_server, real_instance_state_save, token_ok
):
    async with InstanceStateManager("ws-bound", fake_server.port) as manager:
        assert await manager.save_instance_state(_state()) is True
        assert await manager.cleanup_instance_state("inst-a") is True

    save, cleanup = fake_server.requests
    assert (save.method, save.path) == ("POST", "/api/custom_data")
    assert save.body["workspace_id"] == "ws-bound"
    assert "instance_id" not in save.body
    assert (cleanup.method, cleanup.path) == ("DELETE", "/api/custom_data")
    assert cleanup.query["workspace_id"] == ["ws-bound"]
    for seen in (save, cleanup):
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
    assert set(token_ok) == {"internal:cli"}


async def test_should_not_fetch_a_token_for_instance_state_reads(fake_server, token_ok):
    async with InstanceStateManager("ws-bound", fake_server.port) as manager:
        await manager.load_instance_state("inst-a")
        await manager.list_all_instance_states()

    assert len(fake_server.requests) == 2
    assert all(r.authorization is None for r in fake_server.requests)
    assert token_ok == []


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_save_and_cleanup_without_header_when_instance_state_has_no_token(
    fake_server, real_instance_state_save, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)
    with caplog.at_level(logging.DEBUG):
        async with InstanceStateManager("ws-bound", fake_server.port) as manager:
            assert await manager.save_instance_state(_state()) is True
            assert await manager.cleanup_instance_state("inst-a") is True

    assert len(fake_server.requests) == 2
    assert all(r.authorization is None for r in fake_server.requests)
    assert_no_secret(caplog, capsys)


# --------------------------------------------------------------------------
# src/dopemux/profile_analytics.py  (internal:cli; custom_data)
# --------------------------------------------------------------------------


async def test_should_send_cli_token_on_profile_analytics_writes(fake_server, token_ok):
    analytics = profile_analytics.ProfileAnalytics("ws-bound", fake_server.port)

    assert await analytics.log_switch("coding", "manual") is True
    assert (
        await analytics.archive_optimization_suggestions(
            [{"title": "t"}], analytics._empty_stats()
        )
        is True
    )

    assert len(fake_server.requests) == 2
    for seen in fake_server.requests:
        assert (seen.method, seen.path) == ("POST", "/api/custom_data")
        assert seen.body["workspace_id"] == "ws-bound"
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
    assert set(token_ok) == {"internal:cli"}


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_profile_analytics_has_no_token(
    fake_server, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)
    analytics = profile_analytics.ProfileAnalytics("ws-bound", fake_server.port)

    with caplog.at_level(logging.DEBUG):
        assert await analytics.log_switch("coding", "manual") is True

    assert fake_server.requests[0].authorization is None
    assert_no_secret(caplog, capsys)


# --------------------------------------------------------------------------
# src/dopemux/commands/decisions_commands.py  (internal:cli)
# --------------------------------------------------------------------------


@pytest.fixture
def decisions_env(monkeypatch, fake_server):
    monkeypatch.setenv("CONPORT_URL", fake_server.url)
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "ws-bound")
    monkeypatch.setattr(
        decisions_commands,
        "_get_decisions",
        lambda workspace_id, limit=20: [{"id": "decision-1", "summary": "Original"}],
    )


@pytest.mark.parametrize(
    "args",
    [
        ["review", "decision-1", "--note", "ok"],
        ["update-outcome", "decision-1", "--outcome", "worked"],
    ],
)
def test_should_send_cli_token_and_ids_when_writing_decisions(
    fake_server, decisions_env, token_ok, monkeypatch, args
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")

    result = CliRunner().invoke(decisions_commands.decisions, args)

    assert result.exit_code == 0, result.output
    (seen,) = fake_server.requests
    assert seen.path == "/api/decisions"
    assert seen.authorization == f"Bearer {FAKE_TOKEN}"
    assert seen.body["workspace_id"] == "ws-bound"
    assert seen.body["instance_id"] == "inst-a"
    assert token_ok == ["internal:cli"]
    assert FAKE_TOKEN not in result.output


@pytest.mark.parametrize("fixture", NO_TOKEN)
def test_should_write_decisions_without_header_when_no_token(
    fake_server, decisions_env, request, fixture, caplog
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        result = CliRunner().invoke(
            decisions_commands.decisions, ["review", "decision-1", "--note", "ok"]
        )

    assert result.exit_code == 0, result.output
    assert fake_server.requests[0].authorization is None
    assert FAKE_TOKEN not in caplog.text + result.output


def test_should_keep_the_original_post_call_shape_when_no_token(decisions_env, token_missing, monkeypatch):
    """With no token the call is exactly as before: no `headers` argument at all."""
    recorded = {}

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "logged", "decision": {"id": "d-9"}}

    def strict_post(url, *, json, timeout):  # the pre-W05 call shape
        recorded["json"] = json
        return _Resp()

    monkeypatch.setattr(decisions_commands.requests, "post", strict_post)

    result = CliRunner().invoke(
        decisions_commands.decisions, ["review", "decision-1", "--note", "ok"]
    )

    assert result.exit_code == 0, result.output
    assert recorded["json"]["workspace_id"] == "ws-bound"


# --------------------------------------------------------------------------
# src/dopemux/adhd/rte_adapter.py  (internal:adhd)
# --------------------------------------------------------------------------


@pytest.fixture
def rte(monkeypatch, fake_server, tmp_path):
    monkeypatch.setenv("CONPORT_URL", fake_server.url)
    monkeypatch.setattr(rte_adapter, "try_emit_promotable_capture_event", lambda *a, **k: None)
    monkeypatch.setattr(rte_adapter, "ADHD_AVAILABLE", False)
    root = tmp_path / "myws"
    root.mkdir()
    return rte_adapter.RTEAdapter(workspace_root=root)


async def test_should_send_adhd_token_and_ids_from_rte_adapter(fake_server, rte, token_ok, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")
    decision = {"title": "t", "rationale": "r", "workspace_id": "ws-bound"}

    await rte.write_decision_to_conport(decision)

    (seen,) = fake_server.requests
    assert seen.path == "/api/decisions"
    assert seen.authorization == f"Bearer {FAKE_TOKEN}"
    assert seen.body["workspace_id"] == "ws-bound", "the caller's workspace is never overridden"
    assert seen.body["instance_id"] == "inst-a"
    assert token_ok == ["internal:adhd"]
    assert "instance_id" not in decision, "the caller's dict must not be mutated"


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_rte_adapter_has_no_token(
    fake_server, rte, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        result = await rte.write_decision_to_conport({"title": "t", "rationale": "r"})

    assert result["decision_id"] == "dec-1"
    assert fake_server.requests[0].authorization is None
    assert_no_secret(caplog, capsys)


class _Monitor:
    def get_current_metrics(self):
        return {"state": "medium"}


class _Decomposer:
    def add_task(self, **kwargs):
        return "task-1"

    def get_recommended_task(self, energy_level):
        return {"title": "next"}


@pytest.mark.parametrize(
    "env, expected", [("/abs/ws-bound", "/abs/ws-bound"), (None, "myws")]
)
async def test_should_log_rte_decisions_under_the_servers_bound_workspace(
    fake_server, rte, token_ok, monkeypatch, env, expected
):
    if env:
        monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", env)
    monkeypatch.setattr(rte_adapter, "ADHD_AVAILABLE", True)
    rte.attention_monitor = _Monitor()
    rte.task_decomposer = _Decomposer()
    monkeypatch.setattr(rte, "get_latest_truth", lambda artifact_type="x": {"phases": [1]})

    await rte.process_truth_with_adhd_context()

    assert fake_server.requests[0].body["workspace_id"] == expected
