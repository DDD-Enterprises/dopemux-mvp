"""Read-only automation tier and approval policy registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import yaml

from dopemux.orchestrator.validation.report import (
    ValidationIssue,
    ValidationReport,
    issue,
    path_text,
    sort_issues,
)


REQUIRED_TIERS = ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "TX", "TU"]
WRITE_MODES = {"write", "destructive"}
T4_PLUS = {"T4", "T5", "T6"}
REFUSAL_TIERS = {"TX", "TU"}
DEFAULT_POLICY_PATH = Path("config/orchestrator/approval_policy.yaml")
POLICY_AUTHORITY = "task-orchestrator-operator-integration-authority"


@dataclass(frozen=True)
class AutomationTier:
    id: str
    name: str
    mode: str
    automatic_allowed: bool
    approval_required: bool
    receipt_required: bool
    decision: str
    description: str = ""
    typed_confirmation_required: bool = False

    @classmethod
    def from_mapping(cls, tier_id: str, payload: Mapping[str, Any]) -> "AutomationTier":
        return cls(
            id=tier_id,
            name=str(payload.get("name") or tier_id),
            mode=str(payload.get("mode") or "unknown"),
            automatic_allowed=bool(payload.get("automatic_allowed", False)),
            approval_required=bool(payload.get("approval_required", False)),
            receipt_required=bool(payload.get("receipt_required", False)),
            typed_confirmation_required=bool(
                payload.get("typed_confirmation_required", False)
            ),
            decision=str(payload.get("decision") or "refuse"),
            description=str(payload.get("description") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "mode": self.mode,
            "automatic_allowed": self.automatic_allowed,
            "approval_required": self.approval_required,
            "receipt_required": self.receipt_required,
            "decision": self.decision,
            "description": self.description,
        }
        if self.typed_confirmation_required:
            data["typed_confirmation_required"] = True
        return data


@dataclass(frozen=True)
class CapabilityPolicy:
    capability_id: str
    title: str
    tier: str
    mode: str
    canonical_writer: str
    automatic_allowed: bool
    approval_required: bool
    receipt_required: bool
    decision: str
    typed_confirmation_required: bool = False
    bridge_mediated: bool = False
    upstream_canonical_writer: str = ""
    mirror_writer: str = ""

    @classmethod
    def from_mapping(
        cls, capability_id: str, payload: Mapping[str, Any]
    ) -> "CapabilityPolicy":
        return cls(
            capability_id=capability_id,
            title=str(payload.get("title") or capability_id),
            tier=str(payload.get("tier") or "TU"),
            mode=str(payload.get("mode") or "unknown"),
            canonical_writer=str(payload.get("canonical_writer") or ""),
            automatic_allowed=bool(payload.get("automatic_allowed", False)),
            approval_required=bool(payload.get("approval_required", False)),
            receipt_required=bool(payload.get("receipt_required", False)),
            typed_confirmation_required=bool(
                payload.get("typed_confirmation_required", False)
            ),
            bridge_mediated=bool(payload.get("bridge_mediated", False)),
            upstream_canonical_writer=str(
                payload.get("upstream_canonical_writer") or ""
            ),
            mirror_writer=str(payload.get("mirror_writer") or ""),
            decision=str(payload.get("decision") or "refuse"),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "title": self.title,
            "tier": self.tier,
            "mode": self.mode,
            "canonical_writer": self.canonical_writer,
            "automatic_allowed": self.automatic_allowed,
            "approval_required": self.approval_required,
            "receipt_required": self.receipt_required,
            "decision": self.decision,
        }
        if self.typed_confirmation_required:
            data["typed_confirmation_required"] = True
        if self.bridge_mediated:
            data["bridge_mediated"] = True
        if self.upstream_canonical_writer:
            data["upstream_canonical_writer"] = self.upstream_canonical_writer
        if self.mirror_writer:
            data["mirror_writer"] = self.mirror_writer
        return data


@dataclass(frozen=True)
class CapabilityDecision:
    capability_id: str
    tier: str
    mode: str
    canonical_writer: str
    automatic_allowed: bool
    approval_required: bool
    receipt_required: bool
    decision: str
    allowed: bool
    reason: str
    typed_confirmation_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "tier": self.tier,
            "mode": self.mode,
            "canonical_writer": self.canonical_writer,
            "automatic_allowed": self.automatic_allowed,
            "approval_required": self.approval_required,
            "receipt_required": self.receipt_required,
            "typed_confirmation_required": self.typed_confirmation_required,
            "decision": self.decision,
            "allowed": self.allowed,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ApprovalPolicy:
    schema_version: str
    policy_id: str
    authority: str
    updated: str
    defaults: Dict[str, Any]
    tiers: Dict[str, AutomationTier]
    capabilities: Dict[str, CapabilityPolicy]
    source_path: str

    @classmethod
    def from_mapping(
        cls, payload: Mapping[str, Any], *, source_path: str
    ) -> "ApprovalPolicy":
        tiers_payload = payload.get("tiers") or {}
        caps_payload = payload.get("capabilities") or {}
        tiers = {
            tier_id: AutomationTier.from_mapping(tier_id, data)
            for tier_id, data in tiers_payload.items()
            if isinstance(data, Mapping)
        }
        capabilities = {
            cap_id: CapabilityPolicy.from_mapping(cap_id, data)
            for cap_id, data in caps_payload.items()
            if isinstance(data, Mapping)
        }
        return cls(
            schema_version=str(payload.get("schema_version") or ""),
            policy_id=str(payload.get("id") or ""),
            authority=str(payload.get("authority") or ""),
            updated=str(payload.get("updated") or ""),
            defaults=dict(payload.get("defaults") or {}),
            tiers=tiers,
            capabilities=capabilities,
            source_path=source_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.policy_id,
            "authority": self.authority,
            "updated": self.updated,
            "defaults": dict(self.defaults),
            "tiers": {key: tier.to_dict() for key, tier in self.tiers.items()},
            "capabilities": {
                key: capability.to_dict()
                for key, capability in self.capabilities.items()
            },
        }


def default_policy_path() -> Path:
    cwd_candidate = Path.cwd() / DEFAULT_POLICY_PATH
    if cwd_candidate.exists():
        return DEFAULT_POLICY_PATH

    repo_candidate = Path(__file__).resolve().parents[3] / DEFAULT_POLICY_PATH
    if repo_candidate.exists():
        return repo_candidate
    return DEFAULT_POLICY_PATH


def load_approval_policy(path: str | Path | None = None) -> ApprovalPolicy:
    policy_path = Path(path) if path is not None else default_policy_path()
    if not policy_path.exists():
        # Fail closed with empty policy if file is missing
        return ApprovalPolicy.from_mapping(
            {
                "schema_version": 1,
                "id": "missing-policy-fallback",
                "authority": "system",
                "updated": "1970-01-01T00:00:00Z",
                "defaults": {
                    "unregistered_decision": "refuse",
                    "unknown_capability_tier": "TU",
                },
                "tiers": {},
                "capabilities": {},
            },
            source_path=path_text(policy_path)
        )
    payload = _load_yaml_mapping(policy_path)
    return ApprovalPolicy.from_mapping(payload, source_path=path_text(policy_path))


def classify_capability(
    capability_id: str,
    policy: Optional[ApprovalPolicy] = None,
) -> CapabilityDecision:
    active_policy = policy or load_approval_policy()
    capability = active_policy.capabilities.get(capability_id)
    if capability is None:
        return CapabilityDecision(
            capability_id=capability_id,
            tier=str(active_policy.defaults.get("unknown_capability_tier") or "TU"),
            mode="unknown",
            canonical_writer="",
            automatic_allowed=False,
            approval_required=False,
            receipt_required=True,
            typed_confirmation_required=False,
            decision=str(active_policy.defaults.get("unregistered_decision") or "refuse"),
            allowed=False,
            reason=f"Capability {capability_id} is not registered; fail closed.",
        )

    automatic_allowed = capability.automatic_allowed
    if capability.tier in {"T0", "T1"} and capability.mode in {"write", "destructive"}:
        automatic_allowed = False

    allowed = (
        capability.decision == "allow"
        and automatic_allowed
        and not capability.approval_required
        and capability.tier in {"T0", "T1"}
    )
    reason = (
        "registered automatic capability"
        if allowed
        else "registered capability requires gate or refuses by policy"
    )
    return CapabilityDecision(
        capability_id=capability.capability_id,
        tier=capability.tier,
        mode=capability.mode,
        canonical_writer=capability.canonical_writer,
        automatic_allowed=automatic_allowed,
        approval_required=capability.approval_required,
        receipt_required=capability.receipt_required,
        typed_confirmation_required=capability.typed_confirmation_required,
        decision=capability.decision,
        allowed=allowed,
        reason=reason,
    )


def validate_policy_file(
    policy_path: str | Path | None = None,
) -> ValidationReport:
    path = Path(policy_path) if policy_path is not None else default_policy_path()
    errors: list[ValidationIssue] = []
    payload: Dict[str, Any] | None = None

    if not path.exists():
        errors.append(
            issue(
                "POLICY_PATH_MISSING",
                f"Approval policy path is missing: {path_text(path)}",
            )
        )
    else:
        try:
            payload = _load_yaml_mapping(path)
        except ValueError as exc:
            errors.append(issue("POLICY_YAML_INVALID", str(exc)))

    if payload is not None:
        errors.extend(_validate_policy_payload(payload))

    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    details: Dict[str, Any] = {
        "authority_boundary": "read_only_policy_registry_validation_only",
        "required_tiers": REQUIRED_TIERS,
    }
    if payload:
        tiers = payload.get("tiers") or {}
        caps = payload.get("capabilities") or {}
        details.update(
            {
                "tier_count": len(tiers) if isinstance(tiers, Mapping) else 0,
                "capability_count": len(caps) if isinstance(caps, Mapping) else 0,
            }
        )

    return ValidationReport(
        kind="approval_policy",
        path=path_text(path),
        authority=POLICY_AUTHORITY,
        status=status,
        valid=status == "PASS",
        errors=sorted_errors,
        details=details,
        exit_code=0 if status == "PASS" else 2,
    )


def _load_yaml_mapping(path: Path) -> Dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Approval policy YAML is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Approval policy must be a YAML mapping.")
    return payload


def _validate_policy_payload(payload: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    errors: list[ValidationIssue] = []
    tiers = payload.get("tiers")
    capabilities = payload.get("capabilities")

    if not isinstance(tiers, Mapping):
        errors.append(issue("POLICY_TIERS_MISSING", "Policy tiers must be a mapping."))
        tiers = {}
    if not isinstance(capabilities, Mapping):
        errors.append(
            issue(
                "POLICY_CAPABILITIES_MISSING",
                "Policy capabilities must be a mapping.",
            )
        )
        capabilities = {}

    tier_keys = list(tiers.keys())
    if tier_keys != REQUIRED_TIERS:
        errors.append(
            issue(
                "POLICY_REQUIRED_TIERS_MISMATCH",
                f"Policy tiers must be declared in order: {', '.join(REQUIRED_TIERS)}.",
                path="/tiers",
            )
        )

    for tier_id, tier_payload in tiers.items():
        if not isinstance(tier_payload, Mapping):
            errors.append(
                issue(
                    "POLICY_TIER_INVALID",
                    "Tier entry must be a mapping.",
                    path=f"/tiers/{tier_id}",
                )
            )
            continue
        tier = AutomationTier.from_mapping(str(tier_id), tier_payload)
        if tier.automatic_allowed and tier.id not in {"T0", "T1"}:
            errors.append(
                issue(
                    "POLICY_AUTOMATION_SCOPE_VIOLATION",
                    "Only T0/T1 tiers may allow automatic invocation.",
                    path=f"/tiers/{tier_id}/automatic_allowed",
                )
            )
        if tier.id in T4_PLUS:
            _require_t4_gate(errors, f"/tiers/{tier_id}", tier)
        if tier.id in REFUSAL_TIERS and tier.decision != "refuse":
            errors.append(
                issue(
                    "POLICY_UNRESOLVED_REFUSE_REQUIRED",
                    "TX/TU tiers must refuse by default.",
                    path=f"/tiers/{tier_id}/decision",
                )
            )

    for capability_id, capability_payload in capabilities.items():
        if not isinstance(capability_payload, Mapping):
            errors.append(
                issue(
                    "POLICY_CAPABILITY_INVALID",
                    "Capability entry must be a mapping.",
                    path=f"/capabilities/{capability_id}",
                )
            )
            continue
        capability = CapabilityPolicy.from_mapping(
            str(capability_id), capability_payload
        )
        cap_path = f"/capabilities/{capability_id}"
        if capability.tier not in REQUIRED_TIERS:
            errors.append(
                issue(
                    "POLICY_UNKNOWN_TIER",
                    f"Capability references unknown tier: {capability.tier}",
                    path=f"{cap_path}/tier",
                )
            )
            continue
        if capability.automatic_allowed and capability.tier not in {"T0", "T1"}:
            errors.append(
                issue(
                    "POLICY_AUTOMATION_SCOPE_VIOLATION",
                    "Only T0/T1 capabilities may allow automatic invocation.",
                    path=f"{cap_path}/automatic_allowed",
                )
            )
        if capability.tier in T4_PLUS:
            _require_t4_gate(errors, cap_path, capability)
        if capability.mode in WRITE_MODES and not capability.canonical_writer:
            errors.append(
                issue(
                    "POLICY_WRITE_CANONICAL_WRITER_REQUIRED",
                    "Write/destructive capabilities must name the canonical writer.",
                    path=f"{cap_path}/canonical_writer",
                )
            )
        if (
            capability.bridge_mediated
            and capability.mode in WRITE_MODES
            and not capability.upstream_canonical_writer
        ):
            errors.append(
                issue(
                    "POLICY_BRIDGE_WRITER_REQUIRED",
                    "Bridge-mediated writes must name the upstream canonical writer.",
                    path=f"{cap_path}/upstream_canonical_writer",
                )
            )
        if capability.tier in REFUSAL_TIERS and capability.decision not in {
            "refuse",
            "block",
        }:
            errors.append(
                issue(
                    "POLICY_UNRESOLVED_REFUSE_REQUIRED",
                    "TX/TU capabilities must refuse or block by default.",
                    path=f"{cap_path}/decision",
                )
            )

    return errors


def _require_t4_gate(
    errors: list[ValidationIssue],
    path: str,
    item: AutomationTier | CapabilityPolicy,
) -> None:
    if not item.approval_required:
        errors.append(
            issue(
                "POLICY_T4_APPROVAL_REQUIRED",
                "T4 and higher entries must require operator approval.",
                path=f"{path}/approval_required",
            )
        )
    if not item.receipt_required:
        errors.append(
            issue(
                "POLICY_T4_RECEIPT_REQUIRED",
                "T4 and higher entries must require receipts.",
                path=f"{path}/receipt_required",
            )
        )
