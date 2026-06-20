"""DopetaskSequentialPlanRunner — sequence multi-packet execution."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .dopetask_packet_launcher import DopetaskPacketLauncher, PacketLaunchTrace


@dataclass
class PlanPacket:
    """A single packet definition within a sequential plan."""
    tp_id: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class SequentialPlan:
    """Internal plan for sequential execution."""
    plan_id: str
    packets: List[PlanPacket]
    base_branch: str = "main"


@dataclass
class SequentialPlanResult:
    """Aggregate result of a sequential plan execution."""
    plan_id: str
    status: str  # "SUCCESS" | "FAILED" | "ABORTED"
    traces: List[dict] = field(default_factory=list)
    attempted_count: int = 0
    completed_count: int = 0
    failure_point: Optional[str] = None
    computed_at: float = field(default_factory=time.time)


class PlanValidationError(ValueError):
    """Raised when a sequential plan structure is invalid."""


class DopetaskSequentialPlanRunner:
    """Execute an ordered sequence of task packets with fail-stop semantics."""

    def __init__(self, launcher: DopetaskPacketLauncher, bundle_root: Path) -> None:
        self.launcher = launcher
        self.bundle_root = Path(bundle_root)

    def run(self, plan: SequentialPlan, context: dict) -> SequentialPlanResult:
        """Execute the plan sequentially. Stops on first failure."""
        self._validate_plan(plan)

        traces: List[dict] = []
        completed_ids: Set[str] = set()
        status = "SUCCESS"
        failure_point = None

        for p_def in plan.packets:
            # 1. Dependency Check
            for dep_id in p_def.depends_on:
                if dep_id not in completed_ids:
                    # This should be caught by _validate_plan for static order,
                    # but we check here for runtime safety.
                    status = "ABORTED"
                    failure_point = p_def.tp_id
                    break
            
            if status != "SUCCESS":
                break

            # 2. Launch
            trace = self.launcher.launch(p_def.tp_id, context)
            traces.append(asdict(trace))
            
            if not trace.success:
                status = "FAILED"
                failure_point = p_def.tp_id
                break
            
            completed_ids.add(p_def.tp_id)

        result = SequentialPlanResult(
            plan_id=plan.plan_id,
            status=status,
            traces=traces,
            attempted_count=len(traces),
            completed_count=len(completed_ids),
            failure_point=failure_point,
        )

        self._write_result(result)
        return result

    def _validate_plan(self, plan: SequentialPlan) -> None:
        """Ensure all dependencies exist and are ordered before the packet."""
        known_ids = set()
        for p in plan.packets:
            if p.tp_id in known_ids:
                raise PlanValidationError(f"Duplicate packet ID in plan: '{p.tp_id}'")
            
            for dep_id in p.depends_on:
                if dep_id not in known_ids:
                    raise PlanValidationError(
                        f"Packet '{p.tp_id}' depends on '{dep_id}' which is not defined "
                        "before it in the sequential plan."
                    )
            known_ids.add(p.tp_id)

    def _write_result(self, result: SequentialPlanResult) -> None:
        """Persist the aggregate result to the bundle root."""
        out_path = self.bundle_root / "SEQUENTIAL_PLAN_RESULT.json"
        self.bundle_root.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
