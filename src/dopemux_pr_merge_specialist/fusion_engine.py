"""TP-PRMS-054: Edit-Verify-Gate-Signoff Fusion Engine."""

from __future__ import annotations

import json
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .ops_engine import FlightDeckOpsEngine
from .patch_engine import PatchApplicationTrace, PatchClass, PatchEngine, PatchPlan


@dataclass
class SignoffPacket:
    packet_id: str  # uuid4
    patch_id: str
    trigger_reason: str
    patch_class: str
    risk_class: str
    verification_outcome: str
    owner: str
    state: str  # PENDING_SIGNOFF
    created_at: float


@dataclass
class DeferPacket:
    packet_id: str
    patch_id: str
    defer_reason: (
        str  # VERIFICATION_FAILED | INSUFFICIENT_EVIDENCE | POLICY_BLOCK | ...
    )
    blockers: list[dict]
    created_at: float


@dataclass
class FusionTrace:
    trace_id: str
    pr_id: str
    patch_id: str
    stages: list[dict]  # [{stage, outcome, timestamp}]
    signoff_packet: SignoffPacket | None
    defer_packet: DeferPacket | None
    final_state: dict
    computed_at: float


class FusionEngine:
    """Fuses patch application with verification, gate recompute, and signoff/defer surface."""

    def __init__(self, patch_engine: PatchEngine, ops_engine: FlightDeckOpsEngine):
        self.patch_engine = patch_engine
        self.ops = ops_engine

    def run_verification(
        self, plan: PatchPlan, apply_trace: PatchApplicationTrace
    ) -> dict:
        """Determine required checks from patch class + scope. Return {status, checks, passed}."""
        checks: list[str] = []
        patch_class = plan.patch_class

        if patch_class == PatchClass.DISALLOWED_PATCH:
            return {"status": "FAILED", "checks": ["DISALLOWED"], "passed": False}

        if patch_class in (PatchClass.SAFE_LOCAL_EDIT, PatchClass.SAFE_METADATA_EDIT):
            checks = ["SYNTAX_CHECK", "LINT_CHECK"]
        elif patch_class == PatchClass.LOW_RISK_PATCH_PROPOSAL:
            checks = ["SYNTAX_CHECK", "LINT_CHECK", "UNIT_TEST"]
        elif patch_class == PatchClass.SIGNOFF_REQUIRED_PATCH:
            checks = ["SYNTAX_CHECK", "LINT_CHECK", "UNIT_TEST", "INTEGRATION_CHECK"]
            if plan.scope.cross_file:
                checks.append("CROSS_FILE_IMPACT_CHECK")

        if apply_trace.outcome == "FAILED":
            return {"status": "FAILED", "checks": checks, "passed": False}

        # For simulation: all checks pass unless outcome is BLOCKED/FAILED
        passed = apply_trace.outcome not in ("BLOCKED", "FAILED")
        status = "PASSED" if passed else "FAILED"

        return {"status": status, "checks": checks, "passed": passed}

    def recompute_gate(
        self,
        verification: dict,
        posture: str,
        apply_trace: PatchApplicationTrace,
    ) -> dict:
        """Gate decision after patch+verify. Returns {decision, signoff_required, defer_required}."""
        if not verification.get("passed", False):
            return {
                "decision": "DEFER",
                "signoff_required": False,
                "defer_required": True,
                "reason": "Verification did not pass.",
            }

        if apply_trace.outcome in ("BLOCKED", "FAILED"):
            return {
                "decision": "DEFER",
                "signoff_required": False,
                "defer_required": True,
                "reason": f"Patch apply outcome is {apply_trace.outcome}.",
            }

        if apply_trace.outcome == "STAGED":
            return {
                "decision": "PENDING_SIGNOFF",
                "signoff_required": True,
                "defer_required": False,
                "reason": "Patch staged and awaiting signoff.",
            }

        # APPLIED
        gated_postures = {"HOLD", "CAUTION"}
        if posture in gated_postures:
            return {
                "decision": "PENDING_SIGNOFF",
                "signoff_required": True,
                "defer_required": False,
                "reason": f"Posture {posture} requires signoff even after apply.",
            }

        return {
            "decision": "APPROVED",
            "signoff_required": False,
            "defer_required": False,
            "reason": "Verification passed and patch applied cleanly.",
        }

    def generate_signoff_packet(
        self,
        plan: PatchPlan,
        verification: dict,
        gate: dict,
    ) -> SignoffPacket | None:
        """Returns SignoffPacket if signoff_required, else None."""
        if not gate.get("signoff_required", False):
            return None

        conditions = [
            plan.patch_class == PatchClass.SIGNOFF_REQUIRED_PATCH,
            plan.scope.risk_class in ("MEDIUM", "HIGH")
            and verification.get("passed", False),
            gate.get("decision") != "DEFER",
        ]
        # At least one condition triggers signoff
        if gate.get("signoff_required") or any(conditions):
            return SignoffPacket(
                packet_id=str(uuid.uuid4()),
                patch_id=plan.patch_id,
                trigger_reason=gate.get("reason", "Signoff required by policy."),
                patch_class=plan.patch_class.value,
                risk_class=plan.scope.risk_class,
                verification_outcome=verification.get("status", "UNKNOWN"),
                owner="operator",
                state="PENDING_SIGNOFF",
                created_at=time.time(),
            )
        return None

    def generate_defer_packet(
        self,
        plan: PatchPlan,
        verification: dict,
        gate: dict,
        blockers: list,
    ) -> DeferPacket | None:
        """Returns DeferPacket if defer_required, else None."""
        conditions = [
            verification.get("status") == "FAILED",
            gate.get("defer_required", False),
            gate.get("decision") == "DEFER",
            plan.patch_class == PatchClass.DISALLOWED_PATCH,
        ]
        if not any(conditions):
            return None

        if plan.patch_class == PatchClass.DISALLOWED_PATCH:
            reason = "POLICY_BLOCK"
        elif verification.get("status") == "FAILED":
            reason = "VERIFICATION_FAILED"
        else:
            reason = "INSUFFICIENT_EVIDENCE"

        return DeferPacket(
            packet_id=str(uuid.uuid4()),
            patch_id=plan.patch_id,
            defer_reason=reason,
            blockers=list(blockers),
            created_at=time.time(),
        )

    def fuse(
        self,
        pr_id: str,
        plan: PatchPlan,
        apply_trace: PatchApplicationTrace,
    ) -> FusionTrace:
        """Full pipeline: verify -> gate -> signoff/defer -> update state -> emit trace."""
        trace_id = str(uuid.uuid4())
        stages: list[dict] = []

        try:
            # Stage 1: Verify
            stages.append(
                {"stage": "VERIFY", "outcome": "STARTED", "timestamp": time.time()}
            )
            verification = self.run_verification(plan, apply_trace)
            stages.append(
                {
                    "stage": "VERIFY",
                    "outcome": verification["status"],
                    "timestamp": time.time(),
                }
            )

            # Stage 2: Gate recompute
            stages.append(
                {"stage": "GATE", "outcome": "STARTED", "timestamp": time.time()}
            )
            posture = self.patch_engine.posture
            gate = self.recompute_gate(verification, posture, apply_trace)
            stages.append(
                {
                    "stage": "GATE",
                    "outcome": gate["decision"],
                    "timestamp": time.time(),
                }
            )

            # Stage 3: Signoff / Defer
            stages.append(
                {
                    "stage": "SIGNOFF_OR_DEFER",
                    "outcome": "STARTED",
                    "timestamp": time.time(),
                }
            )
            blockers: list = []
            signoff_packet = self.generate_signoff_packet(plan, verification, gate)
            defer_packet = self.generate_defer_packet(
                plan, verification, gate, blockers
            )

            # Invariant: never both non-None simultaneously
            if signoff_packet and defer_packet:
                defer_packet = None

            final_outcome = (
                "SIGNOFF_PENDING"
                if signoff_packet
                else ("DEFERRED" if defer_packet else "CLEAN")
            )
            stages.append(
                {
                    "stage": "SIGNOFF_OR_DEFER",
                    "outcome": final_outcome,
                    "timestamp": time.time(),
                }
            )

            # Stage 4: Final state
            stages.append(
                {
                    "stage": "FINAL_STATE",
                    "outcome": "COMPLETE",
                    "timestamp": time.time(),
                }
            )
            final_state = {
                "pr_id": pr_id,
                "patch_id": plan.patch_id,
                "apply_outcome": apply_trace.outcome,
                "verification_status": verification["status"],
                "gate_decision": gate["decision"],
                "fusion_outcome": final_outcome,
            }

            return FusionTrace(
                trace_id=trace_id,
                pr_id=pr_id,
                patch_id=plan.patch_id,
                stages=stages,
                signoff_packet=signoff_packet,
                defer_packet=defer_packet,
                final_state=final_state,
                computed_at=time.time(),
            )

        except Exception:  # noqa: BLE001
            error_reason = traceback.format_exc()
            defer_pkt = DeferPacket(
                packet_id=str(uuid.uuid4()),
                patch_id=plan.patch_id if plan else "unknown",
                defer_reason="INTERNAL_ERROR",
                blockers=[{"id": "internal_error", "description": error_reason}],
                created_at=time.time(),
            )
            stages.append(
                {
                    "stage": "ERROR",
                    "outcome": "INTERNAL_ERROR",
                    "timestamp": time.time(),
                }
            )
            return FusionTrace(
                trace_id=trace_id,
                pr_id=pr_id,
                patch_id=plan.patch_id if plan else "unknown",
                stages=stages,
                signoff_packet=None,
                defer_packet=defer_pkt,
                final_state={"error": error_reason},
                computed_at=time.time(),
            )

    def emit_fusion_artifacts(self, trace: FusionTrace, out_dir: Path) -> list[str]:
        """Write 5 fusion artifact JSON files."""
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        def _ser(obj: Any) -> Any:
            if obj is None:
                return None
            return asdict(obj)

        artifacts = {
            "LOOP_FUSION_TRACE.json": {
                "trace_id": trace.trace_id,
                "pr_id": trace.pr_id,
                "patch_id": trace.patch_id,
                "stages": trace.stages,
                "final_state": trace.final_state,
                "computed_at": trace.computed_at,
            },
            "VERIFICATION_GATE_REPORT.json": {
                "trace_id": trace.trace_id,
                "patch_id": trace.patch_id,
                "stages": [s for s in trace.stages if s["stage"] in ("VERIFY", "GATE")],
            },
            "SIGNOFF_TRIGGER_REPORT.json": {
                "trace_id": trace.trace_id,
                "patch_id": trace.patch_id,
                "signoff_packet": _ser(trace.signoff_packet),
            },
            "DEFER_TRIGGER_REPORT.json": {
                "trace_id": trace.trace_id,
                "patch_id": trace.patch_id,
                "defer_packet": _ser(trace.defer_packet),
            },
            "POST_EDIT_STATE_RECOMPUTE.json": trace.final_state,
        }

        for name, data in artifacts.items():
            path = out_dir / name
            path.write_text(json.dumps(data, indent=2))
            written.append(str(path))

        return written
