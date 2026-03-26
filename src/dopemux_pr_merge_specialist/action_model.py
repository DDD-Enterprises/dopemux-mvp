from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Set

from .schema import (
    BlockerType,
    Finding,
    FindingSeverity,
    MergeActionType,
    PRResult,
    PRState,
    ValidationStatus,
)


VALIDATION_BLOCKERS = {
    "validation_not_executed",
    BlockerType.VALIDATION_FAILED.value,
}
FIXABLE_BLOCKERS = {
    *VALIDATION_BLOCKERS,
    BlockerType.ACTIVE_THREAD.value,
    BlockerType.CONFLICT_DETECTED.value,
    BlockerType.REQUIRED_CHECK_FAILED.value,
    BlockerType.REQUIRED_CHECK_PENDING.value,
    BlockerType.CHANGES_REQUESTED.value,
    "rebase_conflict",
    "draft_pr",
}
AUTO_MERGE_PASSIVE_BLOCKERS = {
    *VALIDATION_BLOCKERS,
    BlockerType.REQUIRED_CHECK_PENDING.value,
}
NON_AUTOMATABLE_BLOCKERS = {
    "manual_conflict_required",
    "semantic_conflict_blocked",
}
QUEUED_OPERATOR_STATES = {
    "queued_for_merge",
}


def enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def blocker_findings(findings: Sequence[Finding]) -> List[Finding]:
    return [
        item
        for item in findings
        if enum_value(getattr(item, "kind", "")) == FindingSeverity.BLOCKER.value
    ]


def warning_findings(findings: Sequence[Finding]) -> List[Finding]:
    return [
        item
        for item in findings
        if enum_value(getattr(item, "kind", "")) == FindingSeverity.WARNING.value
    ]


def blocker_types(findings: Sequence[Finding]) -> Set[str]:
    return {str(getattr(item, "finding_type", "")) for item in blocker_findings(findings)}


def blocker_types_from_snapshot(snapshot: Mapping[str, Any]) -> Set[str]:
    blockers = snapshot.get("blockers") or []
    return {
        str(item.get("type") or item.get("finding_type") or "")
        for item in blockers
        if isinstance(item, Mapping)
    }


def allowed_actions_for_snapshot(snapshot: Mapping[str, Any]) -> List[str]:
    lifecycle_state = enum_value(snapshot.get("lifecycle_state", ""))
    merge_strategy = enum_value(snapshot.get("merge_strategy", ""))
    pr_state = str(snapshot.get("state") or "").upper()
    is_draft = bool(snapshot.get("is_draft", False))
    auto_merge_enabled = bool(snapshot.get("auto_merge_enabled", False))
    blockers = blocker_types_from_snapshot(snapshot)
    validation_status = enum_value(
        (snapshot.get("validation_report") or {}).get("status", "")
    )

    if pr_state == "MERGED" or lifecycle_state == PRState.MERGED.value:
        return []
        
    # If we need to run validation, we should never be purely passive, even if queued for merge.
    needs_validation = bool(blockers & VALIDATION_BLOCKERS)

    if lifecycle_state == PRState.QUEUED_FOR_MERGE.value and not needs_validation:
        return []
        
    if auto_merge_enabled:
        if needs_validation:
            # We must run validation. Fall through to return APPLY_FIX.
            pass
        elif blockers <= AUTO_MERGE_PASSIVE_BLOCKERS:
            # All validation is done, just waiting on GitHub CI
            return []
            
    if str(snapshot.get("operator_state") or "") in QUEUED_OPERATOR_STATES and not needs_validation:
        return []
            
    if merge_strategy == MergeActionType.AUTO_MERGE_FALLBACK.value and not blockers:
        return []
    if is_draft:
        return ["READY"]
    if lifecycle_state == PRState.MERGE_READY.value:
        return ["MERGE"]
    if (
        not blockers
        and validation_status == ValidationStatus.PASSED.value
        and lifecycle_state in {PRState.APPLIED.value, PRState.APPLY_READY.value}
    ):
        return ["MERGE"]
    if (
        merge_strategy == MergeActionType.AUTO_MERGE_FALLBACK.value
        and blockers <= {BlockerType.REQUIRED_CHECK_PENDING.value}
    ):
        return ["MERGE"]
    if blockers == {BlockerType.APPROVAL_MISSING.value}:
        return ["APPROVE"]
    if blockers & NON_AUTOMATABLE_BLOCKERS:
        return []
    if blockers & FIXABLE_BLOCKERS:
        return ["APPLY_FIX"]
    return []


def allowed_actions_for_result(result: PRResult) -> List[str]:
    return allowed_actions_for_snapshot(result_to_dashboard_entry(result))


def dashboard_tactic_for_snapshot(snapshot: Mapping[str, Any]) -> str:
    allowed = list(snapshot.get("allowed_actions") or allowed_actions_for_snapshot(snapshot))
    blockers = blocker_types_from_snapshot(snapshot)

    if "READY" in allowed:
        return "R"
    if "MERGE" in allowed:
        return "I"
    if "APPROVE" in allowed:
        return "A"
    if "APPLY_FIX" in allowed:
        if blockers and blockers <= {*VALIDATION_BLOCKERS, BlockerType.REQUIRED_CHECK_PENDING.value}:
            return "V"
        return "P"
    return "S"


def result_to_dashboard_entry(result: PRResult) -> Dict[str, Any]:
    merge_strategy = (
        enum_value(result.merge_decision.action)
        if result.merge_decision is not None
        else MergeActionType.BLOCKED.value
    )
    entry = {
        "pr_id": result.pr_state.pr_id,
        "title": result.pr_state.title,
        "state": result.pr_state.state,
        "lifecycle_state": enum_value(result.lifecycle_state),
        "ci_status": getattr(result.pr_state, "ci_status", "UNKNOWN"),
        "unresolved_threads": getattr(result.pr_state, "unresolved_threads", 0),
        "risk_score": getattr(result.pr_state, "risk_score", 0.0),
        "is_draft": getattr(result.pr_state, "is_draft", False),
        "auto_merge_enabled": getattr(result.pr_state, "auto_merge_enabled", False),
        "review_decision": getattr(result.pr_state, "review_decision", ""),
        "mergeable": getattr(result.pr_state, "mergeable", ""),
        "merge_state_status": getattr(result.pr_state, "merge_state_status", ""),
        "validation_report": (
            result.validation_report.to_dict() if result.validation_report else {}
        ),
        "merge_strategy": merge_strategy,
        "rationale": result.merge_decision.reason if result.merge_decision else "",
        "operator_state": str(result.artifacts.get("operator_state", "")),
        "blockers": [item.as_blocker().to_dict() for item in blocker_findings(result.findings)],
        "warnings": [item.to_dict() for item in warning_findings(result.findings)],
    }
    entry["allowed_actions"] = allowed_actions_for_snapshot(entry)
    entry["blocker_types"] = sorted(blocker_types_from_snapshot(entry))
    return entry
