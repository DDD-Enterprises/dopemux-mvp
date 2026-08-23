from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator

from ..models import Claim, LaneEvidence, SourceRef, SourceSnapshot

_PROJECT_ID = "DDD-Enterprises/dnh-crm"
_PINNED_HEAD = "92eb632bb07426ae5159c02bf9da549888e7caf1"
_PROOF_HEAD = "c0818fe8e29bdeb8d14986f2500592f3acdb5cc8"
_LEDGER_HEAD = "300fae3bdf77124a7a0ed9e64feb9a65bc84f111"
_TO_HEAD = "c4ae094956d1e420182d7ac2991da24a78300f54"
_TRANSFORMATION_ID = "dnh-rdcp-extension.v1"
_FIXTURE_REL = Path("reports/project-control-plane/fixtures/dnh_crm_fixture")
_SOURCE_MAP_REL = Path("schemas/dnh_extension/rdcp_source_map.dnh.json")
_STATES = {
    "CURRENT",
    "STALE",
    "MISSING",
    "UNREADABLE",
    "UNPARSEABLE",
    "MIXED_SHA",
    "UNKNOWN",
}
_LANE_IDS = {
    "rdcp-proof-pointer",
    "rdcp-source-ledger",
    "rdcp-review-sensor",
    "rdcp-task-orchestrator",
}
_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")

_EXPECTED_SOURCES = {
    "authority": (
        "AGENTS.md",
        "PRESENT",
        "e1bc0b07411aa79872fca9b283b58e289bd542ed",
        "6f8703ec09fc3e593edd5e9b878483fd889ae46977e0780e6b3139a3c8035e8d",
    ),
    "active_packet": (
        "task-packets/ACTIVE.md",
        "PRESENT",
        "fba1b369825cab2bdbdf65dff4713571375a81b7",
        "715e0db54e8068f1373a069c8da7c531762c879839773bf64f6b23620c32a7c3",
    ),
    "rdcp_architecture": (
        "artifacts/rdcp/architecture/ARCHITECTURE_SYNTHESIS.md",
        "PRESENT",
        "3ab261fa87859bf45adaa47d3d39d2cd5841c308",
        "28d91184625d8cad00309aa1caa5c5f84e2db726e5e6e74f5ebebba4fe8ec3e7",
    ),
    "proof_pointer_schema": (
        "schemas/rdcp/proof_pointer.schema.json",
        "PRESENT",
        "43d8799ed4ac4e86d54d6a3ef4d8c9ce61e7c858",
        "2d98cddcbf09843054c0c74b4262279d594bcac55076ecb27330c03ffc92304c",
    ),
    "proof_pointer": (
        "artifacts/rdcp/proof_adapter/PROOF_POINTER.json",
        "PRESENT",
        "1722ff8a8eaec37d9e0834a18fe17e37cfadfb41",
        "7ff6bc6557754ca16ae1c19ee243bb2c9095484369c57e346d2aebfba6b04e5b",
    ),
    "proof_pointer_manifest": (
        "artifacts/rdcp/proof_adapter/EVIDENCE_MANIFEST.json",
        "PRESENT",
        "f62aad0703b3a11ffcaed4a4fbc59a2606da656a",
        "de11d97469a72c32eeefe31f904ec94f25d19cda32599debe373a8191b4894ff",
    ),
    "source_ledger_schema": (
        "schemas/rdcp/source_ledger.schema.json",
        "PRESENT",
        "5465e7d505497dcaeb366dc7a0ae0b69c5ec151f",
        "fa28c9caa94c2b87fecc5bfb12c0a2b1a3a247b3babc165c6ee047825951d79b",
    ),
    "source_ledger": (
        "artifacts/rdcp/source_ledger/SOURCE_LEDGER.json",
        "PRESENT",
        "bf16714a3e5a32660c8b95480952a8e6a0869ecb",
        "c45431bd4feb260ca836794e849481b152cd0c6a86589dc1c42314ba8fbba342",
    ),
    "review_item_schema": (
        "schemas/rdcp/review_sensor/review_item_ledger.schema.json",
        "PRESENT",
        "8d225c762f6a5d0dbadc6ad7c9722cd865431121",
        "44da0c170a8a6864f7901d8e5c9765a7344ed0e79f92862c89b3e9e1af3aa5e9",
    ),
    "thread_dispositions_schema": (
        "schemas/rdcp/review_sensor/thread_dispositions.schema.json",
        "PRESENT",
        "8af5969b2b4f798011e834aa9f47c6ee5e02d3a3",
        "947c02be723fc14ac4ee4fc8cb1f9c50a1dafa92ea57a56923261623d449d0c3",
    ),
    "review_sensor_receipt": (
        "proof/TP-DNH-RDCP-0016/PROOF.json",
        "PRESENT",
        "17516984ff3c75b8c18c1db29acba29874b633f8",
        "ded75b3062aead796cb8a616d27496ba03354e7be3bd2e92dd311ff8dca2ed72",
    ),
    "review_item_output": (
        "artifacts/rdcp/review_sensor/REVIEW_ITEM_LEDGER.json",
        "MISSING",
        None,
        None,
    ),
    "thread_dispositions_output": (
        "artifacts/rdcp/review_sensor/THREAD_DISPOSITIONS.json",
        "MISSING",
        None,
        None,
    ),
    "task_orchestrator_export_schema": (
        "schemas/task_orchestrator/dnh_rdcp_export.schema.json",
        "PRESENT",
        "e808e38673218a8597b3caf359f82944f7da74ef",
        "47e7d4c462ae73054a43bbdd68372f9e16c17171e6ea338e84980af08a904fbd",
    ),
    "task_orchestrator_export": (
        "artifacts/task-orchestrator/dnh-rdcp-export/latest.json",
        "PRESENT",
        "ab5c2a0c76693d373db5217cb5635c1f815fb7c6",
        "f60fecec49b8052681352cf8849cbb040a5cf0875c2c2574bab869ca12fb40cc",
    ),
}


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _read_json(path: Path) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"required verified JSON is unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"required verified JSON must be an object: {path.name}")
    return value, raw


def _validate_schema(
    instance: Mapping[str, object], schema_path: Path, label: str
) -> None:
    schema, _ = _read_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"{label} schema validation failed: {errors[0].message}")


def _safe_path(root: Path, relative: str) -> Path:
    logical = PurePosixPath(relative)
    if logical.is_absolute() or ".." in logical.parts or logical.as_posix() != relative:
        raise ValueError(f"RDCP source path escape is forbidden: {relative}")
    resolved = (root / Path(*logical.parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"RDCP source path escape is forbidden: {relative}") from exc
    return resolved


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_source_map(
    source_map: Mapping[str, object], root: Path
) -> tuple[Mapping[str, object], ...]:
    if (
        source_map.get("schema_version") != "dnh.rdcp_source_map.v1"
        or source_map.get("repository") != _PROJECT_ID
        or source_map.get("pinned_head") != _PINNED_HEAD
    ):
        raise ValueError("dNh RDCP source map identity conflicts")
    if set(_array(source_map.get("freshness_states"), "freshness_states")) != _STATES:
        raise ValueError("dNh RDCP freshness contract is incomplete")

    sources = _object(source_map.get("sources"), "source map sources")
    for role, raw in sources.items():
        source = _object(raw, f"source map role {role}")
        _safe_path(root, _text(source.get("path"), f"source map path {role}"))
        _text(
            source.get("expected_schema_version"),
            f"source map schema version {role}",
        )
    if set(sources) != set(_EXPECTED_SOURCES) - {
        "authority",
        "active_packet",
        "rdcp_architecture",
    }:
        raise ValueError("dNh RDCP source map roles conflict")

    lanes: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for index, raw in enumerate(_array(source_map.get("lanes"), "lanes")):
        lane = _object(raw, f"lanes[{index}]")
        lane_id = _text(lane.get("lane_id"), f"lanes[{index}].lane_id")
        state = _text(lane.get("observed_state"), f"lanes[{index}].observed_state")
        if lane_id in seen or state not in _STATES:
            raise ValueError("dNh RDCP lane map is invalid")
        roles = _array(lane.get("source_roles"), f"lanes[{index}].source_roles")
        if not roles or any(role not in sources for role in roles):
            raise ValueError("dNh RDCP lane references an unknown source role")
        _text(lane.get("reason"), f"lanes[{index}].reason")
        seen.add(lane_id)
        lanes.append(lane)
    if seen != _LANE_IDS:
        raise ValueError("dNh RDCP lane set conflicts")

    task_orchestrator = _object(
        source_map.get("task_orchestrator"), "task_orchestrator"
    )
    if task_orchestrator != {
        "authority": "NONE",
        "is_proof": False,
        "export_mode": "ARTIFACT_ONLY",
    }:
        raise ValueError("Task Orchestrator must remain artifact-only and inert")
    return tuple(lanes)


def _validate_inventory(
    inventory: Mapping[str, object], inventory_bytes: bytes
) -> tuple[dict[str, Mapping[str, object]], str, str]:
    if (
        inventory.get("schema_version") != "dnh.rdcp_source_inventory.v1"
        or inventory.get("repository") != _PROJECT_ID
        or inventory.get("pinned_head") != _PINNED_HEAD
        or inventory.get("collection_mode") != "READ_ONLY_GITHUB_CONTENTS_API"
    ):
        raise ValueError("dNh frozen source inventory identity conflicts")
    fetched_at = _text(inventory.get("fetched_at"), "inventory fetched_at")

    entries: dict[str, Mapping[str, object]] = {}
    for index, raw in enumerate(_array(inventory.get("sources"), "sources")):
        entry = _object(raw, f"sources[{index}]")
        role = _text(entry.get("role"), f"sources[{index}].role")
        if role in entries:
            raise ValueError(f"duplicate frozen source inventory role: {role}")
        entries[role] = entry
    if set(entries) != set(_EXPECTED_SOURCES):
        raise ValueError("dNh frozen source inventory roles conflict")

    prefix = f"https://github.com/{_PROJECT_ID}/blob/{_PINNED_HEAD}/"
    for role, (path, state, blob_sha, sha256) in _EXPECTED_SOURCES.items():
        entry = entries[role]
        if (
            entry.get("path") != path
            or entry.get("state") != state
            or entry.get("blob_sha") != blob_sha
            or entry.get("sha256") != sha256
            or entry.get("url") != prefix + path
            or entry.get("privacy_class") != "PRIVATE_REPOSITORY_METADATA"
            or not entry.get("redaction_notes")
        ):
            raise ValueError(f"dNh frozen source inventory conflicts: {role}")
        if state == "PRESENT" and (
            _SHA1_RE.fullmatch(str(blob_sha)) is None
            or _SHA256_RE.fullmatch(str(sha256)) is None
        ):
            raise ValueError(f"dNh frozen source digest is invalid: {role}")
        if state == "MISSING" and (blob_sha is not None or sha256 is not None):
            raise ValueError(f"missing dNh source is not fail-closed: {role}")

    normalized = _object(inventory.get("normalized_artifacts"), "normalized_artifacts")
    for name in ("proof_pointer", "proof_pointer_manifest"):
        artifact = _object(normalized.get(name), f"normalized {name}")
        content = _object(artifact.get("content"), f"normalized {name} content")
        expected = _text(artifact.get("sha256"), f"normalized {name} sha256")
        if _canonical_sha256(content) != expected:
            raise ValueError(f"normalized {name} bytes do not match their digest")

    pointer = _object(normalized["proof_pointer"], "normalized proof_pointer")
    pointer_content = _object(pointer.get("content"), "proof pointer content")
    proof = _object(pointer_content.get("proof"), "proof pointer proof")
    if (
        pointer_content.get("schema_version") != "1.0.0"
        or proof.get("head_sha") != _PROOF_HEAD
        or proof.get("validation_status") != "PASS"
        or proof.get("freshness_state") != "CURRENT"
    ):
        raise ValueError("normalized proof_pointer semantics conflict")
    manifest = _object(
        normalized["proof_pointer_manifest"], "normalized proof_pointer_manifest"
    )
    manifest_content = _object(manifest.get("content"), "proof manifest content")
    artifacts = _array(manifest_content.get("artifacts"), "proof manifest artifacts")
    pointer_records = [
        _object(item, "proof manifest artifact")
        for item in artifacts
        if _object(item, "proof manifest artifact").get("path")
        == _EXPECTED_SOURCES["proof_pointer"][0]
    ]
    if (
        manifest_content.get("schema_version") != "1.0.0"
        or len(pointer_records) != 1
        or pointer_records[0].get("sha256") != _EXPECTED_SOURCES["proof_pointer"][3]
    ):
        raise ValueError("normalized proof pointer manifest conflicts")

    observations = _object(inventory.get("observations"), "observations")
    proof_observation = _object(observations.get("proof_pointer"), "proof_pointer")
    ledger_observation = _object(observations.get("source_ledger"), "source_ledger")
    review_observation = _object(observations.get("review_sensor"), "review_sensor")
    task_observation = _object(
        observations.get("task_orchestrator"), "task_orchestrator"
    )
    if (
        observations.get("active_packet_id") != "TP-IDLE-0000"
        or proof_observation.get("candidate_head") != _PINNED_HEAD
        or proof_observation.get("proof_head") != _PROOF_HEAD
        or proof_observation.get("current_auditor_identity") != "UNKNOWN"
        or ledger_observation.get("artifact_head") != _LEDGER_HEAD
        or ledger_observation.get("artifact_dirty") is not True
        or ledger_observation.get("ledger_agents_sha256")
        == ledger_observation.get("pinned_agents_sha256")
        or review_observation.get("review_item_output") != "MISSING"
        or review_observation.get("thread_dispositions_output") != "MISSING"
        or review_observation.get("historical_receipt_is_current_audit") is not False
        or task_observation.get("artifact_head") != _TO_HEAD
        or task_observation.get("artifact_dirty") is not True
        or task_observation.get("authority") != "NONE"
        or task_observation.get("is_proof") is not False
        or task_observation.get("export_mode") != "ARTIFACT_ONLY"
        or task_observation.get("forbidden_actions_performed") is not False
    ):
        raise ValueError("dNh source observations disagree with frozen evidence")
    return entries, fetched_at, hashlib.sha256(inventory_bytes).hexdigest()


def _source_ref(
    entry: Mapping[str, object] | None,
    inventory_locator: str,
    inventory_sha256: str,
    fetched_at: str,
) -> SourceRef:
    if entry is None or entry.get("state") == "MISSING":
        return SourceRef(
            locator=inventory_locator,
            sha256=inventory_sha256,
            observed_head=_PINNED_HEAD,
            fetched_at=fetched_at,
        )
    return SourceRef(
        locator=_text(entry.get("url"), "source URL"),
        sha256=_text(entry.get("sha256"), "source SHA-256"),
        observed_head=_PINNED_HEAD,
        fetched_at=fetched_at,
    )


class DnhRdcpExtensionAdapter:
    extension_id = "dnh-crm-rdcp"

    def matches(self, generic_export: Mapping[str, object]) -> bool:
        return generic_export.get("project_id") == _PROJECT_ID

    def enrich(
        self, generic_export: Mapping[str, object], source_root: Path
    ) -> SourceSnapshot:
        if not self.matches(generic_export):
            raise ValueError("generic export does not match the dNh RDCP extension")

        root = source_root.resolve()
        schema_root = root / "schemas/project_control_plane"
        _validate_schema(
            generic_export,
            schema_root / "project_evidence_export.schema.json",
            "generic export",
        )
        repo_state = _object(generic_export.get("repo_state"), "repo_state")
        dirty_state = _object(generic_export.get("dirty_state"), "dirty_state")
        if repo_state.get("head_sha") != _PINNED_HEAD:
            raise ValueError("generic export does not match the pinned dNh head")
        if (
            repo_state.get("root_verified") is not True
            or repo_state.get("worktree_state") != "CLEAN"
            or dirty_state.get("state") != "CLEAN"
            or dirty_state.get("paths") != []
        ):
            raise ValueError("dNh enrichment requires a clean captured source state")

        fixture_root = _safe_path(root, _FIXTURE_REL.as_posix())
        inventory, inventory_bytes = _read_json(fixture_root / "SOURCES.json")
        entries, fetched_at, inventory_sha256 = _validate_inventory(
            inventory, inventory_bytes
        )
        profile, _ = _read_json(fixture_root / "project_profile.json")
        frozen_export, _ = _read_json(fixture_root / "evidence_export.json")
        _validate_schema(
            profile,
            schema_root / "project_profile.schema.json",
            "dNh project profile",
        )
        _validate_schema(
            frozen_export,
            schema_root / "project_evidence_export.schema.json",
            "dNh evidence fixture",
        )
        if (
            profile.get("project_id") != _PROJECT_ID
            or frozen_export.get("project_id") != _PROJECT_ID
            or _object(frozen_export.get("repo_state"), "frozen repo_state").get(
                "head_sha"
            )
            != _PINNED_HEAD
        ):
            raise ValueError("dNh fixture identity conflicts")

        source_map_path = _safe_path(root, _SOURCE_MAP_REL.as_posix())
        source_map, _ = _read_json(source_map_path)
        lane_maps = _validate_source_map(source_map, root)
        inventory_locator = (_FIXTURE_REL / "SOURCES.json").as_posix()

        def ref(role: str | None = None) -> SourceRef:
            return _source_ref(
                entries.get(role) if role else None,
                inventory_locator,
                inventory_sha256,
                fetched_at,
            )

        state_by_lane = {
            _text(lane.get("lane_id"), "lane_id"): _text(
                lane.get("observed_state"), "observed_state"
            )
            for lane in lane_maps
        }

        def claim(
            claim_id: str,
            lane_id: str,
            field: str,
            value: str,
            role: str | None = None,
        ) -> Claim:
            return Claim(
                claim_id=claim_id,
                project_id=_PROJECT_ID,
                lane_id=lane_id,
                field=field,
                value=value,
                materiality="BLOCKING",
                freshness="UNKNOWN",
                transformation_id=_TRANSFORMATION_ID,
                source=ref(role),
            )

        claims = (
            claim(
                "dnh:proof-pointer:status",
                "rdcp-proof-pointer",
                "rdcp_status",
                state_by_lane["rdcp-proof-pointer"],
                "proof_pointer",
            ),
            claim(
                "dnh:proof-pointer:candidate-head",
                "rdcp-proof-pointer",
                "proof_head",
                _PINNED_HEAD,
            ),
            claim(
                "dnh:proof-pointer:proof-head",
                "rdcp-proof-pointer",
                "proof_head",
                _PROOF_HEAD,
                "proof_pointer",
            ),
            claim(
                "dnh:proof-pointer:auditor",
                "rdcp-proof-pointer",
                "auditor_identity",
                "UNKNOWN",
                "review_sensor_receipt",
            ),
            claim(
                "dnh:source-ledger:status",
                "rdcp-source-ledger",
                "rdcp_status",
                state_by_lane["rdcp-source-ledger"],
                "source_ledger",
            ),
            claim(
                "dnh:source-ledger:candidate-head",
                "rdcp-source-ledger",
                "source_head",
                _PINNED_HEAD,
            ),
            claim(
                "dnh:source-ledger:artifact-head",
                "rdcp-source-ledger",
                "source_head",
                _LEDGER_HEAD,
                "source_ledger",
            ),
            claim(
                "dnh:source-ledger:dirty",
                "rdcp-source-ledger",
                "artifact_dirty",
                "true",
                "source_ledger",
            ),
            claim(
                "dnh:review-sensor:status",
                "rdcp-review-sensor",
                "rdcp_status",
                state_by_lane["rdcp-review-sensor"],
                "review_sensor_receipt",
            ),
            claim(
                "dnh:review-sensor:review-item",
                "rdcp-review-sensor",
                "review_item_output",
                "MISSING",
            ),
            claim(
                "dnh:review-sensor:thread-dispositions",
                "rdcp-review-sensor",
                "thread_dispositions_output",
                "MISSING",
            ),
            claim(
                "dnh:review-sensor:auditor",
                "rdcp-review-sensor",
                "auditor_identity",
                "UNKNOWN",
                "review_sensor_receipt",
            ),
            claim(
                "dnh:task-orchestrator:status",
                "rdcp-task-orchestrator",
                "rdcp_status",
                state_by_lane["rdcp-task-orchestrator"],
                "task_orchestrator_export",
            ),
            claim(
                "dnh:task-orchestrator:authority",
                "rdcp-task-orchestrator",
                "authority",
                "NONE",
                "task_orchestrator_export",
            ),
            claim(
                "dnh:task-orchestrator:is-proof",
                "rdcp-task-orchestrator",
                "is_proof",
                "false",
                "task_orchestrator_export",
            ),
            claim(
                "dnh:task-orchestrator:export-mode",
                "rdcp-task-orchestrator",
                "export_mode",
                "ARTIFACT_ONLY",
                "task_orchestrator_export",
            ),
            claim(
                "dnh:task-orchestrator:artifact-head",
                "rdcp-task-orchestrator",
                "artifact_head",
                _TO_HEAD,
                "task_orchestrator_export",
            ),
        )
        lanes = tuple(
            LaneEvidence(
                project_id=_PROJECT_ID,
                lane_id=lane_id,
                candidate_sha=_PINNED_HEAD,
                dependencies=(),
                gate_status="FAIL",
                audit_status="UNKNOWN",
                lifecycle_state=state_by_lane[lane_id],
            )
            for lane_id in sorted(_LANE_IDS, key=lambda value: value.encode("utf-8"))
        )
        return SourceSnapshot(
            schema_version="pcp.repository_planner_source.v1",
            project_id=_PROJECT_ID,
            authority="NONE",
            surface_class="PROJECTION",
            is_proof=False,
            evidence_class="DNH_RDCP_ARTIFACT_PROJECTION",
            observed_head=_PINNED_HEAD,
            fetched_at=fetched_at,
            freshness="UNKNOWN",
            claims=claims,
            lanes=lanes,
        )
