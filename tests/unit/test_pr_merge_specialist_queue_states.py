from src.dopemux_pr_merge_specialist.plan_builder import build_plan_result
from src.dopemux_pr_merge_specialist.schema import (
    CheckSummary,
    PullRequestState,
    ValidationReport,
    ValidationStatus,
)
from src.dopemux_pr_merge_specialist.ux_engine import (
    dashboard_status_icon,
    dashboard_status_kind,
)


def _base_policy() -> dict:
    return {
        "validation": {"require_local_validation_for_merge_ready": True},
        "gates": {},
        "thread_rules": {},
        "check_rules": {},
        "conflict_rules": {},
        "retry": {},
        "merge": {},
        "platform": {},
        "timeouts": {},
        "safety": {},
        "version": 1,
    }


def _base_check_payload(*, review_decision: str = "REVIEW_REQUIRED") -> dict:
    return {
        "summary": CheckSummary(
            total=1,
            success=1,
            failure=0,
            pending=0,
            required_pending=0,
            required_failure=0,
            optional_pending=0,
            optional_failure=0,
        ),
        "review_decision": review_decision,
        "approval_required": False,
        "mergeable": "MERGEABLE",
        "merge_state_status": "BLOCKED",
        "protection": {
            "available": True,
            "protected": True,
            "branch": "main",
            "required_approving_review_count": 0,
            "approval_required": False,
            "require_code_owner_reviews": False,
            "require_last_push_approval": False,
            "required_conversation_resolution": True,
            "required_status_checks": [],
            "strict_status_checks": True,
            "enforce_admins": True,
            "required_linear_history": True,
        },
        "blocker_types": [],
        "warning_types": ["approval_not_required"],
    }


def test_validation_only_pr_is_not_marked_queued_for_merge() -> None:
    pr = PullRequestState(
        pr_id=233,
        title="validation-only",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature",
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="BLOCKED",
        review_decision="REVIEW_REQUIRED",
        auto_merge_enabled=True,
        check_summary=CheckSummary(total=1, success=1),
    )
    validation = ValidationReport(
        status=ValidationStatus.NOT_EXECUTED,
        required_for_merge_ready=True,
        steps=[],
        attempts=0,
        remediation_applied=False,
    )

    result = build_plan_result(
        active_run_id="test",
        pr=pr,
        threads=[],
        check_payload=_base_check_payload(),
        validation_report=validation,
        policy=_base_policy(),
    )

    assert result.lifecycle_state == "apply_ready"
    assert result.artifacts.get("operator_state", "") == ""
    blocker_types = {item.finding_type for item in result.findings if item.kind.value == "blocker"}
    assert blocker_types == {"validation_not_executed"}


def test_dashboard_status_distinguishes_validation_vs_approval_vs_queued() -> None:
    validation_snapshot = {
        "is_draft": False,
        "lifecycle_state": "apply_blocked",
        "operator_state": "",
        "mergeable": "MERGEABLE",
        "merge_state_status": "BLOCKED",
        "blockers": [{"type": "validation_not_executed"}],
    }
    approval_snapshot = {
        "is_draft": False,
        "lifecycle_state": "apply_blocked",
        "operator_state": "",
        "mergeable": "MERGEABLE",
        "merge_state_status": "BLOCKED",
        "blockers": [{"type": "approval_missing"}],
    }
    queued_snapshot = {
        "is_draft": False,
        "lifecycle_state": "queued_for_merge",
        "operator_state": "queued_for_merge",
        "mergeable": "MERGEABLE",
        "merge_state_status": "BLOCKED",
        "blockers": [{"type": "required_check_pending"}],
    }

    assert dashboard_status_kind(validation_snapshot) == "validation_pending"
    assert dashboard_status_icon(validation_snapshot) == "🟡"
    assert dashboard_status_kind(approval_snapshot) == "approval_required"
    assert dashboard_status_icon(approval_snapshot) == "🟣"
    assert dashboard_status_kind(queued_snapshot) == "queued"
    assert dashboard_status_icon(queued_snapshot) == "🔵"
