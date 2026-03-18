from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal


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


STRATEGY_LIBRARY = {
    # Structural
    "OURS_THEN_PORT_SELECTIVE": StrategyDefinition(
        id="OURS_THEN_PORT_SELECTIVE",
        name="Ours then Port Selective",
        category="STRUCTURAL",
        description="Use ours as structural base, port specific changes from theirs.",
        use_case="Refactor on ours, bugfix on theirs.",
        anti_case="Structural drift is too large to map hunks safely.",
        risk_profile="MEDIUM",
        verification_burden="STANDARD"
    ),
    "THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR": StrategyDefinition(
        id="THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR",
        name="Theirs then Reapply Local",
        category="STRUCTURAL",
        description="Use theirs as structural base, reapply local behavior from ours.",
        use_case="Upstream migration where theirs is authoritative.",
        anti_case="Local behavior is too coupled to old structure.",
        risk_profile="HIGH",
        verification_burden="ENHANCED"
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
        verification_burden="ENHANCED"
    ),
    "MIGRATION_FIRST_THEN_FEATURE_REPLAY": StrategyDefinition(
        id="MIGRATION_FIRST_THEN_FEATURE_REPLAY",
        name="Migration First then Feature Replay",
        category="SEQUENTIAL",
        description="Validate schema/migration first, then replay feature logic.",
        use_case="DB/schema changes with overlapping feature code.",
        anti_case="Pure logic changes with no data/config drift.",
        risk_profile="HIGH",
        verification_burden="CRITICAL"
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
        verification_burden="ENHANCED"
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
        verification_burden="STANDARD"
    ),
    "REVERT_AND_REINTEGRATE": StrategyDefinition(
        id="REVERT_AND_REINTEGRATE",
        name="Revert and Reintegrate",
        category="RISK_REDUCTION",
        description="Revert risky side temporarily, merge safe base, reintegrate later.",
        use_case="Release pressure with low-confidence synthesis.",
        anti_case="Changes are too interdependent to decouple.",
        risk_profile="LOW",
        verification_burden="STANDARD"
    ),
    "SPLIT_DECISION_REQUIRED": StrategyDefinition(
        id="SPLIT_DECISION_REQUIRED",
        name="Split Decision Required",
        category="RISK_REDUCTION",
        description="Split the PR or integration into two separate operations.",
        use_case="Overloaded PRs with unrelated cross-domain changes.",
        anti_case="Cohesive change set that must move together.",
        risk_profile="LOW",
        verification_burden="STANDARD"
    )
}
