"""DopetaskStatusMapper — map Dopetask governance states without flattening."""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Canonical value sets
# ---------------------------------------------------------------------------

TP_STATUS_VALUES = {
    "PLANNED",
    "IN_PROGRESS",
    "VALIDATED",
    "OPERATIONAL",
    "BLOCKED",
    "DEFERRED",
    "FAILED",
    "UNKNOWN",
}

POSTURE_MODE_VALUES = {
    "ADVISORY_ONLY",
    "GO_SUPERVISED_ONLY",
    "LIVE_SAFE",
    "DEFER_ONLY",
    "GO_FULL_AUTO",
    "HOLD",
    "UNKNOWN",
}

HEADLINE_STATE_VALUES = {
    "READY",
    "BLOCKED",
    "DEFERRED",
    "SUPERVISED",
    "INCIDENT",
    "UNKNOWN",
}

# Identity maps — Dopetask semantics preserved exactly
STATUS_MAP: dict[str, str] = {s: s for s in TP_STATUS_VALUES}
POSTURE_MAP: dict[str, str] = {p: p for p in POSTURE_MODE_VALUES}

# Derived headline state (display only — does NOT affect governance)
POSTURE_TO_HEADLINE: dict[str, str] = {
    "GO_SUPERVISED_ONLY": "SUPERVISED",
    "ADVISORY_ONLY": "SUPERVISED",
    "HOLD": "BLOCKED",
    "DEFER_ONLY": "DEFERRED",
    "GO_FULL_AUTO": "READY",
    "LIVE_SAFE": "READY",
    "UNKNOWN": "UNKNOWN",
}

# Default governance actions by posture
POSTURE_ALLOWED_ACTIONS: dict[str, list[str]] = {
    "GO_SUPERVISED_ONLY": ["APPLY_FIX", "MISSION_SUMMARY"],
    "ADVISORY_ONLY": ["MISSION_SUMMARY"],
    "LIVE_SAFE": ["APPLY_FIX", "APPROVE", "MISSION_SUMMARY"],
    "DEFER_ONLY": ["MISSION_SUMMARY"],
    "GO_FULL_AUTO": ["APPLY_FIX", "MERGE", "APPROVE", "MISSION_SUMMARY"],
    "HOLD": [],
    "UNKNOWN": [],
}

POSTURE_BLOCKED_ACTIONS: dict[str, list[str]] = {
    "GO_SUPERVISED_ONLY": ["HIGH_RISK_AUTO_APPLY"],
    "ADVISORY_ONLY": ["APPLY_FIX", "MERGE", "HIGH_RISK_AUTO_APPLY"],
    "LIVE_SAFE": ["HIGH_RISK_AUTO_APPLY"],
    "DEFER_ONLY": ["APPLY_FIX", "MERGE", "APPROVE"],
    "GO_FULL_AUTO": [],
    "HOLD": ["APPLY_FIX", "MERGE", "APPROVE", "HIGH_RISK_AUTO_APPLY"],
    "UNKNOWN": ["APPLY_FIX", "MERGE", "APPROVE", "HIGH_RISK_AUTO_APPLY"],
}


# ---------------------------------------------------------------------------
# Dataclasses (also imported by dopetask_bundle_loader and dopetask_adapter)
# ---------------------------------------------------------------------------


@dataclass
class DopetaskTPIdentity:
    id: str
    family: str
    lane: str
    title: str
    status: str
    run_id: str


@dataclass
class DopetaskTarget:
    repo: str
    worktree: str
    ref: str
    pr_number: int | None
    case_id: str | None


@dataclass
class DopetaskPosture:
    mode: str
    advisory_only: bool
    signoff_required: bool
    defer_only: bool
    auto_apply_allowed: bool
    auto_apply_risk_threshold: str


@dataclass
class DopetaskSummary:
    result: str
    next_action: str
    headline_state: str
    confidence: str
    risk: str
    key_findings: list[str]
    key_caveats: list[str]


@dataclass
class DopetaskProofRef:
    bundle_path: str
    bundle_present: bool
    archive_path: str | None
    archive_present: bool
    supporting_artifacts: list[str]


@dataclass
class DopetaskGovernance:
    allowed_actions: list[str]
    blocked_actions: list[str]
    signoff: dict  # {required, owner, reason}


@dataclass
class DopetaskOperatorView:
    open_first: str
    open_second: str | None
    recommended_panel: str
    artifact_priority: list[str]


@dataclass
class DopetaskIntegration:
    loaded_from: (
        str  # "canonical_bundle" | "compatibility_manifest" | "launch" | "bundle"
    )
    adapter_status: str  # "READY" | "DEGRADED" | "ERROR"
    errors: list[str]
    warnings: list[str]
    compatibility_mode: bool = False
    archive_expected: bool = False


@dataclass
class DopetaskAdapterResult:
    source: str
    schema_version: str
    tp: DopetaskTPIdentity
    target: DopetaskTarget
    posture: DopetaskPosture
    summary: DopetaskSummary
    proof: DopetaskProofRef
    governance: DopetaskGovernance
    operator_view: DopetaskOperatorView
    integration: DopetaskIntegration
    computed_at: str  # ISO-8601 timestamp from utc_now()


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class DopetaskStatusMapper:
    """Map Dopetask governance states preserving all semantics (no flattening)."""

    def map_status(self, status: str) -> str:
        """Return canonical status string; unknown values map to UNKNOWN."""
        return STATUS_MAP.get(status, "UNKNOWN")

    def map_posture(self, posture: str) -> str:
        """Return canonical posture string; unknown values map to UNKNOWN."""
        return POSTURE_MAP.get(posture, "UNKNOWN")

    def derive_posture_obj(self, posture_mode: str) -> DopetaskPosture:
        """Build DopetaskPosture from a canonical posture mode string."""
        m = self.map_posture(posture_mode)
        return DopetaskPosture(
            mode=m,
            advisory_only=(m == "ADVISORY_ONLY"),
            signoff_required=(m in {"GO_SUPERVISED_ONLY", "ADVISORY_ONLY"}),
            defer_only=(m == "DEFER_ONLY"),
            auto_apply_allowed=(
                m in {"GO_FULL_AUTO", "LIVE_SAFE", "GO_SUPERVISED_ONLY"}
            ),
            auto_apply_risk_threshold=(
                "HIGH"
                if m == "GO_FULL_AUTO"
                else "MEDIUM" if m == "LIVE_SAFE" else "LOW"
            ),
        )

    def derive_governance(
        self,
        status: str,
        posture: str,
        bundle: dict,
    ) -> DopetaskGovernance:
        """Derive governance object from posture + bundle data."""
        pm = self.map_posture(posture)
        allowed = list(
            bundle.get("allowed_actions", POSTURE_ALLOWED_ACTIONS.get(pm, []))
        )
        blocked = list(
            bundle.get("blocked_actions", POSTURE_BLOCKED_ACTIONS.get(pm, []))
        )
        signoff_required = pm in {"GO_SUPERVISED_ONLY", "ADVISORY_ONLY"}
        return DopetaskGovernance(
            allowed_actions=allowed,
            blocked_actions=blocked,
            signoff={
                "required": signoff_required,
                "owner": "human_integrator" if signoff_required else "",
                "reason": (
                    "Supervised posture requires explicit review"
                    if pm == "GO_SUPERVISED_ONLY"
                    else (
                        "Advisory posture: no automated action permitted"
                        if pm == "ADVISORY_ONLY"
                        else ""
                    )
                ),
            },
        )

    def derive_next_action(
        self,
        status: str,
        posture: str,
        caveats: list[str],
    ) -> str:
        """Derive a single operator instruction from posture and status."""
        s = self.map_status(status)
        p = self.map_posture(posture)

        if s == "FAILED":
            base = (
                "Engine run failed. Review errors and relaunch with corrected context."
            )
        elif s == "BLOCKED":
            base = "Engine blocked. Resolve blockers before proceeding."
        elif p == "GO_SUPERVISED_ONLY":
            base = "Review engine output and apply approved fixes with signoff."
        elif p == "ADVISORY_ONLY":
            base = "Review advisory output. No automated action will be taken."
        elif p == "HOLD":
            base = "Engine is on HOLD. No actions permitted. Investigate blockers."
        elif p == "DEFER_ONLY":
            base = "All actions deferred. Human operator must initiate manually."
        elif p == "GO_FULL_AUTO" and s == "VALIDATED":
            base = "Automation ready. Engine will apply fixes within risk threshold."
        elif p == "LIVE_SAFE" and s == "VALIDATED":
            base = "Safe automation active. Monitor for unexpected changes."
        else:
            base = "Status unknown. Verify bundle integrity and rerun."

        if caveats:
            note = " Note: " + "; ".join(caveats[:3])
            return base + note
        return base

    def derive_headline_state(self, posture: str, status: str) -> str:
        """Derive display-only headline state.

        Status overrides posture for FAILED and BLOCKED tp states.
        """
        s = self.map_status(status)
        p = self.map_posture(posture)
        if s == "FAILED":
            return "INCIDENT"
        if s == "BLOCKED":
            return "BLOCKED"
        return POSTURE_TO_HEADLINE.get(p, "UNKNOWN")

    def derive_recommended_panel(self, posture: str) -> str:
        """Return recommended operator panel name based on posture."""
        p = self.map_posture(posture)
        panel_map = {
            "GO_SUPERVISED_ONLY": "mission_header",
            "ADVISORY_ONLY": "mission_header",
            "HOLD": "detail",
            "DEFER_ONLY": "summary",
            "GO_FULL_AUTO": "summary",
            "LIVE_SAFE": "summary",
            "UNKNOWN": "detail",
        }
        return panel_map.get(p, "detail")
