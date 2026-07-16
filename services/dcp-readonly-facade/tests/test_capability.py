"""capability_report: configured vs live/callable separation (TP-DCP-MCP-RO-0010).

Only "configured" (family declared + policy-enabled in the registry) is known
in this packet; live reachability requires a backend call, which is out of
scope. ``live`` must always report ``"UNKNOWN"`` and ``callable`` must always
be ``False`` — configured must never imply callable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from dcp_facade.capability import capability_report
from dcp_facade.registry_v2 import parse_registry_v2
from dcp_facade.resolver_core import resolve_target


@pytest.fixture
def build_registry_v2():
    def _build(targets: list[dict], approved_roots: Optional[list[str]] = None):
        doc: dict = {"targets": targets}
        if approved_roots is not None:
            doc["approved_roots"] = approved_roots
        return parse_registry_v2(doc)

    return _build


@pytest.fixture
def target_entry():
    def _entry(
        ws_path: Path,
        *,
        target_id: str = "t",
        identity_project: str = "testproj",
        identity_owner: Optional[str] = "tester",
        enabled: bool = True,
        service_policies: Optional[dict] = None,
    ) -> dict:
        identity: dict = {"project": identity_project}
        if identity_owner is not None:
            identity["owner"] = identity_owner
        return {
            "target_id": target_id,
            "workspace_path": str(ws_path),
            "enabled": enabled,
            "identity": identity,
            "service_policies": service_policies or {},
        }

    return _entry


def _resolved(make_workspace, build_registry_v2, target_entry, service_policies):
    info = make_workspace(project="proj", owner="tester")
    ws = info["path"]
    reg = build_registry_v2(
        [
            target_entry(
                ws,
                target_id="t",
                identity_project="proj",
                identity_owner="tester",
                service_policies=service_policies,
            )
        ],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert reason is None
    return resolved


def test_capability_report_marks_configured_family(make_workspace, build_registry_v2, target_entry):
    resolved = _resolved(
        make_workspace, build_registry_v2, target_entry, {"conport": {"enabled": True}}
    )
    report = capability_report(resolved)
    entry = next(e for e in report if e["family"] == "conport")
    assert entry["configured"] is True
    assert entry["resolution_class"] == "per_worktree_runtime"
    assert entry["chatgpt_posture"] == "conditional_read_only"
    assert entry["live"] == "UNKNOWN"
    assert entry["callable"] is False


def test_capability_report_marks_unconfigured_family(make_workspace, build_registry_v2, target_entry):
    resolved = _resolved(
        make_workspace, build_registry_v2, target_entry, {"pal": {"enabled": False}}
    )
    report = capability_report(resolved)
    entry = next(e for e in report if e["family"] == "pal")
    assert entry["configured"] is False
    assert entry["live"] == "UNKNOWN"
    assert entry["callable"] is False


def test_capability_report_empty_when_no_families_declared(
    make_workspace, build_registry_v2, target_entry
):
    resolved = _resolved(make_workspace, build_registry_v2, target_entry, {})
    assert capability_report(resolved) == []


def test_capability_report_configured_never_implies_live_or_callable(
    make_workspace, build_registry_v2, target_entry
):
    resolved = _resolved(
        make_workspace,
        build_registry_v2,
        target_entry,
        {"conport": {"enabled": True}, "dope_memory": {"enabled": True}},
    )
    report = capability_report(resolved)
    assert len(report) == 2
    for entry in report:
        assert entry["live"] == "UNKNOWN"
        assert entry["callable"] is False


def test_capability_report_entries_have_no_forbidden_public_fields(
    make_workspace, build_registry_v2, target_entry
):
    resolved = _resolved(
        make_workspace, build_registry_v2, target_entry, {"conport": {"enabled": True}}
    )
    report = capability_report(resolved)
    for entry in report:
        assert set(entry) == {
            "family",
            "configured",
            "resolution_class",
            "chatgpt_posture",
            "live",
            "callable",
        }
