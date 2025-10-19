# ML-Based Risk Assessment Service
**Extracted from**: Task-Orchestrator (2025-10-16 audit)
**Status**: Standalone service
**Purpose**: ADHD-optimized predictive blocker detection

---

## Overview

ML-powered risk assessment engine that predicts potential blockers before they impact neurodivergent developers. Uses pattern recognition and historical data for proactive risk mitigation.

## Features

### ADHD-Specific Risk Factors
- **Cognitive Overload**: Detects overwhelming task complexity
- **Hyperfocus Burnout**: Identifies hyperfocus risk patterns
- **Context Switching**: Predicts context switch impacts

### Technical Risk Factors
- Dependency blockers
- Resource conflicts
- Timeline slippage
- Integration failures
- Communication breakdowns

### ML Capabilities
- Historical pattern learning
- Confidence interval calculation
- Real-time risk scoring (0.0-1.0)
- Proactive mitigation suggestions
- Continuous learning from feedback

---

## Why Extracted

**From**: services/task-orchestrator/predictive_risk_assessment.py (562 lines)

**Reason**: Systematic code audit revealed Task-Orchestrator deprecation would lose this unique ML capability. No equivalent exists in ADHD Engine, ConPort, or SuperClaude.

**Value**: Proactive ADHD-aware blocker prediction is core to Dopemux vision.

---

## Integration

**Current Dependencies**:
- ConPort client (for logging assessments)
- Context7 client (optional, for documentation lookup)

**Future Integration** (Week 7+):
- ConPort HTTP API (replace direct SQLite)
- Integration Bridge events
- FastAPI REST endpoints (like ADHD Engine)

---

## Usage

```python
from engine import PredictiveRiskAssessmentEngine, RiskLevel

# Initialize
risk_engine = PredictiveRiskAssessmentEngine(
    conport_client=conport,
    context7_client=context7
)
await risk_engine.initialize()

# Assess risk for a task
risk_profile = await risk_engine.assess_risk(
    entity_id="task_123",
    entity_type="task",
    context_data={
        "complexity": 0.8,
        "dependencies": ["task_120", "task_121"],
        "deadline": "2025-10-20"
    }
)

# Check risk level
if risk_profile.overall_risk_level == RiskLevel.HIGH:
    print("⚠️ High risk detected!")
    for factor in risk_profile.risk_factors:
        print(f"  - {factor.description}")
        for mitigation in factor.mitigation_suggestions:
            print(f"    → {mitigation}")
```

---

## Status

- **Code**: Production-quality (562 lines, comprehensive)
- **Tests**: Integration tests in task-orchestrator/
- **Deployment**: Pending Week 7 architecture integration
- **Priority**: HIGH (unique ADHD value)

---

## Audit Trail

**Audit Decision**: ConPort Decision #5
**Extraction Date**: 2025-10-16
**Reason**: Preserve unique ML capabilities from deprecation
**Next Steps**: Integrate with current architecture
