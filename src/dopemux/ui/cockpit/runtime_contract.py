"""Local-only Cockpit runtime primitives for the accepted IA package contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5


PACKAGE_PACKET_ID = "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA"
RUNTIME_PACKET_ID = "TP-DMX-COCKPIT-RUNTIME-RENDER-001"
SETTINGS_RUNTIME_PACKET_ID = "TP-DMX-COCKPIT-SETTINGS-RUNTIME-001"
UNKNOWN_DRIFT_PACKET_ID = "TP-DMX-COCKPIT-UNKNOWN-DRIFT-001"
SETTINGS_ADMIN_SOURCE_ARTIFACT = "SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md"
UNKNOWN_DRIFT_SOURCE_ARTIFACT = "UNKNOWN_DRIFT_PACKAGE_HANDOFF.md"

TOP_LEVEL_MODES: tuple[str, ...] = (
    "PM",
    "Implementer",
    "Overview",
    "Services",
    "Events",
)

GLOBAL_SURFACES: tuple[str, ...] = (
    "Command Palette",
    "Settings/Admin/Runtime",
    "Safe Actions / Proof Gate",
    "Unknown / Drift Queue",
)

UNKNOWN_DRIFT_REASON_CODES: tuple[str, ...] = (
    "UNKNOWN",
    "AUTHORITY_CONFLICT",
    "PARAM_UNRESOLVED",
    "CWD_UNRESOLVED",
    "PROOF_REQUIREMENT_UNKNOWN",
    "ROLLBACK_UNKNOWN",
    "SIDE_EFFECTS_UNKNOWN",
    "REMOTE_MUTATION_POLICY_MISSING",
    "TP_GATE_ABSENT",
    "AUTHORITY_DRIFT_MID_FLOW",
    "CLASS_DRIFT_MID_FLOW",
    "UNSAFE_SOURCE_SURFACE",
    "STALE_PROOF_GATE",
    "INDEX_DRIFT",
    "STALE_HANDOFF",
    "DEFINED_NOT_REGISTERED",
    "OPTIONAL_IMPORT_UNKNOWN",
    "DEPRECATED_BLOCKED",
    "MISSING_REQUIRED_FIELD",
    "UNKNOWN_CANONICAL_WRITER",
    "UNKNOWN_AUTHORITY_DOMAIN",
    "SETTINGS_ROW_TIER_UNKNOWN",
)

ALLOWED_UNKNOWN_DRIFT_AFFORDANCES: tuple[str, ...] = (
    "Inspect",
    "CopyEvidence",
    "CopyRecommendedPacketPrompt",
    "ShowBlockedReason",
    "ShowUpstreamArtifact",
)

SAFE_ACTION_TIERS: tuple[str, ...] = (
    "T0",
    "T0i",
    "T1",
    "T2",
    "T3",
    "T4",
    "T5",
    "T6",
    "TX",
    "TU",
)

EXECUTABLE_TIERS: frozenset[str] = frozenset(("T0i", "T1", "T2", "T3", "T5", "T6"))
CONFIRMABLE_TIERS: frozenset[str] = frozenset(("T1", "T2", "T3", "T5", "T6"))
NON_CONFIRM_TIERS: frozenset[str] = frozenset(("T0", "T0i"))
BLOCKED_TIERS: frozenset[str] = frozenset(("TX",))
UNKNOWN_TIERS: frozenset[str] = frozenset(("TU",))
SETTINGS_ADMIN_GATE_REQUIRED_TIERS: frozenset[str] = frozenset(
    ("T0i", "T1", "T2", "T3", "T4", "T5", "T6")
)

SETTINGS_ADMIN_FLOW_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "name": "Routing / Model Provider",
        "authority_owner": "routing/model-provider support (LiteLLM/CCR)",
        "primary_tiers": ("T2",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + diff acknowledgment",
        "typical_proof": "CONFIG_DIFF_OR_STATUS",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Profile management",
        "authority_owner": "dopemux operator control",
        "primary_tiers": ("T2",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + diff acknowledgment",
        "typical_proof": "CONFIG_DIFF_OR_STATUS",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Environment management",
        "authority_owner": "dopemux operator control",
        "primary_tiers": ("T2",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + diff acknowledgment",
        "typical_proof": "CONFIG_DIFF_OR_STATUS",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "MCP server control",
        "authority_owner": "dopemux operator control + per-MCP authority",
        "primary_tiers": ("T2", "T5"),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button or typed service-id",
        "typical_proof": "CONFIG_DIFF_OR_STATUS / SERVICE_STATUS_AND_LOG",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Service startup / lifecycle (admin)",
        "authority_owner": "per-service authority (Cockpit shows status only)",
        "primary_tiers": ("T5",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + typed service-id",
        "typical_proof": "SERVICE_STATUS_AND_LOG",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Hooks / native-hooks",
        "authority_owner": "dopemux operator control",
        "primary_tiers": ("T2",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + diff acknowledgment",
        "typical_proof": "CONFIG_DIFF_OR_STATUS",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Runtime configuration",
        "authority_owner": "dopemux operator control",
        "primary_tiers": ("T2",),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "Explicit button + diff acknowledgment",
        "typical_proof": "CONFIG_DIFF_OR_STATUS",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Admin / safe / debug helpers",
        "authority_owner": "dopemux operator control",
        "primary_tiers": ("T0i", "T2", "T5"),
        "inspect_tiers": ("T0i",),
        "confirmation_strength": "per tier",
        "typical_proof": "per tier",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
    {
        "name": "Drift inspection (read-only)",
        "authority_owner": "drift evidence (no execution)",
        "primary_tiers": (),
        "inspect_tiers": ("T0", "T0i"),
        "confirmation_strength": "None / explicit invoke",
        "typical_proof": "INSPECT_RESULT_AND_TIMESTAMP",
        "row_tier_mapping_status": "per-row UNKNOWN until packet evidence exists",
    },
)

ALLOWED_SURFACE_ORIGINS: frozenset[str] = frozenset(
    (
        "COMMAND_PALETTE",
        "SETTINGS_ADMIN_RUNTIME",
        "PM",
        "IMPLEMENTER",
        "OVERVIEW",
        "SERVICES",
        "EVENTS",
    )
)

UNSAFE_SURFACE_ORIGINS: frozenset[str] = frozenset(
    (
        "DEEP_LINK",
        "DIRECT_DEEP_LINK",
        "URL_PARAMETER",
        "KEYBOARD_SHORTCUT_BYPASS",
        "BACKGROUND_TRIGGER",
        "BACKGROUND",
        "BYPASS",
    )
)

RECEIPT_EVENT_TYPES: tuple[str, ...] = (
    "gate_open",
    "gate_refuse",
    "gate_abort",
    "gate_timeout",
    "gate_confirmed",
    "gate_proof_captured",
    "gate_proof_incomplete",
    "gate_proof_stale",
)

REQUIRED_PACKAGE_FILES: tuple[str, ...] = (
    "PROOF.json",
    "PACKAGE_REMEDIATION_INDEX.json",
    "PACKAGE_REMEDIATION_INDEX.md",
    "INTEGRATED_COCKPIT_IA_CONTRACT.md",
    "TOP_LEVEL_MODE_PACKAGE_MATRIX.md",
    "GLOBAL_SURFACE_PACKAGE_MATRIX.md",
    "COMMAND_TO_GATE_TO_SCREEN_MATRIX.md",
    "SAFE_ACTION_GATE_INTEGRATION_MATRIX.md",
    "RUNTIME_RENDERER_PACKAGE_HANDOFF.md",
    "SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md",
    "UNKNOWN_DRIFT_PACKAGE_HANDOFF.md",
    "CLAUDE_DESIGN_PRIMITIVE_BOUNDARY.md",
    "PACKAGE_REMEDIATION_TEST_MATRIX.md",
)

COMMON_REQUIRED_FIELDS: tuple[str, ...] = (
    "command",
    "authority_domain",
    "safety_class",
    "gate_tier",
    "source_provenance",
    "surface_origin",
    "created_at_utc",
)

EXECUTABLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "resolved_params",
    "cwd",
    "worktree_metadata",
    "canonical_writer",
    "operator_intent",
)

MUTATING_REQUIRED_FIELDS: tuple[str, ...] = (
    "side_effects",
    "expected_proof",
    "rollback_or_abort",
    "palette_request_id",
    "palette_index_row_hash",
)

TIER_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "T0": COMMON_REQUIRED_FIELDS,
    "T0i": COMMON_REQUIRED_FIELDS + EXECUTABLE_REQUIRED_FIELDS,
    "T1": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + ("output_target_path", "overwrite_behavior"),
    "T2": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + ("config_target_file_or_service", "effective_config_diff_or_unknown_flag"),
    "T3": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + ("write_target_path", "side_effect_classification"),
    "T4": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + (
        "remote_target_endpoint",
        "remote_account_or_context",
        "idempotency_key",
        "remote_mutation_policy_reference",
    ),
    "T5": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + (
        "service_id",
        "service_scope",
        "expected_state_transition",
        "pre_state_snapshot",
        "typed_confirmation",
    ),
    "T6": COMMON_REQUIRED_FIELDS
    + EXECUTABLE_REQUIRED_FIELDS
    + MUTATING_REQUIRED_FIELDS
    + (
        "tp_or_task_id",
        "runner_id",
        "branch",
        "output_or_proof_target",
        "tp_gate_present",
        "typed_confirmation",
    ),
    "TX": (
        "command",
        "authority_domain",
        "safety_class",
        "gate_tier",
        "block_reason",
        "replacement_command_or_NOT_APPLICABLE",
        "required_external_workflow_or_NOT_APPLICABLE",
        "source_provenance",
        "surface_origin",
        "created_at_utc",
    ),
    "TU": (
        "command",
        "authority_domain",
        "safety_class",
        "gate_tier",
        "unknown_reason",
        "required_investigation_packet_or_UNKNOWN",
        "source_provenance",
        "surface_origin",
        "created_at_utc",
    ),
}

PROOF_BY_TIER: dict[str, str] = {
    "T0": "INSPECT_RESULT_AND_TIMESTAMP",
    "T0i": "INSPECT_RESULT_AND_TIMESTAMP",
    "T1": "ARTIFACT_AND_CHECKSUM",
    "T2": "CONFIG_DIFF_OR_STATUS",
    "T3": "FILESYSTEM_DIFF_OR_EXIT_CODE",
    "T4": "REMOTE_RECEIPT",
    "T5": "SERVICE_STATUS_AND_LOG",
    "T6": "TP_RUNNER_PROOF",
    "TX": "BLOCK_REASON_RECORD",
    "TU": "INVESTIGATION_PACKET_REFERENCE",
}


class PackageLoadError(RuntimeError):
    """Fail-closed package loader error with an operator-visible blocker."""


class RuntimeContractError(RuntimeError):
    """Fail-closed runtime contract validation error."""


@dataclass(frozen=True)
class RuntimeConfig:
    stale_proof_window_seconds: int = 86400
    confirm_flow_timeout_seconds: int = 900
    unauthenticated_operator_id: str = "NULL_NOT_AUTHENTICATED"


@dataclass(frozen=True)
class ArtifactProvenance:
    name: str
    path: str
    expected_sha256: str | None
    actual_sha256: str


@dataclass(frozen=True)
class LoadedPackage:
    package_dir: Path
    index: dict[str, Any]
    proof: dict[str, Any]
    artifacts: tuple[ArtifactProvenance, ...]

    @property
    def package_index_sha256(self) -> str:
        return self._sha_for("PACKAGE_REMEDIATION_INDEX.json")

    @property
    def proof_sha256(self) -> str:
        return self._sha_for("PROOF.json")

    def _sha_for(self, name: str) -> str:
        for artifact in self.artifacts:
            if artifact.name == name:
                return artifact.actual_sha256
        raise RuntimeContractError(f"[BLOCKER] artifact provenance missing for {name}")


@dataclass(frozen=True)
class RuntimeRenderModel:
    top_level_modes: tuple[str, ...]
    global_surfaces: tuple[str, ...]
    safe_action_tiers: tuple[str, ...]
    package_packet_id: str
    package_dir: str
    package_index_sha256: str
    proof_sha256: str
    safe_for_claude_design: str
    ready_for_claude_design: str
    ia_verdict: str
    invariants: dict[str, bool]
    config: RuntimeConfig
    settings_admin_runtime: SettingsAdminRuntimeSummary
    unknown_drift_queue: UnknownDriftQueueSummary


@dataclass(frozen=True)
class PreflightResult:
    status: str
    can_confirm: bool
    refusal_reason: str | None
    missing_fields: tuple[str, ...]
    routing_destination: str
    execution_status: str = "not_attempted"


@dataclass(frozen=True)
class SettingsAdminTierMapping:
    tier: str
    safety_class: str
    source: str
    can_confirm: bool
    gate_required: bool
    refusal_route: str
    refusal_reason: str | None
    execution_status: str = "not_attempted"
    remote_policy_required: bool = False


@dataclass(frozen=True)
class SettingsAdminRuntimeSummary:
    surface_name: str
    surface_kind: str
    source_artifact_path: str
    flow_groups: tuple[dict[str, Any], ...]
    row_count: int | str
    mapped_tier_counts: dict[str, int]
    unknown_tier_count: int | str
    refusal_counts: dict[str, int | str]
    gate_required_count: int | str
    blocked_count: int | str
    open_downstream_owner: str
    safe_for_claude_design: str
    ready_for_claude_design: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "surface_name": self.surface_name,
            "surface_kind": self.surface_kind,
            "source_artifact_path": self.source_artifact_path,
            "flow_groups": list(self.flow_groups),
            "row_count": self.row_count,
            "mapped_tier_counts": dict(self.mapped_tier_counts),
            "unknown_tier_count": self.unknown_tier_count,
            "refusal_counts": dict(self.refusal_counts),
            "gate_required_count": self.gate_required_count,
            "blocked_count": self.blocked_count,
            "open_downstream_owner": self.open_downstream_owner,
            "safe_for_claude_design": self.safe_for_claude_design,
            "READY_FOR_CLAUDE_DESIGN": self.ready_for_claude_design,
        }


@dataclass(frozen=True)
class UnknownDriftQueueItem:
    queue_item_id: str
    source_surface: str
    source_artifact_path: str
    source_packet_id: str
    source_row_id: str
    row_hash: str
    command_or_row_label: str
    reason_code: str
    reason_detail: str
    authority_domain: str
    canonical_writer: str
    safety_class: str
    gate_tier: str
    routing_destination: str
    recommended_next_packet: str
    created_at_utc: str
    evidence_refs: tuple[str, ...]
    aggregated_count: int | str = 1
    can_execute: bool = False
    can_reclassify_at_runtime: bool = False
    requires_packet: bool = True

    def as_payload(self) -> dict[str, Any]:
        return {
            "queue_item_id": self.queue_item_id,
            "source_surface": self.source_surface,
            "source_artifact_path": self.source_artifact_path,
            "source_packet_id": self.source_packet_id,
            "source_row_id": self.source_row_id,
            "row_hash": self.row_hash,
            "command_or_row_label": self.command_or_row_label,
            "reason_code": self.reason_code,
            "reason_detail": self.reason_detail,
            "authority_domain": self.authority_domain,
            "canonical_writer": self.canonical_writer,
            "safety_class": self.safety_class,
            "gate_tier": self.gate_tier,
            "routing_destination": self.routing_destination,
            "recommended_next_packet": self.recommended_next_packet,
            "can_execute": self.can_execute,
            "can_reclassify_at_runtime": self.can_reclassify_at_runtime,
            "requires_packet": self.requires_packet,
            "created_at_utc": self.created_at_utc,
            "evidence_refs": list(self.evidence_refs),
            "aggregated_count": self.aggregated_count,
        }


@dataclass(frozen=True)
class UnknownDriftQueueSummary:
    surface_name: str
    surface_kind: str
    items: tuple[UnknownDriftQueueItem, ...]
    total_queue_items: int
    total_queue_items_is_lower_bound: bool
    aggregated_item_count: int
    aggregated_item_counts: dict[str, int | str]
    reason_counts: dict[str, int | str]
    source_surface_counts: dict[str, int | str]
    owner_packet_counts: dict[str, int | str]
    execution_allowed: bool
    runtime_reclassification_allowed: bool
    requires_packet_for_resolution: bool
    top_unresolved_owners: tuple[dict[str, int | str], ...]
    stale_proof_count: int | str
    index_drift_count: int | str
    settings_unknown_tier_count: int | str
    source_artifact_refs: tuple[str, ...]
    safe_for_claude_design: str
    ready_for_claude_design: str
    allowed_affordances: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "surface_name": self.surface_name,
            "surface_kind": self.surface_kind,
            "total_queue_items": self.total_queue_items,
            "total_queue_items_is_lower_bound": self.total_queue_items_is_lower_bound,
            "aggregated_item_count": self.aggregated_item_count,
            "aggregated_item_counts": dict(self.aggregated_item_counts),
            "reason_counts": dict(self.reason_counts),
            "source_surface_counts": dict(self.source_surface_counts),
            "owner_packet_counts": dict(self.owner_packet_counts),
            "execution_allowed": self.execution_allowed,
            "runtime_reclassification_allowed": self.runtime_reclassification_allowed,
            "requires_packet_for_resolution": self.requires_packet_for_resolution,
            "top_unresolved_owners": list(self.top_unresolved_owners),
            "stale_proof_count": self.stale_proof_count,
            "index_drift_count": self.index_drift_count,
            "settings_unknown_tier_count": self.settings_unknown_tier_count,
            "source_artifact_refs": list(self.source_artifact_refs),
            "safe_for_claude_design": self.safe_for_claude_design,
            "READY_FOR_CLAUDE_DESIGN": self.ready_for_claude_design,
            "allowed_affordances": list(self.allowed_affordances),
            "items": [item.as_payload() for item in self.items],
        }


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackageLoadError(f"[BLOCKER] required JSON failed to parse: {path}") from exc
    if not isinstance(data, dict):
        raise PackageLoadError(f"[BLOCKER] required JSON is not an object: {path}")
    return data


def _read_sha256sums(package_dir: Path) -> dict[str, str]:
    sha_file = package_dir / "sha256sums.txt"
    if not sha_file.exists():
        return {}
    checksums: dict[str, str] = {}
    for raw_line in sha_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            checksums[parts[1].strip()] = parts[0].strip()
    return checksums


def load_package_artifacts(package_dir: str | Path) -> LoadedPackage:
    root = Path(package_dir)
    if not root.exists() or not root.is_dir():
        raise PackageLoadError(f"[BLOCKER] package directory missing: {root}")

    missing = [name for name in REQUIRED_PACKAGE_FILES if not (root / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise PackageLoadError(f"[BLOCKER] package directory missing required files: {joined}")

    index = _load_json(root / "PACKAGE_REMEDIATION_INDEX.json")
    proof = _load_json(root / "PROOF.json")
    if index.get("packet_id") != PACKAGE_PACKET_ID:
        raise PackageLoadError("[BLOCKER] package index packet_id mismatch")
    if proof.get("packet_id") != PACKAGE_PACKET_ID:
        raise PackageLoadError("[BLOCKER] package proof packet_id mismatch")

    expected = _read_sha256sums(root)
    artifacts: list[ArtifactProvenance] = []
    for name in REQUIRED_PACKAGE_FILES:
        path = root / name
        artifacts.append(
            ArtifactProvenance(
                name=name,
                path=str(path),
                expected_sha256=expected.get(name),
                actual_sha256=_file_sha256(path),
            )
        )
    return LoadedPackage(
        package_dir=root,
        index=index,
        proof=proof,
        artifacts=tuple(artifacts),
    )


def _settings_admin_source_path(package: LoadedPackage) -> str:
    return str(package.package_dir / SETTINGS_ADMIN_SOURCE_ARTIFACT)


def _settings_admin_row_count(package: LoadedPackage) -> int | str:
    count = (
        package.index.get("carried_inventory_counts", {})
        .get("placement", {})
        .get("Settings/Admin")
    )
    return count if isinstance(count, int) else "UNKNOWN"


def build_settings_admin_runtime_summary(package: LoadedPackage) -> SettingsAdminRuntimeSummary:
    row_count = _settings_admin_row_count(package)
    unknown_tier_count: int | str = row_count if isinstance(row_count, int) else "UNKNOWN"
    unknown_refusals: int | str = row_count if isinstance(row_count, int) else "UNKNOWN"
    mapped_tier_counts = {tier: 0 for tier in SAFE_ACTION_TIERS}
    return SettingsAdminRuntimeSummary(
        surface_name="Settings/Admin/Runtime",
        surface_kind="secondary/global surface",
        source_artifact_path=_settings_admin_source_path(package),
        flow_groups=SETTINGS_ADMIN_FLOW_GROUPS,
        row_count=row_count,
        mapped_tier_counts=mapped_tier_counts,
        unknown_tier_count=unknown_tier_count,
        refusal_counts={
            "UNKNOWN_DRIFT_QUEUE": unknown_refusals,
            "SHOW_BLOCKED_REASON": "UNKNOWN",
        },
        gate_required_count="UNKNOWN",
        blocked_count="UNKNOWN",
        open_downstream_owner=SETTINGS_RUNTIME_PACKET_ID,
        safe_for_claude_design="NO",
        ready_for_claude_design="not approved",
    )


def _repo_root_from_package(package: LoadedPackage) -> Path:
    package_dir = package.package_dir.resolve()
    if (
        package_dir.name != PACKAGE_PACKET_ID
        or package_dir.parent.name != "cockpit-pack-remediation"
        or package_dir.parent.parent.name != "out"
    ):
        raise RuntimeContractError(
            "[BLOCKER] package directory is not the accepted cockpit package artifact path"
        )
    return package_dir.parent.parent.parent


def _required_source_path(repo_root: Path, *parts: str) -> Path:
    path = repo_root.joinpath(*parts)
    if not path.is_file():
        raise RuntimeContractError(f"[BLOCKER] accepted source artifact missing: {path}")
    return path


def _source_created_at(*sources: Mapping[str, Any]) -> str:
    for source in sources:
        value = source.get("created_at_utc")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "UNKNOWN"


def _count_value(value: Any) -> int | str:
    return value if isinstance(value, int) else "UNKNOWN"


def _redact_queue_text(value: Any) -> str:
    redacted = redact_secrets(value)
    if isinstance(redacted, str):
        return redacted
    return json.dumps(redacted, sort_keys=True, default=str)


def _redact_queue_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_redact_queue_text(value) for value in values)


def build_unknown_drift_queue_item(
    *,
    source_surface: str,
    source_artifact_path: str,
    source_packet_id: str,
    source_row_id: str,
    command_or_row_label: str,
    reason_code: str,
    reason_detail: str,
    authority_domain: str = "UNKNOWN",
    canonical_writer: str = "UNKNOWN",
    safety_class: str = "UNKNOWN",
    gate_tier: str = "TU",
    routing_destination: str = "UNKNOWN_DRIFT_QUEUE",
    recommended_next_packet: str = UNKNOWN_DRIFT_PACKET_ID,
    created_at_utc: str = "UNKNOWN",
    evidence_refs: tuple[str, ...] = (),
    aggregated_count: int | str = 1,
) -> UnknownDriftQueueItem:
    if reason_code not in UNKNOWN_DRIFT_REASON_CODES:
        raise RuntimeContractError(f"[BLOCKER] unsupported Unknown / Drift reason: {reason_code}")
    seed = {
        "source_surface": source_surface,
        "source_artifact_path": source_artifact_path,
        "source_packet_id": source_packet_id,
        "source_row_id": source_row_id,
        "command_or_row_label": command_or_row_label,
        "reason_code": reason_code,
    }
    row_hash = stable_sha256(seed)
    return UnknownDriftQueueItem(
        queue_item_id=f"unknown-drift-{row_hash[:16]}",
        source_surface=_redact_queue_text(source_surface),
        source_artifact_path=_redact_queue_text(source_artifact_path),
        source_packet_id=_redact_queue_text(source_packet_id),
        source_row_id=_redact_queue_text(source_row_id),
        row_hash=row_hash,
        command_or_row_label=_redact_queue_text(command_or_row_label),
        reason_code=reason_code,
        reason_detail=_redact_queue_text(reason_detail),
        authority_domain=_redact_queue_text(authority_domain),
        canonical_writer=_redact_queue_text(canonical_writer),
        safety_class=_redact_queue_text(safety_class),
        gate_tier=_redact_queue_text(gate_tier),
        routing_destination=routing_destination,
        recommended_next_packet=_redact_queue_text(recommended_next_packet),
        created_at_utc=_redact_queue_text(created_at_utc),
        evidence_refs=_redact_queue_refs(evidence_refs),
        aggregated_count=aggregated_count,
    )


def _increment_count(
    counts: dict[str, int | str],
    key: str,
    amount: int | str,
) -> None:
    if isinstance(amount, int):
        current = counts.get(key, 0)
        counts[key] = current + amount if isinstance(current, int) else current
        return
    if key not in counts:
        counts[key] = "UNKNOWN"


def _top_unresolved_owners(counts: dict[str, int | str]) -> tuple[dict[str, int | str], ...]:
    sortable: list[tuple[int, str, int | str]] = []
    for owner, count in counts.items():
        rank = count if isinstance(count, int) else -1
        sortable.append((rank, owner, count))
    sortable.sort(key=lambda item: (-item[0], item[1]))
    return tuple({"owner_packet": owner, "count": count} for _, owner, count in sortable[:5])


def _aggregate_unknown_drift_items(
    package: LoadedPackage,
    settings: SettingsAdminRuntimeSummary,
) -> tuple[UnknownDriftQueueItem, ...]:
    repo_root = _repo_root_from_package(package)
    runtime_proof_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-runtime-render",
        RUNTIME_PACKET_ID,
        "PROOF.json",
    )
    settings_proof_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-settings-runtime",
        SETTINGS_RUNTIME_PACKET_ID,
        "PROOF.json",
    )
    ia_spec_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-ia-reconcile",
        "TP-DMX-COCKPIT-IA-RECONCILE-001",
        "UNKNOWN_DRIFT_QUEUE_SPEC.md",
    )
    ia_policy_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-ia-reconcile",
        "TP-DMX-COCKPIT-IA-RECONCILE-001",
        "COMMAND_EXPOSURE_POLICY.json",
    )
    palette_handoff_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-command-palette",
        "TP-DMX-COCKPIT-COMMAND-PALETTE-001",
        "PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md",
    )
    safe_handoff_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-safe-actions",
        "TP-DMX-COCKPIT-SAFE-ACTIONS-001",
        "SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md",
    )
    safe_refusal_path = _required_source_path(
        repo_root,
        "out",
        "cockpit-safe-actions",
        "TP-DMX-COCKPIT-SAFE-ACTIONS-001",
        "SAFE_ACTION_REFUSAL_RULES.md",
    )
    package_handoff_path = package.package_dir / UNKNOWN_DRIFT_SOURCE_ARTIFACT
    runtime_proof = _load_json(runtime_proof_path)
    settings_proof = _load_json(settings_proof_path)
    ia_policy = _load_json(ia_policy_path)
    source_counts = (
        package.index.get("carried_inventory_counts")
        or ia_policy.get("metadata", {}).get("source_counts")
        or {}
    )
    created_at = _source_created_at(package.proof, runtime_proof, settings_proof)

    items: list[UnknownDriftQueueItem] = []

    def append_item(**kwargs: Any) -> None:
        items.append(build_unknown_drift_queue_item(created_at_utc=created_at, **kwargs))

    inventory_refs = (
        str(ia_spec_path),
        str(ia_policy_path),
        str(package_handoff_path),
    )
    coverage_counts = source_counts.get("coverage", {})
    safe_counts = source_counts.get("safe_ui_exposure", {})
    activation_counts = source_counts.get("activation_status", {})
    authority_counts = source_counts.get("authority_domain", {})

    append_item(
        source_surface="IA Reconcile inventory",
        source_artifact_path=str(ia_policy_path),
        source_packet_id="TP-DMX-COCKPIT-IA-RECONCILE-001",
        source_row_id="coverage.MISSING",
        command_or_row_label="coverage.MISSING carried rows",
        reason_code="UNKNOWN",
        reason_detail=(
            "Accepted inventory carries coverage.MISSING rows; per-row unknown axes are not "
            "available in accepted artifacts, so rows remain aggregate-only."
        ),
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet="Separate inventory-regeneration packet",
        evidence_refs=inventory_refs,
        aggregated_count=_count_value(coverage_counts.get("MISSING")),
    )
    append_item(
        source_surface="IA Reconcile inventory",
        source_artifact_path=str(ia_policy_path),
        source_packet_id="TP-DMX-COCKPIT-IA-RECONCILE-001",
        source_row_id="coverage.UNKNOWN",
        command_or_row_label="coverage.UNKNOWN carried rows",
        reason_code="UNKNOWN",
        reason_detail="Accepted inventory carries coverage.UNKNOWN rows without per-row runtime proof.",
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet="Separate inventory-regeneration packet",
        evidence_refs=inventory_refs,
        aggregated_count=_count_value(coverage_counts.get("UNKNOWN")),
    )
    append_item(
        source_surface="Command Palette",
        source_artifact_path=str(palette_handoff_path),
        source_packet_id="TP-DMX-COCKPIT-COMMAND-PALETTE-001",
        source_row_id="safe_ui_exposure.UNKNOWN",
        command_or_row_label="safe_ui_exposure.UNKNOWN carried rows",
        reason_code="UNKNOWN",
        reason_detail="Palette unknown rows remain visible and non-executable until packet evidence exists.",
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        evidence_refs=(str(palette_handoff_path), str(ia_spec_path)),
        aggregated_count=_count_value(safe_counts.get("UNKNOWN")),
    )
    append_item(
        source_surface="Command Palette",
        source_artifact_path=str(palette_handoff_path),
        source_packet_id="TP-DMX-COCKPIT-COMMAND-PALETTE-001",
        source_row_id="safe_ui_exposure.BLOCKED_IN_COCKPIT",
        command_or_row_label="safe_ui_exposure.BLOCKED_IN_COCKPIT carried rows",
        reason_code="UNKNOWN",
        reason_detail="Blocked rows remain visible through blocked-reason display and never execute.",
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="BLOCKED_IN_COCKPIT",
        gate_tier="TX",
        routing_destination="SHOW_BLOCKED_REASON",
        recommended_next_packet="Separate blocked-row reclassification packet",
        evidence_refs=(str(palette_handoff_path), str(ia_spec_path)),
        aggregated_count=_count_value(safe_counts.get("BLOCKED_IN_COCKPIT")),
    )
    for status, reason_code in (
        ("DEFINED_NOT_REGISTERED", "DEFINED_NOT_REGISTERED"),
        ("OPTIONAL_IMPORT_UNKNOWN", "OPTIONAL_IMPORT_UNKNOWN"),
        ("DEPRECATED_BLOCKED", "DEPRECATED_BLOCKED"),
    ):
        append_item(
            source_surface="Command Palette",
            source_artifact_path=str(palette_handoff_path),
            source_packet_id="TP-DMX-COCKPIT-COMMAND-PALETTE-001",
            source_row_id=f"activation_status.{status}",
            command_or_row_label=f"activation_status.{status} carried rows",
            reason_code=reason_code,
            reason_detail=f"Accepted inventory carries {status} rows; runtime does not reclassify them.",
            authority_domain="UNKNOWN" if status != "DEPRECATED_BLOCKED" else "unknown / conflicting",
            canonical_writer="UNKNOWN",
            safety_class="BLOCKED_IN_COCKPIT" if status == "DEPRECATED_BLOCKED" else "UNKNOWN",
            gate_tier="TX" if status == "DEPRECATED_BLOCKED" else "TU",
            routing_destination="SHOW_BLOCKED_REASON"
            if status == "DEPRECATED_BLOCKED"
            else "UNKNOWN_DRIFT_QUEUE",
            recommended_next_packet="Separate reclassification packet",
            evidence_refs=(str(palette_handoff_path), str(ia_spec_path)),
            aggregated_count=_count_value(activation_counts.get(status)),
        )
    append_item(
        source_surface="IA Reconcile inventory",
        source_artifact_path=str(ia_policy_path),
        source_packet_id="TP-DMX-COCKPIT-IA-RECONCILE-001",
        source_row_id="authority_domain.unknown / conflicting",
        command_or_row_label="authority_domain.unknown / conflicting carried rows",
        reason_code="AUTHORITY_CONFLICT",
        reason_detail="Multiple authority claims remain unresolved; queue records without reclassification.",
        authority_domain="unknown / conflicting",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet="Separate authority reclassification packet",
        evidence_refs=inventory_refs,
        aggregated_count=_count_value(authority_counts.get("unknown / conflicting")),
    )
    append_item(
        source_surface="Settings/Admin/Runtime",
        source_artifact_path=settings.source_artifact_path,
        source_packet_id=SETTINGS_RUNTIME_PACKET_ID,
        source_row_id="settings_admin_runtime.unknown_tier_count",
        command_or_row_label="Settings/Admin unresolved tier rows",
        reason_code="SETTINGS_ROW_TIER_UNKNOWN",
        reason_detail="Accepted Settings/Admin evidence proves 62 rows but not per-row gate tiers.",
        authority_domain="dopemux operator control",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet=SETTINGS_RUNTIME_PACKET_ID,
        evidence_refs=(settings.source_artifact_path, str(settings_proof_path)),
        aggregated_count=settings.unknown_tier_count,
    )
    append_item(
        source_surface="Safe Actions / Proof Gate",
        source_artifact_path=str(safe_refusal_path),
        source_packet_id="TP-DMX-COCKPIT-SAFE-ACTIONS-001",
        source_row_id="gate_tier.T4.remote_mutation_policy_reference",
        command_or_row_label="T4 remote mutation policy missing",
        reason_code="REMOTE_MUTATION_POLICY_MISSING",
        reason_detail="T4 remains refused until a separate approved remote-mutation policy exists.",
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="CONFIRM_REQUIRED",
        gate_tier="T4",
        recommended_next_packet="Separate remote-mutation policy packet",
        evidence_refs=(str(safe_refusal_path), str(safe_handoff_path)),
        aggregated_count=1,
    )
    append_item(
        source_surface="Runtime Render residual risk",
        source_artifact_path=str(runtime_proof_path),
        source_packet_id=RUNTIME_PACKET_ID,
        source_row_id="runtime_render.stale_proof_window",
        command_or_row_label="Stale proof gate representation",
        reason_code="STALE_PROOF_GATE",
        reason_detail="Accepted runtime-render proof preserved stale proof as a downstream queue concern.",
        authority_domain="dopemux operator control",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet=UNKNOWN_DRIFT_PACKET_ID,
        evidence_refs=(str(runtime_proof_path), str(safe_handoff_path)),
        aggregated_count=1,
    )
    append_item(
        source_surface="Package residual risk",
        source_artifact_path=str(package.package_dir / "PACKAGE_REMEDIATION_INDEX.json"),
        source_packet_id=PACKAGE_PACKET_ID,
        source_row_id="residual_unknown.inventory_regeneration_current_head",
        command_or_row_label="Inventory freshness drift risk",
        reason_code="INDEX_DRIFT",
        reason_detail=(
            "Accepted package states inventory was not regenerated against current HEAD; "
            "this is a drift-risk aggregate, not proof of a specific per-row drift."
        ),
        authority_domain="UNKNOWN",
        canonical_writer="UNKNOWN",
        safety_class="UNKNOWN",
        gate_tier="TU",
        recommended_next_packet="Separate inventory-regeneration packet",
        evidence_refs=(str(package.package_dir / "PACKAGE_REMEDIATION_INDEX.json"),),
        aggregated_count=1,
    )

    route_classes = (
        ("PARAM_UNRESOLVED", "required parameter unresolved"),
        ("CWD_UNRESOLVED", "cwd or worktree path unresolved"),
        ("PROOF_REQUIREMENT_UNKNOWN", "expected proof unknown"),
        ("ROLLBACK_UNKNOWN", "rollback or abort unknown"),
        ("SIDE_EFFECTS_UNKNOWN", "side effects unknown"),
        ("TP_GATE_ABSENT", "TP gate absent"),
        ("AUTHORITY_DRIFT_MID_FLOW", "authority drift mid-flow"),
        ("CLASS_DRIFT_MID_FLOW", "class drift mid-flow"),
        ("UNSAFE_SOURCE_SURFACE", "unsafe source surface"),
        ("STALE_HANDOFF", "stale handoff timestamp"),
        ("MISSING_REQUIRED_FIELD", "required preflight field missing"),
        ("UNKNOWN_CANONICAL_WRITER", "canonical writer unknown"),
        ("UNKNOWN_AUTHORITY_DOMAIN", "authority domain unknown"),
    )
    for reason_code, detail in route_classes:
        append_item(
            source_surface="Safe Actions / Proof Gate",
            source_artifact_path=str(safe_handoff_path),
            source_packet_id="TP-DMX-COCKPIT-SAFE-ACTIONS-001",
            source_row_id=f"safe_action_refusal.{reason_code}",
            command_or_row_label=f"Safe Action refusal route: {reason_code}",
            reason_code=reason_code,
            reason_detail=f"Accepted Safe Action handoff routes {detail} to the queue without execution.",
            authority_domain="UNKNOWN",
            canonical_writer="UNKNOWN",
            safety_class="UNKNOWN",
            gate_tier="TU",
            recommended_next_packet=UNKNOWN_DRIFT_PACKET_ID,
            evidence_refs=(str(safe_handoff_path), str(safe_refusal_path)),
            aggregated_count="UNKNOWN",
        )

    package_residuals = package.index.get("residual_unknowns", ())
    if isinstance(package_residuals, list):
        for index, residual in enumerate(package_residuals):
            if not isinstance(residual, Mapping):
                continue
            append_item(
                source_surface="Package residual unknown",
                source_artifact_path=str(package.package_dir / "PACKAGE_REMEDIATION_INDEX.json"),
                source_packet_id=PACKAGE_PACKET_ID,
                source_row_id=f"package_residual_unknown.{index}",
                command_or_row_label=str(residual.get("unknown") or "Package residual unknown"),
                reason_code="UNKNOWN",
                reason_detail=str(residual.get("blocker_condition") or "Accepted package residual UNKNOWN."),
                authority_domain="UNKNOWN",
                canonical_writer="UNKNOWN",
                safety_class="UNKNOWN",
                gate_tier="TU",
                recommended_next_packet=str(residual.get("owner") or UNKNOWN_DRIFT_PACKET_ID),
                evidence_refs=(str(package.package_dir / "PACKAGE_REMEDIATION_INDEX.json"),),
                aggregated_count="UNKNOWN",
            )

    for proof_name, proof_packet_id, proof_path, proof in (
        ("Runtime Render residual risk", RUNTIME_PACKET_ID, runtime_proof_path, runtime_proof),
        ("Settings Runtime residual risk", SETTINGS_RUNTIME_PACKET_ID, settings_proof_path, settings_proof),
    ):
        residuals = proof.get("residual_risks", ())
        if not isinstance(residuals, list):
            continue
        for index, residual in enumerate(residuals):
            detail = str(residual)
            reason_code = "UNKNOWN"
            if "T4" in detail or "remote-mutation" in detail:
                reason_code = "REMOTE_MUTATION_POLICY_MISSING"
            elif "Settings/Admin" in detail and "UNKNOWN" in detail:
                reason_code = "SETTINGS_ROW_TIER_UNKNOWN"
            elif "Inventory regeneration" in detail or "inventory regeneration" in detail:
                reason_code = "INDEX_DRIFT"
            append_item(
                source_surface=proof_name,
                source_artifact_path=str(proof_path),
                source_packet_id=proof_packet_id,
                source_row_id=f"{proof_packet_id}.residual_risk.{index}",
                command_or_row_label=f"{proof_name} {index}",
                reason_code=reason_code,
                reason_detail=detail,
                authority_domain="UNKNOWN",
                canonical_writer="UNKNOWN",
                safety_class="UNKNOWN",
                gate_tier="TU",
                recommended_next_packet=UNKNOWN_DRIFT_PACKET_ID,
                evidence_refs=(str(proof_path),),
                aggregated_count="UNKNOWN",
            )

    return tuple(sorted(items, key=lambda item: item.queue_item_id))


def build_unknown_drift_queue_summary(
    package: LoadedPackage,
    *,
    settings_admin_runtime: SettingsAdminRuntimeSummary | None = None,
) -> UnknownDriftQueueSummary:
    settings = settings_admin_runtime or build_settings_admin_runtime_summary(package)
    items = _aggregate_unknown_drift_items(package, settings)
    aggregated_item_counts = {
        item.command_or_row_label: item.aggregated_count
        for item in sorted(items, key=lambda candidate: candidate.command_or_row_label)
    }
    reason_counts = {reason: 0 for reason in UNKNOWN_DRIFT_REASON_CODES}
    source_surface_counts: dict[str, int | str] = {}
    owner_packet_counts: dict[str, int | str] = {}
    total_known = 0
    has_unknown_counts = False
    for item in items:
        count = item.aggregated_count
        if isinstance(count, int):
            total_known += count
        else:
            has_unknown_counts = True
        _increment_count(reason_counts, item.reason_code, count)
        _increment_count(source_surface_counts, item.source_surface, count)
        _increment_count(owner_packet_counts, item.recommended_next_packet, count)
    source_artifacts = tuple(
        sorted({ref for item in items for ref in (item.source_artifact_path, *item.evidence_refs)})
    )
    return UnknownDriftQueueSummary(
        surface_name="Unknown / Drift Queue",
        surface_kind="secondary/global surface",
        items=items,
        total_queue_items=total_known,
        total_queue_items_is_lower_bound=has_unknown_counts,
        aggregated_item_count=len(items),
        aggregated_item_counts=aggregated_item_counts,
        reason_counts=reason_counts,
        source_surface_counts=source_surface_counts,
        owner_packet_counts=owner_packet_counts,
        execution_allowed=False,
        runtime_reclassification_allowed=False,
        requires_packet_for_resolution=True,
        top_unresolved_owners=_top_unresolved_owners(owner_packet_counts),
        stale_proof_count=reason_counts.get("STALE_PROOF_GATE", 0),
        index_drift_count=reason_counts.get("INDEX_DRIFT", 0),
        settings_unknown_tier_count=settings.unknown_tier_count,
        source_artifact_refs=source_artifacts,
        safe_for_claude_design="NO",
        ready_for_claude_design="not approved",
        allowed_affordances=ALLOWED_UNKNOWN_DRIFT_AFFORDANCES,
    )


def _first_present(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _normalize_token(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else "UNKNOWN"
    return str(value)


def _row_evidence_tokens(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        tokens: list[str] = []
        for child in value.values():
            tokens.extend(_row_evidence_tokens(child))
        return tuple(tokens)
    if isinstance(value, (list, tuple, set)):
        tokens = []
        for child in value:
            tokens.extend(_row_evidence_tokens(child))
        return tuple(tokens)
    return (_normalize_token(value).lower().replace("-", "_").replace(" ", "_"),)


def _settings_admin_side_effect_tokens(row: Mapping[str, Any]) -> tuple[str, ...]:
    values = (
        _first_present(row, "side_effect_kind", "side_effect_classification", "operation_class"),
        row.get("side_effects"),
        row.get("expected_proof"),
        row.get("proof_requirement"),
    )
    tokens: list[str] = []
    for value in values:
        tokens.extend(_row_evidence_tokens(value))
    return tuple(tokens)


def _tokens_match(tokens: tuple[str, ...], *needles: str) -> bool:
    return any(any(needle in token for needle in needles) for token in tokens)


def _settings_admin_mapping(
    *,
    tier: str,
    safety_class: str,
    source: str,
    refusal_route: str,
    refusal_reason: str | None,
    remote_policy_required: bool = False,
) -> SettingsAdminTierMapping:
    return SettingsAdminTierMapping(
        tier=tier,
        safety_class=safety_class,
        source=source,
        can_confirm=tier in CONFIRMABLE_TIERS and not remote_policy_required,
        gate_required=tier in SETTINGS_ADMIN_GATE_REQUIRED_TIERS,
        refusal_route=refusal_route,
        refusal_reason=refusal_reason,
        remote_policy_required=remote_policy_required,
    )


def map_settings_admin_row_to_gate_tier(row: Mapping[str, Any]) -> SettingsAdminTierMapping:
    """Map one Settings/Admin row from explicit evidence; missing evidence fails to TU."""

    safety_class = _normalize_token(_first_present(row, "safety_class", "safe_ui_exposure"))
    explicit_tier = _normalize_token(_first_present(row, "gate_tier", "proposed_gate_tier"))

    if safety_class == "BLOCKED_IN_COCKPIT" or explicit_tier == "TX":
        return _settings_admin_mapping(
            tier="TX",
            safety_class="BLOCKED_IN_COCKPIT",
            source="explicit blocked evidence",
            refusal_route="SHOW_BLOCKED_REASON",
            refusal_reason="BLOCKED_IN_COCKPIT",
        )
    if safety_class in {"UNKNOWN", "EXTERNAL_ONLY"} or explicit_tier == "TU":
        return _settings_admin_mapping(
            tier="TU",
            safety_class=safety_class,
            source="explicit unknown or external-only evidence",
            refusal_route="UNKNOWN_DRIFT_QUEUE",
            refusal_reason="UNKNOWN_CLASS",
        )
    if explicit_tier in SAFE_ACTION_TIERS:
        return _settings_admin_mapping(
            tier=explicit_tier,
            safety_class=safety_class,
            source="explicit gate tier evidence",
            refusal_route="UNKNOWN_DRIFT_QUEUE" if explicit_tier == "T4" else "NOT_APPLICABLE",
            refusal_reason="REMOTE_MUTATION_POLICY_MISSING" if explicit_tier == "T4" else None,
            remote_policy_required=explicit_tier == "T4",
        )
    if safety_class == "DISPLAY_ONLY":
        return _settings_admin_mapping(
            tier="T0",
            safety_class=safety_class,
            source="explicit DISPLAY_ONLY safety class",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    if safety_class == "INSPECT_ACTION":
        return _settings_admin_mapping(
            tier="T0i",
            safety_class=safety_class,
            source="explicit INSPECT_ACTION safety class",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    if safety_class != "CONFIRM_REQUIRED":
        return _settings_admin_mapping(
            tier="TU",
            safety_class=safety_class,
            source="insufficient Settings/Admin tier evidence",
            refusal_route="UNKNOWN_DRIFT_QUEUE",
            refusal_reason="GATE_TIER_UNKNOWN",
        )

    tokens = _settings_admin_side_effect_tokens(row)
    if _tokens_match(tokens, "remote_mutation", "write_remote", "remote_receipt"):
        return _settings_admin_mapping(
            tier="T4",
            safety_class=safety_class,
            source="explicit remote mutation evidence",
            refusal_route="UNKNOWN_DRIFT_QUEUE",
            refusal_reason="REMOTE_MUTATION_POLICY_MISSING",
            remote_policy_required=True,
        )
    if _tokens_match(tokens, "execution_handoff", "tp_runner_proof"):
        return _settings_admin_mapping(
            tier="T6",
            safety_class=safety_class,
            source="explicit execution handoff evidence",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    if _tokens_match(tokens, "service_start", "service_stop", "start_stop_service", "service_status"):
        return _settings_admin_mapping(
            tier="T5",
            safety_class=safety_class,
            source="explicit service lifecycle evidence",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    if _tokens_match(tokens, "local_write", "write_local", "filesystem_diff"):
        return _settings_admin_mapping(
            tier="T3",
            safety_class=safety_class,
            source="explicit local write evidence",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    if _tokens_match(tokens, "config_mutation", "config_diff", "configuration"):
        return _settings_admin_mapping(
            tier="T2",
            safety_class=safety_class,
            source="explicit config mutation evidence",
            refusal_route="NOT_APPLICABLE",
            refusal_reason=None,
        )
    return _settings_admin_mapping(
        tier="TU",
        safety_class=safety_class,
        source="insufficient Settings/Admin tier evidence",
        refusal_route="UNKNOWN_DRIFT_QUEUE",
        refusal_reason="GATE_TIER_UNKNOWN",
    )


def build_runtime_render_model(
    package: LoadedPackage,
    *,
    config: RuntimeConfig | None = None,
) -> RuntimeRenderModel:
    topology = package.index.get("ia_topology", {})
    observed_modes = tuple(topology.get("top_level_modes", ()))
    observed_surfaces = tuple(topology.get("secondary_surfaces", ()))
    if observed_modes != TOP_LEVEL_MODES:
        raise RuntimeContractError("[BLOCKER] package top-level modes drift from contract")
    if observed_surfaces != GLOBAL_SURFACES:
        raise RuntimeContractError("[BLOCKER] package global surfaces drift from contract")
    if package.proof.get("safe_for_claude_design") != "NO":
        raise RuntimeContractError("[BLOCKER] package proof no longer blocks Claude Design")
    if package.proof.get("ready_for_claude_design") is not False:
        raise RuntimeContractError("[BLOCKER] package proof changed Claude Design readiness")

    package_invariants = package.proof.get("package_invariants", {})
    invariants = {
        "no_sixth_top_level_mode": bool(package_invariants.get("no_sixth_top_level_mode")),
        "palette_broker_only": True,
        "gate_cross_cutting": bool(package_invariants.get("safe_action_gate_cross_cutting")),
        "gate_non_executing_in_this_packet": True,
        "t4_blocked_until_policy": bool(
            package_invariants.get("t4_remote_mutation_blocked_until_policy_approves")
        ),
        "tx_tu_never_executable": True,
        "unknown_drift_visible": bool(package_invariants.get("unknowns_preserved")),
        "claude_design_blocked": True,
    }
    if not all(invariants.values()):
        raise RuntimeContractError("[BLOCKER] package invariants are not preserved")

    settings_admin_runtime = build_settings_admin_runtime_summary(package)
    return RuntimeRenderModel(
        top_level_modes=TOP_LEVEL_MODES,
        global_surfaces=GLOBAL_SURFACES,
        safe_action_tiers=SAFE_ACTION_TIERS,
        package_packet_id=PACKAGE_PACKET_ID,
        package_dir=str(package.package_dir),
        package_index_sha256=package.package_index_sha256,
        proof_sha256=package.proof_sha256,
        safe_for_claude_design="NO",
        ready_for_claude_design="not approved",
        ia_verdict=str(package.proof.get("ia_verdict", "UNKNOWN")),
        invariants=invariants,
        config=config or RuntimeConfig(),
        settings_admin_runtime=settings_admin_runtime,
        unknown_drift_queue=build_unknown_drift_queue_summary(
            package,
            settings_admin_runtime=settings_admin_runtime,
        ),
    )


def render_runtime_snapshot(
    package_dir: str | Path,
    *,
    snapshot: tuple[int, int] = (120, 40),
    config: RuntimeConfig | None = None,
) -> str:
    package = load_package_artifacts(package_dir)
    model = build_runtime_render_model(package, config=config)
    cols, rows = snapshot
    lines = [
        "# Dopemux Cockpit Runtime Render Snapshot",
        "RUNTIME PRIMITIVE ONLY  NO ACTION EXECUTION  NO FINAL SCREENS",
        f"snapshot: {cols}x{rows}",
        f"package_packet_id: {model.package_packet_id}",
        f"package_dir: {model.package_dir}",
        f"package_index_sha256: {model.package_index_sha256}",
        f"proof_sha256: {model.proof_sha256}",
        f"artifact_count: {len(package.artifacts)}",
        f"safe_for_claude_design: {model.safe_for_claude_design}",
        f"READY_FOR_CLAUDE_DESIGN: {model.ready_for_claude_design}",
        f"ia_verdict: {model.ia_verdict}",
        f"top_level_modes: {' | '.join(model.top_level_modes)}",
        f"global_surfaces: {' | '.join(model.global_surfaces)}",
        f"safe_action_tiers: {' | '.join(model.safe_action_tiers)}",
        "invariants:",
    ]
    for key in sorted(model.invariants):
        lines.append(f"  {key}: {str(model.invariants[key]).lower()}")
    settings = model.settings_admin_runtime
    lines.extend(
        (
            "settings_admin_runtime:",
            f"  surface_name: {settings.surface_name}",
            f"  surface_kind: {settings.surface_kind}",
            f"  source_artifact_path: {settings.source_artifact_path}",
            f"  flow_group_count: {len(settings.flow_groups)}",
            f"  flow_groups: {' | '.join(group['name'] for group in settings.flow_groups)}",
            f"  row_count: {settings.row_count}",
            f"  mapped_tier_counts: {json.dumps(settings.mapped_tier_counts, sort_keys=True)}",
            f"  unknown_tier_count: {settings.unknown_tier_count}",
            f"  refusal_counts: {json.dumps(settings.refusal_counts, sort_keys=True)}",
            f"  gate_required_count: {settings.gate_required_count}",
            f"  blocked_count: {settings.blocked_count}",
            f"  open_downstream_owner: {settings.open_downstream_owner}",
            f"  safe_for_claude_design: {settings.safe_for_claude_design}",
            f"  READY_FOR_CLAUDE_DESIGN: {settings.ready_for_claude_design}",
        )
    )
    queue = model.unknown_drift_queue
    lines.extend(
        (
            "unknown_drift_queue:",
            f"  surface_name: {queue.surface_name}",
            f"  surface_kind: {queue.surface_kind}",
            f"  total_queue_items: {queue.total_queue_items}",
            f"  total_queue_items_is_lower_bound: {str(queue.total_queue_items_is_lower_bound).lower()}",
            f"  aggregated_item_count: {queue.aggregated_item_count}",
            f"  reason_counts: {json.dumps(queue.reason_counts, sort_keys=True)}",
            f"  source_surface_counts: {json.dumps(queue.source_surface_counts, sort_keys=True)}",
            f"  owner_packet_counts: {json.dumps(queue.owner_packet_counts, sort_keys=True)}",
            f"  execution_allowed: {str(queue.execution_allowed).lower()}",
            "  runtime_reclassification_allowed: "
            f"{str(queue.runtime_reclassification_allowed).lower()}",
            f"  requires_packet_for_resolution: {str(queue.requires_packet_for_resolution).lower()}",
            f"  top_unresolved_owners: {json.dumps(list(queue.top_unresolved_owners), sort_keys=True)}",
            f"  stale_proof_count: {queue.stale_proof_count}",
            f"  index_drift_count: {queue.index_drift_count}",
            f"  settings_unknown_tier_count: {queue.settings_unknown_tier_count}",
            f"  source_artifact_ref_count: {len(queue.source_artifact_refs)}",
            f"  allowed_affordances: {' | '.join(queue.allowed_affordances)}",
            f"  safe_for_claude_design: {queue.safe_for_claude_design}",
            f"  READY_FOR_CLAUDE_DESIGN: {queue.ready_for_claude_design}",
        )
    )
    lines.extend(
        (
            "runtime_config:",
            f"  stale_proof_window_seconds: {model.config.stale_proof_window_seconds}",
            f"  confirm_flow_timeout_seconds: {model.config.confirm_flow_timeout_seconds}",
            f"  unauthenticated_operator_id: {model.config.unauthenticated_operator_id}",
            "boundary:",
            "  T4 blocked until remote mutation policy exists",
            "  TX/TU never executable",
            "  Command Palette broker-only",
            "  Safe Actions / Proof Gate cross-cutting and non-executing here",
            "  Unknown / Drift Queue visible and non-executable",
            "  Claude Design upload blocked",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def runtime_snapshot_payload(
    package_dir: str | Path,
    *,
    snapshot: tuple[int, int] = (120, 40),
    config: RuntimeConfig | None = None,
) -> dict[str, Any]:
    package = load_package_artifacts(package_dir)
    model = build_runtime_render_model(package, config=config)
    return {
        "schema_version": "dopemux.cockpit.runtime_render.snapshot.v1",
        "packet_id": RUNTIME_PACKET_ID,
        "snapshot": {"cols": snapshot[0], "rows": snapshot[1]},
        "package_packet_id": model.package_packet_id,
        "package_dir": model.package_dir,
        "package_index_sha256": model.package_index_sha256,
        "proof_sha256": model.proof_sha256,
        "safe_for_claude_design": model.safe_for_claude_design,
        "READY_FOR_CLAUDE_DESIGN": model.ready_for_claude_design,
        "ia_verdict": model.ia_verdict,
        "top_level_modes": list(model.top_level_modes),
        "global_surfaces": list(model.global_surfaces),
        "safe_action_tiers": list(model.safe_action_tiers),
        "settings_admin_runtime": model.settings_admin_runtime.as_payload(),
        "unknown_drift_queue": model.unknown_drift_queue.as_payload(),
        "artifact_provenance": [
            {
                "name": artifact.name,
                "path": artifact.path,
                "expected_sha256": artifact.expected_sha256,
                "actual_sha256": artifact.actual_sha256,
            }
            for artifact in package.artifacts
        ],
        "invariants": dict(model.invariants),
        "runtime_config": {
            "stale_proof_window_seconds": model.config.stale_proof_window_seconds,
            "confirm_flow_timeout_seconds": model.config.confirm_flow_timeout_seconds,
            "operator_id_when_unauthenticated": model.config.unauthenticated_operator_id,
        },
    }


def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in {"", "UNKNOWN"}
    if isinstance(value, (tuple, list, dict, set)):
        return len(value) == 0
    return False


def _nested_unknowns(prefix: str, value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        missing: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}"
            if _is_unknown(child):
                missing.append(child_prefix)
            else:
                missing.extend(_nested_unknowns(child_prefix, child))
        return tuple(missing)
    if isinstance(value, (list, tuple)):
        missing = []
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            if _is_unknown(child):
                missing.append(child_prefix)
            else:
                missing.extend(_nested_unknowns(child_prefix, child))
        return tuple(missing)
    return ()


def _missing_required_fields(candidate: dict[str, Any], tier: str) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in TIER_REQUIRED_FIELDS.get(tier, COMMON_REQUIRED_FIELDS):
        if field_name not in candidate or _is_unknown(candidate[field_name]):
            missing.append(field_name)
        else:
            missing.extend(_nested_unknowns(field_name, candidate[field_name]))
    return tuple(dict.fromkeys(missing))


def _parse_utc(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def evaluate_safe_action_preflight(
    candidate: dict[str, Any],
    *,
    current_row_hash: str | None = None,
    current_handoff_version: str | None = None,
    evaluated_at_utc: datetime | None = None,
    config: RuntimeConfig | None = None,
) -> PreflightResult:
    cfg = config or RuntimeConfig()
    tier = str(candidate.get("gate_tier", "UNKNOWN"))
    safety_class = str(candidate.get("safety_class", "UNKNOWN"))
    surface_origin = str(candidate.get("surface_origin", "UNKNOWN"))

    if tier in BLOCKED_TIERS or safety_class == "BLOCKED_IN_COCKPIT":
        return PreflightResult(
            "REFUSE_BLOCKED",
            False,
            "BLOCKED_IN_COCKPIT",
            (),
            "SHOW_BLOCKED_REASON",
        )
    if tier in UNKNOWN_TIERS or safety_class == "UNKNOWN":
        return PreflightResult(
            "REFUSE_UNKNOWN",
            False,
            "UNKNOWN_CLASS",
            (),
            "UNKNOWN_DRIFT_QUEUE",
        )
    if surface_origin in UNSAFE_SURFACE_ORIGINS or (
        surface_origin != "UNKNOWN" and surface_origin not in ALLOWED_SURFACE_ORIGINS
    ):
        return PreflightResult(
            "REFUSE_UNSAFE_SOURCE_SURFACE",
            False,
            "UNSAFE_SOURCE_SURFACE",
            (),
            "UNKNOWN_DRIFT_QUEUE",
        )
    if tier in EXECUTABLE_TIERS or tier == "T4":
        authority = str(candidate.get("authority_domain", "UNKNOWN"))
        writer = str(candidate.get("canonical_writer", "UNKNOWN"))
        if authority in {"UNKNOWN", "unknown / conflicting"} or writer in {
            "UNKNOWN",
            "unknown / conflicting",
        }:
            return PreflightResult(
                "REFUSE_AUTHORITY_CONFLICT",
                False,
                "AUTHORITY_CONFLICT",
                (),
                "UNKNOWN_DRIFT_QUEUE",
            )
    if tier == "T4":
        return PreflightResult(
            "REFUSE_T4_POLICY_MISSING",
            False,
            "REMOTE_MUTATION_POLICY_MISSING",
            (),
            "UNKNOWN_DRIFT_QUEUE",
        )
    if current_row_hash is not None:
        observed_hash = candidate.get("palette_index_row_hash")
        if observed_hash != current_row_hash:
            return PreflightResult(
                "REFUSE_INDEX_DRIFT",
                False,
                "INDEX_DRIFT",
                (),
                "RE_RENDER",
            )
    if current_handoff_version is not None:
        observed_version = candidate.get("handoff_contract_version")
        if observed_version not in {None, current_handoff_version}:
            return PreflightResult(
                "REFUSE_STALE_HANDOFF",
                False,
                "STALE_HANDOFF",
                (),
                "RE_RENDER",
            )
    created_at = candidate.get("created_at_utc")
    if isinstance(created_at, str):
        created_dt = _parse_utc(created_at)
        if created_dt is None:
            return PreflightResult(
                "REFUSE_STALE_HANDOFF",
                False,
                "STALE_HANDOFF",
                (),
                "RE_RENDER",
            )
        now = (evaluated_at_utc or datetime.now(UTC)).astimezone(UTC)
        age_seconds = int((now - created_dt).total_seconds())
        if age_seconds > cfg.stale_proof_window_seconds:
            return PreflightResult(
                "REFUSE_STALE_HANDOFF",
                False,
                "STALE_HANDOFF",
                (),
                "RE_RENDER",
            )

    missing = _missing_required_fields(candidate, tier)
    if missing:
        return PreflightResult(
            "REFUSE_MISSING_FIELD",
            False,
            "MISSING_REQUIRED_FIELD",
            missing,
            "UNKNOWN_DRIFT_QUEUE",
        )
    if tier in NON_CONFIRM_TIERS:
        return PreflightResult(
            "REFUSE_NON_EXECUTABLE_TIER",
            False,
            "NON_EXECUTABLE_TIER",
            (),
            "INSPECT_RESULT",
        )
    if tier not in CONFIRMABLE_TIERS:
        return PreflightResult(
            "REFUSE_MISSING_FIELD",
            False,
            "NON_EXECUTABLE_TIER",
            (),
            "UNKNOWN_DRIFT_QUEUE",
        )
    return PreflightResult(
        "ALLOW_CONFIRM",
        True,
        None,
        (),
        "NOT_APPLICABLE",
    )


SECRET_KEY_RE = re.compile(
    r"(token|password|secret|api[_-]?key|authorization|cookie|private[_-]?key|session)",
    re.IGNORECASE,
)

SECRET_VALUE_RE = re.compile(
    r"(bearer\s+)[A-Za-z0-9._~+/=-]+|"
    r"([A-Za-z0-9_]*token=)[^&\s]+|"
    r"((?:authorization|cookie|session)[=:]\s*)[^&\n]+|"
    r"((?:api[_-]?key|password|secret|private[_-]?key)[=:]\s*)[^&\s]+",
    re.IGNORECASE,
)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            if SECRET_KEY_RE.search(str(key)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_secrets(child)
        return redacted
    if isinstance(value, list):
        return [redact_secrets(child) for child in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(child) for child in value)
    if isinstance(value, str):
        return SECRET_VALUE_RE.sub(
            lambda match: (
                f"{match.group(1) or match.group(2) or match.group(3) or match.group(4)}"
                "[REDACTED]"
            ),
            value,
        )
    return value


def _utc_now_string(now: datetime | None = None) -> str:
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return current.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _gate_request_id(seed: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"dopemux:{RUNTIME_PACKET_ID}:{seed}"))


def build_gate_receipt(
    *,
    event_type: str,
    candidate: dict[str, Any],
    preflight: PreflightResult,
    proof_artifacts: dict[str, Any] | None = None,
    operator_id: str | None = None,
    created_at_utc: str | None = None,
    gate_request_id: str | None = None,
    config: RuntimeConfig | None = None,
) -> dict[str, Any]:
    if event_type not in RECEIPT_EVENT_TYPES:
        raise RuntimeContractError(f"[BLOCKER] unsupported receipt event type: {event_type}")

    cfg = config or RuntimeConfig()
    event_timestamp = created_at_utc or _utc_now_string()
    action_row_hash = str(candidate.get("action_row_hash") or stable_sha256(candidate))
    request_id = gate_request_id or _gate_request_id(f"{action_row_hash}:{event_timestamp}")
    confirmation_status = {
        "gate_open": "pending" if preflight.can_confirm else "refused",
        "gate_refuse": "refused",
        "gate_abort": "aborted",
        "gate_timeout": "timeout",
        "gate_confirmed": "confirmed",
        "gate_proof_captured": "confirmed",
        "gate_proof_incomplete": "confirmed",
        "gate_proof_stale": "pending",
    }[event_type]
    proof_status = {
        "gate_open": "not_yet_captured" if preflight.can_confirm else "not_required",
        "gate_refuse": "not_required",
        "gate_abort": "not_required",
        "gate_timeout": "not_required",
        "gate_confirmed": "not_yet_captured",
        "gate_proof_captured": "captured",
        "gate_proof_incomplete": "incomplete",
        "gate_proof_stale": "stale",
    }[event_type]
    receipt = {
        "gate_request_id": request_id,
        "palette_request_id": candidate.get("palette_request_id"),
        "action_row_hash": action_row_hash,
        "tier": candidate.get("gate_tier", "UNKNOWN"),
        "safety_class": candidate.get("safety_class", "UNKNOWN"),
        "authority_domain": candidate.get("authority_domain", "UNKNOWN"),
        "canonical_writer": candidate.get("canonical_writer", "UNKNOWN"),
        "preflight_status": (
            "resolved"
            if not preflight.missing_fields
            else f"unknown_fields:{list(preflight.missing_fields)}"
        ),
        "confirmation_status": confirmation_status,
        "execution_status": "not_attempted",
        "proof_status": proof_status,
        "proof_artifacts": proof_artifacts or {},
        "refusal_reason": preflight.refusal_reason,
        "routing_destination": preflight.routing_destination,
        "surface_origin": candidate.get("surface_origin", "UNKNOWN"),
        "operator_id": operator_id or cfg.unauthenticated_operator_id,
        "created_at_utc": event_timestamp,
        "event_type": event_type,
        "schema_version": "dopemux.cockpit.safe_action_gate.receipt.runtime_render.v1",
    }
    return redact_secrets(receipt)
