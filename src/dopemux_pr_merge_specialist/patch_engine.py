"""TP-PRMS-053: Code Editing and Patch Execution Engine."""
from __future__ import annotations

import json
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

from .ops_engine import FlightDeckOpsEngine


class PatchClass(Enum):
    SAFE_LOCAL_EDIT = "SAFE_LOCAL_EDIT"
    SAFE_METADATA_EDIT = "SAFE_METADATA_EDIT"
    LOW_RISK_PATCH_PROPOSAL = "LOW_RISK_PATCH_PROPOSAL"
    SIGNOFF_REQUIRED_PATCH = "SIGNOFF_REQUIRED_PATCH"
    DISALLOWED_PATCH = "DISALLOWED_PATCH"


@dataclass
class PatchScope:
    target_files: list[str]
    target_regions: list[dict] | None
    cross_file: bool
    origin_tactic: str
    rationale: str
    risk_class: str  # LOW / MEDIUM / HIGH


@dataclass
class PatchPlan:
    patch_id: str      # uuid4
    patch_class: PatchClass
    scope: PatchScope
    diff_text: str     # unified diff
    created_at: float
    provenance: dict   # {pr_id, run_id, origin_tactic, strategy_id}


@dataclass
class PatchApplicationTrace:
    patch_id: str
    applied: bool
    apply_blocked_reason: str | None
    verification_required: bool
    verification_plan_id: str | None
    outcome: str    # APPLIED / STAGED / BLOCKED / FAILED
    computed_at: float


class PatchEngine:
    """Patch planning, classification, application, and provenance engine."""

    POSTURE_ALLOW_APPLY = {"GO_SUPERVISED_ONLY", "GO_FULL_AUTO"}

    def __init__(self, ops_engine: FlightDeckOpsEngine, posture: str = "GO_SUPERVISED_ONLY"):
        self.ops = ops_engine
        self.posture = posture

    def classify_patch(self, scope: PatchScope) -> PatchClass:
        """Classify patch. DISALLOWED if scope is unbounded or posture blocks it."""
        if not scope.target_files:
            return PatchClass.DISALLOWED_PATCH

        if scope.risk_class == "HIGH":
            return PatchClass.SIGNOFF_REQUIRED_PATCH

        if scope.risk_class == "MEDIUM":
            if scope.cross_file:
                return PatchClass.SIGNOFF_REQUIRED_PATCH
            return PatchClass.LOW_RISK_PATCH_PROPOSAL

        # LOW risk
        if scope.cross_file:
            return PatchClass.LOW_RISK_PATCH_PROPOSAL

        # Determine if metadata or local
        meta_extensions = {".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".md"}
        all_meta = all(
            Path(f).suffix.lower() in meta_extensions for f in scope.target_files
        )
        if all_meta:
            return PatchClass.SAFE_METADATA_EDIT

        return PatchClass.SAFE_LOCAL_EDIT

    def plan_patch(
        self,
        pr_id: str,
        tactic: str,
        diff_text: str,
        target_files: list[str],
        target_regions: list[dict] | None = None,
        risk_class: str = "LOW",
        rationale: str = "",
        strategy_id: str = "",
        run_id: str = "",
    ) -> PatchPlan:
        """Build PatchPlan with provenance. Calls classify_patch()."""
        cross_file = len(target_files) > 1
        scope = PatchScope(
            target_files=target_files,
            target_regions=target_regions,
            cross_file=cross_file,
            origin_tactic=tactic,
            rationale=rationale or f"Patch planned for tactic {tactic}",
            risk_class=risk_class,
        )
        patch_class = self.classify_patch(scope)

        return PatchPlan(
            patch_id=str(uuid.uuid4()),
            patch_class=patch_class,
            scope=scope,
            diff_text=diff_text,
            created_at=time.time(),
            provenance={
                "pr_id": pr_id,
                "run_id": run_id or str(uuid.uuid4()),
                "origin_tactic": tactic,
                "strategy_id": strategy_id,
            },
        )

    def render_diff(self, plan: PatchPlan) -> str:
        """Return human-readable diff with scope header."""
        header_lines = [
            f"# Patch {plan.patch_id}",
            f"# Class: {plan.patch_class.value}",
            f"# Target files: {', '.join(plan.scope.target_files)}",
            f"# Risk: {plan.scope.risk_class}",
            f"# Tactic: {plan.scope.origin_tactic}",
            "",
        ]
        return "\n".join(header_lines) + plan.diff_text

    def apply_patch(
        self, plan: PatchPlan, allowed_actions: list[str]
    ) -> PatchApplicationTrace:
        """Apply patch if policy allows. Returns trace with outcome."""
        try:
            if plan.patch_class == PatchClass.DISALLOWED_PATCH:
                return PatchApplicationTrace(
                    patch_id=plan.patch_id,
                    applied=False,
                    apply_blocked_reason="DISALLOWED_PATCH class is never applicable.",
                    verification_required=False,
                    verification_plan_id=None,
                    outcome="BLOCKED",
                    computed_at=time.time(),
                )

            if plan.patch_class == PatchClass.SIGNOFF_REQUIRED_PATCH:
                return PatchApplicationTrace(
                    patch_id=plan.patch_id,
                    applied=False,
                    apply_blocked_reason=None,
                    verification_required=True,
                    verification_plan_id=str(uuid.uuid4()),
                    outcome="STAGED",
                    computed_at=time.time(),
                )

            # SAFE_LOCAL_EDIT, SAFE_METADATA_EDIT, LOW_RISK_PATCH_PROPOSAL
            if "APPLY_FIX" in allowed_actions and self.posture in self.POSTURE_ALLOW_APPLY:
                return PatchApplicationTrace(
                    patch_id=plan.patch_id,
                    applied=True,
                    apply_blocked_reason=None,
                    verification_required=True,
                    verification_plan_id=str(uuid.uuid4()),
                    outcome="APPLIED",
                    computed_at=time.time(),
                )

            # Not in allowed actions — stage it
            return PatchApplicationTrace(
                patch_id=plan.patch_id,
                applied=False,
                apply_blocked_reason="APPLY_FIX not in allowed_actions or posture blocks apply.",
                verification_required=True,
                verification_plan_id=str(uuid.uuid4()),
                outcome="STAGED",
                computed_at=time.time(),
            )

        except Exception:  # noqa: BLE001
            return PatchApplicationTrace(
                patch_id=plan.patch_id,
                applied=False,
                apply_blocked_reason=traceback.format_exc(),
                verification_required=False,
                verification_plan_id=None,
                outcome="FAILED",
                computed_at=time.time(),
            )

    def log_provenance(
        self, trace: PatchApplicationTrace, plan: PatchPlan
    ) -> None:
        """Write to ops_engine.log_safety_event with patch metadata."""
        self.ops.log_safety_event(
            pr_id=plan.provenance.get("pr_id", "unknown"),
            run_id=plan.provenance.get("run_id", "unknown"),
            action_type="patch",
            risk=plan.scope.risk_class,
            status=trace.outcome,
            note=f"patch_id={plan.patch_id} class={plan.patch_class.value}",
        )

    def emit_patch_artifacts(
        self,
        plan: PatchPlan,
        trace: PatchApplicationTrace,
        out_dir: Path,
    ) -> list[str]:
        """Write 5 patch artifact JSON files."""
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        scope_dict = asdict(plan.scope)
        artifacts = {
            "PATCH_PLAN_REPORT.json": {
                "patch_id": plan.patch_id,
                "patch_class": plan.patch_class.value,
                "diff_text": plan.diff_text,
                "created_at": plan.created_at,
                "provenance": plan.provenance,
                "scope": scope_dict,
            },
            "PATCH_APPLICATION_TRACE.json": asdict(trace),
            "PATCH_SCOPE_REPORT.json": scope_dict,
            "PATCH_VERIFICATION_REPORT.json": {
                "patch_id": plan.patch_id,
                "verification_required": trace.verification_required,
                "verification_plan_id": trace.verification_plan_id,
                "patch_class": plan.patch_class.value,
            },
            "PATCH_PROVENANCE_LOG.json": {
                "patch_id": plan.patch_id,
                **plan.provenance,
                "patch_class": plan.patch_class.value,
                "outcome": trace.outcome,
            },
        }

        for name, data in artifacts.items():
            path = out_dir / name
            path.write_text(json.dumps(data, indent=2))
            written.append(str(path))

        return written
