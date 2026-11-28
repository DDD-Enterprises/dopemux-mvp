"""Opt-in existing-only tenant resolution never reaches database/gate writers."""

from __future__ import annotations

import contextlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.mcp import conport_tenant as ct
from dopemux.mcp import lifecycle


@pytest.fixture
def tenant(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime" / "instances.json")
    )
    monkeypatch.setenv("DOPEMUX_CONPORT_EXISTING_TENANT_ONLY", "true")
    identity = SimpleNamespace(
        project_id="project-abcd", project_root=str(tmp_path), project_hash="abcd"
    )
    path = ct.secrets_path(identity.project_id)
    ct.write_secrets(
        path,
        ct.TenantCredentials(
            "conport_existing", "conport_existing", "synthetic-test-password"
        ),
    )
    return identity, path


@pytest.mark.parametrize("state", ["gate", "database", "database:001", "unknown-state"])
def test_existing_only_pending_or_unknown_state_never_resumes(
    tenant, monkeypatch, state
):
    identity, path = tenant
    path.with_name(ct.STATE_FILENAME).write_text(state)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("existing-only must not reach any writer")

    monkeypatch.setattr(ct, "provision_database", forbidden)
    with pytest.raises(ct.TenantError) as error:
        ct.resolve_tenant(identity, envrc_values={}, psql=forbidden)
    assert error.value.code == "CONPORT_TENANT_EXISTING_ONLY_REQUIRED"
    assert state not in error.value.detail
    assert not calls


def test_existing_only_does_not_adopt_legacy_or_provision(tenant, monkeypatch):
    identity, path = tenant
    path.unlink()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("existing-only must not reach credential or SQL writer")

    monkeypatch.setattr(ct, "write_secrets", forbidden)
    with pytest.raises(ct.TenantError):
        ct.resolve_tenant(
            identity,
            envrc_values={
                "CONPORT_DB_NAME": "legacy",
                "CONPORT_DB_USER": "legacy",
                "CONPORT_DB_PASSWORD": "synthetic",
            },
            psql=forbidden,
        )
    assert not calls


def test_existing_only_valid_state_is_rechecked_under_provision_lock(
    tenant, monkeypatch
):
    identity, path = tenant
    locks = []

    @contextlib.contextmanager
    def lock(project_id):
        locks.append(project_id)
        yield

    monkeypatch.setattr(ct, "provision_lock", lock)

    def forbidden(*args):
        raise AssertionError("No SQL in existing-only qualification")

    creds = ct.resolve_tenant(identity, envrc_values={}, psql=forbidden)
    assert creds.db_name == "conport_existing" and not creds.gate_pending
    assert locks == [identity.project_id]


def test_existing_only_gate_cannot_apply_pending_state(tenant, monkeypatch):
    identity, path = tenant
    path.with_name(ct.STATE_FILENAME).write_text("gate")
    calls = []
    monkeypatch.setattr(ct, "adopt_with_gate", lambda *a, **kw: calls.append("apply"))
    monkeypatch.setattr(ct, "mark_gate_done", lambda *a, **kw: calls.append("clear"))
    findings = lifecycle._run_tenant_gate(identity, "existing", None, expected=True)
    assert any(f["severity"] == "FAIL" for f in findings)
    assert not calls


@pytest.mark.parametrize("value", ["TRUE", "yes", ""])
def test_existing_only_malformed_process_policy_holds(tenant, monkeypatch, value):
    identity, _ = tenant
    monkeypatch.setenv("DOPEMUX_CONPORT_EXISTING_TENANT_ONLY", value)
    with pytest.raises(ct.TenantError) as error:
        ct.resolve_tenant(identity, envrc_values={}, psql=lambda *args: None)
    assert error.value.code == "CONPORT_TENANT_POLICY_INVALID"


@pytest.mark.parametrize(
    "failure", ["unknown", "unreadable", "invalid_utf8", "unsafe_secrets"]
)
def test_read_only_existing_qualifier_holds_without_leaking_or_writing(
    tenant, monkeypatch, failure
):
    identity, path = tenant
    state = path.with_name(ct.STATE_FILENAME)
    if failure == "unknown":
        state.write_text("private-state-marker")
    elif failure == "invalid_utf8":
        state.write_bytes(b"\xff")
    elif failure == "unsafe_secrets":
        path.chmod(0o644)
    else:
        monkeypatch.setattr(
            ct,
            "_read_state",
            lambda *a: (_ for _ in ()).throw(
                ct.TenantError("TENANT_STATE_UNREADABLE", "private-state-marker")
            ),
        )
    before = {p: p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    with pytest.raises(ct.TenantError) as error:
        ct.qualify_existing_tenant(identity)
    assert "private-state-marker" not in str(error.value)
    assert {p: p.read_bytes() for p in before} == before


def test_existing_only_gate_rechecks_pending_state_under_lock_and_pins_mode(
    tenant, monkeypatch
):
    identity, path = tenant
    calls = []

    @contextlib.contextmanager
    def lock(project_id):
        path.with_name(ct.STATE_FILENAME).write_text("gate")
        monkeypatch.setenv(ct.EXISTING_ONLY_ENV, "false")
        yield

    monkeypatch.setattr(lifecycle, "provision_lock", lock)
    monkeypatch.setattr(ct, "adopt_with_gate", lambda *a, **kw: calls.append("apply"))
    monkeypatch.setattr(ct, "mark_gate_done", lambda *a, **kw: calls.append("clear"))
    findings = lifecycle._run_tenant_gate(
        identity, "existing", None, expected=True, existing_only=True
    )
    assert any(f["severity"] == "FAIL" for f in findings)
    assert not calls and path.with_name(ct.STATE_FILENAME).read_text() == "gate"


def test_default_resolution_and_gate_behavior_is_preserved(tenant, monkeypatch):
    identity, path = tenant
    monkeypatch.delenv(ct.EXISTING_ONLY_ENV)
    path.with_name(ct.STATE_FILENAME).write_text("gate")
    creds = ct.resolve_tenant(identity, envrc_values={}, psql=lambda *a: None)
    assert creds.gate_pending
    calls = []
    monkeypatch.setattr(ct, "adopt_with_gate", lambda *a, **kw: calls.append("apply"))
    monkeypatch.setattr(ct, "mark_gate_done", lambda *a, **kw: calls.append("clear"))
    findings = lifecycle._run_tenant_gate(identity, "existing", None, expected=True)
    assert not any(f["severity"] == "FAIL" for f in findings)
    assert calls == ["apply", "clear"]


def test_existing_only_read_only_resolution_does_not_create_lock_state(
    tenant, monkeypatch
):
    identity, _ = tenant

    def forbidden(*args):
        raise AssertionError("Read-only qualification must not create lock state")

    monkeypatch.setattr(ct, "provision_lock", forbidden)
    creds = ct.resolve_tenant(
        identity, envrc_values={}, psql=forbidden, provision=False
    )
    assert not creds.gate_pending
