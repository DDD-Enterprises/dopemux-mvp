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
        if not allowed_actions:
            return {
                "tactic": "DEFER",
                "rationale": "No allowed actions available; failing closed to DEFER.",
                "safe_to_auto_stage": False,
                "strategy_id": strategy_id,
                }

        # Fallback: pick first allowed action
        first = allowed_actions[0]
        return {
            "tactic": first,
            "rationale": f"No priority match; selected first allowed action: '{first}'.",
            "safe_to_auto_stage": False,
            "strategy_id": strategy_id,
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
