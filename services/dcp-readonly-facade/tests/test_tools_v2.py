"""Public v2 facade tools: target_id-only, local evidence, fail-closed."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from dopemux.mcp.project_identity import ProjectIdentity

from dcp_facade import envelope as E
from dcp_facade.registry_v2 import parse_registry_v2
from dcp_facade import tools_v2


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _workspace(tmp_path: Path, *, bundles: dict[str, dict] | None = None) -> tuple[Path, str]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _git(workspace, "init", "-q")
    _git(workspace, "config", "user.email", "tests@example.invalid")
    _git(workspace, "config", "user.name", "Facade Tests")
    (workspace / ".dopemux").mkdir()
    (workspace / ".repo_id").write_text("project=test-project\nowner=test-owner\n")
    (workspace / "README.md").write_text("fixture\n")
    _git(workspace, "add", ".repo_id", "README.md")
    _git(workspace, "commit", "-qm", "fixture")
    head_sha = _git(workspace, "rev-parse", "HEAD")

    for bundle_id, proof in (bundles or {}).items():
        bundle = workspace / "proof" / bundle_id
        bundle.mkdir(parents=True)
        (bundle / "PROOF.json").write_text(json.dumps(proof))
    return workspace, head_sha


def _registry(workspace: Path, *, target_id: str = "target-main"):
    return parse_registry_v2(
        {
            "approved_roots": [str(workspace.parent)],
            "targets": [
                {
                    "target_id": target_id,
                    "workspace_path": str(workspace),
                    "enabled": True,
                    "identity": {"project": "test-project", "owner": "test-owner"},
                    "service_policies": {
                        "conport": {"enabled": True},
                        "dope_memory": {"enabled": True},
                    },
                }
            ],
        }
    )


def test_list_targets_reports_enabled_opaque_ids_only(tmp_path: Path):
    workspace, _ = _workspace(tmp_path)
    registry = _registry(workspace)

    envelope = tools_v2.list_targets(registry)

    assert envelope["status"] == E.OK
    assert envelope["target_id"] is None
    assert envelope["data"] == {
        "registry_generation": registry.generation,
        "targets": [{"target_id": "target-main"}],
    }
    assert str(workspace) not in repr(envelope)


def test_target_capabilities_resolve_v2_target_and_stay_non_callable(tmp_path: Path):
    workspace, _ = _workspace(tmp_path)

    envelope = tools_v2.get_target_capabilities(_registry(workspace), "target-main")

    assert envelope["status"] == E.OK
    assert envelope["target_id"] == "target-main"
    assert envelope["data"]["target_id"] == "target-main"
    assert {entry["family"] for entry in envelope["data"]["capabilities"]} == {
        "conport",
        "dope_memory",
    }
    assert all(entry["live"] == "UNKNOWN" for entry in envelope["data"]["capabilities"])
    assert all(entry["callable"] is False for entry in envelope["data"]["capabilities"])
    assert "project_id" not in envelope
    assert str(workspace) not in repr(envelope)


def test_unsafe_target_input_is_blocked_without_reflection():
    registry = parse_registry_v2({"targets": []})
    unsafe = "http://127.0.0.1:3020/private/secret"

    envelope = tools_v2.get_target_capabilities(registry, unsafe)

    assert envelope["status"] == E.BLOCKED
    assert envelope["target_id"] is None
    rendered = repr(envelope)
    for forbidden in ("http", "127.0.0.1", "3020", "private", "secret"):
        assert forbidden not in rendered


def test_token_shaped_target_input_is_blocked_without_reflection():
    registry = parse_registry_v2({"targets": []})
    unsafe = "sk-abcdefghijklmnopqrstuvwxyz"

    envelope = tools_v2.get_target_capabilities(registry, unsafe)

    assert envelope["status"] == E.BLOCKED
    assert envelope["target_id"] is None
    assert unsafe not in repr(envelope)


def test_locator_shaped_target_ids_are_blocked_without_reflection():
    """Port-like and numeric-dotted IDs must not be echoed as opaque target_id."""
    registry = parse_registry_v2({"targets": []})
    for unsafe in ("3020", "8080", "127.0.0.1", "1.2.3.4", "127.1"):
        envelope = tools_v2.get_target_capabilities(registry, unsafe)

        assert envelope["status"] == E.BLOCKED, unsafe
        assert envelope["target_id"] is None, unsafe
        assert unsafe not in repr(envelope), unsafe
        assert tools_v2._is_opaque_target_id(unsafe) is False


def test_repo_and_proof_tools_use_target_id(tmp_path: Path):
    workspace, head_sha = _workspace(
        tmp_path, bundles={"TP-TEST-0001": {"head_sha": "stale-head"}}
    )
    registry = _registry(workspace)

    snapshot = tools_v2.get_target_repo_state_snapshot(registry, "target-main")
    bundles = tools_v2.list_target_proof_bundles(registry, "target-main", "TP-TEST")
    bundle = tools_v2.fetch_target_proof_bundle(registry, "target-main", "TP-TEST-0001")

    assert snapshot["status"] == E.OK
    assert snapshot["head_sha"] == head_sha
    assert bundles["data"]["bundles"] == [{"bundle_id": "TP-TEST-0001", "files": ["PROOF.json"]}]
    assert bundle["target_id"] == "target-main"
    assert bundle["data"]["stale"] is True
    assert any(warning.startswith("stale proof bundle") for warning in bundle["warnings"])
    assert str(workspace) not in repr([snapshot, bundles, bundle])


def test_runtime_receipt_is_redacted_and_never_callable(tmp_path: Path, monkeypatch):
    workspace, _ = _workspace(tmp_path)
    registry = _registry(workspace)
    identity = ProjectIdentity(
        worktree_root=workspace.resolve(), project_root=workspace.resolve(), git_common_dir=None
    )
    catalog_path = tmp_path / "catalog.yaml"
    runtime_path = tmp_path / "instances.json"
    catalog_path.write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "conport": {
                        "scope": "per-worktree",
                        "identity_scope": "per-worktree",
                        "management_model": "compose-service",
                    }
                }
            }
        )
    )
    runtime_path.write_text(
        json.dumps(
            {
                "instances": [
                    {
                        "service": "conport",
                        "project_id": identity.project_id,
                        "project_root": str(workspace),
                        "worktree_root": str(workspace),
                        "urls": {"mcp": "http://127.0.0.1:3020/mcp"},
                        "ports": {"mcp": 3020},
                    }
                ]
            }
        )
    )
    monkeypatch.setenv("DCP_FACADE_MCP_CATALOG", str(catalog_path))
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(runtime_path))

    envelope = tools_v2.get_target_runtime_receipt(registry, "target-main")

    assert envelope["status"] == E.OK
    assert envelope["data"] == {
        "services": [
            {
                "family": "conport",
                "state": "UNKNOWN",
                "callable": False,
                "reason": "runtime candidate joined; live verification required",
            },
            {
                "family": "dope_memory",
                "state": "BLOCKED",
                "callable": False,
                "reason": "canonical catalog policy mismatch",
            },
        ]
    }
    rendered = repr(envelope)
    for forbidden in (str(workspace), str(catalog_path), str(runtime_path), "127.0.0.1", "3020"):
        assert forbidden not in rendered
    assert all(service["callable"] is False for service in envelope["data"]["services"])
