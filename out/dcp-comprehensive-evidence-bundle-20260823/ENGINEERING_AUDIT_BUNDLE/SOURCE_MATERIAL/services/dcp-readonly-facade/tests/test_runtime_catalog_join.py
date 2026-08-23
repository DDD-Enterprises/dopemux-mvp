"""TP-DCP-MCP-RO-0011 runtime/catalog join contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from dopemux.mcp.project_identity import ProjectIdentity
from dcp_facade.registry_v2 import FAMILY_POLICY_TABLE, ExposureTarget, ServicePolicy
from dcp_facade.resolver_core import ResolvedTarget
from dcp_facade.runtime_catalog_join import RuntimeCatalogEntry, join_runtime_catalog


def _resolved(*families: str) -> ResolvedTarget:
    workspace = Path("/approved/dopemux-mvp")
    target = ExposureTarget(
        target_id="dopemux-main",
        workspace_path=str(workspace),
        enabled=True,
        binding_mode="PRIMARY_CHECKOUT_ONLY",
        identity_project="dopemux-mvp",
        identity_owner="hu3mann",
        service_policies={
            family: ServicePolicy(
                family=family,
                configured=True,
                resolution_class=FAMILY_POLICY_TABLE[family][0],
                chatgpt_posture=FAMILY_POLICY_TABLE[family][1],
            )
            for family in families
        },
    )
    return ResolvedTarget(
        target=target,
        workspace=workspace,
        project_root=Path("/approved"),
        worktree_root=workspace,
        service_policies=target.service_policies,
    )


def _catalog() -> dict:
    return {
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "identity_scope": "per-worktree",
                "management_model": "compose-service",
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "identity_scope": "per-worktree",
                "management_model": "compose-service",
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "single_active_project",
                "transport": "http",
                "identity_scope": "per-repo",
                "management_model": "wrapper-singleton",
            },
        }
    }


def _runtime(
    *,
    service: str,
    project_id: str | None = None,
    project_root: str = "/approved",
    worktree_root: str = "/approved/dopemux-mvp",
) -> dict:
    return {
        "parse_status": "OK",
        "present": True,
        "instances": [
            {
                "instance_id": "runtime-secret-id",
                "project_id": project_id
                or _lifecycle_project_id(project_root, worktree_root),
                "project_root": project_root,
                "worktree_root": worktree_root,
                "service": service,
                "status": "running",
                "ports": {"http": 3020},
                "urls": {"mcp": "http://127.0.0.1:3020/mcp"},
            }
        ],
    }


def _lifecycle_project_id(project_root: str, worktree_root: str) -> str:
    return ProjectIdentity(
        project_root=Path(project_root),
        worktree_root=Path(worktree_root),
        git_common_dir=None,
    ).project_id


def test_exact_per_worktree_join_is_non_callable_and_maps_operational_name():
    result = join_runtime_catalog(
        _resolved("dope_memory"),
        _catalog(),
        _runtime(service="dope-memory"),
    )

    entry = result.entries[0]
    assert entry.family == "dope_memory"
    assert entry.catalog_name == "dope-memory"
    assert entry.candidate_count == 1
    assert entry.state == "UNKNOWN"
    assert entry.callable is False


def test_lifecycle_generated_project_id_joins_when_dcp_identity_is_unhashed():
    project_root = "/approved"
    worktree_root = "/approved/dopemux-mvp"
    result = join_runtime_catalog(
        _resolved("conport"),
        _catalog(),
        _runtime(
            service="conport",
            project_id=_lifecycle_project_id(project_root, worktree_root),
            project_root=project_root,
            worktree_root=worktree_root,
        ),
    )

    entry = result.entries[0]
    assert entry.state == "UNKNOWN"
    assert entry.candidate_count == 1
    assert entry.callable is False


def test_dcp_repository_identity_is_not_accepted_as_lifecycle_project_id():
    result = join_runtime_catalog(
        _resolved("conport"),
        _catalog(),
        _runtime(service="conport", project_id="dopemux-mvp"),
    )

    entry = result.entries[0]
    assert entry.state == "UNAVAILABLE"
    assert entry.candidate_count == 0
    assert entry.callable is False


def test_wrapper_family_stays_blocked_even_when_operational_record_exists():
    result = join_runtime_catalog(
        _resolved("to_mcp_wrapper"),
        _catalog(),
        _runtime(service="task-orchestrator"),
    )

    entry = result.entries[0]
    assert entry.family == "to_mcp_wrapper"
    assert entry.state == "BLOCKED"
    assert entry.callable is False


def test_scope_mismatch_does_not_join_by_project_name_alone():
    result = join_runtime_catalog(
        _resolved("conport"),
        _catalog(),
        _runtime(service="conport", worktree_root="/approved/other-worktree"),
    )

    entry = result.entries[0]
    assert entry.state == "UNAVAILABLE"
    assert entry.candidate_count == 0
    assert entry.callable is False


def test_duplicate_matching_candidates_block_without_selection():
    runtime = _runtime(service="conport")
    runtime["instances"].append(dict(runtime["instances"][0], instance_id="runtime-secret-id-2"))

    result = join_runtime_catalog(_resolved("conport"), _catalog(), runtime)

    entry = result.entries[0]
    assert entry.state == "BLOCKED"
    assert entry.candidate_count == 2
    assert entry.callable is False


def test_malformed_runtime_registry_is_unknown_and_non_callable():
    result = join_runtime_catalog(
        _resolved("conport"),
        _catalog(),
        {"parse_status": "ERROR", "instances": "not-a-list"},
    )

    entry = result.entries[0]
    assert entry.state == "UNKNOWN"
    assert entry.candidate_count == 0
    assert entry.callable is False


def test_malformed_runtime_member_blocks_candidate_join():
    runtime = _runtime(service="conport")
    runtime["instances"].append([])

    result = join_runtime_catalog(_resolved("conport"), _catalog(), runtime)

    entry = result.entries[0]
    assert entry.state == "UNKNOWN"
    assert entry.candidate_count == 0
    assert entry.reason == "operational runtime registry unavailable"
    assert entry.callable is False


def test_catalog_policy_drift_blocks_candidate_join():
    catalog = _catalog()
    catalog["servers"]["conport"]["management_model"] = "wrapper-singleton"

    result = join_runtime_catalog(
        _resolved("conport"),
        catalog,
        _runtime(service="conport"),
    )

    entry = result.entries[0]
    assert entry.state == "BLOCKED"
    assert entry.reason == "canonical catalog policy mismatch"
    assert entry.callable is False


def test_compose_rest_has_no_supported_catalog_binding():
    result = join_runtime_catalog(
        _resolved("to_compose_rest"),
        _catalog(),
        _runtime(service="task-orchestrator"),
    )

    entry = result.entries[0]
    assert entry.state == "BLOCKED"
    assert entry.catalog_name is None
    assert entry.callable is False


def test_unknown_direct_task_orchestrator_family_is_blocked():
    resolved = _resolved("conport")
    resolved = ResolvedTarget(
        target=resolved.target,
        workspace=resolved.workspace,
        project_root=resolved.project_root,
        worktree_root=resolved.worktree_root,
        service_policies={
            "task-orchestrator": ServicePolicy(
                family="task-orchestrator",
                configured=True,
                resolution_class="host_singleton_single_active_project",
                chatgpt_posture="blocked",
            )
        },
    )
    result = join_runtime_catalog(
        resolved,
        _catalog(),
        _runtime(service="task-orchestrator"),
    )

    entry = result.entries[0]
    assert entry.state == "BLOCKED"
    assert entry.catalog_name is None
    assert entry.callable is False


def test_public_result_redacts_operational_details():
    result = join_runtime_catalog(
        _resolved("dope_memory"),
        _catalog(),
        _runtime(service="dope-memory"),
    )

    public = result.to_public_dict()
    rendered = repr(public)
    assert public == {
        "services": [
            {
                "family": "dope_memory",
                "state": "UNKNOWN",
                "callable": False,
                "reason": "runtime candidate joined; live verification required",
            }
        ]
    }
    for forbidden in ("runtime-secret-id", "3020", "127.0.0.1", "/approved"):
        assert forbidden not in rendered


def test_runtime_catalog_entry_rejects_callable_override():
    with pytest.raises(TypeError):
        RuntimeCatalogEntry(
            family="conport",
            catalog_name="conport",
            state="UNKNOWN",
            candidate_count=1,
            callable=True,
            reason="runtime candidate joined; live verification required",
        )
