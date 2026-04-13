from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    adapter_name: str
    case_id: str
    succeeded: bool
    contract_gate_pass: bool
    contract_gate_strength: str
    contract_fail_reason: str | None
    output_artifact_ref: str
    outputs: dict[str, Any]
    route_trace: dict[str, Any]
    task_eval: dict[str, Any]
    executor_links: dict[str, Any]
    validator_inputs: dict[str, Any]
    repair_invocations: int = 0
    sidefill_invocations: int = 0
    route_hop_total: int = 0
    work_root: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutorAdapter:
    adapter_name = "base"

    def validate_case(self, case: dict[str, Any]) -> None:
        if not isinstance(case, dict) or not str(case.get("case_id") or "").strip():
            raise ValueError("benchmark case is required for executor adapter")

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        raise NotImplementedError

