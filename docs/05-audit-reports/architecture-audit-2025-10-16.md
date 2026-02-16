---
id: architecture-audit-2025-10-16
title: Architecture Audit 2025 10 16
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Architecture Audit 2025 10 16 (reference) for dopemux documentation and developer
  workflows.
---
# Architecture Audit Report - Two-Plane System
**Date**: 2025-10-16
**Analyst**: Claude Code (Sonnet 4.5)
**Method**: Zen thinkdeep systematic analysis
**Status**: ✅ Complete

---

## Executive Summary

Two-plane architecture is **well-designed** (9/10) but **partially implemented** (5/10). DopeconBridge exists with authority enforcement, but services are **not wired to use it**. Services operate independently with direct database access patterns bypassing the coordination layer.

### Architecture Quality Score: 6/10 ⚠️
- **Design**: 9/10 (✅ Clear separation, authority matrix)
- **Implementation**: 5/10 (⚠️ Partial - cognitive plane works, coordination disconnected)
- **Integration**: 3/10 (❌ Services bypass DopeconBridge)
- **Enforcement**: 4/10 (⚠️ Authority code exists but not used)

### Recommendation: ⚠️ **WEEK 7 INTEGRATION REQUIRED**
- Wire services to DopeconBridge (8-12 hours)
- Remove direct database access patterns
- Enforce authority boundaries
- Validate cross-plane coordination

---

## Two-Plane Architecture Overview

### Design (from .claude/CLAUDE.md)

**PM Plane** (Project Management):
- **Authorities**: Status updates, team visibility, task decomposition, dependencies
- **Services**: Leantime, Task-Master, Task-Orchestrator

**Cognitive Plane** (Development):
- **Authorities**: Decisions, code navigation, memory, context, semantic search
- **Services**: Serena LSP, ConPort, Dope-Context

**DopeconBridge** (Coordination):
- **Port**: PORT_BASE+16 (3016 default)
- **Purpose**: Cross-plane communication, authority enforcement, event routing
- **Rule**: "No direct cross-plane communication allowed"

---

## Implementation Status

### ✅ Cognitive Plane: Operational

**ConPort** (9/10):
- Decision logging ✅
- Knowledge graph ✅
- Context preservation ✅
- **Issue**: Orchestrator has DopeconBridge TODOs

**Serena v2** (8.5/10):
- LSP code navigation ✅
- ADHD accommodations ✅
- Fully implemented intelligence ✅

**Dope-Context**:
- Semantic search ✅
- AST-aware chunking ✅
- Complexity scoring ✅

**Status**: ✅ **Cognitive plane fully functional**

---

### ⚠️ DopeconBridge: Exists But Disconnected

**DopeconBridge Service** (`services/mcp-dopecon-bridge/`):

**Files**:
- main.py (FastAPI application) ✅
- kg_authority.py (authority enforcement) ✅
- kg_endpoints.py (API endpoints) ✅
- Dockerfile (containerization) ✅

**Features Implemented**:
- Port allocation (PORT_BASE+16 = 3016) ✅
- Multi-instance support ✅
- Authority middleware (KGAuthorityMiddleware) ✅
- PostgreSQL shared state ✅
- Redis caching ✅

**Authority Enforcement Code**:
```python
class KGAuthorityMiddleware:
    AUTHORITY_RULES = {
        "/kg/decisions": {
            "allowed_planes": ["pm_plane", "cognitive_plane"],
            "allowed_methods": ["GET"]  # PM plane read-only
        }
    }
```

✅ **DopeconBridge is implemented**

**Problem**: **Services don't use it!**

---

### ❌ Service Integration: Not Connected

**Evidence from ConPort Orchestrator**:
```python
# Line 127
if impl_decisions:
    print(f"   → Would publish decision.requires_implementation event")
    # TODO: Publish to DopeconBridge event bus  # ❌ Not wired

# Line 211
# TODO: Update Serena sidebar  # ❌ Not wired

# Line 254
# TODO: Cache for Leantime  # ❌ Not wired
```

**All DopeconBridge calls are TODOs!**

**Evidence from ADHD Engine**:
```python
# conport_client.py:296
conn = self._get_connection(write_mode=True)  # ❌ Direct DB write
conn.execute(
    "INSERT INTO custom_data (category, key, value) VALUES (?, ?, ?)",
    (category, key, json_value)
)
# Should use DopeconBridge HTTP API instead!
```

**Status**: ❌ **Services bypass DopeconBridge**

---

## Authority Boundary Violations

### 🔴 Critical Violation: ADHD Engine → ConPort

**What Should Happen**:
```
ADHD Engine → DopeconBridge → ConPort HTTP API → ConPort Database
(respects authority boundaries)
```

**What Actually Happens**:
```
ADHD Engine → ConPort SQLite Database (direct write)
(bypasses authority, violates boundaries)
```

**Impact**:
- Two services writing to same database
- Bypasses ConPort validation logic
- Data corruption risk
- Authority enforcement bypassed

**Severity**: MEDIUM (documented as technical debt, Week 7 fix)

---

### ⚠️ Medium Violation: ConPort Orchestrator Not Using Bridge

**What Should Happen**:
```
ConPort Orchestrator → DopeconBridge → Event Bus → Services
(proper event routing)
```

**What Actually Happens**:
```
ConPort Orchestrator → (TODOs, events not published)
(no cross-service coordination)
```

**Impact**:
- Event-driven automation non-functional
- Cross-plane coordination broken
- DopeconBridge unused

**Severity**: MEDIUM (automation layer incomplete)

---

## PM Plane Status

**Not Audited** (outside scope):
- Leantime integration
- Task-Master service
- PM plane authority compliance

**Assumption**: PM plane likely has similar integration gaps

---

## Integration Work Required

### Week 7 Integration Plan (8-12 hours)

**1. Wire ConPort to DopeconBridge** (3 hours):
- Replace orchestrator TODOs with actual event publishing
- Implement DopeconBridge client
- Add error handling and retries

**2. Wire ADHD Engine to ConPort API** (3 hours):
- Replace direct SQLite access
- Use DopeconBridge HTTP endpoints
- Respect service boundaries

**3. Authority Enforcement Validation** (2 hours):
- Test X-Source-Plane header enforcement
- Verify PM plane read-only compliance
- Validate authority rules

**4. Event Routing Testing** (4 hours):
- Test cross-plane event flow
- Validate event bus functionality
- Integration tests

**Total**: 12 hours for complete integration

---

## Recommendations

### Immediate (Documentation)

1. **Document Integration Gap** ✅ (this report)
1. **Update Architecture Docs** (1 hour)
- Current state: Designed but not fully integrated
- Week 7 plan: Complete integration work
- Workaround: Services operate independently

### Week 7 (Integration Work)

1. **Complete Service Integration** (12 hours)
- Wire all services to DopeconBridge
- Remove direct database access
- Enforce authority boundaries
- Validate event routing

### Long-term

1. **PM Plane Audit** (6-8 hours)
- Leantime integration status
- Task-Master compliance
- Cross-plane coordination validation

---

## Architecture Compliance Matrix

| Service | Plane | Authority Respected | DopeconBridge | Status |
|---------|-------|--------------------|--------------------|--------|
| ConPort | Cognitive | ✅ Yes (decisions) | ❌ Not wired | ⚠️ Partial |
| Serena v2 | Cognitive | ✅ Yes (navigation) | Unknown | ✅ Independent |
| ADHD Engine | Cognitive | ❌ **Violates** | ❌ Bypasses | ❌ Non-compliant |
| Dope-Context | Cognitive | ✅ Yes (search) | Unknown | ✅ Independent |
| DopeconBridge | Coordination | N/A | ✅ Implemented | ⚠️ Unused |

---

## Decision Log

```
Decision #[NEW]: Two-Plane Architecture Partially Implemented

Summary: Architecture is well-designed but coordination layer (DopeconBridge)
         is disconnected from services. Services operate independently with
         some authority boundary violations (ADHD Engine direct DB writes).

Rationale:
- Design quality: Excellent (9/10) - clear separation, authority matrix
- Implementation: Partial (5/10) - cognitive plane works, coordination disconnected
- DopeconBridge: Exists (0 TODOs) but services don't use it
- Violations: ADHD Engine direct DB writes, ConPort orchestrator not wired
- Impact: Services work independently, cross-plane coordination non-functional

Implementation:
- Week 7 (12h): Wire services to DopeconBridge
- Remove direct database access patterns
- Enforce authority boundaries
- Validate event routing and cross-plane coordination

Tags: ["architecture", "two-plane", "integration-gap", "audit-2025-10-16"]

ASSESSMENT: 6/10 (good design, incomplete integration)
PRIORITY: Week 7 integration work required
```

---

## Conclusion

Two-plane architecture demonstrates **excellent design thinking** but **incomplete execution**. DopeconBridge exists with proper authority enforcement, but services bypass it through direct database access and missing event wiring.

**For Production**: Services can operate independently (they work)
**For Architecture Maturity**: Integration work needed (Week 7, 12 hours)

**Architecture Score**: 6/10
- Design: 9/10
- Implementation: 5/10
- Integration: 3/10

---

**Architecture Audit Complete** ✅
**Key Finding**: Design excellent, integration incomplete
**Action**: Week 7 wiring work (12 hours)
