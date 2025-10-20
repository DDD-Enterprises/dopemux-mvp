"""
Component 6: ADHD Intelligence Layer

Advanced ADHD-optimized workflow intelligence with ML predictions,
cognitive load management, and context preservation.

Created: 2025-10-20
Phase: Architecture 3.0 Component 6 (COMPLETE)

Phases:
- Phase 1: Observability + Context Switch Recovery (COMPLETE)
- Phase 2: Predictive Orchestration + Cognitive Load (COMPLETE)
  - Week 3: Rule-based recommendations (COMPLETE)
  - Week 4: ML infrastructure (COMPLETE)
  - Week 5: Hybrid deployment (COMPLETE)
"""

# Phase 1: Context Switch Recovery
from .context_switch_recovery import (
    ContextSwitchRecovery,
    ContextSwitch,
    RecoveryContext,
    SwitchReason
)

# Week 3: Rule-Based Recommendations
from .predictive_orchestrator import (
    RuleBasedRecommender,
    TaskRecommendation,
    RecommendationContext,
    RecommendationSource
)

# Week 3: Cognitive Load Balancer
from .cognitive_load_balancer import (
    CognitiveLoadBalancer,
    CognitiveLoad,
    LoadFactors,
    LoadStatus,
    UserLoadProfile
)

# Week 3: Load Alert Manager
from .load_alert_manager import (
    LoadAlertManager,
    LoadAlert,
    AlertSettings,
    AlertPriority,
    AlertHistory
)

# Week 4-5: ML-Powered Recommendations
from .predictive_orchestrator import (
    ContextualBanditRecommender,
    HybridTaskRecommender,
    get_task_recommendations
)

__all__ = [
    # Phase 1: Context Switch Recovery
    "ContextSwitchRecovery",
    "ContextSwitch",
    "RecoveryContext",
    "SwitchReason",

    # Week 3: Predictive Orchestration
    "RuleBasedRecommender",
    "TaskRecommendation",
    "RecommendationContext",
    "RecommendationSource",

    # Week 3: Cognitive Load Management
    "CognitiveLoadBalancer",
    "CognitiveLoad",
    "LoadFactors",
    "LoadStatus",
    "UserLoadProfile",

    # Week 3: Alert Management
    "LoadAlertManager",
    "LoadAlert",
    "AlertSettings",
    "AlertPriority",
    "AlertHistory",

    # Week 4-5: ML-Powered Recommendations
    "ContextualBanditRecommender",
    "HybridTaskRecommender",
    "get_task_recommendations",
]
