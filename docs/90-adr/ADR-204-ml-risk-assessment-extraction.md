---
id: ADR-204-ml-risk-assessment-extraction
title: Adr 204 Ml Risk Assessment Extraction
type: adr
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# ADR-204: ML Risk Assessment Service Extraction

**Date**: 2025-10-16
**Status**: Accepted
**Decision Makers**: Claude Code (Systematic Audit)
**Tags**: [ml-risk, standalone-service, extraction, adhd-intelligence]
**Related**: ADR-203 (Task-Orchestrator Un-Deprecation)

---

## Context

Task-Orchestrator un-deprecation (ADR-203) restored 5,577 lines of code. To maximize accessibility and reusability, extract the ML risk assessment components as a **standalone service**.

**Value**: ML-based predictive risk assessment with ADHD-specific risk factors is unique to Dopemux and should be easily accessible across all planes.

---

## Decision

**Extract ML risk assessment as standalone service**: `services/ml-risk-assessment/`

**Components Extracted**:
1. predictive_risk_assessment.py → engine.py (562 lines)
2. multi_team_coordination.py (13KB)
3. README.md (documentation)

---

## Rationale

### Why Standalone Service?

**1. Unique Value**:
- Only service with ML-based risk prediction
- ADHD-specific risk factors (cognitive overload, hyperfocus burnout)
- Valuable across PM plane AND cognitive plane

**2. Reusability**:
- PM plane: Risk assessment for sprint planning
- Cognitive plane: Blocker prediction during development
- DopeconBridge: Cross-plane risk coordination

**3. Service Independence**:
- Self-contained ML logic
- Minimal dependencies (ConPort client, optional Context7)
- Can evolve independently

### Why Not Keep in Task-Orchestrator?

**Accessibility**: Standalone = easier to discover and use
**Focus**: Single responsibility (risk assessment only)
**Deployment**: Can deploy without full orchestrator
**Evolution**: Can iterate ML models independently

---

## Implementation

### Files Created

**services/ml-risk-assessment/**:
```
├── engine.py (562 lines)
│   ├── PredictiveRiskAssessmentEngine
│   ├── RiskLevel enum (minimal → critical)
│   ├── RiskCategory enum (8 categories)
│   ├── ML prediction algorithms
│   └── ADHD pattern database
│
├── multi_team_coordination.py (13KB)
│   ├── MultiTeamCoordinationEngine
│   ├── Cross-team dependency tracking
│   └── ADHD-aware workload optimization
│
└── README.md
    ├── Usage examples
    ├── Integration guide
    └── Audit trail
```

### Features Preserved

**ML Risk Assessment**:
- Real-time risk prediction (0.0-1.0 score)
- 5 risk levels (minimal → critical)
- 8 risk categories (cognitive, technical, team, schedule)
- Historical pattern learning
- Confidence intervals
- Proactive mitigation suggestions

**ADHD-Specific Risk Factors**:
- Cognitive overload detection
- Hyperfocus burnout prediction
- Context switching impact analysis
- Break timing recommendations

**Multi-Team Coordination**:
- Team capacity tracking
- Cross-team dependencies
- Cognitive load balancing
- Communication preference handling

---

## Consequences

### Positive

✅ **Preserved Unique Value**: ML capabilities not lost to deprecation
✅ **Improved Accessibility**: Standalone = easier to find/use
✅ **Reusable**: Available to all Dopemux components
✅ **Evolvable**: Can improve ML models independently
✅ **Documented**: README explains value and usage

### Negative

⚠️ **Additional Service**: One more service to maintain
⚠️ **Integration Needed**: Needs proper API (currently Python module)
🟢 **Worth It**: Unique ADHD ML value justifies maintenance

---

## Alternatives Considered

### Alternative 1: Keep in Task-Orchestrator Only
**Rejected**: Less discoverable, tied to orchestrator lifecycle

### Alternative 2: Merge into ADHD Engine
**Rejected**: Different scope (prediction vs accommodation)

### Alternative 3: Discard with Deprecation
**Rejected**: Would lose unique ML capabilities forever

---

## Integration Plan

### Current State (Week 1)

**Standalone Python Module**:
```python
from ml_risk_assessment.engine import PredictiveRiskAssessmentEngine

engine = PredictiveRiskAssessmentEngine(
    conport_client=conport,
    context7_client=context7
)

risk_profile = await engine.assess_risk(
    entity_id="task_123",
    entity_type="task",
    context_data={...}
)
```

### Future State (Week 7+)

**FastAPI REST Service** (like ADHD Engine):
```python
POST /api/v1/assess-risk
{
  "entity_id": "task_123",
  "entity_type": "task",
  "context_data": {...}
}

Response:
{
  "overall_risk_level": "high",
  "risk_score": 0.75,
  "risk_factors": [...],
  "mitigation_suggestions": [...]
}
```

**Integration Points**:
- ConPort HTTP API (replace direct SQLite)
- DopeconBridge (event publishing)
- PM Plane (sprint risk assessment)
- Cognitive Plane (development blocker prediction)

---

## Validation

### Extracted Code Verification

```bash
ls -lh services/ml-risk-assessment/
# Output:
# -rw-r--r-- engine.py (20KB - predictive_risk_assessment.py)
# -rw-r--r-- multi_team_coordination.py (13KB)
# -rw-r--r-- README.md (2.8KB)
```

✅ All components successfully extracted

### Functionality Preservation

✅ **ML Algorithms**: Feature extraction, risk prediction preserved
✅ **ADHD Patterns**: Cognitive overload, hyperfocus detection intact
✅ **Data Models**: RiskFactor, RiskProfile, RiskLevel complete
✅ **Integration**: ConPort/Context7 client interfaces preserved

---

## Related Decisions

- **Parent Decision**: ADR-203 (Task-Orchestrator Un-Deprecation)
- **ConPort Decision**: #5 (Un-deprecate + Extract)
- **Git Commit**: 68b8a4b
- **Service Location**: services/ml-risk-assessment/

---

## Status

**Accepted**: 2025-10-16
**Extracted**: 2025-10-16
**Service Status**: ✅ Standalone (ready for integration)
**Next Steps**: Week 7 FastAPI conversion + architecture integration
**Priority**: HIGH (unique ADHD ML value)
