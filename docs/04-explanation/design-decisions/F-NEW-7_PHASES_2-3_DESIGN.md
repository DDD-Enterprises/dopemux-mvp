# F-NEW-7 Phases 2-3: Unified Queries + Cross-Agent Intelligence

**Status**: Architecture designed (Option 4 from quadruple execution)
**Prerequisites**: Phase 1 (Multi-Tenancy) must be complete
**Duration**: 3 weeks (Phase 2: 1 week, Phase 3: 2 weeks)

---

## Phase 2: Unified Query Layer (Week 3)

### Overview
Enable users to query their data across all workspaces with a single API call.

### Architecture

```
User Request: "Find all auth-related decisions"
  ↓
Unified Query API
  ├─ user_id: "alice"
  ├─ query: "authentication"
  └─ workspaces: ["project-a", "project-b", "project-c"]
  ↓
PostgreSQL AGE Query
  WHERE user_id = 'alice'
  AND workspace_id IN ('project-a', 'project-b', 'project-c')
  AND to_tsvector(summary || rationale) @@ plainto_tsquery('authentication')
  ↓
Aggregated Results (ranked by relevance + recency)
```

### Key Features

**1. Cross-Workspace Search**
```python
async def search_across_workspaces(
    user_id: str,
    query: str,
    workspaces: List[str] = None  # None = all user's workspaces
) -> List[Decision]:
    # Full-text search across multiple workspaces
    # Results ranked by relevance + workspace priority
```

**2. Multi-Workspace Relationship Traversal**
```python
async def get_related_decisions(
    decision_id: UUID,
    user_id: str,
    include_workspaces: bool = True,
    max_depth: int = 3
) -> Graph:
    # Traverse relationships across workspace boundaries
    # Respects user permissions
```

**3. Workspace Aggregations**
```python
async def get_workspace_summary(user_id: str) -> Dict:
    # Per-workspace statistics
    # Total decisions, recent activity, patterns
```

### Performance Optimization

**Composite Indexes**:
```sql
CREATE INDEX idx_decisions_user_fts
ON decisions(user_id) INCLUDE (summary, rationale);

CREATE INDEX idx_decisions_user_workspace_recent
ON decisions(user_id, workspace_id, created_at DESC);
```

**Caching Strategy**:
- User workspace list: 5 min TTL
- Cross-workspace results: 1 min TTL
- Relationship graphs: 30 min TTL

### Success Criteria
- Cross-workspace search < 200ms (ADHD target)
- Works with 5+ workspaces per user
- Relationship traversal < 500ms for depth-3

---

## Phase 3: Cross-Agent Intelligence (Weeks 4-5)

### Overview
Automatically generate insights from cross-agent event correlations.

### Intelligence Types

**Type 1: Pattern-Based Insights**
```
IF Serena detects 3+ high complexity files in same directory
AND Dope-Context shows repeated searches in that directory
THEN: "💡 High complexity cluster detected in services/auth/
      Consider refactoring or adding documentation"
```

**Type 2: Cognitive-Code Correlation**
```
IF ADHD Engine shows energy declining
AND Serena shows user editing high complexity code (>0.7)
THEN: "⚠️ Low energy + high complexity task
      Switch to simpler task or take break"
```

**Type 3: Context Switch Recovery**
```
IF Desktop Commander detects workspace switch
AND Last workspace had uncommitted work
THEN: "🔄 Context switch to {new_workspace}
      You left {files} uncommitted in {old_workspace}"
```

**Type 4: Pattern Learning**
```
IF Dope-Context shows repeated search pattern
AND Search results consistent
THEN: "📚 You've searched 'authentication' 5x this week
      Bookmark: services/auth/middleware.py, services/auth/jwt.py"
```

### Architecture

```
Pattern Detectors (already built!)
  ├─ High Complexity Cluster
  ├─ False Starts Pattern
  ├─ Search Pattern Cluster
  ├─ Low Energy Pattern
  ├─ Frequent Context Switch
  ├─ Refactoring Opportunity
  └─ Task Bottleneck
  ↓
Insight Generator (NEW)
  ├─ Correlate patterns across agents
  ├─ Generate actionable insights
  ├─ Rank by ADHD impact
  └─ Filter by user preferences
  ↓
Delivery
  ├─ F-NEW-6 Dashboard (primary)
  ├─ Terminal notifications
  └─ ConPort decisions (auto-logged)
```

### Implementation Files

**Week 4**:
1. `services/insight-generator/correlator.py` (~400 lines)
   - Cross-agent pattern correlation
   - Insight generation rules
   - ADHD-optimized ranking

2. `services/insight-generator/insight_types.py` (~300 lines)
   - 4 insight type implementations
   - Template system for new types
   - Confidence scoring

**Week 5**:
3. Integration with F-NEW-6 dashboard (~200 lines)
4. Auto-logging to ConPort (~100 lines)
5. Testing suite (~400 lines)
6. User preferences system (~200 lines)

### Success Criteria

- 3+ actionable insights per session
- <200ms insight generation
- User reports reduced decision fatigue
- 80%+ insight relevance rate

### ADHD Optimization

**Progressive Disclosure**:
- Show 3 top insights max
- Expand for details on request
- Gentle, non-intrusive delivery

**Personalization**:
- Learn which insights user acts on
- Suppress low-relevance patterns
- Adapt to individual workflows

---

## Integration with Existing Infrastructure

### Leverages (Already Built)

**From ConPort-KG Phase 2** (Decision #247):
- EventBus with deduplication ✅
- 7 pattern detectors ✅
- Event aggregation ✅
- 6 agent integrations ✅

**From F-NEW Features**:
- F-NEW-6: Dashboard delivery ✅
- F-NEW-8: Break correlation logic ✅
- ADHD Engine: Cognitive state ✅
- Serena: Complexity events ✅

### New Components Needed

**Phase 2**:
- Cross-workspace query optimizer
- User workspace permissions cache
- Query result aggregator

**Phase 3**:
- Insight correlation engine
- Confidence scoring system
- User preference learning
- Progressive disclosure UI

---

## Deployment Sequence

**Phase 2 Deployment**:
1. Execute Migration 003 (Phase 1 complete)
2. Deploy unified query API
3. Test with 2-3 users × 3-5 workspaces each
4. Performance validation
5. Ship to production

**Phase 3 Deployment**:
1. Deploy insight generator (background service)
2. Enable 1 insight type at a time
3. Collect user feedback
4. Iterate and add more types
5. Full rollout

---

## Estimated Effort

**Phase 2**: 1 week (5 days × 4 hours) = 20 hours
**Phase 3**: 2 weeks (10 days × 4 hours) = 40 hours
**Total**: 60 hours ADHD-chunked work

**Dependencies**:
- Phase 1 complete (Migration 003 executed)
- EventBus operational (already ✅)
- Pattern detectors running (already ✅)

---

**Ready for Implementation**: Design complete, prerequisites validated
