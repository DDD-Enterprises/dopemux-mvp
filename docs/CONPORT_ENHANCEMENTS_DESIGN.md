---
id: CONPORT_ENHANCEMENTS_DESIGN
title: Conport_Enhancements_Design
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# ConPort Enhancement Design - Comprehensive Specification

**Created**: 2025-10-16
**Status**: Design Phase
**Priority**: High - Critical for ADHD workflow optimization

---

## 🎯 Vision

Transform ConPort from basic decision logging into an intelligent ADHD-optimized decision support system with pattern learning, confidence tracking, and proactive recommendations.

---

## 📋 Current State

### Existing Features (Solid Foundation)
- ✅ Decision logging (summary, rationale, implementation_details, tags)
- ✅ Async embedding pipeline (Voyage embeddings)
- ✅ Semantic search via Qdrant vector store
- ✅ PostgreSQL AGE graph database
- ✅ Redis caching for performance
- ✅ System patterns tracking
- ✅ Progress entries (task tracking)
- ✅ Custom data (flexible key-value)
- ✅ Knowledge graph relationships

### Gaps & Opportunities
- ❌ No decision confidence tracking
- ❌ No success criteria or review dates
- ❌ No decision outcome tracking (did it work?)
- ❌ Limited pattern detection (manual tags only)
- ❌ No ADHD-specific decision metrics
- ❌ No decision visualization tools
- ❌ No proactive review reminders

---

## 🚀 Phase 1: Enhanced Decision Tracking

### 1.1 Extended Decision Model

**New Fields**:
```python
class DecisionEnhanced(Decision):
    # Existing fields:
    # id, timestamp, summary, rationale, implementation_details, tags

    # New metadata fields:
    decision_type: Literal["architectural", "technical", "process", "adhd-pattern", "tooling"]
    confidence_level: float  # 0.0-1.0 (how certain are we?)
    impact_score: float  # 0.0-1.0 (estimated impact)
    reversibility: Literal["easy", "moderate", "difficult", "irreversible"]

    # Context fields:
    alternatives_considered: List[str]  # What we didn't choose and why
    success_criteria: List[str]  # How to measure if this worked
    review_date: Optional[datetime]  # When to revisit this decision
    related_decisions: List[int]  # Decision genealogy (builds on, supersedes)

    # Outcome tracking:
    outcome_status: Optional[Literal["pending", "successful", "failed", "mixed", "abandoned"]]
    outcome_notes: Optional[str]  # What actually happened
    outcome_date: Optional[datetime]  # When we learned the outcome
    lessons_learned: Optional[List[str]]  # What we learned from this

    # ADHD-specific:
    cognitive_load: Optional[float]  # 0.0-1.0 (how hard was this decision?)
    decision_time_minutes: Optional[float]  # How long did it take to decide?
    energy_level_when_decided: Optional[Literal["low", "medium", "high"]]
    requires_followup: bool = False  # Flag for later review
```

**Migration Strategy**:
- Add new columns to existing `decisions` table
- All new fields nullable for backward compatibility
- Provide defaults for existing decisions
- Progressive enhancement (use new fields when available)

### 1.2 Decision Genealogy Graph

**Relationship Types**:
```python
class DecisionRelationship:
    source_decision_id: int
    target_decision_id: int
    relationship_type: Literal[
        "builds_upon",      # This decision extends another
        "supersedes",       # This replaces a previous decision
        "conflicts_with",   # Incompatible decisions
        "validates",        # Confirms/tests another decision
        "implements",       # Puts another decision into practice
        "questions",        # Raises concerns about another decision
    ]
    notes: Optional[str]
    created_at: datetime
```

**Graph Queries**:
```sql
-- Find all decisions that led to this one:
SELECT * FROM decision_genealogy(decision_id, depth=3, direction='ancestors');

-- Find all decisions that followed from this:
SELECT * FROM decision_genealogy(decision_id, depth=3, direction='descendants');

-- Find conflicting decisions:
SELECT * FROM decisions d
JOIN decision_relationships r ON d.id = r.target_decision_id
WHERE r.source_decision_id = $1 AND r.relationship_type = 'conflicts_with';
```

### 1.3 Decision Lifecycle Management

**States**:
```
draft → proposed → accepted → implemented → validated → archived
                              ↓ (if failed)
                           abandoned → lessons_learned
```

**Automatic Transitions**:
- `draft → proposed`: When summary + rationale complete
- `proposed → accepted`: When implementation_details added
- `accepted → implemented`: When linked progress_entry marked DONE
- `implemented → validated`: When outcome_status set to "successful"
- `* → abandoned`: Manual user action

**Review Triggers**:
- 30 days after decision: Check if implemented
- 90 days after implementation: Check outcome
- When confidence < 0.5: Flag for team review
- When related decisions conflict: Alert user

---

## 🧠 Phase 2: Pattern Learning System

### 2.1 Decision Pattern Detection

**Auto-Detected Patterns**:

**By Tags** (Clustering):
```python
# Detect: "We make a lot of architectural decisions about database choices"
pattern = {
    "pattern_type": "tag_cluster",
    "tags": ["database", "architecture"],
    "frequency": 15,  # decisions/month
    "avg_confidence": 0.72,
    "avg_time_to_decide": 45,  # minutes
    "success_rate": 0.85  # of completed decisions
}
```

**By Decision Chain** (Genealogy):
```python
# Detect: "Database decisions often lead to caching decisions"
pattern = {
    "pattern_type": "decision_chain",
    "sequence": ["database selection", "caching strategy", "optimization"],
    "frequency": 8,  # chains/month
    "avg_chain_length": 3.2,
    "completion_rate": 0.90
}
```

**By Timing** (ADHD Indicator):
```python
# Detect: "Quick decisions (<15min) have lower success rate"
pattern = {
    "pattern_type": "timing_correlation",
    "finding": "Decisions made in <15min have 60% success vs 85% for >30min decisions",
    "recommendation": "Suggest taking more time for high-impact decisions",
    "confidence": 0.78
}
```

**By Energy Level** (ADHD Optimization):
```python
# Detect: "Decisions made during high-energy windows are more successful"
pattern = {
    "pattern_type": "energy_correlation",
    "finding": "High-energy decisions: 88% success, Low-energy: 62% success",
    "recommendation": "Defer complex decisions when energy is low",
    "peak_decision_times": ["10:00-12:00", "14:00-16:00"]
}
```

### 2.2 Success Prediction Model

**Features**:
```python
def predict_decision_success(decision: Decision) -> float:
    """Predict likelihood of success based on historical patterns."""

    features = {
        # Decision characteristics:
        "has_alternatives": len(decision.alternatives_considered) > 0,
        "has_success_criteria": len(decision.success_criteria) > 0,
        "confidence_level": decision.confidence_level,
        "decision_time": decision.decision_time_minutes,
        "energy_level": decision.energy_level_when_decided,

        # Historical patterns:
        "similar_decision_success_rate": get_similar_decision_success_rate(decision),
        "tag_cluster_performance": get_tag_cluster_performance(decision.tags),
        "user_track_record": get_user_decision_performance(decision.workspace_id),

        # Context:
        "time_of_day": decision.timestamp.hour,
        "day_of_week": decision.timestamp.weekday(),
        "decisions_today": count_decisions_today(decision.workspace_id),
    }

    # Simple weighted model (can be upgraded to ML later):
    score = (
        0.25 * (1.0 if features["has_alternatives"] else 0.5) +
        0.25 * (1.0 if features["has_success_criteria"] else 0.5) +
        0.20 * features["confidence_level"] +
        0.15 * features["similar_decision_success_rate"] +
        0.15 * features["user_track_record"]
    )

    return score
```

### 2.3 Pattern Learning Pipeline

**Data Flow**:
```
Decision Logged
  ↓
Extract Features (tags, type, timing, confidence)
  ↓
Match Against Historical Patterns
  ↓
Update Pattern Statistics
  ↓
Check for New Emerging Patterns
  ↓
Generate Recommendations
  ↓
Cache for Fast Retrieval
```

**Storage**:
```sql
CREATE TABLE decision_patterns (
    id SERIAL PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_signature JSONB NOT NULL,  -- Defines the pattern
    occurrence_count INT DEFAULT 1,
    success_count INT DEFAULT 0,
    avg_confidence FLOAT,
    avg_decision_time_minutes FLOAT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    recommendations JSONB,  -- Generated recommendations
    confidence FLOAT  -- How confident are we in this pattern?
);

CREATE INDEX idx_patterns_workspace ON decision_patterns(workspace_id);
CREATE INDEX idx_patterns_type ON decision_patterns(pattern_type);
CREATE INDEX idx_patterns_signature ON decision_patterns USING GIN(pattern_signature);
```

---

## 📊 Phase 3: Decision Visualization & Querying

### 3.1 CLI Tools

**Decision List** (`dopemux decisions list`):
```bash
$ dopemux decisions list --recent 10

📋 Recent Decisions (Last 10)

ID  Date       Type          Confidence  Summary
──────────────────────────────────────────────────────────────
145 Oct 16 2pm Architectural 0.85       Use Zen MCP for research
144 Oct 16 1pm Process       0.92       Implement cleanup handlers
143 Oct 15 3pm Technical     0.78       Cache instance detection

Patterns Detected:
• 🎯 High confidence on process decisions (avg 0.90)
• ⏱️  Quick decisions (<20min) recently
• 🔄 3 decisions related to MCP optimization

💡 Tip: Review decision #143 next week (low confidence)
```

**Decision Graph** (`dopemux decisions graph`):
```bash
$ dopemux decisions graph --decision 145

🌳 Decision Genealogy: #145 (Use Zen MCP for research)

                    #140: Evaluate MCP options
                        ↓ builds_upon
                    #142: SuperClaude integration
                        ↓ builds_upon
              ┌─────→ #143: MCP customization ←─────┐
              │         ↓ extends                   │
    #144: Cleanup ← #145: Use Zen MCP      #146: Update commands
    handlers         (YOU ARE HERE)               ↓ implements
              │                                    │
              └──────────────→ #147: Test workflow

Related Patterns:
• Tag cluster: [mcp-integration, empirical-testing] (8 decisions)
• Success rate: 87% for similar decisions
• Avg time: 35 minutes (healthy decision time)
```

**Decision Stats** (`dopemux decisions stats`):
```bash
$ dopemux decisions stats --since "30 days"

📈 Decision Statistics (Last 30 Days)

Total Decisions: 42
├─ Architectural: 12 (29%)
├─ Technical:     18 (43%)
├─ Process:       8  (19%)
└─ ADHD-pattern:  4  (9%)

Confidence Distribution:
High (>0.8):   25 decisions (60%) ████████████
Med (0.5-0.8): 14 decisions (33%) ██████
Low (<0.5):    3 decisions (7%)   ██

Success Metrics:
✅ Implemented: 28/42 (67%)
✅ Validated:   18/28 (64% of implemented)
⚠️  Failed:      2/28 (7%)
⏳ Pending:     14/42 (33%)

ADHD Insights:
• Best decision time: 10:00-12:00 (89% success)
• Worst decision time: 16:00-18:00 (54% success) - energy dip
• Optimal decision time: 25-45 minutes (85% success)
• Quick decisions (<15min): 62% success (risky!)
• Overthought decisions (>90min): 71% success (fatigue factor)

Top Patterns:
1. Database → Caching → Optimization (6 chains, 83% success)
2. MCP evaluation → Integration → Testing (4 chains, 90% success)
3. ADHD optimization → Validation → Iteration (5 chains, 80% success)

🔔 Reminders:
• 3 decisions need review this week
• 2 low-confidence decisions may need revisiting
• 1 decision exceeded review date (90+ days old)
```

**Decision Review** (`dopemux decisions review`):
```bash
$ dopemux decisions review

🔔 Decisions Pending Review (3)

ID  Age  Confidence  Summary                        Action
──────────────────────────────────────────────────────────────────────
128 92d  0.65       Use Redis for session caching   ⚠️  OVERDUE - Review now
135 31d  0.58       Async embedding pipeline        ⏰  Review this week
140 8d   0.72       Evaluate MCP options            ✅  On track

Review Questions:
#128: Did Redis caching improve performance as expected?
      → Check metrics, update outcome_status
      → Consider: Keep, modify, or abandon?

#135: Is async embedding pipeline working well?
      → Any blocking issues?
      → Performance meeting expectations?

Interactive Review Mode:
Would you like to review #128 now? [y/N]
```

### 3.2 Decision Dashboard (TUI)

**Rich Terminal Dashboard**:
```
╭────────────────────────── Decision Dashboard ──────────────────────────╮
│                                                                         │
│  Recent Activity                          Decision Health               │
│  ┌─────────────────────────┐             ┌──────────────────────────┐  │
│  │ 10:15am  #145 logged    │             │ Pending Review:     3    │  │
│  │  9:45am  #144 validated │             │ Low Confidence:     2    │  │
│  │  9:30am  #143 updated   │             │ Overdue Review:     1    │  │
│  └─────────────────────────┘             │ Success Rate:      85%   │  │
│                                           │ Avg Confidence:    0.78  │  │
│  Top Patterns (30d)                       └──────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. MCP Integration (8 decisions, 88% success)        ████████     │ │
│  │ 2. Database Optimization (6 decisions, 83% success)  ███████      │ │
│  │ 3. ADHD Features (5 decisions, 80% success)          ███████      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ADHD Insights                                                          │
│  • 🎯 Best decision time: 10am-12pm (high energy, high success)        │
│  • ⚡ Quick decisions risky: <15min = 62% success                      │
│  • 💡 Optimal time to decide: 25-45 minutes                            │
│  • 🔔 Next review reminder: Tomorrow 10am (#128)                       │
│                                                                         │
│  [L]ist  [G]raph  [S]tats  [R]eview  [Q]uit                           │
╰─────────────────────────────────────────────────────────────────────────╯
```

### 3.3 Decision Query Language

**Flexible Queries**:
```bash
# By confidence:
dopemux decisions query "confidence < 0.6" --review

# By pattern:
dopemux decisions query "tags contains mcp-integration AND type = architectural"

# By outcome:
dopemux decisions query "outcome_status = failed" --lessons

# By age:
dopemux decisions query "age > 90 days AND outcome_status = pending"

# By relationships:
dopemux decisions query "builds_upon #140" --depth 3
```

---

## 🎨 Phase 4: ADHD Dashboard

### 4.1 Real-Time Metrics Dashboard

**Components**:

**Energy Tracker**:
```
Current Energy:  ███████░░░ 70%
Energy History (24h):
  00:00 ████░░░░░░ 40%  (sleep)
  06:00 ████████░░ 80%  (morning peak)
  10:00 █████████░ 90%  (hyperfocus!)
  14:00 ██████░░░░ 60%  (lunch dip)
  18:00 ████░░░░░░ 40%  (evening low)
  NOW → 70% (good for coding, not complex decisions)

Recommendations:
• ✅ Good time for: Implementation, testing, documentation
• ⚠️  Defer: Major architectural decisions, complex refactoring
• 💡 Next peak: Tomorrow 10am (schedule important decisions)
```

**Focus Session Tracker**:
```
Active Session: 📝 ConPort Enhancements
Started: 2:15pm (45 minutes ago)
Breaks Taken: 1/3
Energy Burn Rate: Normal
Estimated Remaining Focus: 30-45 minutes

Productivity:
├─ Decisions logged: 2
├─ Progress entries: 5
├─ Code commits: 1
└─ Interruptions: 0 (great!)

💡 Recommendations:
• Take 5-min break in 15 minutes
• Current session sweet spot: wrap up by 3:45pm
• Next session: 4:00pm (after break)
```

**Attention Metrics**:
```
Attention State: 🎯 Focused
Context Switches (today): 3 (target: <5)
Hyperfocus Events: 1 (2h 15m)
Distraction Recovery Time: 2.3 minutes (good!)

Patterns Detected:
• 🌟 Morning hyperfocus: 9-11am (protect this time!)
• ⚠️  Afternoon scattering: 2-4pm (schedule easy tasks)
• 🔄 Best for context switching: 4-5pm
```

### 4.2 Progress Tracking Dashboard

**Task Overview**:
```
╭──────────────── Progress Dashboard ────────────────╮
│                                                     │
│  Active Tasks (5)                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │ 🔄 ConPort enhancements    [████████░░] 80% │  │
│  │ 🔄 Shell integration       [██████████] 100%│  │
│  │ 📝 Security fixes          [████████░░] 75% │  │
│  │ ⏳ Documentation           [████░░░░░░] 40% │  │
│  │ 🎯 GPT-researcher fix      [██░░░░░░░░] 20% │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Completed Today: 8 tasks ✅                        │
│  Blocked: 1 task ⚠️                                 │
│  Estimated completion: 2 hours (with breaks)        │
│                                                     │
│  Velocity: 6.5 tasks/day (above avg!)               │
│  Streak: 5 days of consistent progress 🔥           │
│                                                     │
╰─────────────────────────────────────────────────────╯
```

### 4.3 Pattern Insights Dashboard

**Learning Insights**:
```
╭──────────────── Your Decision Patterns ────────────────╮
│                                                         │
│  You tend to:                                           │
│  • ✅ Make confident architectural decisions (avg 0.85) │
│  • ⚡ Decide quickly on tooling (<20min avg)           │
│  • 🎯 Follow database→cache→optimize pattern           │
│  • 🔄 Revisit ADHD optimizations regularly (good!)     │
│                                                         │
│  Your sweet spots:                                      │
│  • 🌟 Best time: 10-11am (91% success rate)            │
│  • ⏱️  Optimal duration: 30-40 minutes                  │
│  • ⚡ Peak energy decisions: 88% success               │
│                                                         │
│  Watch out for:                                         │
│  • ⚠️  Late afternoon decisions (62% success)          │
│  • 🏃 Rushed decisions (<15min, 58% success)           │
│  • 😴 Low energy decisions (64% success)               │
│                                                         │
│  Recommendations:                                       │
│  • Schedule complex decisions for morning               │
│  • Take 25-30 minutes minimum for architecture         │
│  • Defer decisions when energy <60%                     │
│  • Review low-confidence decisions weekly               │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

---

## 🔧 Phase 5: Integration & Workflows

### 5.1 Dopemux CLI Integration

**New Commands**:
```bash
# Decision management:
dopemux decisions list [--recent N] [--type TYPE] [--low-confidence]
dopemux decisions show ID
dopemux decisions graph ID [--depth N]
dopemux decisions stats [--since DATE]
dopemux decisions review [--overdue] [--interactive]
dopemux decisions outcome ID --status STATUS --notes "..."

# Pattern exploration:
dopemux patterns list [--type TYPE]
dopemux patterns show PATTERN_ID
dopemux patterns insights [--workspace WORKSPACE]

# Dashboard:
dopemux dashboard [--focus | --energy | --decisions | --progress]
dopemux dashboard watch  # Live updating dashboard

# Quick helpers:
dopemux decide "Should I...?" --get-recommendation
dopemux review-reminder --list
```

### 5.2 Automated Workflows

**Decision Lifecycle Automation**:
```python
# On decision logged:
1. Generate embedding (async)
2. Detect related decisions
3. Check for pattern matches
4. Predict success likelihood
5. Set review reminder
6. Cache for fast retrieval

# Daily cron (via dopemux health?):
1. Check decisions needing review
2. Update pattern statistics
3. Generate daily insights
4. Send review reminders
5. Clean up old drafts

# Weekly analysis:
1. Compute success rates
2. Update ADHD insights
3. Detect new patterns
4. Generate recommendations
5. Export metrics
```

### 5.3 IDE Integration (Future)

**VSCode Extension**:
- Decision timeline in sidebar
- Inline decision annotations
- Quick decision logger
- Pattern suggestions while coding
- Review notifications

**Neovim Plugin**:
- `:DecisionLog` command
- `:DecisionReview` interactive menu
- Telescope integration for searching
- LSP integration for code→decision linking

---

## 🔮 Long-Term Feature Ideas

### Epic 1: AI-Powered Decision Assistant
- **Decision Draft Generator**: AI suggests rationale based on context
- **Alternative Generator**: "Have you considered...?" suggestions
- **Success Criteria Generator**: Auto-suggest measurable criteria
- **Review Question Generator**: "Ask yourself..." prompts

### Epic 2: Team Decision Collaboration
- **Shared Decisions**: Team-wide decision log
- **Decision Reviews**: Peer review workflow
- **Decision Voting**: Team consensus tracking
- **Decision Templates**: Reusable decision formats
- **Decision Notifications**: Slack/Discord integration

### Epic 3: Advanced Pattern Learning
- **ML-Based Prediction**: Train on your decision history
- **Anomaly Detection**: "This decision is unusual for you"
- **Outcome Correlation**: What factors predict success?
- **Temporal Patterns**: Seasonal/cyclical decision trends
- **Cross-Workspace Learning**: Learn from all your projects

### Epic 4: ADHD Super Features
- **Energy Prediction**: "Your energy will be high at 10am tomorrow"
- **Optimal Scheduling**: Auto-schedule decisions for peak times
- **Decision Fatigue Detection**: "You've made 8 decisions today, take a break"
- **Cognitive Load Management**: "This decision cluster is too complex, break it down"
- **Hyperfocus Protection**: "You've been deciding for 90min, step back"

### Epic 5: Decision Export & Reporting
- **Decision Reports**: PDF/Markdown decision summaries
- **Architecture Decision Records**: Auto-generate ADRs
- **Decision Changelog**: What changed and why
- **Decision Analytics**: Grafana dashboards
- **Decision API**: REST API for external tools

### Epic 6: Enhanced Worktree Tools
- **Smart Worktree Naming**: AI suggests branch names from decisions
- **Auto-Cleanup Scheduling**: "Delete worktrees older than 30 days"
- **Worktree Templates**: Pre-configured setups
- **Branch Protection**: Prevent work on main even harder
- **Worktree Analytics**: Which worktrees are most productive?

### Epic 7: Intelligent Context Switching
- **Context Snapshots**: Save full mental model per worktree
- **Quick Resume**: "Pick up where you left off in 0.5s"
- **Context Diff**: "What changed since you were here?"
- **Related Context**: "You were also working on X in ui-build"
- **Focus Mode**: Block interruptions during deep work

### Epic 8: Multi-User ADHD Platform
- **Team ADHD Profiles**: Coordinate energy levels
- **Pair Programming Matching**: Match complementary ADHD patterns
- **Shared Focus Sessions**: Team pomodoros
- **Interrupt Coordination**: "Alice is in hyperfocus, wait 30min"
- **Knowledge Sharing**: Best practices across team

---

## 🗺️ Implementation Roadmap

### Sprint 1: Enhanced Decision Model (1 week)
- [ ] Add new fields to Decision model
- [ ] Database migration script
- [ ] Update handlers for new fields
- [ ] Test backward compatibility
- [ ] Update MCP tool schemas

### Sprint 2: Basic Visualization (1 week)
- [ ] Implement `dopemux decisions list`
- [ ] Implement `dopemux decisions show`
- [ ] Add filtering and sorting
- [ ] Rich terminal formatting
- [ ] Test with real data

### Sprint 3: Pattern Detection (2 weeks)
- [ ] Create decision_patterns table
- [ ] Implement tag clustering
- [ ] Implement timing analysis
- [ ] Implement success prediction
- [ ] Pattern storage and retrieval

### Sprint 4: Decision Graph (1 week)
- [ ] Implement decision relationships
- [ ] Build graph visualization
- [ ] Add genealogy queries
- [ ] Interactive graph navigation
- [ ] Export graph as SVG/PNG

### Sprint 5: ADHD Dashboard Alpha (2 weeks)
- [ ] Energy tracking system
- [ ] Focus session timer
- [ ] Attention metrics
- [ ] Basic TUI dashboard
- [ ] Integration with ConPort

### Sprint 6: Review System (1 week)
- [ ] Review reminder system
- [ ] Interactive review workflow
- [ ] Outcome tracking
- [ ] Lessons learned capture
- [ ] Review analytics

### Sprint 7: Advanced Features (4 weeks)
- [ ] Decision stats command
- [ ] Pattern insights
- [ ] Success prediction
- [ ] AI decision drafting
- [ ] Full dashboard polish

---

## 📊 Technical Architecture

### Database Schema Extensions

```sql
-- Enhanced decisions table:
ALTER TABLE decisions ADD COLUMN decision_type TEXT;
ALTER TABLE decisions ADD COLUMN confidence_level FLOAT;
ALTER TABLE decisions ADD COLUMN impact_score FLOAT;
ALTER TABLE decisions ADD COLUMN reversibility TEXT;
ALTER TABLE decisions ADD COLUMN alternatives_considered JSONB;
ALTER TABLE decisions ADD COLUMN success_criteria JSONB;
ALTER TABLE decisions ADD COLUMN review_date TIMESTAMPTZ;
ALTER TABLE decisions ADD COLUMN outcome_status TEXT;
ALTER TABLE decisions ADD COLUMN outcome_notes TEXT;
ALTER TABLE decisions ADD COLUMN outcome_date TIMESTAMPTZ;
ALTER TABLE decisions ADD COLUMN lessons_learned JSONB;
ALTER TABLE decisions ADD COLUMN cognitive_load FLOAT;
ALTER TABLE decisions ADD COLUMN decision_time_minutes FLOAT;
ALTER TABLE decisions ADD COLUMN energy_level TEXT;
ALTER TABLE decisions ADD COLUMN requires_followup BOOLEAN DEFAULT FALSE;

-- Decision relationships (graph):
CREATE TABLE decision_relationships (
    id SERIAL PRIMARY KEY,
    source_decision_id INT REFERENCES decisions(id) ON DELETE CASCADE,
    target_decision_id INT REFERENCES decisions(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_decision_id, target_decision_id, relationship_type)
);

-- Pattern learning:
CREATE TABLE decision_patterns (
    id SERIAL PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_signature JSONB NOT NULL,
    occurrence_count INT DEFAULT 1,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    avg_confidence FLOAT,
    avg_decision_time_minutes FLOAT,
    avg_implementation_time_days FLOAT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    recommendations JSONB,
    pattern_confidence FLOAT,
    adhd_insights JSONB
);

-- ADHD metrics:
CREATE TABLE adhd_metrics (
    id SERIAL PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    user_session_id TEXT,
    metric_type TEXT NOT NULL,  -- 'energy', 'focus', 'attention'
    value FLOAT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    context JSONB  -- What was happening
);

-- Review reminders:
CREATE TABLE review_reminders (
    id SERIAL PRIMARY KEY,
    decision_id INT REFERENCES decisions(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMPTZ NOT NULL,
    reminder_type TEXT,  -- 'implementation', 'outcome', 'periodic'
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ
);
```

### API Extensions

**New MCP Tools**:
```python
# Decision enhancements:
mcp__conport__log_decision_enhanced(
    summary, rationale, implementation_details,
    decision_type, confidence_level, alternatives, success_criteria,
    review_date, cognitive_load, energy_level
)

mcp__conport__update_decision_outcome(
    decision_id, outcome_status, outcome_notes, lessons_learned
)

mcp__conport__relate_decisions(
    source_id, target_id, relationship_type, notes
)

# Pattern learning:
mcp__conport__detect_patterns(workspace_id, pattern_type, since_date)
mcp__conport__get_pattern_insights(workspace_id, pattern_id)
mcp__conport__predict_decision_success(decision_draft)

# Reviews:
mcp__conport__get_pending_reviews(workspace_id, overdue_only)
mcp__conport__complete_review(decision_id, review_notes)
mcp__conport__schedule_review(decision_id, review_date, reminder_type)

# ADHD metrics:
mcp__conport__log_energy_level(workspace_id, energy_level, context)
mcp__conport__start_focus_session(workspace_id, task_description)
mcp__conport__end_focus_session(session_id, completed, notes)
mcp__conport__get_adhd_insights(workspace_id, metric_type, timeframe)
```

---

## 🎯 Quick Wins (Can Implement Today)

### 1. Decision Review Command (2 hours)
```bash
dopemux decisions review --overdue
```
- Query decisions >30 days old with outcome_status=pending
- Interactive prompts for updating outcome
- Simple but immediately useful

### 2. Decision Stats (3 hours)
```bash
dopemux decisions stats
```
- Count by type, confidence, outcome
- Basic charts with Rich library
- Pattern detection starter

### 3. Energy Logging (2 hours)
```bash
dopemux energy log [high|medium|low]
dopemux energy status
```
- Simple energy tracking
- Time-series visualization
- Foundation for ADHD dashboard

---

## 📚 Documentation Needs

1. **CONPORT_ENHANCEMENT_GUIDE.md** - User guide for new features
2. **DECISION_TRACKING_BEST_PRACTICES.md** - How to use effectively
3. **PATTERN_LEARNING_EXPLAINED.md** - How patterns work
4. **ADHD_DASHBOARD_MANUAL.md** - Dashboard features
5. **API_REFERENCE_ENHANCED.md** - New MCP tools

---

## 🎓 Success Criteria

### Phase 1 Success:
- ✅ Can track decision outcomes
- ✅ Can query decisions by multiple criteria
- ✅ Decision graphs show relationships
- ✅ Review reminders work

### Phase 2 Success:
- ✅ Patterns auto-detected from history
- ✅ Success prediction >70% accurate
- ✅ ADHD insights actionable
- ✅ CLI tools intuitive and fast

### Full Success:
- ✅ Decisions inform future decisions
- ✅ Pattern learning reduces cognitive load
- ✅ ADHD metrics improve workflow
- ✅ Users report less decision fatigue

---

**Next Steps**: Clear conversation, implement Phase 1 Quick Wins
**Estimated Time**: 6-8 hours for core features
**ADHD Impact**: High - directly addresses decision fatigue and context management
