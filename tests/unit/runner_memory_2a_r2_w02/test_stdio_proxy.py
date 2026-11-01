"""``conport_mcp_stdio.py``: the in-image stdio proxy forwards the caller's token.

A stdio process has no HTTP headers, so the caller's token comes from the
process environment (``CONPORT_STDIO_TOKEN``) and the ``internal:bridge-proxy``
fallback from the injectable provider (production default: none, until the W03
helper exists).
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")

from .test_mcp_surfaces import WRITE_CALLS, fake_rest  # noqa: E402
from .conftest import load_conport_module  # noqa: E402
from .helpers import SSE_TOOL_NAMES, fake_token, write_hash_file  # noqa: E402


@pytest.fixture()
def load_stdio(monkeypatch, tmp_path):
    def factory(mode="log", tokens=None, proxy_token=None, rest_url=None, caller_token=None):
        monkeypatch.setenv("CONPORT_AUTH_MODE", mode)
        write_hash_file(tmp_path / "auth", tokens or {})
        monkeypatch.setenv("CONPORT_AUTH_DIR", str(tmp_path / "auth"))
        if caller_token:
            monkeypatch.setenv("CONPORT_STDIO_TOKEN", caller_token)
        else:
            monkeypatch.delenv("CONPORT_STDIO_TOKEN", raising=False)
        module = load_conport_module("conport_mcp_stdio", monkeypatch)
        module.PROXY_TOKEN_PROVIDER = lambda: proxy_token
        if rest_url:
            module.CONPORT_URL = rest_url
        return module

    return factory


async def test_should_keep_the_17_tool_names(load_stdio):
    module = load_stdio()
    assert {tool.name for tool in await module.mcp.list_tools()} == SSE_TOOL_NAMES


@pytest.mark.parametrize("tool", list(WRITE_CALLS))
async def test_should_forward_the_callers_token_from_the_environment(load_stdio, tool):
    token = fake_token()
    arguments, method, path = WRITE_CALLS[tool]
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("enforce", {token: "runner:codex"}, rest_url=rest_url, caller_token=token)
        await module.mcp.call_tool(tool, arguments)
    (call,) = calls
    assert (call["method"], call["path"]) == (method, path)
    assert call["headers"]["authorization"] == f"Bearer {token}"


async def test_should_refuse_an_unverified_write_in_enforce_mode(load_stdio):
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("enforce", {fake_token(): "runner:codex"}, rest_url=rest_url)
        with pytest.raises(Exception, match="401|unauthorized"):
            await module.mcp.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    assert calls == []


async def test_should_use_the_proxy_principal_only_in_log_mode_with_no_caller_token(load_stdio):
    proxy = fake_token("proxy")
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("log", {proxy: "internal:bridge-proxy"}, proxy_token=proxy, rest_url=rest_url)
        await module.mcp.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    (call,) = calls
    assert call["headers"]["authorization"] == f"Bearer {proxy}"
    assert call["headers"]["x-dopemux-unverified-caller"] == "stdio"


async def test_should_send_no_credentials_when_there_is_no_token_at_all(load_stdio):
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("log", {}, rest_url=rest_url)
        await module.mcp.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    (call,) = calls
    assert "authorization" not in call["headers"]
    assert call["headers"]["x-dopemux-unverified-caller"] == "stdio"


async def test_should_not_send_credentials_with_reads(load_stdio):
    token = fake_token()
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("enforce", {token: "runner:codex"}, rest_url=rest_url, caller_token=token)
        await module.mcp.call_tool("get_context", {"workspace_id": "/w"})
    assert "authorization" not in calls[0]["headers"]
