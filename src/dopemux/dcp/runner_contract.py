"""Backend runner interface — DMX-DCP-MODEL-ROUTING-MVP-0008 / R6.

Pure data models for runner invocation plans, results, proof envelopes,
and runner adapter protocols.

Hard invariants:
- ``invocation_authorized`` is always False for constructed plans/documents in this packet.
- No process execution, network, model, MCP, Dopetask, or shell execution is performed.
- ``execute_runner_plan`` always fails closed without running anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable


class RunnerPlanStatus(str, Enum):
    PLANNED_ONLY = "PLANNED_ONLY"
    BLOCKED = "BLOCKED"
    NOT_RUN = "NOT_RUN"


class RunnerContractError(ValueError):
    """Fail-closed runner contract error."""


@dataclass(frozen=True)
class RunnerInvocationPlan:
    runner_id: str
    argv: tuple[str, ...]
    cwd: str = "."
    env_allowlist: tuple[str, ...] = ()
    timeout_seconds: Optional[float] = None
    notes: str = ""
    invocation_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.runner_id.strip():
            raise RunnerContractError("runner_id must be non-empty")
        if self.invocation_authorized:
            raise RunnerContractError(
                "invocation_authorized must be false; no runner may be authorized in 0008/R6"
            )
        object.__setattr__(self, "argv", tuple(self.argv))
        object.__setattr__(self, "env_allowlist", tuple(self.env_allowlist))

    def to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary matching runner_contract.schema.json plan property."""
        d: dict[str, Any] = {
            "runner_id": self.runner_id,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "env_allowlist": list(self.env_allowlist),
        }
        if self.timeout_seconds is not None:
            d["timeout_seconds"] = float(self.timeout_seconds)
        if self.notes:
            d["notes"] = self.notes
        return d


@dataclass(frozen=True)
class RunnerResult:
    status: RunnerPlanStatus
    exit_code: Optional[int] = None
    stdout_digest: str = ""
    stderr_digest: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "exit_code": self.exit_code,
            "stdout_digest": self.stdout_digest,
            "stderr_digest": self.stderr_digest,
            "error": self.error,
        }


@dataclass(frozen=True)
class RunnerProofEnvelope:
    evidence_refs: tuple[str, ...] = ()
    non_claims: tuple[str, ...] = (
        "no_process_spawned",
        "no_network_call",
        "no_model_inference",
        "invocation_authorized=false",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_refs": list(self.evidence_refs),
            "non_claims": list(self.non_claims),
        }


@dataclass(frozen=True)
class RunnerContractDocument:
    plan: RunnerInvocationPlan
    result: RunnerResult
    proof_envelope: RunnerProofEnvelope = field(default_factory=RunnerProofEnvelope)
    schema_version: str = "1.0.0"
    invocation_authorized: bool = False

    def __post_init__(self) -> None:
        if self.invocation_authorized or self.plan.invocation_authorized:
            raise RunnerContractError("document cannot authorize invocation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "invocation_authorized": False,
            "plan": self.plan.to_dict(),
            "result": self.result.to_dict(),
            "proof_envelope": self.proof_envelope.to_dict(),
        }


@runtime_checkable
class RunnerAdapter(Protocol):
    """Protocol for inert backend runner adapters."""

    def plan_invocation(
        self,
        argv: Sequence[str],
        *,
        cwd: str = ".",
        timeout_seconds: Optional[float] = None,
        notes: str = "",
    ) -> RunnerInvocationPlan:
        """Construct a non-authorized runner invocation plan."""
        ...

    def execute(self, plan: RunnerInvocationPlan) -> RunnerResult:
        """Execute runner plan (fail-closed, invocation disabled)."""
        ...


class InertRunnerAdapter:
    """Default inert runner adapter enforcing invocation-disabled boundary."""

    def __init__(self, runner_id: str) -> None:
        self.runner_id = runner_id

    def plan_invocation(
        self,
        argv: Sequence[str],
        *,
        cwd: str = ".",
        timeout_seconds: Optional[float] = None,
        notes: str = "planned only; not authorized",
    ) -> RunnerInvocationPlan:
        return RunnerInvocationPlan(
            runner_id=self.runner_id,
            argv=tuple(argv),
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            notes=notes,
            invocation_authorized=False,
        )

    def execute(self, plan: RunnerInvocationPlan) -> RunnerResult:
        return execute_runner_plan(plan)


def build_blocked_plan(
    runner_id: str,
    argv: Sequence[str],
    *,
    cwd: str = ".",
    timeout_seconds: Optional[float] = None,
    notes: str = "planned only; not authorized",
) -> RunnerInvocationPlan:
    """Construct a non-authorized plan. Never sets invocation_authorized true."""
    return RunnerInvocationPlan(
        runner_id=runner_id,
        argv=tuple(argv),
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        notes=notes,
        invocation_authorized=False,
    )


def execute_runner_plan(plan: RunnerInvocationPlan) -> RunnerResult:
    """Fail-closed non-executor.

    Always returns NOT_RUN / BLOCKED without performing process execution or network I/O.
    """
    if plan.invocation_authorized:
        # Unreachable under normal construction; belt-and-suspenders.
        return RunnerResult(
            status=RunnerPlanStatus.BLOCKED,
            error="invocation_authorized true is forbidden",
        )
    return RunnerResult(
        status=RunnerPlanStatus.NOT_RUN,
        exit_code=None,
        error="runner execution is not authorized (0008 inert contract)",
    )


def document_plan(plan: RunnerInvocationPlan) -> RunnerContractDocument:
    result = execute_runner_plan(plan)
    return RunnerContractDocument(plan=plan, result=result)


__all__ = [
    "RunnerPlanStatus",
    "RunnerContractError",
    "RunnerInvocationPlan",
    "RunnerResult",
    "RunnerProofEnvelope",
    "RunnerContractDocument",
    "RunnerAdapter",
    "InertRunnerAdapter",
    "build_blocked_plan",
    "execute_runner_plan",
    "document_plan",
]
