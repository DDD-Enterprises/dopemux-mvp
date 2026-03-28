"""TP-PRMS-052: Closed-Loop Automation Engine."""

from __future__ import annotations

import json
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .ops_engine import FlightDeckOpsEngine


@dataclass
class ClosedLoopTrace:
    """Audit record for one full closed-loop cycle."""

    pr_id: str
    cycle_id: str  # uuid4
    implicit_actions: list[dict]  # {action, reason, timestamp}
    state_before: dict
    state_after: dict
    next_tactic: str
    posture: str
    computed_at: float
    error: str | None = None
    strategy_id: str = ""


TACTIC_PRIORITY = [
    "MERGE",
    "REQUEST_CHANGES",
    "APPROVE",
    "APPLY_FIX",
    "REQUEST_REVIEW",
    "DEFER",
]


class ClosedLoopEngine:
    """Closed-loop automation engine for mission state refresh and tactic selection."""

    def __init__(self, ops_engine: FlightDeckOpsEngine, strategy_library: dict):
        self.ops = ops_engine
        self.strategy_library = strategy_library

    def refresh_mission_state(self, pr_id: str, current_report: dict) -> dict:
        """Reload posture, blockers, artifacts. Returns updated state dict."""
        state = dict(current_report)
        state.setdefault("pr_id", pr_id)
        state.setdefault("posture", "HOLD")
        state.setdefault("blockers", [])
        state.setdefault("allowed_actions", [])
        state.setdefault("refreshed_at", time.time())
        return state

    def select_strategy_for_state(self, state: dict) -> str:
        """Derive merge strategy from PR state signals. Returns strategy_id."""
        pr_class = str(state.get("pr_state", {}).get("pr_class", "") or "")
        ci_status = str(
            state.get("pr_state", {}).get("ci_status", "") or ""
        ).upper()
        mergeable = str(
            state.get("pr_state", {}).get("mergeable", "") or ""
        ).upper()
        lifecycle = str(state.get("lifecycle_state", "") or "").lower()

        # Conflicting PRs
        if mergeable == "CONFLICTING":
            if pr_class == "MIXED":
                return "STAGED_SEQUENCE_MERGE"
            return "OURS_THEN_PORT_SELECTIVE"

        # Green and ready
        if lifecycle in ("merge_ready", "queued_for_merge") and ci_status == "SUCCESS":
            return "DIRECT_REBASE_MERGE"

        # CI failures
        if pr_class == "CI_ONLY":
            return "PATCH_ISOLATION_PLAN"

        # Mixed blockers
        if pr_class == "MIXED":
            return "STAGED_SEQUENCE_MERGE"

        return "DIRECT_REBASE_MERGE"

    def select_next_tactic(self, state: dict, allowed_actions: list[str]) -> dict:
        """Return {tactic, rationale, safe_to_auto_stage, strategy_id}. Fails closed -> DEFER."""
        strategy_id = self.select_strategy_for_state(state)

        if not allowed_actions:
            return {
                "tactic": "DEFER",
                "rationale": "No allowed actions available; failing closed to DEFER.",
                "safe_to_auto_stage": False,
                "strategy_id": strategy_id,
            }

        for tactic in TACTIC_PRIORITY:
            if tactic in allowed_actions:
                safe = tactic not in ("MERGE", "APPLY_FIX", "APPROVE")
                return {
                    "tactic": tactic,
                    "rationale": f"Selected '{tactic}' as highest-priority available action.",
                    "safe_to_auto_stage": safe,
                    "strategy_id": strategy_id,
                }

        # Fallback: pick first allowed action
        first = allowed_actions[0]
        return {
            "tactic": first,
            "rationale": f"No priority match; selected first allowed action: '{first}'.",
            "safe_to_auto_stage": False,
            "strategy_id": strategy_id,
        }

    def recompute_summary(self, pr_id: str, event: dict, state: dict) -> dict:
        """After any meaningful event, recompute posture + blockers + next action."""
        new_state = dict(state)
        event_type = event.get("type", "unknown")

        # Update posture based on event type
        if event_type == "checks_passed":
            new_state["posture"] = "GO_SUPERVISED_ONLY"
        elif event_type == "checks_failed":
            new_state["posture"] = "HOLD"
        elif event_type == "patch_applied":
            new_state["posture"] = new_state.get("posture", "GO_SUPERVISED_ONLY")

        # Recompute blockers
        blockers = list(new_state.get("blockers", []))
        resolved = event.get("resolved_blockers", [])
        blockers = [b for b in blockers if b.get("id") not in resolved]
        new_state["blockers"] = blockers
        new_state["recomputed_at"] = time.time()
        new_state["last_event"] = event

        return new_state

    def run_cycle(self, pr_id: str, report: dict) -> ClosedLoopTrace:
        """Full loop: refresh -> select tactic -> recompute -> emit trace."""
        cycle_id = str(uuid.uuid4())
        implicit_actions: list[dict] = []
        state_before = dict(report)

        try:
            # Phase 1: Refresh
            implicit_actions.append(
                {
                    "action": "REFRESH_STATE",
                    "reason": "Starting closed-loop cycle",
                    "timestamp": time.time(),
                }
            )
            state = self.refresh_mission_state(pr_id, report)

            # Phase 2: Select tactic
            implicit_actions.append(
                {
                    "action": "SELECT_TACTIC",
                    "reason": "Computing next safe tactic",
                    "timestamp": time.time(),
                }
            )
            allowed = state.get("allowed_actions", [])
            tactic_result = self.select_next_tactic(state, allowed)

            # Phase 3: Recompute summary
            implicit_actions.append(
                {
                    "action": "RECOMPUTE_SUMMARY",
                    "reason": "Updating posture and blockers after tactic selection",
                    "timestamp": time.time(),
                }
            )
            state_after = self.recompute_summary(
                pr_id, {"type": "cycle_complete"}, state
            )
            state_after["selected_tactic"] = tactic_result["tactic"]

            return ClosedLoopTrace(
                pr_id=pr_id,
                cycle_id=cycle_id,
                implicit_actions=implicit_actions,
                state_before=state_before,
                state_after=state_after,
                next_tactic=tactic_result["tactic"],
                posture=state_after.get("posture", "HOLD"),
                computed_at=time.time(),
                strategy_id=tactic_result.get("strategy_id", ""),
            )

        except Exception as exc:  # noqa: BLE001
            return ClosedLoopTrace(
                pr_id=pr_id,
                cycle_id=cycle_id,
                implicit_actions=implicit_actions,
                state_before=state_before,
                state_after=state_before,
                next_tactic="DEFER",
                posture="HOLD",
                computed_at=time.time(),
                error=traceback.format_exc(),
            )

    def emit_trace_artifacts(self, trace: ClosedLoopTrace, out_dir: Path) -> list[str]:
        """Write 4 JSON trace artifacts."""
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        artifacts = {
            "CLOSED_LOOP_TRACE.json": asdict(trace),
            "IMPLICIT_ACTION_LOG.json": {
                "pr_id": trace.pr_id,
                "cycle_id": trace.cycle_id,
                "implicit_actions": trace.implicit_actions,
            },
            "STATE_RECOMPUTE_REPORT.json": {
                "pr_id": trace.pr_id,
                "cycle_id": trace.cycle_id,
                "state_before": trace.state_before,
                "state_after": trace.state_after,
            },
            "NEXT_ACTION_SELECTION_REPORT.json": {
                "pr_id": trace.pr_id,
                "cycle_id": trace.cycle_id,
                "next_tactic": trace.next_tactic,
                "strategy_id": trace.strategy_id,
                "posture": trace.posture,
                "computed_at": trace.computed_at,
            },
        }

        for name, data in artifacts.items():
            path = out_dir / name
            path.write_text(json.dumps(data, indent=2))
            written.append(str(path))

        return written
