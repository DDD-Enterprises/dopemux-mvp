"""pm/adapters/dope_memory.py: HTTP writes to dope-memory as internal:cli."""

from __future__ import annotations

import logging

import pytest

from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter

from .conftest import FAKE_TOKEN, assert_no_secret

pytestmark = pytest.mark.asyncio


async def _append(adapter: DopeMemoryAdapter):
    return await adapter.append_chronicle(
        workspace_id="ws-bound",
        entry_type="note",
        summary="s",
        category="work_chronicle",
    )


async def _correct(adapter: DopeMemoryAdapter):
    return await adapter.correct_chronicle(
        workspace_id="ws-bound",
        entry_id="e-1",
        correction_type="summary",
        corrected_summary="s2",
    )


@pytest.mark.parametrize("call, path", [(_append, "/tools/memory_store"), (_correct, "/tools/memory_correct")])
async def test_should_send_cli_token_and_ids_when_writing(
    fake_server, token_ok, monkeypatch, call, path
):
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "inst-a")
    adapter = DopeMemoryAdapter(base_url=fake_server.url)

    await call(adapter)

    (seen,) = fake_server.requests
    assert seen.path == path
    assert seen.authorization == f"Bearer {FAKE_TOKEN}"
    assert token_ok == ["internal:cli"]
    assert seen.body["workspace_id"] == "ws-bound"
    assert seen.body["instance_id"] == "inst-a"


async def test_should_prefer_constructor_instance_id_over_env(fake_server, token_ok, monkeypatch):
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "from-env")
    adapter = DopeMemoryAdapter(base_url=fake_server.url, instance_id="from-ctor")

    await _append(adapter)

    assert fake_server.requests[0].body["instance_id"] == "from-ctor"


async def test_should_omit_instance_id_when_none_is_known(fake_server, token_ok):
    await _append(DopeMemoryAdapter(base_url=fake_server.url))

    assert "instance_id" not in fake_server.requests[0].body


@pytest.mark.parametrize("fixture", ["token_missing", "token_keychain_down", "no_auth_package"])
async def test_should_write_without_header_when_no_token(
    fake_server, request, fixture, caplog, capsys
):
    request.getfixturevalue(fixture)
    adapter = DopeMemoryAdapter(base_url=fake_server.url)

    with caplog.at_level(logging.DEBUG):
        result = await _append(adapter)

    (seen,) = fake_server.requests
    assert seen.authorization is None
    assert result["entry_id"] == "entry-1"
    assert_no_secret(caplog, capsys)


async def test_should_log_principal_name_not_token_when_token_missing(
    fake_server, token_missing, caplog
):
    with caplog.at_level(logging.DEBUG):
        await _append(DopeMemoryAdapter(base_url=fake_server.url))

    assert "internal:cli" in caplog.text


async def test_should_not_fetch_a_token_for_reads(fake_server, token_ok):
    await DopeMemoryAdapter(base_url=fake_server.url).search_chronicle(workspace_id="ws-bound")

    (seen,) = fake_server.requests
    assert seen.path == "/tools/memory_search"
    assert seen.authorization is None
    assert token_ok == []
