"""Synthetic owner records and private local command fixtures."""

import dataclasses
import hashlib
import json
import os
import sys
import time


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    path.write_bytes(canonical(value))
    path.chmod(0o600)


def owner_fixture(root):
    from dopemux.mcp.identity_registry import IdentityRegistry
    from dopemux.governed_execution.admission.identity import ExpectedScope
    from dopemux.governed_execution.admission.owner_admission import native_schema_digest

    root.mkdir(mode=0o700)
    work = root / "project"
    work.mkdir(mode=0o700)
    registry = IdentityRegistry.load(root / "registry.json", create_missing=True)
    project = registry.register_project(aliases=[])
    workspace = registry.register_workspace(
        project_id=project, aliases=[{"kind": "cwd", "value": str(work)}]
    )
    instance = registry.register_instance(project_id=project, workspace_id=workspace, aliases=[])
    (root / "registry.json").chmod(0o600)
    scope = ExpectedScope(
        project_id=project,
        workspace_id=workspace,
        instance_id=instance,
        worktree=str(work),
        actor_id="fixture-actor",
        client_id="fixture-client",
        macro_id="macro-one",
        packet_id="packet-one",
        subject_digest="1" * 64,
        effects=("read", "write", "test"),
        resources=("fixture-output",),
        route_refs=("fixture-local",),
        active_seconds=60,
        wall_seconds=90,
        spend_limit_micros=0,
        max_attempts=4,
        repair_limit=1,
        max_parallel=1,
        delegation_depth=0,
        expires_at=time.time() + 120,
        policy_digest="2" * 64,
        trust_digest="3" * 64,
        schema_set_digest=native_schema_digest(),
    )
    grant = dataclasses.asdict(scope)
    receipt = {
        "schema_version": "dopemux.governed_execution.dispatch_input_receipt.v1",
        "receipt_type": "ScopeAuthority",
        "macro_id": scope.macro_id,
        "packet_id": scope.packet_id,
        "source_ref": "fixture-native-record",
        "authority": "NONE",
        "scope_status": "PASS",
        "allowlist_digest": hashlib.sha256(canonical(grant)).hexdigest(),
    }
    write_json(root / "receipt.json", receipt)
    ref = {
        "ref_id": "fixture-native-record",
        "sha256": hashlib.sha256(canonical(receipt)).hexdigest(),
        "classification": "INTERNAL",
        "locator": "receipt.json",
    }
    config = {
        "fixture_only": True,
        "owner_domain": "NATIVE_CT",
        "issuer_ref": "fixture-native",
        "generation": 1,
        "registry_generation": registry.data["generation"],
        "registry_file": "registry.json",
        "revoked": False,
        "expires_at": scope.expires_at,
        "principals": {"fixture-actor": {"uid": os.getuid(), "roles": ["NATIVE_CT"]}},
        "trust_digest": scope.trust_digest,
        "receipts": {
            ref["ref_id"]: {
                "evidence": ref,
                "kind": "dispatch_input_receipt.v1",
                "generation": 1,
                "revoked": False,
                "expires_at": scope.expires_at,
                "scope": grant,
                "delegation_depth_limit": 2,
            }
        },
    }
    write_json(root / "owner.json", config)
    return scope, ref, config


def manifest(project, mandate="m1", project_id="p1", deadline=None, code=None):
    deadline = deadline or time.time() + 60

    def step(name, kind, code, deps, paths):
        return {
            "step_id": name,
            "kind": kind,
            "argv": [sys.executable, "-B", "-c", code],
            "effects": ["read", "write"] if paths else ["read", "test"],
            "write_paths": paths,
            "depends_on": deps,
            "timeout_seconds": 5,
            "heavy": False,
        }

    return {
        "schema_version": "dopemux.project_mandate.v1",
        "mandate_id": mandate,
        "issuer_ref": "fixture-issued",
        "project_id": project_id,
        "project_root": str(project),
        "expires_at": deadline,
        "active_seconds": 15,
        "spend_limit_micros": 0,
        "max_parallel": 1,
        "repair_limit": 1,
        "stop_conditions": ["owner-stop", "security"],
        "gates": {"security": "PASS", "spending": "PASS", "workflow": "PASS"},
        "route": {
            "binding_id": "shared-local-label",
            "kind": "local_command",
            "model_class": "deterministic",
            "executable": sys.executable,
            "valid_until": deadline,
        },
        "steps": [
            step(
                "implement",
                "implementation",
                code or "from pathlib import Path;Path('result.txt').write_text('done')",
                [],
                ["result.txt"],
            ),
            step(
                "verify",
                "validation",
                "from pathlib import Path;assert Path('result.txt').read_text()=='done'",
                ["implement"],
                [],
            ),
        ],
        "success_steps": ["verify"],
    }
