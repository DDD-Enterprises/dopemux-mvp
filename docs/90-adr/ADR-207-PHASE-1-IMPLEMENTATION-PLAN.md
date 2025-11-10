---
id: ADR-207-PHASE-1-IMPLEMENTATION-PLAN
title: Adr 207 Phase 1 Implementation Plan
type: adr
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# ADR-207 Phase 1: Core Orchestration - Detailed Implementation Plan

**Date**: 2025-10-19
**Related**: ADR-207 (Architecture 3.0)
**Phase**: Phase 1 - Core Orchestration Integration
**Duration**: 20 hours over 2 weeks
**Goal**: Integrate Task-Orchestrator dependency analysis with ConPort via Integration Bridge

---

## Overview

**Phase 1 Objectives**:
- ✅ Task-Orchestrator receives ConPort task events
- ✅ Dependency analysis runs on task changes
- ✅ Insights published back to ConPort
- ✅ No authority violations
- ✅ ADHD optimizations preserved

**Success Criteria**:
1. Task-Orchestrator processes ConPort events without errors
2. Dependency analysis identifies blockers accurately
3. Results flow: ConPort → Task-Orchestrator → ConPort (< 2s latency)
4. Integration test suite passes (>90% coverage)
5. No data stored in Task-Orchestrator (ConPort authority enforced)

---

## Task Breakdown - ADHD-Optimized

**Total Tasks**: 16 tasks across 5 components
**Total Effort**: 20 hours (1,200 minutes)
**Average Task**: 75 minutes (range: 25-90 minutes)

### Component 1: Dependency Audit (4 hours, 240 minutes)

#### Task 1.1: Inventory External Dependencies
**Duration**: 45 minutes
**Complexity**: 0.4 (moderate-low)
**Energy**: Medium
**Dependencies**: None (can start immediately)

**Objective**: Document all external dependencies Task-Orchestrator requires

**Specific Actions**:
1. Read `requirements.txt` or `setup.py` (if exists)
2. Scan all 13 modules for imports (aiohttp, redis, etc.)
3. Check Docker dependencies
4. List required environment variables
5. Document API key requirements (Leantime, OpenAI if ML features)

**Deliverable**: `task-orchestrator-dependencies.md` with:
- Python package dependencies
- External services (Redis, Leantime, OpenAI)
- Environment variables required
- Infrastructure needs (Docker, ports)

**Acceptance Criteria**:
- ✅ All Python dependencies listed with versions
- ✅ All external services identified
- ✅ All environment variables documented
- ✅ Infrastructure requirements clear

---

#### Task 1.2: Verify Redis Infrastructure
**Duration**: 30 minutes
**Complexity**: 0.3 (low)
**Energy**: Low
**Dependencies**: Task 1.1 (needs dependency list)

**Objective**: Ensure Redis is available and properly configured

**Specific Actions**:
1. Check if Redis is running (`redis-cli ping`)
2. Verify Redis port availability (default 6379)
3. Test Redis connectivity from Python
4. Check Redis DB allocation (Task-Orchestrator uses DB 2 & 3)
5. Verify Redis persistence configuration

**Deliverable**: Redis connection validated

**Acceptance Criteria**:
- ✅ Redis responds to ping
- ✅ Python can connect to Redis
- ✅ DBs 2 and 3 available
- ✅ Persistence configured (AOF or RDB)

---

#### Task 1.3: Audit Task-Orchestrator Code for ConPort API Usage
**Duration**: 90 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: High
**Dependencies**: None (can run in parallel with 1.1-1.2)

**Objective**: Find all places where Task-Orchestrator expects ConPort APIs (pre-v2.0)

**Specific Actions**:
1. Search for ConPort API calls across all modules
2. Identify schema assumptions (what fields are expected)
3. Find direct storage operations (`self.orchestrated_tasks[...]`)
4. Document current vs needed API contracts
5. Create migration checklist

**Deliverable**: `conport-api-audit.md` with:
- List of all ConPort API calls in current code
- Expected schema fields
- Direct storage operations to replace
- API contract gaps

**Acceptance Criteria**:
- ✅ All ConPort API usages found
- ✅ Schema expectations documented
- ✅ Storage operations identified
- ✅ Migration checklist created

---

#### Task 1.4: Check Deployment Infrastructure
**Duration**: 45 minutes
**Complexity**: 0.4 (moderate-low)
**Energy**: Medium
**Dependencies**: Task 1.1 (needs dependency list)

**Objective**: Verify Docker, environment configs, and deployment readiness

**Specific Actions**:
1. Check for Dockerfile in `services/task-orchestrator/`
2. Check for docker-compose configuration
3. Verify environment variable setup (`.env.example`)
4. Check CI/CD integration (if any)
5. Document missing infrastructure

**Deliverable**: `deployment-audit.md` with:
- Existing infrastructure (Docker, configs)
- Missing components
- Setup requirements

**Acceptance Criteria**:
- ✅ Dockerfile status documented
- ✅ Environment config status clear
- ✅ Missing infrastructure identified
- ✅ Setup steps documented

---

#### Task 1.5: Create Phase 1 Audit Summary
**Duration**: 30 minutes
**Complexity**: 0.3 (low)
**Energy**: Low
**Dependencies**: Tasks 1.1, 1.2, 1.3, 1.4 (all audit tasks)

**Objective**: Synthesize audit findings into actionable summary

**Specific Actions**:
1. Compile findings from Tasks 1.1-1.4
2. Identify critical blockers (if any)
3. Prioritize remediation work
4. Update Phase 1 timeline if needed
5. Create go/no-go recommendation

**Deliverable**: `phase-1-audit-summary.md` with:
- Infrastructure readiness score
- Critical blockers identified
- Remediation plan
- Updated timeline estimate

**Acceptance Criteria**:
- ✅ All audit findings synthesized
- ✅ Blockers prioritized
- ✅ Go/no-go decision clear
- ✅ Timeline validated or updated

---

### Component 2: Data Contract Adapters (6 hours, 360 minutes)

#### Task 2.1: Design ConPort Event Schema
**Duration**: 60 minutes
**Complexity**: 0.7 (high)
**Energy**: High
**Dependencies**: Task 1.3 (needs API audit results)

**Objective**: Define event schemas for ConPort → Task-Orchestrator communication

**Specific Actions**:
1. Review ConPort's current event structure (Integration Bridge)
2. Map ConPort `progress_entry` fields to OrchestrationTask
3. Define event types (progress.created, progress.updated, progress.deleted)
4. Add versioning to schemas (v1.0)
5. Document event payload examples

**Deliverable**: `conport-event-schema.json` with:
```json
{
  "version": "1.0",
  "events": {
    "conport.progress.created": {
      "payload": {...},
      "required_fields": [...]
    }
  }
}
```

**Acceptance Criteria**:
- ✅ All event types defined
- ✅ Schemas versioned
- ✅ Payload examples provided
- ✅ Required vs optional fields clear

---

#### Task 2.2: Create ConPort Event Adapter Class
**Duration**: 90 minutes
**Complexity**: 0.7 (high)
**Energy**: High
**Dependencies**: Task 2.1 (needs event schema)

**Objective**: Build adapter that converts ConPort events to OrchestrationTask

**Specific Actions**:
1. Create `adapters/conport_event_adapter.py`
2. Implement `ConPortEventAdapter` class
3. Add schema validation (pydantic)
4. Map ConPort fields → OrchestrationTask fields
5. Handle missing/optional fields gracefully
6. Add comprehensive error handling

**Deliverable**: `adapters/conport_event_adapter.py` with:
- ConPortEventAdapter class
- Schema validation
- Field mapping logic
- Error handling

**Code Structure**:
```python
class ConPortEventAdapter:
    def adapt_progress_entry(self, conport_event: Dict) -> OrchestrationTask:
        """Convert ConPort progress_entry event to OrchestrationTask."""
        return OrchestrationTask(
            id=conport_event["id"],
            title=self._extract_title(conport_event["description"]),
            description=conport_event["description"],
            status=self._map_status(conport_event["status"]),
            complexity_score=conport_event.get("complexity_score", 0.5),
            # ... map all fields
        )
```

**Acceptance Criteria**:
- ✅ Adapter class implements all mappings
- ✅ Schema validation prevents invalid data
- ✅ Error handling with logging
- ✅ Unit tests written

---

#### Task 2.3: Create Insight Publisher Class
**Duration**: 60 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: High
**Dependencies**: Task 2.1 (needs event schema for insights)

**Objective**: Build publisher that sends Task-Orchestrator insights to ConPort

**Specific Actions**:
1. Create `adapters/insight_publisher.py`
2. Define insight event schemas (dependency_analysis_complete, risk_assessment_complete)
3. Implement `InsightPublisher` class
4. Add Integration Bridge publishing logic
5. Handle publishing failures (queue for retry)

**Deliverable**: `adapters/insight_publisher.py` with:
- InsightPublisher class
- Event schema definitions
- Retry logic for failures

**Code Structure**:
```python
class InsightPublisher:
    async def publish_dependency_analysis(
        self,
        task_id: str,
        dependencies: List[str],
        blockers: List[str],
        critical_path: List[str]
    ) -> bool:
        """Publish dependency analysis results to ConPort."""
        event = {
            "type": "orchestrator.analysis.complete",
            "source": "task-orchestrator",
            "target": "conport",
            "data": {
                "task_id": task_id,
                "dependencies": dependencies,
                "blockers": blockers,
                "critical_path": critical_path
            }
        }
        return await self.integration_bridge.publish(event)
```

**Acceptance Criteria**:
- ✅ Publisher class complete
- ✅ All insight types supported
- ✅ Retry logic implemented
- ✅ Integration Bridge integration working

---

#### Task 2.4: Implement OrchestrationTask ↔ ConPort Mapping
**Duration**: 45 minutes
**Complexity**: 0.5 (moderate)
**Energy**: Medium
**Dependencies**: Task 2.2 (uses adapter)

**Objective**: Create bidirectional mapping utilities

**Specific Actions**:
1. Create `utils/schema_mapping.py`
2. Implement `conport_to_orchestration_task()`
3. Implement `orchestration_task_to_conport()`
4. Handle ADHD metadata preservation
5. Add validation

**Deliverable**: `utils/schema_mapping.py` with mapping functions

**Acceptance Criteria**:
- ✅ Bidirectional mapping works
- ✅ No data loss in round-trip
- ✅ ADHD metadata preserved
- ✅ Unit tests pass

---

#### Task 2.5: Remove Direct Storage from Task-Orchestrator
**Duration**: 75 minutes
**Complexity**: 0.7 (high)
**Energy**: High
**Dependencies**: Task 2.2, 2.3 (needs adapters ready)

**Objective**: Replace `self.orchestrated_tasks` dict with ConPort queries

**Specific Actions**:
1. Find all `self.orchestrated_tasks` usage in enhanced_orchestrator.py
2. Replace with ConPort queries via Integration Bridge
3. Update to event-driven pattern (subscribe/publish)
4. Remove local storage dictionary
5. Update all methods that read/write tasks

**Deliverable**: `enhanced_orchestrator.py` updated to use ConPort as authority

**Code Changes**:
```python
# OLD:
task = self.orchestrated_tasks[task_id]

# NEW:
task = await self.conport_client.get_task(task_id)

# OLD:
self.orchestrated_tasks[task_id] = updated_task

# NEW:
await self.insight_publisher.publish_task_update(updated_task)
```

**Acceptance Criteria**:
- ✅ No local task storage remains
- ✅ All task access via ConPort
- ✅ All updates via event publishing
- ✅ Tests updated and passing

---

#### Task 2.6: Integration Test for Event Flow
**Duration**: 50 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: High
**Dependencies**: Task 2.2, 2.3, 2.5 (adapters + updated code)

**Objective**: Test complete event flow: ConPort → Task-Orchestrator → ConPort

**Specific Actions**:
1. Create `tests/integration/test_conport_event_flow.py`
2. Test: Create task in ConPort → Event received by Task-Orchestrator
3. Test: Task-Orchestrator publishes insight → Received by ConPort
4. Test: Round-trip latency < 2 seconds
5. Test: Error handling (malformed events, connection failures)

**Deliverable**: Integration test suite for event flow

**Acceptance Criteria**:
- ✅ Event flow tests pass
- ✅ Latency < 2 seconds
- ✅ Error handling validated
- ✅ Test coverage > 80%

---

### Component 3: Integration Bridge Wiring (4 hours, 240 minutes)

#### Task 3.1: Configure Integration Bridge for Task-Orchestrator
**Duration**: 60 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: Medium
**Dependencies**: None (can start early)

**Objective**: Set up Integration Bridge routing for Task-Orchestrator

**Specific Actions**:
1. Review Integration Bridge configuration (PORT_BASE+16)
2. Add Task-Orchestrator as subscriber/publisher
3. Configure event routing rules
4. Set up Redis Streams integration
5. Test connection to Integration Bridge

**Deliverable**: Integration Bridge config updated

**Configuration**:
```python
# Integration Bridge config
task_orchestrator_config = {
    "service_name": "task-orchestrator",
    "subscriptions": [
        "conport.progress.created",
        "conport.progress.updated",
        "conport.decision.logged"
    ],
    "publications": [
        "orchestrator.analysis.complete",
        "orchestrator.risk.assessed",
        "orchestrator.blocker.identified"
    ],
    "redis_stream": "task-orchestrator-events",
    "consumer_group": "task-orchestrator-group"
}
```

**Acceptance Criteria**:
- ✅ Integration Bridge recognizes Task-Orchestrator
- ✅ Subscriptions configured
- ✅ Publications configured
- ✅ Connection test passes

---

#### Task 3.2: Implement Event Subscription in Task-Orchestrator
**Duration**: 75 minutes
**Complexity**: 0.7 (high)
**Energy**: High
**Dependencies**: Task 3.1 (Bridge configured), Task 2.2 (adapter ready)

**Objective**: Enable Task-Orchestrator to receive ConPort events

**Specific Actions**:
1. Update `enhanced_orchestrator.py` with event subscription
2. Implement `_subscribe_to_conport_events()` method
3. Add event handlers for each event type
4. Integrate ConPortEventAdapter
5. Add error handling and logging

**Deliverable**: Event subscription working in enhanced_orchestrator.py

**Code Implementation**:
```python
async def _subscribe_to_conport_events(self):
    """Subscribe to ConPort task events via Integration Bridge."""
    await self.integration_bridge.subscribe(
        event_type="conport.progress.created",
        handler=self._handle_task_created
    )
    await self.integration_bridge.subscribe(
        event_type="conport.progress.updated",
        handler=self._handle_task_updated
    )

async def _handle_task_created(self, event: Dict):
    """Handle new task creation from ConPort."""
    orchestration_task = self.conport_adapter.adapt_progress_entry(event["data"])
    await self._analyze_task_dependencies(orchestration_task)
```

**Acceptance Criteria**:
- ✅ Subscription code implemented
- ✅ Event handlers working
- ✅ Adapter integration complete
- ✅ Logging comprehensive

---

#### Task 3.3: Implement Insight Publishing to ConPort
**Duration**: 60 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: Medium
**Dependencies**: Task 3.1 (Bridge configured), Task 2.3 (publisher ready)

**Objective**: Enable Task-Orchestrator to send insights back to ConPort

**Specific Actions**:
1. Update dependency analysis methods to use InsightPublisher
2. Publish results via Integration Bridge
3. Format insights for ConPort decision logging
4. Add retry logic for failed publishes
5. Log all publish events

**Deliverable**: Insight publishing integrated into all analysis methods

**Code Implementation**:
```python
async def _analyze_task_dependencies(self, task: OrchestrationTask):
    """Analyze task dependencies and publish insights."""
    # Perform analysis
    dependencies = await self._find_dependencies(task)
    blockers = await self._identify_blockers(task)
    critical_path = await self._calculate_critical_path(task)

    # Publish insights to ConPort
    await self.insight_publisher.publish_dependency_analysis(
        task_id=task.id,
        dependencies=dependencies,
        blockers=blockers,
        critical_path=critical_path
    )
```

**Acceptance Criteria**:
- ✅ All analysis methods publish insights
- ✅ Integration Bridge receives events
- ✅ ConPort receives and stores insights
- ✅ Retry logic working

---

#### Task 3.4: Integration Test for Bridge Communication
**Duration**: 45 minutes
**Complexity**: 0.5 (moderate)
**Energy**: Medium
**Dependencies**: Task 3.2, 3.3 (subscription + publishing working)

**Objective**: Validate bidirectional Integration Bridge communication

**Specific Actions**:
1. Create `tests/integration/test_integration_bridge.py`
2. Test: ConPort event → Integration Bridge → Task-Orchestrator
3. Test: Task-Orchestrator insight → Integration Bridge → ConPort
4. Test: Event latency < 2 seconds
5. Test: Error handling (Bridge down, malformed events)

**Deliverable**: Integration Bridge test suite

**Acceptance Criteria**:
- ✅ Bidirectional communication working
- ✅ Latency acceptable (< 2s)
- ✅ Error handling robust
- ✅ Tests pass consistently

---

### Component 4: Core Module Activation (4 hours, 240 minutes)

#### Task 4.1: Enable Dependency Analysis Module
**Duration**: 75 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: High
**Dependencies**: Task 2.5 (storage removed), Task 3.2 (events wired)

**Objective**: Activate dependency analysis tools (Tools 1-10)

**Specific Actions**:
1. Review dependency analysis code in enhanced_orchestrator.py
2. Update to use ConPort task queries (not local storage)
3. Test analyze_dependencies, find_critical_path, identify_blockers
4. Validate insights are published correctly
5. Ensure no direct storage operations

**Deliverable**: Dependency analysis operational

**Test Scenarios**:
```python
# Scenario 1: Simple dependency chain
Task A (no deps) → Task B (depends on A) → Task C (depends on B)
Expected: Critical path = [A, B, C], B blocked by A, C blocked by B

# Scenario 2: Parallel tasks
Task A, B, C (no deps)
Expected: Can parallelize, critical path = any single task

# Scenario 3: Complex graph
Task A, B (no deps) → Task C (depends A, B) → Task D (depends C)
Expected: Critical path includes C (waiting for both A and B)
```

**Acceptance Criteria**:
- ✅ All 10 dependency tools operational
- ✅ No local storage used
- ✅ Insights published to ConPort
- ✅ Test scenarios pass

---

#### Task 4.2: Configure ADHD Engine Integration
**Duration**: 60 minutes
**Complexity**: 0.5 (moderate)
**Energy**: Medium
**Dependencies**: Task 4.1 (dependency analysis working)

**Objective**: Integrate Task-Orchestrator ADHD engine with ConPort

**Specific Actions**:
1. Review adhd_engine.py requirements
2. Configure Redis connection (DB 3)
3. Enable energy level tracking
4. Enable attention state monitoring
5. Test ADHD metadata flows through system

**Deliverable**: ADHD engine operational and integrated

**ADHD Features to Validate**:
- Energy level tracking (VERY_LOW → HYPERFOCUS)
- Attention state monitoring (SCATTERED → HYPERFOCUSED)
- Cognitive load calculation
- Break enforcement
- Context switch monitoring

**Acceptance Criteria**:
- ✅ ADHD engine initialized
- ✅ Energy/attention tracking works
- ✅ Cognitive load calculated correctly
- ✅ Break reminders trigger appropriately

---

#### Task 4.3: Disable Advanced Features for Phase 3
**Duration**: 45 minutes
**Complexity**: 0.4 (moderate-low)
**Energy**: Low
**Dependencies**: Task 4.1, 4.2 (core features working)

**Objective**: Safely disable tools 11-37 (defer to Phase 3)

**Specific Actions**:
1. Add feature flags for advanced modules
2. Disable multi-team coordination (tools 11-17)
3. Disable ML risk assessment (tools 18-25)
4. Disable workflow automation (tools 26-31)
5. Disable performance optimizer (tools 32-35)
6. Disable deployment orchestration (tools 36-37)
7. Log which features are disabled

**Deliverable**: Feature flag system with Phase 3 features disabled

**Configuration**:
```python
ORCHESTRATOR_FEATURES = {
    "dependency_analysis": True,      # Phase 1 ✅
    "adhd_engine": True,              # Phase 1 ✅
    "multi_team_coordination": False, # Phase 3 ⏳
    "ml_risk_assessment": False,      # Phase 3 ⏳
    "workflow_automation": False,     # Phase 3 ⏳
    "performance_optimizer": False,   # Phase 3 ⏳
    "deployment_orchestration": False # Phase 3 ⏳
}
```

**Acceptance Criteria**:
- ✅ Feature flags implemented
- ✅ Advanced features disabled
- ✅ No errors from disabled features
- ✅ Logs show feature status

---

#### Task 4.4: End-to-End Validation
**Duration**: 60 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: Medium
**Dependencies**: Task 4.1, 4.2, 4.3 (all core features ready)

**Objective**: Validate complete Phase 1 integration works end-to-end

**Specific Actions**:
1. Create real ConPort task
2. Verify Task-Orchestrator receives event
3. Verify dependency analysis runs
4. Verify insights published back to ConPort
5. Verify ConPort stores insights
6. Measure end-to-end latency

**Deliverable**: End-to-end validation report

**Test Flow**:
```
1. Create task in ConPort (via mcp__conport__log_progress)
   ↓
2. Wait for Task-Orchestrator to receive event (< 1s)
   ↓
3. Wait for dependency analysis to complete (< 500ms)
   ↓
4. Wait for insights to publish (< 500ms)
   ↓
5. Verify ConPort received insights (query decisions/patterns)
   ↓
Total latency target: < 2 seconds
```

**Acceptance Criteria**:
- ✅ Full flow completes successfully
- ✅ Latency < 2 seconds
- ✅ No data loss
- ✅ No errors logged

---

### Component 5: Testing (2 hours, 120 minutes)

#### Task 5.1: Create Integration Test Suite
**Duration**: 60 minutes
**Complexity**: 0.6 (moderate-high)
**Energy**: High
**Dependencies**: Task 4.4 (end-to-end working)

**Objective**: Comprehensive integration test coverage

**Specific Actions**:
1. Create `tests/integration/test_phase1_integration.py`
2. Test: Simple dependency chain (3 tasks)
3. Test: Parallel tasks (no dependencies)
4. Test: Complex dependency graph (10+ tasks)
5. Test: Blocker identification
6. Test: Critical path calculation
7. Test: Authority boundaries (Task-Orchestrator doesn't store)
8. Test: Error recovery (ConPort down, Bridge down)

**Deliverable**: Comprehensive integration test suite

**Test Cases** (minimum 8):
1. Simple dependency chain
2. Parallel task detection
3. Complex dependency graph
4. Blocker identification
5. Critical path accuracy
6. Authority boundary enforcement
7. Error recovery (ConPort unavailable)
8. Error recovery (Integration Bridge unavailable)

**Acceptance Criteria**:
- ✅ All test cases pass
- ✅ Coverage > 90%
- ✅ Tests run in < 30 seconds
- ✅ Clear test output

---

#### Task 5.2: Performance and Load Testing
**Duration**: 60 minutes
**Complexity**: 0.5 (moderate)
**Energy**: Medium
**Dependencies**: Task 5.1 (integration tests passing)

**Objective**: Validate performance under load

**Specific Actions**:
1. Create `tests/load/test_phase1_load.py`
2. Test: 100 tasks created in ConPort simultaneously
3. Test: Dependency analysis completes for all (< 5s)
4. Test: Memory usage stays < 500MB
5. Test: CPU usage stays < 50%
6. Measure throughput (events/second)

**Deliverable**: Load test suite with performance report

**Load Test Scenarios**:
- 100 tasks created (burst)
- 1000 tasks created (sustained over 1 minute)
- Complex dependency graph (100 tasks, 200 dependencies)
- Stress test (create until failure, measure limits)

**Performance Targets**:
- Event processing: > 50 events/second
- Memory usage: < 500MB for 1000 tasks
- CPU usage: < 50% average
- Latency: P95 < 2 seconds

**Acceptance Criteria**:
- ✅ All load tests pass
- ✅ Performance targets met
- ✅ No memory leaks
- ✅ Graceful degradation under load

---

## Task Summary Table

| # | Task | Duration | Complexity | Energy | Dependencies | Component |
|---|------|----------|------------|--------|--------------|-----------|
| 1.1 | Inventory External Dependencies | 45m | 0.4 | Medium | - | Audit |
| 1.2 | Verify Redis Infrastructure | 30m | 0.3 | Low | 1.1 | Audit |
| 1.3 | Audit ConPort API Usage | 90m | 0.6 | High | - | Audit |
| 1.4 | Check Deployment Infrastructure | 45m | 0.4 | Medium | 1.1 | Audit |
| 1.5 | Create Audit Summary | 30m | 0.3 | Low | 1.1-1.4 | Audit |
| 2.1 | Design ConPort Event Schema | 60m | 0.7 | High | 1.3 | Adapters |
| 2.2 | Create ConPort Event Adapter | 90m | 0.7 | High | 2.1 | Adapters |
| 2.3 | Create Insight Publisher | 60m | 0.6 | High | 2.1 | Adapters |
| 2.4 | Implement Schema Mapping | 45m | 0.5 | Medium | 2.2 | Adapters |
| 2.5 | Remove Direct Storage | 75m | 0.7 | High | 2.2, 2.3 | Adapters |
| 2.6 | Integration Test Event Flow | 50m | 0.6 | High | 2.2, 2.3, 2.5 | Adapters |
| 3.1 | Configure Integration Bridge | 60m | 0.6 | Medium | - | Bridge |
| 3.2 | Implement Event Subscription | 75m | 0.7 | High | 3.1, 2.2 | Bridge |
| 3.3 | Implement Insight Publishing | 60m | 0.6 | Medium | 3.1, 2.3 | Bridge |
| 3.4 | Test Bridge Communication | 45m | 0.5 | Medium | 3.2, 3.3 | Bridge |
| 4.1 | Enable Dependency Analysis | 75m | 0.6 | High | 2.5, 3.2 | Activation |
| 4.2 | Configure ADHD Engine | 60m | 0.5 | Medium | 4.1 | Activation |
| 4.3 | Disable Advanced Features | 45m | 0.4 | Low | 4.1, 4.2 | Activation |
| 4.4 | End-to-End Validation | 60m | 0.6 | Medium | 4.1, 4.2, 4.3 | Activation |
| 5.1 | Create Integration Test Suite | 60m | 0.6 | High | 4.4 | Testing |
| 5.2 | Performance and Load Testing | 60m | 0.5 | Medium | 5.1 | Testing |

**Totals**: 20 tasks, 1,200 minutes (20 hours)

---

## Dependency Graph

```
Start
  ├─ 1.1 (Inventory Dependencies) ─┬─ 1.2 (Verify Redis)
  │                                └─ 1.4 (Check Deployment) ─┐
  ├─ 1.3 (Audit ConPort API) ────────── 2.1 (Event Schema) ─┤
  │                                                          │
  │                                     1.5 (Audit Summary) ─┘
  │                                           │
  │                                           v
  │                     2.1 ─┬─ 2.2 (Event Adapter) ───┬─ 2.5 (Remove Storage) ─┐
  │                          └─ 2.3 (Insight Publisher) ┘                        │
  │                                     │                                         │
  │                                     v                                         │
  ├─ 3.1 (Configure Bridge) ─┬─ 3.2 (Event Subscription) ──────────────────────┤
  │                          └─ 3.3 (Insight Publishing)                         │
  │                                     │                                         │
  │                                     v                                         │
  │                          3.4 (Test Bridge Comm) ────────────────────────────┤
  │                                     │                                         │
  │                                     v                                         │
  │                          4.1 (Enable Dependency Analysis) ─┬─ 4.2 (ADHD)    │
  │                                                            └─ 4.3 (Disable)  │
  │                                                                   │           │
  │                                                                   v           │
  │                                                       4.4 (E2E Validation) ───┤
  │                                                                   │           │
  │                                                                   v           │
  └────────────────────────────────────────────────── 5.1 (Integration Tests) ──┤
                                                                      │           │
                                                                      v           │
                                                          5.2 (Load Testing) ─────┘
                                                                      │
                                                                      v
                                                                   Done!
```

---

## Parallelization Opportunities

### Week 1: Audit + Initial Design (Can Run in Parallel)

**Parallel Track A**:
- Task 1.1 (Inventory Dependencies) → 1.2 (Verify Redis) → 1.4 (Deployment)

**Parallel Track B**:
- Task 1.3 (Audit ConPort API) → 2.1 (Event Schema Design)

**Parallel Track C**:
- Task 3.1 (Configure Bridge) - can start independently

**Convergence**: Task 1.5 (Audit Summary) - waits for all tracks

### Week 2: Implementation + Testing (Sequential with Some Parallelism)

**Sequential Critical Path**:
- 2.1 → 2.2 → 2.5 → 3.2 → 4.1 → 4.4 → 5.1 → 5.2

**Parallel Opportunities**:
- 2.3 (Insight Publisher) can develop parallel to 2.2
- 3.3 (Publishing) can develop parallel to 3.2
- 4.2 (ADHD) + 4.3 (Disable) can run parallel to 4.1 completion

---

## ADHD Optimization for Implementation

### Session Structure

**25-Minute Sessions** (Pomodoro):
- Tasks ≤ 45 minutes: Single session
- Tasks 60-75 minutes: Two sessions with 5-min break
- Tasks 90 minutes: Three sessions with 5-min breaks

**Energy Matching**:
- **High Energy** (morning): Tasks 1.3, 2.2, 2.5, 3.2, 4.1, 5.1
- **Medium Energy** (afternoon): Tasks 1.1, 1.4, 2.3, 3.1, 3.3, 4.2, 4.4, 5.2
- **Low Energy** (evening): Tasks 1.2, 1.5, 2.4, 3.4, 4.3

### Break Points

**Natural Stopping Points** (safe to pause):
- After any completed task
- After Component 1 (Audit) - 4 hours
- After Component 2 (Adapters) - 10 hours
- After Component 3 (Bridge) - 14 hours
- After Component 4 (Activation) - 18 hours
- After Component 5 (Testing) - 20 hours

**Don't Interrupt** (focus required):
- Task 2.5 (Remove Storage) - critical refactoring
- Task 3.2 (Event Subscription) - complex integration
- Task 4.1 (Enable Analysis) - core feature activation

---

## Risk Register

### Risk 1: Missing Dependencies
**Impact**: High (blocks progress)
**Probability**: Low (audit will find)
**Mitigation**: Task 1.1 runs first, identifies all dependencies before implementation
**Owner**: Task 1.1

### Risk 2: ConPort API Schema Mismatch
**Impact**: High (adapters fail)
**Probability**: Medium (pre-v2.0 code)
**Mitigation**: Task 1.3 audits early, Task 2.1 designs schemas with validation
**Owner**: Task 1.3, 2.1

### Risk 3: Integration Bridge Not Ready
**Impact**: High (can't communicate)
**Probability**: Low (existing infrastructure)
**Mitigation**: Task 3.1 validates early, can use direct Redis if needed
**Owner**: Task 3.1

### Risk 4: Event Latency Too High
**Impact**: Medium (user experience)
**Probability**: Low (simple operations)
**Mitigation**: Task 3.4 and 5.2 measure latency, optimize if needed
**Owner**: Task 3.4, 5.2

### Risk 5: ADHD Engine Conflicts
**Impact**: Medium (two ADHD engines)
**Probability**: Medium (services/adhd_engine exists)
**Mitigation**: Task 4.2 validates no conflicts, can use orchestrator's engine only
**Owner**: Task 4.2

---

## Success Metrics

### Technical Metrics
- ✅ Event processing latency: P95 < 2 seconds
- ✅ Integration test coverage: > 90%
- ✅ Load test throughput: > 50 events/second
- ✅ Memory usage: < 500MB
- ✅ Zero authority violations

### Functional Metrics
- ✅ Dependency analysis accuracy: > 95%
- ✅ Blocker identification: All blockers found
- ✅ Critical path calculation: Matches manual analysis
- ✅ Parallel task detection: Identifies all parallel opportunities

### ADHD Metrics
- ✅ Cognitive load calculated for all tasks
- ✅ Energy level tracking operational
- ✅ Break enforcement working
- ✅ Context preservation < 2 minutes after interruption

---

## Week-by-Week Timeline

### Week 1: Foundation (8-10 hours)

**Monday-Tuesday** (4h):
- Task 1.1, 1.2, 1.3 (parallel tracks)
- Task 1.4, 1.5 (sequential)
- **Deliverable**: Complete audit with go/no-go decision

**Wednesday-Thursday** (4h):
- Task 2.1 (Event Schema Design)
- Task 3.1 (Configure Bridge)
- Task 2.2 (Event Adapter - start)
- **Deliverable**: Schemas defined, Bridge configured

**Friday** (2h):
- Task 2.2 (Event Adapter - finish)
- Task 2.3 (Insight Publisher)
- **Deliverable**: Adapters complete

### Week 2: Integration (10-12 hours)

**Monday** (4h):
- Task 2.4 (Schema Mapping)
- Task 2.5 (Remove Storage)
- Task 2.6 (Test Event Flow)
- **Deliverable**: Adapters integrated and tested

**Tuesday-Wednesday** (4h):
- Task 3.2 (Event Subscription)
- Task 3.3 (Insight Publishing)
- Task 3.4 (Test Bridge)
- **Deliverable**: Integration Bridge wired and working

**Thursday** (4h):
- Task 4.1 (Enable Analysis)
- Task 4.2 (ADHD Engine)
- Task 4.3 (Disable Advanced)
- Task 4.4 (E2E Validation)
- **Deliverable**: Core features operational

**Friday** (2h):
- Task 5.1 (Integration Tests)
- Task 5.2 (Load Testing)
- **Deliverable**: Phase 1 complete, tested, validated

---

## Next Actions

### Immediate (This Session)
1. ✅ Review this implementation plan
2. **Import to ConPort** (optional): Create progress entries for all 20 tasks
3. **Begin Task 1.1** (Inventory Dependencies) - 45 minutes, can start now

### This Week
4. Complete Component 1 (Audit) - 4 hours
5. Make go/no-go decision based on audit
6. Begin Component 2 (Adapters) if go

### Next Week
7. Complete integration and activation
8. Run comprehensive tests
9. Validate Phase 1 complete

---

## ConPort Import Ready

This plan is structured for import to ConPort using `/dx:prd-parse` format:

**Ready to import**:
- 20 tasks with descriptions
- Complexity scores (0.0-1.0)
- Duration estimates (minutes)
- Energy requirements (low/medium/high)
- Dependencies identified
- Acceptance criteria defined

**To import**: Can create ConPort progress entries manually or via batch_log_items

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Status**: ✅ Ready for Implementation
**Total Effort**: 20 hours, 20 tasks, 2 weeks
