from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import PRResult


@dataclass(frozen=True)
class StrategyDefinition:
    id: str
    name: str
    category: Literal["STRUCTURAL", "SEQUENTIAL", "CONTRACT", "RISK_REDUCTION"]
    description: str
    use_case: str
    anti_case: str
    risk_profile: Literal["LOW", "MEDIUM", "HIGH"]
    verification_burden: Literal["STANDARD", "ENHANCED", "CRITICAL"]


@dataclass(frozen=True)
class StrategyAssignment:
    strategy_id: str
    rationale: str
    priority_boost: float


STRATEGY_LIBRARY = {
    # Direct (simplest path)
    "DIRECT_REBASE_MERGE": StrategyDefinition(
        id="DIRECT_REBASE_MERGE",
        name="Direct Rebase Merge",
        category="STRUCTURAL",
        description="Standard rebase onto main and merge. No special handling needed.",
        use_case="Clean PRs with green CI and no conflicts.",
        anti_case="PRs with conflicts or failing CI.",
        risk_profile="LOW",
        verification_burden="STANDARD",
    ),
    # Structural
    "OURS_THEN_PORT_SELECTIVE": StrategyDefinition(
        id="OURS_THEN_PORT_SELECTIVE",
        name="Ours then Port Selective",
        category="STRUCTURAL",
        description="Use ours as structural base, port specific changes from theirs.",
        use_case="Refactor on ours, bugfix on theirs.",
        anti_case="Structural drift is too large to map hunks safely.",
        risk_profile="MEDIUM",
        verification_burden="STANDARD",
    ),
    "THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR": StrategyDefinition(
        id="THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR",
        name="Theirs then Reapply Local",
        category="STRUCTURAL",
        description="Use theirs as structural base, reapply local behavior from ours.",
        use_case="Upstream migration where theirs is authoritative.",
        anti_case="Local behavior is too coupled to old structure.",
        risk_profile="HIGH",
        verification_burden="ENHANCED",
    ),
    # Sequential
    "STAGED_SEQUENCE_MERGE": StrategyDefinition(
        id="STAGED_SEQUENCE_MERGE",
        name="Staged Sequence Merge",
        category="SEQUENTIAL",
        description="Merge in stages: structural -> config -> behavior -> verify.",
        use_case="Multi-layer integration (infra + code).",
        anti_case="Simple semantic changes with no layer separation.",
        risk_profile="MEDIUM",
        verification_burden="ENHANCED",
    ),
    "MIGRATION_FIRST_THEN_FEATURE_REPLAY": StrategyDefinition(
        id="MIGRATION_FIRST_THEN_FEATURE_REPLAY",
        name="Migration First then Feature Replay",
        category="SEQUENTIAL",
        description="Validate schema/migration first, then replay feature logic.",
        use_case="DB/schema changes with overlapping feature code.",
        anti_case="Pure logic changes with no data/config drift.",
        risk_profile="HIGH",
        verification_burden="CRITICAL",
    ),
    # Contract-driven
    "INTERFACE_FIRST_RECONCILIATION": StrategyDefinition(
        id="INTERFACE_FIRST_RECONCILIATION",
        name="Interface First Reconciliation",
        category="CONTRACT",
        description="Resolve shared contracts/types first, then implement both sides.",
        use_case="API/Protocol drift at shared boundaries.",
        anti_case="Internal implementation detail conflicts.",
        risk_profile="HIGH",
        verification_burden="ENHANCED",
    ),
    # Risk-reduction
    "PATCH_ISOLATION_PLAN": StrategyDefinition(
        id="PATCH_ISOLATION_PLAN",
        name="Patch Isolation Plan",
        category="RISK_REDUCTION",
        description="Isolate risky core to a standalone patch before merging.",
        use_case="Small high-risk core inside a huge noisy diff.",
        anti_case="Diff is already minimal and focused.",
        risk_profile="LOW",
        verification_burden="STANDARD",
    ),
    "REVERT_AND_REINTEGRATE": StrategyDefinition(
        id="REVERT_AND_REINTEGRATE",
        name="Revert and Reintegrate",
        category="RISK_REDUCTION",
        description="Revert risky side temporarily, merge safe base, reintegrate later.",
        use_case="Release pressure with low-confidence synthesis.",
        anti_case="Changes are too interdependent to decouple.",
        risk_profile="LOW",
        verification_burden="STANDARD",
    ),
    "SPLIT_DECISION_REQUIRED": StrategyDefinition(
        id="SPLIT_DECISION_REQUIRED",
        name="Split Decision Required",
        category="RISK_REDUCTION",
        description="Split the PR or integration into two separate operations.",
        use_case="Overloaded PRs with unrelated cross-domain changes.",
        anti_case="Cohesive change set that must move together.",
        risk_profile="LOW",
        verification_burden="STANDARD",
    ),
}


# --------------------------------------------------------------------------- #
# Strategy priority boosts for queue ordering (higher = merged sooner)
# --------------------------------------------------------------------------- #

STRATEGY_PRIORITY_BOOSTS: Dict[str, float] = {
    "PATCH_ISOLATION_PLAN": 50.0,
    "REVERT_AND_REINTEGRATE": 40.0,
    "DIRECT_REBASE_MERGE": 30.0,
    "SPLIT_DECISION_REQUIRED": 20.0,
    "OURS_THEN_PORT_SELECTIVE": 10.0,
    "STAGED_SEQUENCE_MERGE": 5.0,
    "INTERFACE_FIRST_RECONCILIATION": 0.0,
    "THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR": -10.0,
    "MIGRATION_FIRST_THEN_FEATURE_REPLAY": -20.0,
}

# Strategies safe for speculative rebase train (low risk, standard verification)
TRAIN_ELIGIBLE_STRATEGIES = {"DIRECT_REBASE_MERGE", "PATCH_ISOLATION_PLAN"}

# Execution order within the train (lower = executed first)
STRATEGY_EXECUTION_ORDER: Dict[str, int] = {
    "DIRECT_REBASE_MERGE": 0,
    "PATCH_ISOLATION_PLAN": 1,
    "REVERT_AND_REINTEGRATE": 2,
    "OURS_THEN_PORT_SELECTIVE": 3,
    "SPLIT_DECISION_REQUIRED": 4,
    "STAGED_SEQUENCE_MERGE": 5,
    "INTERFACE_FIRST_RECONCILIATION": 6,
    "THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR": 7,
    "MIGRATION_FIRST_THEN_FEATURE_REPLAY": 8,
}


# --------------------------------------------------------------------------- #
# Strategy selector
# --------------------------------------------------------------------------- #

def select_strategy(result: PRResult, policy: Dict[str, Any]) -> StrategyAssignment:
    """Select the best merge strategy for a PR based on its current state."""
    from .classification import has_conflicts
    from .conflict import conflict_recovery_state, recommend_conflict_strategy

    pr = result.pr_state
    lifecycle = (
        result.lifecycle_state.value
        if hasattr(result.lifecycle_state, "value")
        else str(result.lifecycle_state)
    )

    # Conflicting PRs: delegate to conflict strategy recommender
    if has_conflicts(pr.mergeable, pr.merge_state_status):
        recovery = conflict_recovery_state(pr, policy)
        if recovery == "eligible":
            conflict_paths: list[str] = []
            if result.validation_report:
                for step in result.validation_report.steps:
                    if step.status == "failed" and step.stderr:
                        for line in step.stderr.splitlines():
                            stripped = line.strip()
                            if stripped and not stripped.startswith(
                                ("error", "hint", "fatal", "CONFLICT")
                            ):
                                conflict_paths.append(stripped)
            strategy_id, rationale = recommend_conflict_strategy(
                conflict_file_paths=conflict_paths,
                rebase_error="",
                pr=pr,
            )
            return StrategyAssignment(
                strategy_id=strategy_id,
                rationale=rationale,
                priority_boost=STRATEGY_PRIORITY_BOOSTS.get(strategy_id, 0.0),
            )
        if recovery == "semantic_conflict_blocked":
            return StrategyAssignment(
                strategy_id="SPLIT_DECISION_REQUIRED",
                rationale="Semantic conflict requires human decision on split",
                priority_boost=STRATEGY_PRIORITY_BOOSTS["SPLIT_DECISION_REQUIRED"],
            )
        return StrategyAssignment(
            strategy_id="SPLIT_DECISION_REQUIRED",
            rationale=f"Conflict recovery state '{recovery}' requires manual intervention",
            priority_boost=STRATEGY_PRIORITY_BOOSTS["SPLIT_DECISION_REQUIRED"],
        )

    # MERGE_READY or QUEUED with green CI: direct rebase merge
    if lifecycle in ("merge_ready", "queued_for_merge") and pr.ci_status == "SUCCESS":
        return StrategyAssignment(
            strategy_id="DIRECT_REBASE_MERGE",
            rationale="Clean PR with green CI, eligible for direct rebase merge",
            priority_boost=STRATEGY_PRIORITY_BOOSTS["DIRECT_REBASE_MERGE"],
        )

    # CI failures only: isolate the fix
    if pr.pr_class == "CI_ONLY":
        return StrategyAssignment(
            strategy_id="PATCH_ISOLATION_PLAN",
            rationale="CI failure suggests isolating fix as standalone patch",
            priority_boost=STRATEGY_PRIORITY_BOOSTS["PATCH_ISOLATION_PLAN"],
        )

    # Mixed blockers: staged approach
    if pr.pr_class == "MIXED":
        return StrategyAssignment(
            strategy_id="STAGED_SEQUENCE_MERGE",
            rationale="Multiple blocker types require staged resolution",
            priority_boost=STRATEGY_PRIORITY_BOOSTS["STAGED_SEQUENCE_MERGE"],
        )

    # Default
    return StrategyAssignment(
        strategy_id="DIRECT_REBASE_MERGE",
        rationale="Default strategy for PR in current state",
        priority_boost=STRATEGY_PRIORITY_BOOSTS["DIRECT_REBASE_MERGE"],
    )
