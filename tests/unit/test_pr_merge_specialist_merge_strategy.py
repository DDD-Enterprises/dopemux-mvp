from src.dopemux_pr_merge_specialist.closed_loop_engine import ClosedLoopEngine
from src.dopemux_pr_merge_specialist.merge import decide_merge_action
from src.dopemux_pr_merge_specialist.schema import (
    CheckSummary,
    MergeActionType,
    PRResult,
    PRState,
    PullRequestState,
    ValidationReport,
    ValidationStatus,
)
from src.dopemux_pr_merge_specialist.strategy_library import (
    STRATEGY_EXECUTION_ORDER,
    STRATEGY_PRIORITY_BOOSTS,
    TRAIN_ELIGIBLE_STRATEGIES,
    select_strategy,
)


def _pr_state(*, ci_status: str = "SUCCESS", lifecycle_state: PRState = PRState.MERGE_READY) -> PullRequestState:
    return PullRequestState(
        pr_id=900,
        title="PR 900",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/900",
        ci_status=ci_status,
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="APPROVED",
        lifecycle_state=lifecycle_state,
    )


def _result(*, ci_status: str = "SUCCESS", lifecycle_state: str = PRState.MERGE_READY.value) -> PRResult:
    return PRResult(
        run_id="run",
        pr_state=_pr_state(ci_status=ci_status),
        lifecycle_state=lifecycle_state,
    )


def test_decide_merge_action_uses_auto_merge_enable_when_check_summary_is_pending() -> None:
    pr = _pr_state()
    pr = PullRequestState(**{**pr.to_dict(), "check_summary": CheckSummary(total=2, success=1, pending=1)})
    validation = ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=True,
        steps=[],
        attempts=1,
        remediation_applied=False,
    )

    decision = decide_merge_action(pr=pr, findings=[], validation_report=validation)

    assert decision.action == MergeActionType.AUTO_MERGE_ENABLE
    assert decision.reason_code == "auto_merge_active_checks"


def test_decide_merge_action_keeps_rebase_merge_when_check_summary_absent() -> None:
    validation = ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=True,
        steps=[],
        attempts=1,
        remediation_applied=False,
    )

    decision = decide_merge_action(pr=_pr_state(), findings=[], validation_report=validation)

    assert decision.action == MergeActionType.REBASE_MERGE
    assert decision.reason_code == "rebase_merge_ready"


def test_select_strategy_prefers_auto_merge_fallback_for_ready_pr_without_green_ci() -> None:
    assignment = select_strategy(_result(ci_status="PENDING"), {})

    assert assignment.strategy_id == "AUTO_MERGE_FALLBACK"
    assert assignment.priority_boost == STRATEGY_PRIORITY_BOOSTS["AUTO_MERGE_FALLBACK"]
    assert "AUTO_MERGE_FALLBACK" in TRAIN_ELIGIBLE_STRATEGIES
    assert STRATEGY_EXECUTION_ORDER["AUTO_MERGE_FALLBACK"] < STRATEGY_EXECUTION_ORDER["PATCH_ISOLATION_PLAN"]


def test_closed_loop_engine_prefers_auto_merge_fallback_for_ready_pr_without_green_ci() -> None:
    engine = ClosedLoopEngine(ops_engine=object(), strategy_library={})

    strategy_id = engine.select_strategy_for_state(
        {
            "lifecycle_state": "merge_ready",
            "pr_state": {
                "pr_class": "READY",
                "ci_status": "PENDING",
                "mergeable": "MERGEABLE",
                "merge_state_status": "CLEAN",
            },
        }
    )

    assert strategy_id == "AUTO_MERGE_FALLBACK"
