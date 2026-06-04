"""Deterministic local DCP proof-family classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


class ProofFamily(str, Enum):
    DCP_PROOF_POINTER = "DCP_PROOF_POINTER"
    DCP_PROOF_BUNDLE = "DCP_PROOF_BUNDLE"
    DCP_AUDIT_REPORT = "DCP_AUDIT_REPORT"
    DCP_MERGE_READINESS = "DCP_MERGE_READINESS"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class AuthorityLabel(str, Enum):
    OBSERVED = "OBSERVED"
    CLAIMED = "CLAIMED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class LiveWriteStatus(str, Enum):
    NONE = "NONE"
    DETECTED = "DETECTED"
    UNKNOWN = "UNKNOWN"


class LiveWriteReadyStatus(str, Enum):
    UNDEFINED_AND_BLOCKING = "UNDEFINED_AND_BLOCKING"
    OPERATIONAL = "OPERATIONAL"
    UNKNOWN = "UNKNOWN"


class MergeSeamStatus(str, Enum):
    PRESERVED = "PRESERVED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FieldObservation:
    value: Any
    authority_label: AuthorityLabel

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "authority_label": self.authority_label.value,
        }


@dataclass(frozen=True)
class ArtifactInspection:
    path: str
    family: ProofFamily
    authority_label: AuthorityLabel
    freshness: FreshnessStatus
    fields: dict[str, FieldObservation]
    referenced_paths: list[str] = field(default_factory=list)
    raw_references: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    live_write_status: LiveWriteStatus = LiveWriteStatus.NONE
    live_write_ready_status: LiveWriteReadyStatus = (
        LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING
    )
    merge_seam_status: MergeSeamStatus = MergeSeamStatus.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "family": self.family.value,
            "authority_label": self.authority_label.value,
            "freshness": self.freshness.value,
            "fields": {key: value.to_dict() for key, value in self.fields.items()},
            "referenced_paths": list(self.referenced_paths),
            "raw_references": list(self.raw_references),
            "errors": list(self.errors),
            "live_write_status": self.live_write_status.value,
            "live_write_ready_status": self.live_write_ready_status.value,
            "merge_seam_status": self.merge_seam_status.value,
        }


_MINIMUM_FIELDS = (
    "packet_id",
    "branch",
    "base_branch",
    "base_sha",
    "head_sha",
    "commit_sha",
    "changed_files",
    "audit_verdict",
    "pr_url",
    "pr_steward_readiness_result",
    "proof_freshness",
    "live_write_ready_status",
    "merge_seam_status",
    "live_write_status",
    "residual_risks",
)


def classify_artifact(
    artifact_path: str | Path,
    *,
    expected_head_sha: str | None = None,
) -> ArtifactInspection:
    """Classify a local DCP proof artifact without following external references."""

    path = Path(artifact_path)
    fields = _unknown_minimum_fields()
    if not path.exists():
        return ArtifactInspection(
            path=str(path),
            family=ProofFamily.UNKNOWN,
            authority_label=AuthorityLabel.UNKNOWN,
            freshness=FreshnessStatus.UNKNOWN,
            fields=fields,
            errors=[f"missing artifact: {path}"],
            merge_seam_status=MergeSeamStatus.UNKNOWN,
        )

    text = path.read_text(encoding="utf-8")
    live_write_ready_status, live_write_status = _live_write_status(text, None)
    merge_seam_status = _merge_seam_status(text, None)

    if _looks_like_audit_report(path, text):
        audit_fields = dict(fields)
        audit_fields["audit_verdict"] = _observed(
            _extract_markdown_verdict(text) or "UNKNOWN"
        )
        return ArtifactInspection(
            path=str(path),
            family=ProofFamily.DCP_AUDIT_REPORT,
            authority_label=AuthorityLabel.OBSERVED,
            freshness=FreshnessStatus.UNKNOWN,
            fields=audit_fields,
            live_write_status=live_write_status,
            live_write_ready_status=live_write_ready_status,
            merge_seam_status=merge_seam_status,
        )

    if path.suffix.lower() != ".json":
        return ArtifactInspection(
            path=str(path),
            family=ProofFamily.UNKNOWN,
            authority_label=AuthorityLabel.UNKNOWN,
            freshness=FreshnessStatus.UNKNOWN,
            fields=fields,
            errors=["unknown non-JSON proof artifact"],
            live_write_status=live_write_status,
            live_write_ready_status=live_write_ready_status,
            merge_seam_status=merge_seam_status,
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return ArtifactInspection(
            path=str(path),
            family=ProofFamily.CONFLICTING,
            authority_label=AuthorityLabel.CONFLICTING,
            freshness=FreshnessStatus.CONFLICTING,
            fields=fields,
            errors=[f"malformed JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"],
            live_write_status=live_write_status,
            live_write_ready_status=live_write_ready_status,
            merge_seam_status=merge_seam_status,
        )

    if not isinstance(payload, dict):
        return ArtifactInspection(
            path=str(path),
            family=ProofFamily.UNKNOWN,
            authority_label=AuthorityLabel.UNKNOWN,
            freshness=FreshnessStatus.UNKNOWN,
            fields=fields,
            errors=["JSON artifact root is not an object"],
            live_write_status=live_write_status,
            live_write_ready_status=live_write_ready_status,
            merge_seam_status=merge_seam_status,
        )

    live_write_ready_status, live_write_status = _live_write_status(text, payload)
    merge_seam_status = _merge_seam_status(text, payload)
    family = _classify_json_family(path, payload)
    fields = _extract_fields(payload, family)
    raw_references, referenced_paths, reference_errors = _extract_references(payload)
    conflicts = _conflicts(payload)
    freshness = _freshness(payload, expected_head_sha, conflicts)
    errors = list(reference_errors)

    if family is ProofFamily.UNKNOWN:
        errors.append("unknown proof family")

    if live_write_ready_status is LiveWriteReadyStatus.OPERATIONAL:
        errors.append("LIVE_WRITE_READY appears operational")
        family = ProofFamily.CONFLICTING
        freshness = FreshnessStatus.CONFLICTING

    if conflicts:
        errors.extend(conflicts)
        family = ProofFamily.CONFLICTING
        freshness = FreshnessStatus.CONFLICTING

    authority_label = (
        AuthorityLabel.CONFLICTING
        if family is ProofFamily.CONFLICTING
        else AuthorityLabel.UNKNOWN
        if family is ProofFamily.UNKNOWN
        else AuthorityLabel.OBSERVED
    )

    return ArtifactInspection(
        path=str(path),
        family=family,
        authority_label=authority_label,
        freshness=freshness,
        fields=fields,
        referenced_paths=referenced_paths,
        raw_references=raw_references,
        errors=errors,
        live_write_status=live_write_status,
        live_write_ready_status=live_write_ready_status,
        merge_seam_status=merge_seam_status,
    )


def _unknown_minimum_fields() -> dict[str, FieldObservation]:
    return {name: _unknown() for name in _MINIMUM_FIELDS}


def _observed(value: Any) -> FieldObservation:
    return FieldObservation(value=value, authority_label=AuthorityLabel.OBSERVED)


def _unknown() -> FieldObservation:
    return FieldObservation(value="UNKNOWN", authority_label=AuthorityLabel.UNKNOWN)


def _looks_like_audit_report(path: Path, text: str) -> bool:
    return path.name == "AUDIT.md" or bool(
        re.search(r"\bAudit\s+Verdict\s*:", text, flags=re.IGNORECASE)
    )


def _extract_markdown_verdict(text: str) -> str | None:
    match = re.search(
        r"\bAudit\s+Verdict\s*:\s*`?([A-Z_]+)`?",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).upper() if match else None


def _classify_json_family(path: Path, payload: dict[str, Any]) -> ProofFamily:
    signals: set[ProofFamily] = set()

    if (
        payload.get("schema_version") == "dcp-proof-pointer.v0"
        or payload.get("proof_family") == ProofFamily.DCP_PROOF_POINTER.value
        or ("pointer_id" in payload and "source_artifact_ref" in payload)
    ):
        signals.add(ProofFamily.DCP_PROOF_POINTER)

    readiness_values = {"READY", "BLOCKED", "UNKNOWN", "NOT_RUN"}
    status = payload.get("status")
    if (
        path.name == "MERGE_READINESS.json"
        or payload.get("proof_family") == ProofFamily.DCP_MERGE_READINESS.value
        or (
            isinstance(status, str)
            and status in readiness_values
            and ("checks_current" in payload or "proof_fresh" in payload)
        )
    ):
        signals.add(ProofFamily.DCP_MERGE_READINESS)

    if (
        path.name == "PROOF.json"
        or payload.get("proof_family") == ProofFamily.DCP_PROOF_BUNDLE.value
        or (
            ("packet_id" in payload or "tp_id" in payload)
            and any(
                key in payload
                for key in ("commands", "tests", "changed_files", "proof_freshness")
            )
        )
    ):
        signals.add(ProofFamily.DCP_PROOF_BUNDLE)

    if len(signals) > 1:
        return ProofFamily.CONFLICTING
    if not signals:
        return ProofFamily.UNKNOWN
    return next(iter(signals))


def _extract_fields(
    payload: dict[str, Any],
    family: ProofFamily,
) -> dict[str, FieldObservation]:
    fields = _unknown_minimum_fields()
    for name in _MINIMUM_FIELDS:
        if name in payload:
            fields[name] = _observed(payload[name])

    if "tp_id" in payload and "packet_id" not in payload:
        fields["packet_id"] = _observed(payload["tp_id"])

    if family is ProofFamily.DCP_MERGE_READINESS and "status" in payload:
        fields["pr_steward_readiness_result"] = _observed(payload["status"])

    if family is ProofFamily.DCP_PROOF_POINTER:
        for name in ("validation_state", "auditor_verdict", "source_artifact_ref"):
            if name in payload:
                fields[name] = _observed(payload[name])
        source_head_sha = _source_head_sha(payload)
        if source_head_sha:
            fields["head_sha"] = _observed(source_head_sha)

    return fields


def _extract_references(
    payload: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    refs: list[str] = []
    for key in (
        "source_artifact_ref",
        "proof_path",
        "audit_path",
        "merge_readiness_path",
    ):
        value = payload.get(key)
        if isinstance(value, str):
            refs.append(value)

    referenced_paths: list[str] = []
    errors: list[str] = []
    for ref in refs:
        parsed = urlparse(ref)
        if parsed.scheme in {"http", "https"}:
            errors.append(f"remote reference not followed: {ref}")
            continue
        if parsed.scheme:
            errors.append(f"unsupported reference scheme not followed: {ref}")
            continue
        candidate = Path(ref)
        if candidate.is_absolute() or ".." in candidate.parts:
            errors.append(f"unsafe local reference not followed: {ref}")
            continue
        referenced_paths.append(ref)

    return refs, referenced_paths, errors


def _source_head_sha(payload: dict[str, Any]) -> str | None:
    source_head = payload.get("source_head_sha")
    if isinstance(source_head, dict) and isinstance(source_head.get("value"), str):
        return source_head["value"]
    if isinstance(source_head, str):
        return source_head
    return None


def _declared_head_sha(payload: dict[str, Any]) -> str | None:
    if isinstance(payload.get("head_sha"), str):
        return payload["head_sha"]

    freshness = payload.get("proof_freshness")
    if isinstance(freshness, dict) and isinstance(freshness.get("head_sha"), str):
        return freshness["head_sha"]

    return _source_head_sha(payload)


def _conflicts(payload: dict[str, Any]) -> list[str]:
    conflicts: list[str] = []

    head_values: dict[str, str] = {}
    if isinstance(payload.get("head_sha"), str):
        head_values["head_sha"] = payload["head_sha"]

    freshness = payload.get("proof_freshness")
    if isinstance(freshness, dict) and isinstance(freshness.get("head_sha"), str):
        head_values["proof_freshness.head_sha"] = freshness["head_sha"]

    source_head = _source_head_sha(payload)
    if source_head:
        head_values["source_head_sha"] = source_head

    if len(set(head_values.values())) > 1:
        conflicts.append(f"conflicting head_sha fields: {head_values}")

    audit = payload.get("audit")
    if (
        isinstance(audit, dict)
        and isinstance(payload.get("audit_verdict"), str)
        and isinstance(audit.get("auditor_verdict"), str)
        and payload["audit_verdict"] != audit["auditor_verdict"]
    ):
        conflicts.append(
            "conflicting audit_verdict fields: "
            f"audit_verdict={payload['audit_verdict']} "
            f"audit.auditor_verdict={audit['auditor_verdict']}"
        )

    readiness = payload.get("pr_steward_readiness_result")
    status = payload.get("status")
    if (
        isinstance(readiness, str)
        and isinstance(status, str)
        and readiness != status
    ):
        conflicts.append(
            "conflicting readiness fields: "
            f"pr_steward_readiness_result={readiness} status={status}"
        )

    return conflicts


def _freshness(
    payload: dict[str, Any],
    expected_head_sha: str | None,
    conflicts: list[str],
) -> FreshnessStatus:
    if any("head_sha" in conflict for conflict in conflicts):
        return FreshnessStatus.CONFLICTING

    declared_head = _declared_head_sha(payload)
    if expected_head_sha and declared_head:
        return (
            FreshnessStatus.FRESH
            if declared_head == expected_head_sha
            else FreshnessStatus.STALE
        )

    freshness = payload.get("proof_freshness")
    if isinstance(freshness, dict) and freshness.get("stale") is True:
        return FreshnessStatus.STALE

    return FreshnessStatus.UNKNOWN


def _live_write_status(
    text: str,
    payload: dict[str, Any] | None,
) -> tuple[LiveWriteReadyStatus, LiveWriteStatus]:
    if payload:
        live_ready_value = payload.get("LIVE_WRITE_READY")
        if live_ready_value is True or live_ready_value == "OPERATIONAL":
            return LiveWriteReadyStatus.OPERATIONAL, LiveWriteStatus.DETECTED

        if payload.get("live_write_ready_status") == "OPERATIONAL":
            return LiveWriteReadyStatus.OPERATIONAL, LiveWriteStatus.DETECTED

        if payload.get("live_write_status") == "DETECTED":
            return LiveWriteReadyStatus.UNKNOWN, LiveWriteStatus.DETECTED

    operational_patterns = (
        "LIVE_WRITE_READY=1",
        "LIVE_WRITE_READY=true",
        "LIVE_WRITE_READY: OPERATIONAL",
        '"live_write_status": "DETECTED"',
    )
    if any(pattern in text for pattern in operational_patterns):
        return LiveWriteReadyStatus.OPERATIONAL, LiveWriteStatus.DETECTED

    return LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING, LiveWriteStatus.NONE


def _merge_seam_status(
    text: str,
    payload: dict[str, Any] | None,
) -> MergeSeamStatus:
    if payload and payload.get("merge_seam_status") == "PRESERVED":
        return MergeSeamStatus.PRESERVED
    if payload and payload.get("merge_seam_status") == "VIOLATED":
        return MergeSeamStatus.VIOLATED
    if "DCP-RED-MERGE-SEAM-0001" in text:
        return MergeSeamStatus.PRESERVED
    return MergeSeamStatus.UNKNOWN
