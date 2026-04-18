from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted({value for value in values if value})


@dataclass(frozen=True)
class MutationPolicyDecision:
    operation: str
    operation_class: str
    preview: bool
    allowed: bool
    workspace_scoped: bool
    deterministic: bool
    preview_required: bool
    execution_mode: str
    requires_approval: bool
    blast_radius: int
    affected_files: List[str] = field(default_factory=list)
    approval_level: str = "direct"
    risk_tier: str = "low"
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "operation_class": self.operation_class,
            "preview": self.preview,
            "allowed": self.allowed,
            "workspace_scoped": self.workspace_scoped,
            "deterministic": self.deterministic,
            "preview_required": self.preview_required,
            "execution_mode": self.execution_mode,
            "requires_approval": self.requires_approval,
            "blast_radius": self.blast_radius,
            "affected_files": list(self.affected_files),
            "approval_level": self.approval_level,
            "risk_tier": self.risk_tier,
            "reason": self.reason,
        }

    def approval_receipt(self) -> Dict[str, Any]:
        if self.execution_mode == "direct":
            execution_status = "ready"
        elif self.preview:
            execution_status = "preview_only"
        else:
            execution_status = "approval_required"

        return {
            "operation": self.operation,
            "operation_class": self.operation_class,
            "execution_mode": self.execution_mode,
            "execution_status": execution_status,
            "requires_approval": self.requires_approval,
            "preview_required": self.preview_required,
            "approval_level": self.approval_level,
            "risk_tier": self.risk_tier,
            "blast_radius": self.blast_radius,
            "affected_files": list(self.affected_files),
            "affected_file_summary": {
                "count": len(self.affected_files),
                "files": list(self.affected_files),
            },
            "reason": self.reason,
        }


class MutationPolicy:
    """Explicit, deterministic mutation policy for dopeCode operations."""

    def __init__(self, workspace_root: Path, workspace_id: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = workspace_id

    def _decision(
        self,
        *,
        operation: str,
        operation_class: str,
        preview: bool,
        affected_files: Sequence[str],
        approval_level: str,
        preview_required: bool,
        execution_mode: str,
        requires_approval: bool,
        risk_tier: str,
        reason: str,
    ) -> MutationPolicyDecision:
        files = _sorted_unique(affected_files)
        return MutationPolicyDecision(
            operation=operation,
            operation_class=operation_class,
            preview=preview,
            allowed=True,
            workspace_scoped=True,
            deterministic=True,
            preview_required=preview_required,
            execution_mode=execution_mode,
            requires_approval=requires_approval,
            blast_radius=len(files),
            affected_files=files,
            approval_level=approval_level,
            risk_tier=risk_tier,
            reason=reason,
        )

    def single_file_patch(self, relative_path: str, preview: bool) -> MutationPolicyDecision:
        return self._decision(
            operation="apply_patch",
            operation_class="single_file_patch",
            preview=preview,
            affected_files=[relative_path],
            approval_level="direct",
            preview_required=False,
            execution_mode="direct",
            requires_approval=False,
            risk_tier="low",
            reason="Bounded patch on one workspace file remains directly executable.",
        )

    def batch_patch(self, operations: Sequence[Dict[str, Any]], preview: bool) -> MutationPolicyDecision:
        files = [op.get("path") for op in operations if op.get("path")]
        return self._decision(
            operation="batch_apply_patch",
            operation_class="multi_file_patch",
            preview=preview,
            affected_files=files,
            approval_level="preview_required" if preview else "apply_after_preview",
            preview_required=True,
            execution_mode="preview_required" if preview else "approval_required",
            requires_approval=not preview,
            risk_tier="medium" if len(_sorted_unique(files)) <= 3 else "high",
            reason="Batch operations expose blast radius and require explicit preview semantics.",
        )

    def refactor(self, operation: str, symbol_id: str, affected_files: Sequence[str], preview: bool) -> MutationPolicyDecision:
        files = _sorted_unique(affected_files)
        approval_level = "single_file" if len(files) <= 1 else "multi_file"
        return self._decision(
            operation=operation,
            operation_class="symbol_refactor",
            preview=preview,
            affected_files=files,
            approval_level=approval_level,
            preview_required=True,
            execution_mode="preview_required" if preview else "approval_required",
            requires_approval=not preview,
            risk_tier="medium" if len(files) <= 1 else "high",
            reason="Symbol refactors must surface blast radius before apply.",
        )
