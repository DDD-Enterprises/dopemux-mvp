"""Service-side ConPort REST writers: services/adhd_engine/conport_client.py
(internal:adhd), services/claude_brain/brain_manager.py (internal:brain) and the
two services/dopecon-bridge files (internal:dopecon).

These run in Linux containers where the macOS keychain does not exist, so each
class below also proves the container case: `get_token` fails, the write is sent
without a header, and nothing else changes.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from .conftest import FAKE_TOKEN, assert_no_secret

REPO = Path(__file__).resolve().parents[3]
SERVICES = REPO / "services"
NO_TOKEN = ["token_missing", "token_keychain_down", "no_auth_package"]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# services/adhd_engine/conport_client.py  (internal:adhd, container)
# --------------------------------------------------------------------------


@pytest.fixture
def adhd_engine_module():
    return _load("w05_adhd_engine_conport_client", SERVICES / "adhd_engine" / "conport_client.py")


@pytest.fixture
def adhd_engine_client(fake_server, adhd_engine_module):
    return adhd_engine_module.ConPortClient(base_url=fake_server.url)


async def _adhd_writes(client):
    await client.update_active_context("ws-x", {"focus": "x"})
    await client.log_decision("ws-x", "sum", "why")
    await client.log_progress("ws-x", "IN_PROGRESS", "doing", 5)
    await client.close()


async def test_should_send_adhd_token_and_ids_from_adhd_engine(
    fake_server, adhd_engine_module, token_ok, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")

    await _adhd_writes(adhd_engine_module.ConPortClient(base_url=fake_server.url))

    ctx, dec, prog = fake_server.requests
    assert [r.path for r in (ctx, dec, prog)] == ["/api/context/ws-x", "/api/decisions", "/api/progress"]
    for seen in (ctx, dec, prog):
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
        assert seen.body["instance_id"] == "inst-a"
    assert dec.body["workspace_id"] == prog.body["workspace_id"] == "ws-x"
    assert set(token_ok) == {"internal:adhd"}


async def test_should_not_fetch_a_token_for_adhd_engine_reads(fake_server, adhd_engine_client, token_ok):
    await adhd_engine_client.get_active_context("ws-x")
    await adhd_engine_client.get_progress()
    await adhd_engine_client.close()

    assert all(r.authorization is None for r in fake_server.requests)
    assert token_ok == []


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_adhd_engine_has_no_token(
    fake_server, adhd_engine_client, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        await _adhd_writes(adhd_engine_client)

    assert len(fake_server.requests) == 3
    assert all(r.authorization is None for r in fake_server.requests)
    assert_no_secret(caplog, capsys)


async def test_should_degrade_in_a_container_without_the_security_binary(
    fake_server, adhd_engine_client, caplog
):
    """No patching of get_token: the real helper fails because /usr/bin/security is absent."""
    with caplog.at_level(logging.DEBUG):
        await _adhd_writes(adhd_engine_client)

    assert len(fake_server.requests) == 3
    assert all(r.authorization is None for r in fake_server.requests)
    assert "internal:adhd" in caplog.text


# --------------------------------------------------------------------------
# services/claude_brain/brain_manager.py  (internal:brain, container)
# --------------------------------------------------------------------------

FAKE_API_KEY = "fake-conport-api-key"


@pytest.fixture
def brain(monkeypatch, fake_server):
    """A manager built with stubbed siblings: config.py cannot import under pydantic 2."""
    package = types.ModuleType("claude_brain")
    package.__path__ = [str(SERVICES / "claude_brain")]
    config = types.ModuleType("claude_brain.config")
    config.settings = SimpleNamespace(
        ADHD_ENGINE_URL="http://adhd.invalid",
        ADHD_ENGINE_API_KEY="",
        CONPORT_URL=fake_server.url,
        CONPORT_API_KEY=FAKE_API_KEY,
        SERENA_URL="http://serena.invalid",
        SERENA_API_KEY="",
    )
    cache = types.ModuleType("claude_brain.cache_manager")
    cache.CacheManager = type("CacheManager", (), {})
    failure = types.ModuleType("claude_brain.failure_handler")
    failure.FailureHandler = type("FailureHandler", (), {})
    for name, module in {
        "claude_brain": package,
        "claude_brain.config": config,
        "claude_brain.cache_manager": cache,
        "claude_brain.failure_handler": failure,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    spec = importlib.util.spec_from_file_location(
        "claude_brain.brain_manager", SERVICES / "claude_brain" / "brain_manager.py"
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "claude_brain.brain_manager", module)
    spec.loader.exec_module(module)
    return module.ClaudeBrainManager()


async def test_should_send_brain_token_and_ids_when_logging_a_decision(
    fake_server, brain, token_ok, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "ws-bound")
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")

    await brain._log_decision("optimize", "anthropic", 0.01, True)

    (seen,) = fake_server.requests
    assert seen.path == "/api/decisions"
    assert seen.authorization == f"Bearer {FAKE_TOKEN}", "the principal token replaces the legacy api key"
    assert seen.body["workspace_id"] == "ws-bound"
    assert seen.body["instance_id"] == "inst-a"
    assert seen.body["summary"].startswith("AI Provider Selection")
    assert token_ok == ["internal:brain"]


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_keep_the_legacy_api_key_header_when_brain_has_no_token(
    fake_server, brain, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        await brain._log_decision("optimize", "anthropic", 0.01, True)

    (seen,) = fake_server.requests
    assert seen.authorization == f"Bearer {FAKE_API_KEY}", "exactly the header sent before W05"
    assert_no_secret(caplog, capsys)


async def test_should_not_invent_ids_when_brain_has_none(fake_server, brain, token_ok):
    await brain._log_decision("optimize", "anthropic", 0.01, True)

    body = fake_server.requests[0].body
    assert "workspace_id" not in body
    assert "instance_id" not in body


# --------------------------------------------------------------------------
# services/dopecon-bridge/dopecon_bridge/clients.py  (internal:dopecon, container)
# --------------------------------------------------------------------------


@pytest.fixture
def bridge_client(monkeypatch, request, fake_server):
    """clients.py with `core` stubbed: the real one needs sqlalchemy (a services extra)."""
    monkeypatch.syspath_prepend(str(SERVICES / "dopecon-bridge"))
    core = types.ModuleType("dopecon_bridge.core")
    core.cache_manager = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "dopecon_bridge.core", core)
    monkeypatch.delitem(sys.modules, "dopecon_bridge.clients", raising=False)
    request.addfinalizer(lambda: sys.modules.pop("dopecon_bridge.clients", None))
    clients = importlib.import_module("dopecon_bridge.clients")
    client = clients.ConPortClient()
    client.base_url = fake_server.url
    return client


async def _bridge_writes(client):
    await client.save_custom_data({"workspace_id": "ws-x", "category": "c", "key": "k", "value": {}})
    await client.claim_custom_data({"workspace_id": "ws-x", "category": "c", "key": "k", "value": {}})
    await client.log_decision({"workspace_id": "ws-x", "summary": "s", "rationale": "r"})
    await client.log_progress({"workspace_id": "ws-x", "description": "d"})
    await client.close()


async def test_should_send_dopecon_token_and_ids_on_bridge_writes(
    fake_server, bridge_client, token_ok, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")

    await _bridge_writes(bridge_client)

    custom, claim, decision, progress = fake_server.requests
    assert [r.path for r in fake_server.requests] == [
        "/api/custom_data",
        "/api/custom_data/claim",
        "/api/decisions",
        "/api/progress",
    ]
    for seen in fake_server.requests:
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
        assert seen.body["workspace_id"] == "ws-x", "the caller's workspace is never overridden"
    assert progress.body["instance_id"] == "inst-a"
    assert decision.body["instance_id"] == "inst-a"
    assert "instance_id" not in custom.body, "custom_data has no instance column"
    assert set(token_ok) == {"internal:dopecon"}


async def test_should_keep_a_caller_supplied_instance_id_on_bridge_progress(
    fake_server, bridge_client, token_ok, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "from-env")
    payload = {"workspace_id": "ws-x", "description": "d", "instance_id": "from-caller"}

    await bridge_client.log_progress(payload)
    await bridge_client.close()

    assert fake_server.requests[0].body["instance_id"] == "from-caller"
    assert payload == {"workspace_id": "ws-x", "description": "d", "instance_id": "from-caller"}


async def test_should_not_fetch_a_token_for_bridge_reads(fake_server, bridge_client, token_ok):
    await bridge_client.list_decisions(workspace_id="ws-x")
    await bridge_client.list_progress(workspace_id="ws-x")
    await bridge_client.get_custom_data({"workspace_id": "ws-x"})
    await bridge_client.close()

    assert len(fake_server.requests) == 3
    assert all(r.authorization is None for r in fake_server.requests)
    assert token_ok == []


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_bridge_has_no_token(
    fake_server, bridge_client, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        await _bridge_writes(bridge_client)

    assert len(fake_server.requests) == 4
    assert all(r.authorization is None for r in fake_server.requests)
    assert_no_secret(caplog, capsys)


# --------------------------------------------------------------------------
# services/dopecon-bridge/ddg_mcp_stdio.py  (internal:dopecon, `docker exec` in the bridge container)
# --------------------------------------------------------------------------


@pytest.fixture
def ddg(monkeypatch):
    class _Server:
        def __init__(self, *args, **kwargs):
            pass

        def tool(self):
            return lambda fn: fn

    def mod(name, **attrs):
        module = types.ModuleType(name)
        module.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, module)

    mod("mcp")
    mod("mcp.server", Server=_Server)
    mod("mcp.server.models", InitializationOptions=object)
    mod("mcp.server.stdio", stdio_server=None)
    mod("mcp.types", TextContent=lambda type, text: SimpleNamespace(type=type, text=text))
    return _load("w05_ddg_mcp_stdio", SERVICES / "dopecon-bridge" / "ddg_mcp_stdio.py")


async def test_should_send_dopecon_token_on_every_ddg_write(fake_server, ddg, token_ok):
    await ddg.conport_fork_instance(
        "ws-x", source_instance="a", target_instance="b", conport_url=fake_server.url
    )
    await ddg.conport_promote(
        "p-1", workspace_id="ws-x", instance_id="inst-a", conport_url=fake_server.url
    )
    await ddg.conport_promote_all("ws-x", instance_id="inst-a", conport_url=fake_server.url)

    fork, promote, promote_all = fake_server.requests
    assert [r.path for r in fake_server.requests] == [
        "/api/instance/fork",
        "/api/progress/promote",
        "/api/progress/promote_all",
    ]
    for seen in fake_server.requests:
        assert seen.authorization == f"Bearer {FAKE_TOKEN}"
        assert seen.body["workspace_id"] == "ws-x"
    assert fork.body["target_instance"] == "b"
    assert promote.body["instance_id"] == promote_all.body["instance_id"] == "inst-a"
    assert set(token_ok) == {"internal:dopecon"}


async def test_should_fill_ddg_promote_ids_from_the_environment(fake_server, ddg, token_ok, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "ws-bound")
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "inst-a")

    await ddg.conport_promote("p-1", conport_url=fake_server.url)
    await ddg.conport_promote_all("ws-x", conport_url=fake_server.url)

    promote, promote_all = fake_server.requests
    assert promote.body == {"progress_id": "p-1", "workspace_id": "ws-bound", "instance_id": "inst-a"}
    assert promote_all.body == {"workspace_id": "ws-x", "instance_id": "inst-a"}


async def test_should_not_invent_ddg_ids(fake_server, ddg, token_ok):
    await ddg.conport_promote("p-1", conport_url=fake_server.url)
    await ddg.conport_promote_all("ws-x", conport_url=fake_server.url)

    promote, promote_all = fake_server.requests
    assert promote.body == {"progress_id": "p-1"}
    assert promote_all.body == {"workspace_id": "ws-x"}


@pytest.mark.parametrize("fixture", NO_TOKEN)
async def test_should_write_without_header_when_ddg_has_no_token(
    fake_server, ddg, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)

    with caplog.at_level(logging.DEBUG):
        await ddg.conport_promote_all("ws-x", conport_url=fake_server.url)

    assert fake_server.requests[0].authorization is None
    assert_no_secret(caplog, capsys)
