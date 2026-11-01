"""mcp_stdio_adapter must not send fabricated "default"/"A" identities (W2-F03)."""

import importlib.util
from pathlib import Path

import pytest

_P = Path(__file__).resolve().parents[2] / "services/dope-memory/mcp_stdio_adapter.py"
_spec = importlib.util.spec_from_file_location("mcp_stdio_adapter_under_test", _P)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _adapter(monkeypatch):
    sent = {}
    a = mod.DopeMemoryMCPAdapter()
    monkeypatch.setattr(a, "_call_rest_endpoint", lambda ep, payload: sent.update(ep=ep, p=payload) or {})
    return a, sent


def _call(a, tool, params):
    return a.tools[tool](params)


TOOLS = [("memory_store", {"summary": "s"}), ("memory_search", {"query": "q"})]


@pytest.mark.parametrize("tool,base", TOOLS)
def test_omits_ids_when_unset(monkeypatch, tool, base):
    monkeypatch.delenv("DOPE_MEMORY_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("DOPE_MEMORY_INSTANCE_ID", raising=False)
    a, sent = _adapter(monkeypatch)
    _call(a, tool, base)
    assert "workspace_id" not in sent["p"] and "instance_id" not in sent["p"]


@pytest.mark.parametrize("tool,base", TOOLS)
def test_placeholder_and_blank_env_count_as_unset(monkeypatch, tool, base):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "default")
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "  ")
    a, sent = _adapter(monkeypatch)
    _call(a, tool, base)
    assert "workspace_id" not in sent["p"] and "instance_id" not in sent["p"]


@pytest.mark.parametrize("tool,base", TOOLS)
def test_env_used_when_params_absent(monkeypatch, tool, base):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    a, sent = _adapter(monkeypatch)
    _call(a, tool, base)
    assert sent["p"]["workspace_id"] == "proj" and sent["p"]["instance_id"] == "ab12"


@pytest.mark.parametrize("tool,base", TOOLS)
def test_params_win_over_env(monkeypatch, tool, base):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    a, sent = _adapter(monkeypatch)
    _call(a, tool, {**base, "workspace_id": "other", "instance_id": "zz"})
    assert sent["p"]["workspace_id"] == "other" and sent["p"]["instance_id"] == "zz"
