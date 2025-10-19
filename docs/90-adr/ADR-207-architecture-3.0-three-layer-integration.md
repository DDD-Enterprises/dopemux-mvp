# ADR-207: Architecture 3.0 - Three-Layer Integration Model

**Date**: 2025-10-19
**Status**: Proposed
**Decision Makers**: User + Claude Code (Ultrathink Analysis)
**Tags**: [critical, architecture, task-orchestrator, leantime, multi-project, three-layer]
**Builds Upon**: ADR-203 (Task-Orchestrator Un-Deprecation)

---

## Context

### Current State: Architecture 2.0 (Simplified)

**Active Components**:
- **ConPort** (PostgreSQL AGE): Task storage, decisions, knowledge graph
- **SuperClaude**: PRD parsing via `/dx:prd-parse` with Zen planner
- **Python ADHD Engine**: Energy tracking, cognitive load, break management
- **Serena LSP**: Code navigation and semantic analysis
- **Integration Bridge**: Event routing (PORT_BASE+16)

**Simplification Goals Achieved**:
- ✅ Clear authority boundaries
- ✅ Event-driven architecture
- ✅ Reduced coupling
- ✅ ConPort as single source of truth

### Problem Statement

**User Requirements**:
1. **PM Interface**: Need visual design tracking and project management dashboard
2. **Multi-Project Management**: Single interface managing multiple projects with Dopemux orchestrating dev time across projects
3. **Advanced Orchestration**: Leverage Task-Orchestrator's 37 specialized tools (un-deprecated in ADR-203)

**Architecture 2.0 Gaps**:
- ❌ No PM visualization layer (team dashboards, sprint planning UI)
- ❌ No multi-project management capabilities
- ❌ Task-Orchestrator exists but not architecturally integrated
- ❌ Leantime integration removed during v2.0 simplification

### Discovery: Task-Orchestrator Status

**From ADR-203** (2025-10-16):
- ✅ Task-Orchestrator un-deprecated (5,577 lines production code)
- ✅ Provides unique value: ML risk assessment, multi-team coordination, workflow automation
- ✅ 83% functionality had NO replacement in Architecture 2.0
- ⏳ Week 7 integration planned (13 hours)

**Additional Discovery** (Ultrathink Investigation, 2025-10-19):
- ✅ Task-Orchestrator has **built-in Leantime integration** (EnhancedTaskOrchestrator class)
- ✅ 13 Python modules across 8,889 lines (expanded from initial 5,577 count)
- ✅ Includes: `multi_team_coordination.py`, `predictive_risk_assessment.py`, `adhd_engine.py`, `sync_engine.py`, `automation_workflows.py`, `performance_optimizer.py`, `deployment_orchestration.py`, `external_dependency_integration.py`

---

## Decision

**Adopt Architecture 3.0: Three-Layer Integration Model**

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  Layer 3: LEANTIME (Visualization)              │
│  • Multi-project PM dashboards                  │
│  • Sprint planning interface                    │
│  • Team collaboration UI                        │
│  • Stakeholder communication                    │
│  Authority: Visual representation ONLY          │
└─────────────┬───────────────────────────────────┘
              │ (reads from ConPort, updates via ConPort)
              ▼
┌─────────────────────────────────────────────────┐
│  Layer 2: TASK-ORCHESTRATOR (Intelligence)      │
│  • 37 specialized tools                         │
│  • Dependency analysis & critical path          │
│  • ML-based predictive risk assessment          │
│  • Multi-team coordination                      │
│  • Performance optimization                     │
│  • Workflow automation                          │
│  Authority: Analysis & recommendations          │
└─────────────┬───────────────────────────────────┘
              │ (subscribes to events, publishes insights)
              ▼
┌─────────────────────────────────────────────────┐
│  Layer 1: CONPORT (Storage Authority)           │
│  • Task data (progress_entry)                   │
│  • Decisions & knowledge graph                  │
│  • Multi-project context                        │
│  Authority: Single source of truth              │
└─────────────────────────────────────────────────┘
```

### Authority Matrix Update

| System | OWNS (Exclusive Authority) | NEVER Does |
|--------|---------------------------|------------|
| **ConPort** | Task storage (progress_entry)<br>Decisions (log_decision)<br>Knowledge graph (link_conport_items)<br>Multi-project context | Orchestration logic<br>PM visualization<br>Direct Leantime sync |
| **Task-Orchestrator** | Dependency analysis<br>ML risk assessment<br>Multi-team coordination<br>Workflow automation<br>Performance optimization<br>Orchestration recommendations | Task storage<br>Decisions<br>PM visualization<br>Direct user interaction |
| **Leantime** | PM dashboard visualization<br>Multi-project interface<br>Team collaboration UI<br>Sprint planning views | Task storage<br>Orchestration logic<br>Authoritative data source |

### Integration Strategy

**Data Flow**:
1. Tasks created/updated → **ConPort** (storage)
2. ConPort publishes events → **Integration Bridge**
3. **Task-Orchestrator** subscribes → analyzes dependencies, risk, performance
4. Task-Orchestrator publishes insights → **Integration Bridge**
5. ConPort stores orchestration results
6. **Leantime** polls ConPort → visualizes multi-project dashboards
7. Leantime status updates → flow through ConPort → trigger Task-Orchestrator re-analysis

**Communication Pattern**:
- ConPort ↔ Task-Orchestrator: Event-driven (pub/sub via Integration Bridge)
- ConPort ↔ Leantime: Polling + webhook (read-mostly, updates via ConPort)
- Task-Orchestrator → Leantime: NO direct communication (through ConPort)

---

## Rationale

### Separation of Concerns

**Architecture 2.0 simplified storage but inadvertently removed orchestration and visualization**. These are three distinct architectural concerns:

1. **Storage Layer** (ConPort): Persistence, data integrity, single source of truth
2. **Intelligence Layer** (Task-Orchestrator): Analysis, prediction, optimization, coordination
3. **Presentation Layer** (Leantime): Visualization, user interaction, stakeholder communication

**Each layer has distinct responsibilities that don't overlap.**

### Proven Code Value

**Task-Orchestrator provides**:
- ✅ 8,889 lines of production-ready Python code
- ✅ 37 specialized orchestration tools
- ✅ Built-in Leantime integration (EnhancedTaskOrchestrator class)
- ✅ ML-based predictive risk assessment
- ✅ Multi-team coordination engine
- ✅ ADHD-optimized workflow automation
- ✅ Performance optimizer
- ✅ Deployment orchestration
- ✅ External dependency integration

**Rebuilding this would take 40-60 hours** vs **13 hours integration** (from ADR-203).

### Addresses Real User Requirements

1. **Multi-Project Management**: Leantime provides native multi-project dashboards
2. **PM Interface for Design Tracking**: Leantime sprint planning, task boards, team collaboration
3. **Advanced Orchestration**: Task-Orchestrator's 37 tools provide capabilities missing from Architecture 2.0
4. **Dopemux Time Management**: ADHD Engine + Task-Orchestrator coordinate dev time across projects

### Preserves Architecture 2.0 Benefits

- ✅ **Clear Authority Boundaries**: Each layer has exclusive authority over its domain
- ✅ **Event-Driven Integration**: Maintains loose coupling via Integration Bridge
- ✅ **ConPort Remains Authoritative**: Single source of truth unchanged
- ✅ **Independently Replaceable**: Each layer can be swapped without affecting others

### Architectural Soundness

**Expert Analysis** (gpt-5-codex via Zen thinkdeep):
- ✅ Three-layer model is standard enterprise architecture pattern
- ✅ Separation of concerns prevents authority violations
- ✅ Event-driven integration prevents tight coupling
- ✅ Each layer can scale independently

---

## Implementation Plan

### Option B: Selective Integration (RECOMMENDED)

**Rationale**: Balances proven orchestration value with manageable complexity. Can expand to full integration after validation.

### Phase 1: Core Orchestration (Weeks 1-2, ~20 hours)

**Goal**: Integrate Task-Orchestrator with ConPort via Integration Bridge

**Tasks**:
1. **Dependency Audit** (4h)
   - Inventory Task-Orchestrator external dependencies
   - Verify Redis, OpenAI API, Leantime API requirements
   - Check deployment infrastructure (Docker, env configs)

2. **Data Contract Adapters** (6h)
   - Create ConPort event → Task-Orchestrator adapter
   - Map `progress_entry` changes to orchestration triggers
   - Handle schema differences from pre-v2.0 APIs

3. **Integration Bridge Wiring** (4h)
   - Configure event routing: ConPort → Task-Orchestrator
   - Configure insight publishing: Task-Orchestrator → ConPort
   - Set up event schemas and versioning

4. **Core Module Activation** (4h)
   - Enable dependency analysis module
   - Enable basic orchestration features
   - Disable advanced features for Phase 3

5. **Testing** (2h)
   - Integration tests (ConPort + Task-Orchestrator)
   - Validate dependency analysis works
   - Verify event flows

**Success Criteria**:
- ✅ Task-Orchestrator receives ConPort events
- ✅ Dependency analysis runs on task changes
- ✅ Results published back to ConPort
- ✅ No authority violations

### Phase 2: Leantime Visualization (Weeks 3-4, ~24 hours)

**Goal**: Add multi-project PM dashboard

**Tasks**:
1. **Leantime Deployment** (4h)
   - Deploy Leantime instance (Docker/cloud)
   - Configure multi-project setup
   - Set up user access and permissions

2. **ConPort → Leantime Sync** (8h)
   - Create Leantime sync adapter
   - Map ConPort `progress_entry` → Leantime tasks
   - Implement polling + webhook mechanism
   - Handle multi-project workspace mapping

3. **Leantime → ConPort Updates** (6h)
   - Implement status update flow (Leantime → ConPort)
   - Ensure updates trigger Task-Orchestrator re-analysis
   - Validate authority boundaries (Leantime read-mostly)

4. **Multi-Project Configuration** (4h)
   - Configure Leantime projects
   - Set up project-level dashboards
   - Test cross-project workflows

5. **Testing** (2h)
   - End-to-end workflow testing
   - Multi-project scenario validation
   - Performance testing (sync latency)

**Success Criteria**:
- ✅ Leantime displays ConPort tasks
- ✅ Multi-project dashboard functional
- ✅ Status updates flow: Leantime → ConPort → Task-Orchestrator
- ✅ No data inconsistencies

### Phase 3: Advanced Orchestration (Weeks 5-6, ~16 hours)

**Goal**: Enable full Task-Orchestrator capabilities

**Tasks**:
1. **ML Risk Assessment** (6h)
   - Enable predictive risk assessment module
   - Configure ML model training (if needed)
   - Integrate with ConPort decision logging

2. **Multi-Team Coordination** (4h)
   - Enable multi-team coordination engine
   - Configure team profiles and capacity
   - Test cross-team dependency tracking

3. **Performance Optimizer** (2h)
   - Enable workflow performance optimization
   - Configure optimization rules

4. **Full Feature Validation** (4h)
   - Comprehensive testing of all 37 tools
   - Load testing and performance profiling
   - Documentation updates

**Success Criteria**:
- ✅ ML risk predictions accurate
- ✅ Multi-team coordination working
- ✅ Performance within acceptable limits
- ✅ All 37 tools operational

### Total Effort: ~60 hours (6-8 weeks at 8-10h/week)

---

## Risk Mitigation

### Risk 1: Data Contract Drift

**Risk**: Task-Orchestrator expects pre-v2.0 ConPort APIs

**Mitigation**:
- Create adapter layer mapping current ConPort schema to Task-Orchestrator expectations
- Document schema mapping in ADR
- Version event schemas for future changes

**Owner**: Phase 1 implementation

### Risk 2: Service Boundary Violations

**Risk**: Systems bypass authority boundaries (e.g., Task-Orchestrator tries to store data)

**Mitigation**:
- Document API contracts explicitly
- Integration Bridge enforces boundaries (rejects invalid operations)
- Add monitoring/alerts for boundary violations

**Owner**: Phase 1 + ongoing monitoring

### Risk 3: Operational Readiness

**Risk**: Deployment infrastructure missing (Docker configs, CI/CD)

**Mitigation**:
- Audit deployment requirements in Phase 1
- Recreate missing infrastructure
- Document deployment process

**Owner**: Phase 1 dependency audit

### Risk 4: Security Posture

**Risk**: Auth flows broken (Leantime → Task-Orchestrator → ConPort)

**Mitigation**:
- Revalidate auth flows before Phase 2
- Follow ConPort/Serena security patterns (from ADR-201, ADR-202)
- Security audit before production

**Owner**: Phase 2 + security review

### Risk 5: Integration Testing Gaps

**Risk**: Cross-layer workflows untested, leading to runtime failures

**Mitigation**:
- Create integration test suite (Phase 1)
- End-to-end scenario testing (Phase 2)
- Load/performance testing (Phase 3)

**Owner**: All phases

### Risk 6: Performance Degradation

**Risk**: ConPort's simplified storage changes Task-Orchestrator performance assumptions

**Mitigation**:
- Profile critical paths during Phase 1
- Optimize hot paths if needed
- Load testing in Phase 3

**Owner**: Phase 1 + Phase 3 validation

---

## Alternatives Considered

### Alternative 1: Maintain Architecture 2.0 (No Changes)

**Pros**:
- ✅ Zero integration effort
- ✅ No added complexity

**Cons**:
- ❌ Doesn't address user requirements (multi-project, PM interface)
- ❌ Leaves 8,889 lines of proven code unused
- ❌ No orchestration capabilities (dependency analysis, ML risk)

**Verdict**: ❌ Rejected - Fails to meet user needs

### Alternative 2: Thin Leantime Integration (Read-Only)

**Approach**: Leantime reads from ConPort only, no Task-Orchestrator

**Pros**:
- ✅ Simpler than full integration
- ✅ Addresses PM visualization requirement
- ✅ Lower risk

**Cons**:
- ❌ Doesn't leverage Task-Orchestrator's orchestration value
- ❌ No dependency analysis, ML risk assessment
- ❌ Limited multi-project coordination

**Verdict**: ❌ Rejected - Leaves orchestration capabilities on table

### Alternative 3: Enhance ConPort with Orchestration

**Approach**: Add orchestration features directly to ConPort

**Pros**:
- ✅ No additional services
- ✅ Simpler architecture

**Cons**:
- ❌ Violates ConPort's storage-only authority
- ❌ Rebuilds 8,889 lines of existing code (40-60 hours)
- ❌ ConPort becomes monolithic

**Verdict**: ❌ Rejected - Violates separation of concerns, expensive rebuild

### Alternative 4: Full Integration (Option A)

**Approach**: Restore all 37 Task-Orchestrator tools + Leantime immediately

**Pros**:
- ✅ Maximum value immediately
- ✅ All capabilities available

**Cons**:
- ❌ Higher complexity from day 1
- ❌ Harder to validate incrementally
- ❌ Higher risk of integration issues

**Verdict**: ⚠️ Deferred - Use as expansion path after Option B proves successful

### Alternative 5: Gradual Restoration (Option C)

**Approach**: Phase 1 (Leantime only) → Phase 2 (Dependency analysis) → Phase 3 (ML risk) → Phase 4 (Multi-team)

**Pros**:
- ✅ Lowest risk per phase
- ✅ Incremental validation

**Cons**:
- ❌ Slower to full value
- ❌ More integration cycles
- ❌ Complexity spread across longer timeline

**Verdict**: ⚠️ Considered but Option B preferred for better risk/value balance

---

## Consequences

### Positive

✅ **Multi-Project Management**: Leantime provides native multi-project PM dashboards
✅ **Advanced Orchestration**: 37 specialized tools operational (dependency analysis, ML risk, multi-team)
✅ **Proven Code Reuse**: Leverage 8,889 lines of production-ready code vs 40-60h rebuild
✅ **ADHD Optimization**: Task-Orchestrator's ADHD engine + Leantime visual progress
✅ **Architectural Soundness**: Three-layer separation of concerns (storage, intelligence, visualization)
✅ **Architecture 2.0 Preserved**: Event-driven, clear boundaries, ConPort authoritative
✅ **Scalability**: Each layer scales independently
✅ **Flexibility**: Can swap any layer without affecting others

### Negative

⚠️ **Maintenance Burden**: 3 systems to monitor, debug, upgrade vs 1 (ConPort)
⚠️ **Integration Complexity**: Event-driven doesn't mean simple - need robust adapters
⚠️ **Operational Overhead**: More infrastructure (Leantime instance, Task-Orchestrator service, Redis)
⚠️ **Learning Curve**: Team needs to understand three-layer model
⚠️ **Risk Surface**: More integration points = more potential failure modes

### Trade-offs

**Complexity vs Value**:
- Added complexity justified by:
  - 8,889 lines of proven code
  - Multi-project management requirement
  - ML risk assessment capabilities
  - Multi-team coordination features

**Effort vs Rebuild**:
- Integration: ~60 hours
- Rebuild: 80-120 hours (Task-Orchestrator + Leantime equivalent)
- **Savings**: 20-60 hours

---

## Validation & Success Metrics

### Pilot Period: 6 Weeks (Phases 1-3)

**Go/No-Go Decision Point**: End of Phase 2 (Week 4)

**Success Criteria**:
1. **Technical**:
   - ✅ Task-Orchestrator processes ConPort events without errors
   - ✅ Leantime displays accurate multi-project data
   - ✅ Event latency < 2 seconds (ConPort → Task-Orchestrator → ConPort)
   - ✅ No authority boundary violations
   - ✅ Integration test suite passes (>90% coverage)

2. **Operational**:
   - ✅ Service uptime > 99%
   - ✅ No data inconsistencies between ConPort ↔ Leantime
   - ✅ Deployment automation working

3. **Value**:
   - ✅ Dependency analysis identifies at least 3 blockers per sprint
   - ✅ Multi-project dashboard usable by stakeholders
   - ✅ ML risk predictions have >60% accuracy

**Rollback Plan**:
- If success criteria not met → revert to Architecture 2.0
- Feature flags enable/disable Task-Orchestrator + Leantime
- ConPort continues independently (no data loss)

### Long-Term Metrics (Post-Launch)

**Efficiency Gains**:
- Hours saved via dependency analysis per sprint
- Blockers prevented via ML risk assessment
- Multi-team coordination improvements

**ADHD Optimization**:
- Context preservation success rate
- Break enforcement adherence
- Hyperfocus protection effectiveness

**System Health**:
- Event processing latency (P50, P95, P99)
- Service availability (uptime %)
- Integration failure rate

---

## Related Decisions

- **Builds Upon**: ADR-203 (Task-Orchestrator Un-Deprecation)
- **References**: ADR-201 (ConPort Security Hardening), ADR-202 (Serena v2 Production Validation)
- **Supersedes**: Architecture 2.0 (extends, doesn't replace)
- **Investigation**: Zen thinkdeep analysis (2025-10-19, continuation_id: 58a5114f-c2fc-4281-b06c-def8ffbb5c77)

---

## Implementation Tracking

**Status**: Proposed (2025-10-19)
**Target Start**: Week 1 (TBD)
**Estimated Completion**: Week 6-8
**Priority**: HIGH (addresses critical user requirements)

**Milestones**:
- [ ] Phase 1 Complete: Core orchestration operational
- [ ] Phase 2 Complete: Leantime visualization live
- [ ] Phase 3 Complete: All 37 tools operational
- [ ] Go/No-Go Decision: End of Week 4
- [ ] Production Deployment: End of Week 8

---

## Approval

**Proposed By**: User + Claude Code (Ultrathink)
**Date**: 2025-10-19
**Pending Approval**: Yes

**Next Steps**:
1. Review ADR with stakeholders
2. Finalize implementation timeline
3. Begin Phase 1: Core Orchestration

---

## Appendix A: Task-Orchestrator Modules

**13 Python Modules (8,889 lines)**:
1. `enhanced_orchestrator.py` - Main orchestration engine + Leantime integration
2. `multi_team_coordination.py` - Cross-team dependency tracking
3. `predictive_risk_assessment.py` - ML-based risk prediction
4. `external_dependency_integration.py` - External API coordination
5. `performance_optimizer.py` - Workflow optimization
6. `deployment_orchestration.py` - Deployment coordination
7. `adhd_engine.py` - ADHD-specific optimizations
8. `sync_engine.py` - Multi-system synchronization (ConPort, Leantime)
9. `automation_workflows.py` - Workflow templates and automation
10. `event_coordinator.py` - Event-driven coordination
11. `claude_context_manager.py` - Context preservation
12. `server.py` - MCP server wrapper
13. `orchestrator_integration_test.py` - Integration tests

**37 Specialized Tools** (from ADR-203):
- Dependency analysis tools (10)
- Risk assessment tools (8)
- Multi-team coordination tools (7)
- Workflow automation tools (6)
- Performance optimization tools (4)
- Deployment orchestration tools (2)

---

## Appendix B: Leantime Integration Details

**EnhancedTaskOrchestrator Class**:
- Built-in Leantime API client
- Task synchronization engine
- Multi-project workspace mapping
- Event-driven sync (polling + webhooks)

**Leantime API Coverage**:
- Project management
- Task CRUD operations
- Sprint planning
- Team collaboration
- Dashboard visualization

**Integration Pattern**:
```python
# ConPort → Leantime (via sync_engine.py)
sync_engine.sync_to_leantime(
    conport_tasks=...,
    leantime_project_id=...,
    workspace_mapping=...
)

# Leantime → ConPort (via webhook)
@webhook("/leantime/update")
async def handle_leantime_update(task_update):
    # Flow through ConPort authority
    await conport.update_progress(task_update)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
