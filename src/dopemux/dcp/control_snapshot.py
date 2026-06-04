"""Local-only DCP control snapshot generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from dopemux.dcp.proof_family import (
    AuthorityLabel,
    FreshnessStatus,
    LiveWriteReadyStatus,
    LiveWriteStatus,
    MergeSeamStatus,
    ProofFamily,
    classify_artifact,
)


PACKET_ID = "TP-DCP-0004"
SNAPSHOT_FAMILY = "DCP_CONTROL_SNAPSHOT"
SCHEMA_VERSION = "dcp-control-snapshot.v0"
SNAPSHOT_CONTRACT_VERSION = "0.1.0"
EXPECTED_PACKETS = ("TP-DCP-0001", "TP-DCP-0002", "TP-DCP-0003", "TP-DCP-0004")


class SnapshotBlocked(RuntimeError):
    """Raised when a required local dependency is absent."""


@dataclass(frozen=True)
class _ArtifactPathSet:
    task_packet_path: str | None
    proof_path: str | None
    audit_path: str | None
    merge_readiness_path: str | None


def generate_control_snapshot(
    root: str | Path,
    *,
    generated_at: str | None = None,
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic local DCP control snapshot from repo-local files."""

    root_path = Path(root)
    if not root_path.exists():
        raise SnapshotBlocked(f"snapshot root does not exist: {root_path}")
    if not root_path.is_dir():
        raise SnapshotBlocked(f"snapshot root is not a directory: {root_path}")

    if generated_at is None:
        generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    tp3_paths = _paths_for_packet(root_path, "TP-DCP-0003")
    if not tp3_paths.task_packet_path or not tp3_paths.proof_path:
        raise SnapshotBlocked("TP-DCP-0003 proof-family dispatcher artifacts are missing")

    source_artifacts = _source_artifacts(root_path, expected_head_sha)
    packet_states = [
        _packet_state(root_path, packet_id, expected_head_sha)
        for packet_id in EXPECTED_PACKETS
    ]
    guards = _guard_summary(packet_states)
    readiness = _readiness(packet_states, guards)
    residual_risks = _unique(
        risk
        for state in packet_states
        for risk in state.get("residual_risks", [])
        if isinstance(risk, str)
    )
    stop_conditions = _unique(
        condition
        for state in packet_states
        for condition in state.get("stop_conditions", [])
        if isinstance(condition, str)
    )

    head_sha = expected_head_sha or _read_git_head_sha(root_path)

    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_family": SNAPSHOT_FAMILY,
        "snapshot_contract_version": SNAPSHOT_CONTRACT_VERSION,
        "provenance": {
            "tag": "SYNTHESIS_INVENTED",
            "source_ref": "TP-DCP-0004 local control snapshot generator",
        },
        "validation": {
            "state": "PROVISIONAL_UNVERIFIED_ENFORCEMENT",
            "notes": "Generated snapshot is derived local evidence, not source authority.",
        },
        "snapshot_id": "TP-DCP-0004-local-control-snapshot",
        "project_id": "dopemux-mvp",
        "created_at_utc": generated_at,
        "generated_at": generated_at,
        "source_pack_refs": list(EXPECTED_PACKETS),
        "authority_order_ref": "AGENTS.md",
        "surfaces": {
            "status": "DERIVED_NON_AUTHORITATIVE",
            "note": "Source artifacts remain authoritative; this snapshot is a local derived view.",
        },
        "field_provenance": _field_provenance(),
        "generator": {
            "packet_id": PACKET_ID,
            "implementation": "local",
            "live_adapters_used": False,
            "external_writes_used": False,
        },
        "repo": {
            "base_branch": "main",
            "base_sha": head_sha,
            "head_sha": head_sha,
            "worktree": str(root_path),
        },
        "source_artifacts": source_artifacts,
        "packet_states": packet_states,
        "guards": guards,
        "endpoint_certainty": {
            "task_orchestrator": "PROJECTION_ONLY",
            "conport": "UNKNOWN",
            "dope_memory": "UNKNOWN",
            "dope_context": "UNKNOWN",
            "dopecon_bridge": "PROXY_ONLY",
        },
        "readiness": readiness,
        "authority_label_summary": {
            "snapshot": AuthorityLabel.INFERRED.value,
            "source_artifacts": _dominant_authority(source_artifacts),
            "packet_states": _dominant_state(packet_states),
        },
        "residual_risks": residual_risks,
        "stop_conditions": stop_conditions,
        "stop_condition_summary": list(stop_conditions),
        "derived": True,
        "authoritative": False,
    }


def write_control_snapshot(
    root: str | Path,
    output_path: str | Path,
    *,
    generated_at: str | None = None,
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    """Generate and write a snapshot only when explicitly requested."""

    snapshot = generate_control_snapshot(
        root,
        generated_at=generated_at,
        expected_head_sha=expected_head_sha,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot


def _paths_for_packet(root: Path, packet_id: str) -> _ArtifactPathSet:
    task_packet_path = _first_existing(
        root,
        (
            f"task-packets/{packet_id}.md",
            f"task-packets/{packet_id}.json",
        ),
    )
    proof_path = _first_existing(root, (f"proof/{packet_id}/PROOF.json",))
    audit_path = _first_existing(root, (f"proof/{packet_id}/AUDIT.md",))
    merge_readiness_path = _first_existing(
        root,
        (f"proof/{packet_id}/MERGE_READINESS.json",),
    )
    return _ArtifactPathSet(
        task_packet_path=task_packet_path,
        proof_path=proof_path,
        audit_path=audit_path,
        merge_readiness_path=merge_readiness_path,
    )


def _first_existing(root: Path, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if (root / candidate).exists():
            return candidate
    return None


def _source_artifacts(root: Path, expected_head_sha: str | None) -> list[dict[str, Any]]:
    paths: set[str] = set()
    for packet_id in EXPECTED_PACKETS:
        packet_paths = _paths_for_packet(root, packet_id)
        paths.update(
            path
            for path in (
                packet_paths.task_packet_path,
                packet_paths.proof_path,
                packet_paths.audit_path,
                packet_paths.merge_readiness_path,
            )
            if path
        )

    for pattern in (
        "schemas/dcp/*",
        "tests/dcp/*",
    ):
        paths.update(
            str(path.relative_to(root))
            for path in sorted(root.glob(pattern))
            if path.is_file()
        )

    paths.add("schemas/dcp/dcp_control_snapshot.schema.json")

    return [
        _source_artifact(root, path, expected_head_sha)
        for path in sorted(paths)
    ]


def _source_artifact(
    root: Path,
    relative_path: str,
    expected_head_sha: str | None,
) -> dict[str, Any]:
    path = root / relative_path
    exists = path.exists()
    family = _family_for_path(relative_path)
    notes: list[str] = []
    authority_label = AuthorityLabel.OBSERVED.value if exists else AuthorityLabel.UNKNOWN.value
    freshness = FreshnessStatus.UNKNOWN.value

    if exists and path.name in {"PROOF.json", "MERGE_READINESS.json", "AUDIT.md"}:
        inspection = classify_artifact(path, expected_head_sha=expected_head_sha)
        family = inspection.family.value
        authority_label = inspection.authority_label.value
        freshness = inspection.freshness.value
        notes.extend(inspection.errors)
        if path.name == "PROOF.json" and _explicitly_non_operational(path):
            notes = [
                note
                for note in notes
                if note
                not in {
                    "LIVE_WRITE_READY appears operational",
                    "live_write_status appears detected",
                }
            ]
            if family == ProofFamily.CONFLICTING.value and not notes:
                family = ProofFamily.DCP_PROOF_BUNDLE.value
                authority_label = AuthorityLabel.OBSERVED.value
                freshness = _freshness_from_payload(path, expected_head_sha).value

    if relative_path == "schemas/dcp/dcp_control_snapshot.schema.json":
        notes.append("existing repo schema convention")

    return {
        "path": relative_path,
        "family": family,
        "exists": exists,
        "authority_label": authority_label,
        "freshness": freshness,
        "notes": notes,
    }


def _packet_state(
    root: Path,
    packet_id: str,
    expected_head_sha: str | None,
) -> dict[str, Any]:
    paths = _paths_for_packet(root, packet_id)
    proof = (
        classify_artifact(root / paths.proof_path, expected_head_sha=expected_head_sha)
        if paths.proof_path
        else None
    )
    audit = (
        classify_artifact(root / paths.audit_path, expected_head_sha=expected_head_sha)
        if paths.audit_path
        else None
    )
    readiness = (
        classify_artifact(root / paths.merge_readiness_path, expected_head_sha=expected_head_sha)
        if paths.merge_readiness_path
        else None
    )

    state = AuthorityLabel.UNKNOWN.value
    freshness = FreshnessStatus.UNKNOWN.value
    residual_risks: list[str] = []
    stop_conditions: list[str] = []
    errors: list[str] = []

    if paths.task_packet_path and proof:
        state = AuthorityLabel.OBSERVED.value
        freshness = proof.freshness.value
        proof_packet_id = proof.fields.get("packet_id")
        if proof_packet_id and proof_packet_id.value not in {"UNKNOWN", packet_id}:
            state = AuthorityLabel.CONFLICTING.value
            freshness = FreshnessStatus.CONFLICTING.value
            errors.append(
                f"proof packet_id {proof_packet_id.value!r} does not match {packet_id!r}"
            )
    elif proof:
        state = AuthorityLabel.CLAIMED.value

    for artifact in (proof, audit, readiness):
        if not artifact:
            continue
        artifact_errors = list(artifact.errors)
        artifact_family = artifact.family
        artifact_freshness = artifact.freshness
        if (
            paths.proof_path
            and artifact is proof
            and _explicitly_non_operational(root / paths.proof_path)
        ):
            artifact_errors = [
                error
                for error in artifact_errors
                if error
                not in {
                    "LIVE_WRITE_READY appears operational",
                    "live_write_status appears detected",
                }
            ]
            if artifact_family is ProofFamily.CONFLICTING and not artifact_errors:
                artifact_family = ProofFamily.DCP_PROOF_BUNDLE
                artifact_freshness = _freshness_from_payload(
                    root / paths.proof_path,
                    expected_head_sha,
                )

        errors.extend(artifact_errors)
        if artifact_family is ProofFamily.CONFLICTING:
            state = AuthorityLabel.CONFLICTING.value
            freshness = FreshnessStatus.CONFLICTING.value
        elif artifact_freshness is FreshnessStatus.STALE and state != AuthorityLabel.CONFLICTING.value:
            freshness = FreshnessStatus.STALE.value

    if proof:
        residual_risks = _field_list(proof.fields.get("residual_risks", None))
        stop_conditions = _proof_list(root / paths.proof_path, "stop_conditions")

    return {
        "packet_id": packet_id,
        "task_packet_path": paths.task_packet_path,
        "proof_path": paths.proof_path,
        "audit_path": paths.audit_path,
        "merge_readiness_path": paths.merge_readiness_path,
        "state": state,
        "freshness": freshness,
        "residual_risks": residual_risks,
        "stop_conditions": stop_conditions,
        "errors": errors,
    }


def _field_list(observation: Any) -> list[str]:
    value = getattr(observation, "value", None)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _proof_list(path: Path, key: str) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    value = payload.get(key)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _explicitly_non_operational(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("live_write_ready_status") == LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING.value
        and payload.get("live_write_status") == LiveWriteStatus.NONE.value
        and payload.get("LIVE_WRITE_READY") is None
    )


def _freshness_from_payload(path: Path, expected_head_sha: str | None) -> FreshnessStatus:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return FreshnessStatus.UNKNOWN
    if not isinstance(payload, dict):
        return FreshnessStatus.UNKNOWN
    head_sha = payload.get("head_sha")
    freshness = payload.get("proof_freshness")
    if isinstance(freshness, dict) and isinstance(freshness.get("head_sha"), str):
        head_sha = freshness["head_sha"]
    if expected_head_sha and isinstance(head_sha, str):
        return FreshnessStatus.FRESH if head_sha == expected_head_sha else FreshnessStatus.STALE
    if isinstance(freshness, dict) and freshness.get("stale") is True:
        return FreshnessStatus.STALE
    return FreshnessStatus.UNKNOWN


def _guard_summary(packet_states: list[dict[str, Any]]) -> dict[str, str]:
    live_ready = LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING
    live_write = LiveWriteStatus.NONE
    merge_seam = MergeSeamStatus.UNKNOWN
    dopetask_execution = LiveWriteStatus.NONE
    external_write = LiveWriteStatus.NONE

    for state in packet_states:
        for path_key in ("proof_path", "audit_path", "merge_readiness_path"):
            path = state.get(path_key)
            if not path:
                continue
            artifact_root = state.get("_root")
            _ = artifact_root

    # Re-read through state errors and freshness only; live-write details are
    # derived during source artifact inspection in a stable second pass.
    for state in packet_states:
        if any("LIVE_WRITE_READY appears operational" in error for error in state["errors"]):
            live_ready = LiveWriteReadyStatus.OPERATIONAL
            live_write = LiveWriteStatus.DETECTED
        if any("live_write_status appears detected" in error for error in state["errors"]):
            live_write = LiveWriteStatus.DETECTED
            if live_ready is not LiveWriteReadyStatus.OPERATIONAL:
                live_ready = LiveWriteReadyStatus.UNKNOWN
        if any("merge_seam_status" in error for error in state["errors"]):
            merge_seam = MergeSeamStatus.VIOLATED

    if merge_seam is MergeSeamStatus.UNKNOWN and not any(
        state["state"] == AuthorityLabel.CONFLICTING.value for state in packet_states
    ):
        merge_seam = MergeSeamStatus.PRESERVED

    return {
        "live_write_ready_status": live_ready.value,
        "live_write_status": live_write.value,
        "merge_seam_status": merge_seam.value,
        "dopetask_execution_status": dopetask_execution.value,
        "external_write_status": external_write.value,
    }


def _readiness(
    packet_states: list[dict[str, Any]],
    guards: dict[str, str],
) -> dict[str, Any]:
    blocking: list[str] = []
    warnings: list[str] = []
    status = "READY"

    if guards["live_write_ready_status"] == LiveWriteReadyStatus.OPERATIONAL.value:
        blocking.append("live write readiness detected")
    if guards["live_write_status"] == LiveWriteStatus.DETECTED.value:
        blocking.append("live write path detected")
    if guards["merge_seam_status"] == MergeSeamStatus.VIOLATED.value:
        blocking.append("merge seam violation detected")

    for state in packet_states:
        if state["packet_id"] == PACKET_ID and state["state"] == AuthorityLabel.UNKNOWN.value:
            warnings.append("TP-DCP-0004 proof not present during snapshot generation")
            continue
        live_write_conflict = any(
            error in {
                "LIVE_WRITE_READY appears operational",
                "live_write_status appears detected",
            }
            for error in state["errors"]
        )
        if state["state"] == AuthorityLabel.CONFLICTING.value and not live_write_conflict:
            status = "CONFLICTING"
        elif state["freshness"] == FreshnessStatus.STALE.value:
            blocking.append("stale proof artifact detected")

    if blocking and status != "CONFLICTING":
        status = "BLOCKED"
    if status == "READY" and warnings:
        recommended = "Generate TP-DCP-0004 proof and audit artifacts."
    elif status == "READY":
        recommended = "Proceed with local inspection."
    else:
        recommended = "Resolve blocking local evidence before downstream use."

    return {
        "snapshot_status": status,
        "blocking_reasons": _unique(blocking),
        "warnings": _unique(warnings),
        "recommended_next_action": recommended,
    }


def _family_for_path(path: str) -> str:
    if path.startswith("task-packets/"):
        return "TASK_PACKET"
    if path.startswith("schemas/dcp/"):
        return "DCP_SCHEMA"
    if path.startswith("tests/dcp/"):
        return "DCP_TEST"
    return ProofFamily.UNKNOWN.value


def _dominant_authority(items: list[dict[str, Any]]) -> str:
    labels = {item["authority_label"] for item in items}
    if AuthorityLabel.CONFLICTING.value in labels:
        return AuthorityLabel.CONFLICTING.value
    if AuthorityLabel.UNKNOWN.value in labels:
        return AuthorityLabel.UNKNOWN.value
    return AuthorityLabel.OBSERVED.value


def _dominant_state(states: list[dict[str, Any]]) -> str:
    labels = {state["state"] for state in states}
    if AuthorityLabel.CONFLICTING.value in labels:
        return AuthorityLabel.CONFLICTING.value
    if AuthorityLabel.UNKNOWN.value in labels:
        return AuthorityLabel.UNKNOWN.value
    if AuthorityLabel.CLAIMED.value in labels:
        return AuthorityLabel.CLAIMED.value
    return AuthorityLabel.OBSERVED.value


def _unique(values: Any) -> list[str]:
    return sorted(set(values))


def _read_git_head_sha(root: Path) -> str | None:
    git_path = root / ".git"
    if not git_path.exists():
        return None

    git_dir = git_path
    if git_path.is_file():
        text = git_path.read_text(encoding="utf-8").strip()
        prefix = "gitdir: "
        if not text.startswith(prefix):
            return None
        git_dir = (root / text[len(prefix) :]).resolve()

    head_path = git_dir / "HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref_path = git_dir / head[len("ref: ") :]
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()
        packed_refs = git_dir / "packed-refs"
        if packed_refs.exists():
            ref_name = head[len("ref: ") :]
            for line in packed_refs.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#") or line.startswith("^"):
                    continue
                sha, _, ref = line.partition(" ")
                if ref == ref_name:
                    return sha
        return None
    return head or None


def _field_provenance() -> dict[str, str]:
    fields = (
        "snapshot_id",
        "project_id",
        "created_at_utc",
        "generated_at",
        "source_pack_refs",
        "authority_order_ref",
        "surfaces",
        "snapshot_family",
        "snapshot_contract_version",
        "generator",
        "repo",
        "source_artifacts",
        "packet_states",
        "guards",
        "endpoint_certainty",
        "readiness",
        "authority_label_summary",
        "residual_risks",
        "stop_conditions",
        "stop_condition_summary",
        "derived",
        "authoritative",
    )
    return {field: AuthorityLabel.INFERRED.value for field in fields}
