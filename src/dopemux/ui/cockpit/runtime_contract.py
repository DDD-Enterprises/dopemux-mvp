"""Local-only Cockpit runtime primitives for the accepted IA package contract."""

from __future__ import annotations

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


@dataclass(frozen=True)
class PreflightResult:
    status: str
    can_confirm: bool
    refusal_reason: str | None
    missing_fields: tuple[str, ...]
    routing_destination: str
    execution_status: str = "not_attempted"


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
    r"(bearer\s+)[A-Za-z0-9._~+/=-]+|([A-Za-z0-9_]*token=)[^&\s]+",
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
        return SECRET_VALUE_RE.sub(lambda match: f"{match.group(1) or match.group(2)}[REDACTED]", value)
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
