---
id: COMPONENT_6_PHASE2_SPECIFICATION
title: Component_6_Phase2_Specification
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Component_6_Phase2_Specification (explanation) for dopemux documentation
  and developer workflows.
---
# Component 6: Phase 2 Implementation Specification

**Phase**: Intelligence Core (50% of Component 6)
**Timeline**: Weeks 3-5 (3 weeks)
**Scope**: Predictive Task Orchestration + Cognitive Load Balancer
**Status**: Ready for Implementation

## Summary

Phase 2 adds ML-powered intelligence to Component 6:
1. **Predictive Task Orchestration**: ML learns individual ADHD patterns to recommend optimal next tasks
1. **Cognitive Load Balancer**: Real-time load estimation prevents overwhelm before it happens

**Implementation**: ~1,900 lines over 3 weeks
- Week 3: Rule-based recommendations + core load calculation
- Week 4: Optimization + data collection for ML
- Week 5: ML training + hybrid system deployment

---

## Feature 1: Predictive Task Orchestration

### Architecture Overview

```
Rule-Based (Weeks 1-4)          ML-Based (Week 5+)           Hybrid (Production)
─────────────────────           ──────────────────           ─────────────────
Energy → Complexity Match       Historical Patterns           Try ML First
Priority Sorting                Temporal Context              ↓
Duration Matching               Feature Engineering           High Confidence?
↓                              ↓                             ↓
Top 3 Tasks                     Completion Probability        Yes: Use ML
Confidence: 0.7                 Confidence: Variable          No: Use Rules
                                                              ↓
                                                              Always 3 Recommendations
```

### Implementation Files

1. **services/task-orchestrator/intelligence/predictive_orchestrator.py** (~800 lines)
- `RuleBasedRecommender`: Energy-complexity matching
- `MLTaskRecommender`: ML-powered predictions
- `HybridTaskRecommender`: Intelligent combination

1. **services/task-orchestrator/ml/feature_engineering.py** (~200 lines)
- Feature extraction from ADHD state
- One-hot encoding for categorical features
- Feature scaling and normalization

1. **services/task-orchestrator/ml/completion_predictor.py** (~400 lines)
- GradientBoostingClassifier training
- Model persistence and loading
- Continuous learning from outcomes

---

## Feature 2: Cognitive Load Balancer

### Architecture Overview

```
Load Calculation (Every 10s)          Alert System                  User Configuration
────────────────────────────          ────────────                  ──────────────────
Task Complexity (0.4)                 Load > 0.85?                  Custom Weights
+ Decision Count (0.2)                ↓                             ↓
+ Context Switches (0.2)              Yes: CRITICAL Alert           task_complexity: 0.4
+ Time Since Break (0.1)              ↓                             decision_count: 0.2
+ Interruptions (0.1)                 Max 1/hour                    ...
= Cognitive Load (0.0-1.0)            ↓
↓                                     Dismiss or Act                Learn Optimal Range
Classification                        ↓                             ↓
LOW/OPTIMAL/HIGH/CRITICAL             Log Event                     Adaptive Thresholds
```

### Implementation Files

1. **services/task-orchestrator/intelligence/cognitive_load_balancer.py** (~600 lines)
- Real-time load calculation
- Caching strategy (30s cache for sub-queries)
- Load classification and recommendations
- User profile management

1. **services/task-orchestrator/intelligence/load_alert_manager.py** (~300 lines)
- Alert generation and rate limiting
- Adaptive threshold learning
- Alert acknowledgment tracking

---

## Integration Points

### ConPort Integration
- Query recent decisions (`get_decisions`)
- Query in-progress tasks (`get_progress`)
- Query ADHD state (`get_active_context`)
- Log recommendations for learning
- Log load alerts

### Serena Integration
- Get current task complexity
- Query navigation state
- Estimate code complexity

### Task-Orchestrator Integration
- Get candidate tasks (TODO status)
- Get current task
- Get task completion history

### Metrics Integration
- Record recommendation accuracy
- Record cognitive load over time
- Track alert frequency

---

## Testing Strategy

### Unit Tests
- Rule-based recommendation logic
- ML feature extraction
- Cognitive load formula
- Alert rate limiting

### Integration Tests
- End-to-end recommendation flow
- Hybrid fallback scenarios
- Load calculation with real MCP data

### Performance Tests
- Load calculation < 50ms
- Recommendation generation < 200ms
- ML prediction < 100ms

---

## Success Criteria

### Predictive Task Orchestration
- ✅ Rule-based working (Week 3)
- ✅ ML model trained with 50+ samples (Week 5)
- ✅ Hybrid system operational
- ✅ Recommendation accuracy > 70%
- ✅ 3 recommendations always provided

### Cognitive Load Balancer
- ✅ Load updates every 10 seconds
- ✅ Calculation latency < 50ms
- ✅ Alerts working (max 1/hour)
- ✅ Per-user weights configurable
- ✅ Optimal load time tracked

---

## Next Steps

1. Review this specification
1. Start Week 3 implementation (rule-based + core load)
1. Monitor metrics from Phase 1 (Context Switch Recovery)
1. Iterate based on real ADHD user feedback

---

**Created**: 2025-10-20
**Status**: ✅ Specification Complete - Ready for Implementation
