"""WRITE tools reject foreign/blank workspace and mismatched instance (W2-F03).

The checks live in the shared DopeMemoryMCPServer methods, so REST (-> HTTP 400
via ``not result.success``) and MCP (-> ToolError via ``_unwrap``) both get them.
"""

import pytest

WRITE_ARGS = {
    "memory_store": dict(category="implementation", entry_type="manual_note", summary="s"),
    "memory_link_resolution": dict(issue_entry_id="a", resolution_entry_id="b"),
    "memory_correct": dict(entry_id="a", correction_type="summary", corrected_summary="x"),
    "memory_generate_reflection": dict(),
    "memory_mark_issue": dict(issue_entry_id="a", description="d"),
}
IDENT_ERR = "identity"


@pytest.fixture()
def backend(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "chronicle.sqlite"))
    monkeypatch.delenv("DOPE_MEMORY_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("DOPE_MEMORY_INSTANCE_ID", raising=False)
    from dope_memory_main import DopeMemoryMCPServer

    return DopeMemoryMCPServer(workspace_id="proj", instance_id="A")


def _call(backend, tool, **ids):
    return getattr(backend, tool)(**ids, **WRITE_ARGS[tool])


def _is_identity_rejection(res):
    return (not res.success) and IDENT_ERR in (res.error or "").lower()


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
def test_foreign_workspace_rejected(backend, monkeypatch, tool):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    assert _is_identity_rejection(_call(backend, tool, workspace_id="/x/other", instance_id="A"))


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_workspace_rejected(backend, tool, blank):
    assert _is_identity_rejection(_call(backend, tool, workspace_id=blank, instance_id="A"))


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
def test_instance_mismatch_rejected(backend, monkeypatch, tool):
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    assert _is_identity_rejection(_call(backend, tool, workspace_id="proj", instance_id="zzzz"))


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
def test_own_identity_unset_not_rejected_for_identity(backend, tool):
    res = _call(backend, tool, workspace_id="/x/whatever", instance_id="whatever")
    assert not _is_identity_rejection(res)


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
def test_placeholder_own_workspace_skips_foreign_check(backend, monkeypatch, tool):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "default")
    assert not _is_identity_rejection(_call(backend, tool, workspace_id="/x/other", instance_id="A"))


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
def test_matching_own_identity_passes_identity_check(backend, monkeypatch, tool):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    res = _call(backend, tool, workspace_id="/home/me/proj", instance_id="ab12")
    assert not _is_identity_rejection(res)


def test_store_succeeds_with_own_identity(backend, monkeypatch):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    res = _call(backend, "memory_store", workspace_id="/home/me/proj", instance_id="ab12")
    assert res.success, res.error


def test_read_tool_unaffected_by_foreign_workspace(backend, monkeypatch):
    monkeypatch.setenv("DOPE_MEMORY_WORKSPACE_ID", "proj")
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    res = backend.memory_recap(workspace_id="/x/other", instance_id="zzzz", scope="today")
    assert not _is_identity_rejection(res)
