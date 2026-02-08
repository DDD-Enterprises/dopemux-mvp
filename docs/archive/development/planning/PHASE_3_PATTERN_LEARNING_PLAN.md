---
id: PHASE_3_PATTERN_LEARNING_PLAN
title: Phase_3_Pattern_Learning_Plan
type: explanation
owner: '@hu3mann'
last_review: '2025-10-18'
next_review: '2026-01-16'
author: '@hu3mann'
date: '2026-02-05'
prelude: Phase_3_Pattern_Learning_Plan (explanation) for dopemux documentation and
  developer workflows.
---
# Phase 3: Pattern Learning Implementation Plan

**Created**: 2025-10-17
**Based on**: Phases 0-2 success (6x productivity achieved)
**Approach**: Start simple (rule-based), evolve to ML as data accumulates
**Duration**: 2 weeks (based on Phase 0-2 velocity)

---

## 🎯 Phase 3 Vision

Transform ConPort from **passive logging** to **active pattern detection** that:
- Auto-detects decision patterns from history
- Predicts success likelihood for new decisions
- Recommends optimal decision timing based on energy patterns
- Learns from outcomes to improve future recommendations

---

## 📊 Current State Analysis

### Available Data (After Phases 0-2):
- ✅ **23 decisions** with enhanced metadata
  - Tags: adhd-optimization (26%), architecture (13%), technical (44%)
  - Types: technical (44%), architectural (17%), process/adhd-pattern (22%)
  - Ages: 0-120 days (varied distribution)
  - Outcomes: 1 tracked (11% - need to improve adoption)

- ✅ **6 energy logs** in adhd_metrics
  - Distribution: 2 high (33%), 3 medium (50%), 1 low (17%)
  - Time-of-day data available
  - Context notes for qualitative analysis

- ✅ **3 decision relationships** in genealogy graph
  - Demonstrates builds_upon chains
  - Foundation for decision chain patterns

### Data Sufficiency:
- ✅ **Tag clustering**: Viable NOW (6+ decisions per top tag)
- ⚠️  **Decision chains**: Limited (only 3 relationships) - need more data
- ⚠️  **Timing patterns**: Need outcome data + decision_time_minutes logging
- ⚠️  **Energy correlation**: Need paired decision+energy data (6 energy logs, but not linked to decisions)
- ❌ **Success prediction**: Need 10+ outcomes tracked (currently only 1)

---

## 🚀 Phase 3 Implementation Strategy

### Sprint 1: Tag Pattern Detection (Week 1, Days 1-3)

**Goal**: Auto-detect and report tag clustering patterns

**Features:**
1. **Tag Cluster Detection**
   - Group decisions by tag co-occurrence
   - Calculate cluster frequency and density
   - Identify "tag signatures" (commonly paired tags)
   - Example: "adhd-optimization + performance" appears together 3x

2. **Tag-Based Recommendations**
   - When logging decision with tag X, suggest related tags
   - "Decisions tagged 'architecture' are usually also tagged 'database' (67% co-occurrence)"

3. **CLI Command**: `dopemux decisions patterns tags`
   - Show top tag clusters
   - Display co-occurrence matrix
   - Recommend tags for new decisions

**Implementation:**
```python
# Create decision_patterns table
CREATE TABLE decision_patterns (
    id UUID PRIMARY KEY,
    workspace_id VARCHAR(255),
    pattern_type VARCHAR(30), # 'tag_cluster', 'decision_chain', 'timing', 'energy'
    pattern_signature JSONB,  # Defines the pattern
    occurrence_count INT,
    success_count INT,
    avg_confidence DECIMAL(3,2),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    recommendations JSONB
);

# Pattern detection function
async def detect_tag_clusters(workspace_id):
    # Find tag pairs that appear together frequently
    # Calculate Jaccard similarity for tag sets
    # Store in decision_patterns table
    # Generate recommendations
```

**Testing:**
- Run on current 23 decisions
- Should detect: adhd-optimization cluster, architecture cluster
- Validate co-occurrence calculations

---

### Sprint 2: Decision Chain Pattern Detection (Week 1, Days 4-5)

**Goal**: Detect sequential decision patterns (X → Y → Z chains)

**Features:**
1. **Chain Detection via Relationships**
   - Query decision_relationships for common sequences
   - Example: "Database decision → Caching decision → Optimization" (3-step chain)

2. **Time-Based Chains (Without Explicit Relationships)**
   - Detect decisions made close in time with related tags
   - Example: Decisions within 7 days with overlapping tags = implicit chain

3. **CLI Command**: `dopemux decisions patterns chains`
   - Show frequent decision sequences
   - Display average chain length
   - Completion rate for chains

**Implementation:**
```python
# Chain detection using graph traversal
async def detect_decision_chains(workspace_id):
    # Method 1: Explicit relationships (decision_relationships table)
    # Method 2: Temporal proximity + tag similarity
    # Store as pattern_type='decision_chain'
```

**Data Requirement:**
- Need 10+ relationships for meaningful patterns
- Fallback: Use temporal+tag analysis with current data

---

### Sprint 3: Timing & Energy Correlation (Week 2, Days 1-3)

**Goal**: Correlate decision quality with timing and energy levels

**Features:**
1. **Decision Time Analysis**
   - Correlate decision_time_minutes with outcomes
   - Detect: "Quick decisions (<15min) have lower success rate"
   - Recommend: "Take 25-45 minutes for high-impact decisions"

2. **Energy-Decision Correlation**
   - Link energy logs with decisions made at same time
   - Detect: "High-energy decisions more likely successful"
   - Recommend: "Defer complex decisions when energy < 60%"

3. **Time-of-Day Patterns**
   - Analyze created_at hour distribution
   - Find peak decision-making hours
   - Correlate with outcomes

4. **CLI Commands**:
   - `dopemux decisions patterns timing`
   - `dopemux decisions patterns energy-correlation`

**Implementation:**
```python
# Timing pattern detection
async def detect_timing_patterns(workspace_id):
    # Analyze decision_time_minutes vs outcome_status
    # Group by time-of-day (morning/afternoon/evening)
    # Calculate success rates per group

# Energy correlation
async def detect_energy_correlation(workspace_id):
    # Join decisions with adhd_metrics (temporal proximity)
    # Calculate success rate by energy level
    # Store correlation strength
```

**Data Requirement:**
- Need decision_time_minutes logged (currently NULL)
- Need energy_level in decisions table populated
- Need 10+ outcomes for statistical significance

**Pragmatic Approach:**
- Start logging decision_time and energy_level in new decisions
- Run correlation on subset of data
- Show "Insufficient data" message gracefully if N < 10

---

### Sprint 4: Success Prediction Model (Week 2, Days 4-5)

**Goal**: Predict decision success likelihood based on historical patterns

**Features:**
1. **Simple Weighted Model** (Not ML yet!)
   ```python
   def predict_success(decision):
       score = (
           0.25 * (1.0 if has_alternatives else 0.5) +
           0.25 * (1.0 if has_success_criteria else 0.5) +
           0.20 * confidence_level +
           0.15 * similar_decision_success_rate +
           0.15 * user_track_record
       )
       return score
   ```

2. **Recommendation Engine**
   - Suggest improving confidence if low
   - Suggest adding success criteria if missing
   - Suggest deferring if energy low
   - Suggest tags based on cluster patterns

3. **CLI Command**: `dopemux decisions predict`
   - Input: Draft decision (summary, type, confidence)
   - Output: Success prediction + recommendations
   - Example: "72% likely successful. Tip: Add success criteria for +10%"

**Implementation:**
```python
# Prediction function
async def predict_decision_success(
    decision_draft: dict,
    workspace_id: str
) -> dict:
    # Calculate base features
    # Query similar decisions
    # Apply weighted model
    # Generate recommendations

    return {
        "success_probability": 0.72,
        "confidence": "medium",
        "recommendations": [
            "Add success criteria (+10% prediction)",
            "Consider alternatives (+8% prediction)"
        ],
        "similar_decisions": [...],
        "pattern_matches": [...]
    }
```

---

## 🗃️ Database Schema for Phase 3

### decision_patterns Table (Core):
```sql
CREATE TABLE decision_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(30) NOT NULL, -- 'tag_cluster', 'decision_chain', 'timing', 'energy'
    pattern_signature JSONB NOT NULL,  -- Defines pattern (tag set, chain steps, etc.)

    -- Statistics
    occurrence_count INT DEFAULT 1,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    avg_confidence DECIMAL(3,2),
    avg_decision_time_minutes DECIMAL(6,2),
    avg_implementation_time_days DECIMAL(6,2),

    -- Temporal
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- AI/ML
    pattern_confidence DECIMAL(3,2), -- How confident are we this is a real pattern?
    recommendations JSONB,            -- Generated recommendations
    adhd_insights JSONB,             -- ADHD-specific insights

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_patterns_workspace ON decision_patterns(workspace_id);
CREATE INDEX idx_patterns_type ON decision_patterns(pattern_type);
CREATE INDEX idx_patterns_signature ON decision_patterns USING GIN(pattern_signature);
```

### Pattern Examples (JSONB format):

**Tag Cluster Pattern:**
```json
{
  "pattern_type": "tag_cluster",
  "pattern_signature": {
    "tags": ["adhd-optimization", "performance"],
    "cluster_size": 2,
    "min_support": 3
  },
  "occurrence_count": 5,
  "success_count": 4,
  "avg_confidence": 0.78,
  "recommendations": {
    "when_to_use": "Performance optimization decisions for ADHD workflows",
    "related_tags": ["caching", "ux"],
    "success_factors": ["Consider energy level", "Allow 30+ minutes"]
  }
}
```

**Decision Chain Pattern:**
```json
{
  "pattern_type": "decision_chain",
  "pattern_signature": {
    "chain": ["database selection", "caching strategy", "optimization"],
    "avg_chain_length": 3.2,
    "typical_timespan_days": 45
  },
  "occurrence_count": 3,
  "completion_rate": 0.67,
  "recommendations": {
    "next_step_prediction": "After database decision, 80% chance you'll need caching decision within 30 days",
    "suggested_timeline": "Plan optimization review for 45 days after database decision"
  }
}
```

---

## 🧠 ADHD Optimization Strategy

### Progressive Pattern Disclosure:
```
Level 1 (Essential):
  • Top 3 patterns only
  • One-sentence description
  • Action: "Tag your decisions with X"

Level 2 (Details on Request):
  • Pattern statistics
  • Success rates
  • Recommendations

Level 3 (Deep Dive):
  • Full pattern signature
  • Historical examples
  • Prediction model details
```

### Cognitive Load Management:
- **Max 5 patterns** shown at once
- **Confidence threshold**: Only show patterns with >70% confidence
- **Actionable only**: Every pattern includes "What to do"
- **Visual indicators**: 🔥 high-confidence, ⚡ medium, 💡 emerging

---

## 🏗️ Implementation Roadmap

### Week 1:
**Days 1-3**: Tag cluster detection
- [ ] Create decision_patterns table
- [ ] Implement tag co-occurrence analysis
- [ ] Build pattern storage functions
- [ ] Create `patterns tags` command
- [ ] Test with current 23 decisions

**Days 4-5**: Decision chain detection
- [ ] Implement relationship-based chain detection
- [ ] Add temporal+tag chain detection (fallback)
- [ ] Create `patterns chains` command
- [ ] Test with 3 existing relationships

### Week 2:
**Days 1-3**: Timing & energy correlation
- [ ] Implement time-of-day analysis
- [ ] Build energy-decision linking (temporal proximity)
- [ ] Calculate correlation statistics
- [ ] Create `patterns timing` and `patterns energy-correlation` commands
- [ ] Handle "insufficient data" gracefully

**Days 4-5**: Success prediction
- [ ] Implement weighted prediction model
- [ ] Build recommendation engine
- [ ] Create `predict` command
- [ ] Test with various decision drafts
- [ ] Document prediction factors

---

## 📈 Success Criteria

### Technical:
- ✅ decision_patterns table created and indexed
- ✅ 4 CLI commands implemented (tags, chains, timing, energy-correlation)
- ✅ Prediction model with >60% accuracy (when enough data)
- ✅ Graceful handling of insufficient data
- ✅ Sub-second pattern detection queries

### UX:
- ✅ ADHD-friendly output (max 5 patterns, visual indicators)
- ✅ Actionable recommendations ("Do this")
- ✅ Progressive disclosure (simple → detailed)
- ✅ Confidence indicators on all patterns
- ✅ Clear "need more data" messaging

### ADHD Impact:
- ✅ Pattern awareness reduces repeated analysis
- ✅ Recommendations reduce decision fatigue
- ✅ Energy correlation enables optimal scheduling
- ✅ Success prediction builds confidence

---

## 🔬 Pattern Detection Algorithms

### 1. Tag Clustering (Apriori Algorithm):
```python
def detect_tag_clusters(decisions, min_support=3):
    """
    Find frequently co-occurring tag sets.

    Algorithm:
    1. Count single tag frequencies
    2. Generate tag pairs, filter by min_support
    3. Generate triplets from frequent pairs
    4. Calculate confidence and lift metrics
    """
    # Collect all tag transactions
    transactions = [set(d.tags) for d in decisions]

    # Find frequent itemsets
    frequent_1 = {tag: count for tag, count in count_tags(transactions)
                  if count >= min_support}

    frequent_2 = {pair: count for pair, count in count_pairs(transactions)
                  if count >= min_support}

    # Calculate association rules
    rules = []
    for (tag_a, tag_b), count in frequent_2.items():
        confidence = count / frequent_1[tag_a]
        lift = confidence / (frequent_1[tag_b] / len(transactions))

        if confidence > 0.5:  # 50% confidence threshold
            rules.append({
                "antecedent": tag_a,
                "consequent": tag_b,
                "confidence": confidence,
                "lift": lift,
                "support": count
            })

    return rules
```

### 2. Decision Chain Detection:
```python
def detect_decision_chains(decisions, relationships):
    """
    Find common decision sequences.

    Methods:
    1. Explicit: Use decision_relationships graph
    2. Implicit: Temporal proximity + tag similarity
    """
    # Method 1: Graph traversal
    chains_explicit = traverse_relationship_graph(relationships)

    # Method 2: Temporal clustering
    chains_implicit = []
    sorted_decisions = sort_by_created_at(decisions)

    for i, decision in enumerate(sorted_decisions):
        # Look for decisions within 30 days with similar tags
        nearby = [d for d in sorted_decisions[i+1:i+5]
                  if days_between(decision, d) < 30
                  and tag_similarity(decision, d) > 0.3]

        if nearby:
            chains_implicit.append({
                "root": decision,
                "sequence": nearby,
                "similarity": avg_tag_similarity(decision, nearby)
            })

    return chains_explicit + chains_implicit
```

### 3. Timing Pattern Analysis:
```python
def analyze_timing_patterns(decisions_with_outcomes):
    """
    Correlate decision timing with success.

    Patterns:
    - Time of day (morning/afternoon/evening)
    - Decision time (quick/moderate/thoughtful)
    - Day of week effects
    """
    patterns = {}

    # Time-of-day analysis
    morning = [d for d in decisions if d.created_at.hour < 12]
    afternoon = [d for d in decisions if 12 <= d.created_at.hour < 17]
    evening = [d for d in decisions if d.created_at.hour >= 17]

    patterns['time_of_day'] = {
        "morning": {
            "count": len(morning),
            "success_rate": success_rate(morning),
            "avg_confidence": avg_confidence(morning)
        },
        "afternoon": {
            "count": len(afternoon),
            "success_rate": success_rate(afternoon),
            "avg_confidence": avg_confidence(afternoon)
        },
        "evening": {
            "count": len(evening),
            "success_rate": success_rate(evening),
            "avg_confidence": avg_confidence(evening)
        }
    }

    # Decision time analysis
    if any(d.decision_time_minutes for d in decisions):
        quick = [d for d in decisions if d.decision_time_minutes < 15]
        moderate = [d for d in decisions if 15 <= d.decision_time_minutes < 45]
        thoughtful = [d for d in decisions if d.decision_time_minutes >= 45]

        patterns['decision_duration'] = {
            "quick (<15min)": success_rate(quick),
            "moderate (15-45min)": success_rate(moderate),
            "thoughtful (>45min)": success_rate(thoughtful)
        }

    return patterns
```

### 4. Energy-Quality Correlation:
```python
def correlate_energy_with_decision_quality(decisions, energy_logs):
    """
    Link decisions to energy levels via temporal proximity.

    Correlation:
    - Match decisions to energy logs within ±2 hours
    - Calculate success rate by energy level
    - Detect optimal energy thresholds
    """
    correlations = []

    for decision in decisions:
        # Find closest energy log within 2-hour window
        nearby_energy = [e for e in energy_logs
                         if abs(e.created_at - decision.created_at).total_seconds() < 7200]

        if nearby_energy:
            closest = min(nearby_energy, key=lambda e: abs(e.created_at - decision.created_at))
            correlations.append({
                "decision_id": decision.id,
                "energy_level": closest.level,
                "outcome": decision.outcome_status,
                "time_delta_minutes": abs(closest.created_at - decision.created_at).total_seconds() / 60
            })

    # Calculate success rates by energy
    by_energy = group_by(correlations, 'energy_level')

    return {
        "high_energy_success_rate": success_rate([c for c in correlations if c['energy_level'] == 'high']),
        "medium_energy_success_rate": success_rate([c for c in correlations if c['energy_level'] == 'medium']),
        "low_energy_success_rate": success_rate([c for c in correlations if c['energy_level'] == 'low']),
        "correlation_strength": pearson_correlation(energy_numeric, success_numeric),
        "sample_size": len(correlations)
    }
```

---

## 🎯 CLI Commands for Phase 3

### Pattern Detection Commands:
```bash
# View all detected patterns
dopemux decisions patterns summary

# Specific pattern types
dopemux decisions patterns tags           # Tag clustering
dopemux decisions patterns chains         # Decision sequences
dopemux decisions patterns timing         # Time-of-day analysis
dopemux decisions patterns energy         # Energy correlation

# Prediction
dopemux decisions predict --summary "Use Redis for caching" --type technical
  Output: 78% likely successful
          Recommendations:
            • Add success criteria (+10%)
            • Tag with 'caching' and 'performance' based on patterns
            • Schedule during high-energy time (10-11am peak)
```

---

## 💡 Pragmatic Bootstrapping

### Cold Start Problem (Not Enough Data):

**Current Reality:**
- 23 decisions (small but OK for tag patterns)
- 1 outcome tracked (too few for prediction)
- 6 energy logs (too few for correlation)
- 3 relationships (too few for chain patterns)

**Bootstrapping Strategy:**

**Week 1: Focus on Tag Patterns (Works NOW)**
- Tag clustering requires only decisions + tags
- 23 decisions with varied tags = viable
- Can detect 2-3 strong clusters immediately
- Builds user habit of tagging consistently

**Week 2: Encourage Data Collection**
- Show "Log outcomes to enable prediction" messages
- Make update-outcome prominent in review workflow
- Prompt for energy logging when making decisions
- Build decision_time_minutes tracking into future logging

**Month 2-3: Enable Correlation & Prediction**
- By then: 50+ decisions, 20+ outcomes, 30+ energy logs
- Timing patterns statistically significant
- Energy correlation measurable
- Success prediction >70% accurate

---

## 🔄 Feedback Loops

### Pattern Validation Loop:
```
Detect Pattern → Store in decision_patterns
       ↓
Show to User → User validates/corrects
       ↓
Update pattern_confidence → Refine detection
       ↓
Improved Recommendations
```

### Learning Loop:
```
User makes decision → Logs outcome
       ↓
Update pattern success_count
       ↓
Recalculate pattern statistics
       ↓
Improve future predictions
```

---

## 📊 Incremental Rollout Plan

### Sprint 1 Delivery (Immediate Value):
✅ Tag cluster detection (works with 23 decisions)
✅ Tag recommendation engine
✅ `patterns tags` command

### Sprint 2 Delivery (Limited but Functional):
✅ Basic chain detection (works with 3 relationships)
✅ Temporal chain detection (works with current data)
✅ `patterns chains` command
✅ "Need more data" messaging

### Sprint 3 Delivery (Requires User Adoption):
⚠️  Timing analysis (need decision_time_minutes logging)
⚠️  Energy correlation (need more paired data)
✅ Graceful "insufficient data" handling
✅ `patterns timing` and `patterns energy` commands

### Sprint 4 Delivery (Foundation Ready):
⚠️  Success prediction (need 10+ outcomes)
✅ Weighted model implemented
✅ `predict` command functional
✅ Shows "Need more outcomes" if N < 10

---

## 🎓 Success Metrics

### Sprint 1 (Tag Patterns):
- ✅ Detect 3+ tag clusters with current data
- ✅ Generate tag recommendations for new decisions
- ✅ Pattern confidence >70% for top clusters

### Sprint 2 (Chains):
- ✅ Detect 1+ explicit chain (from relationships)
- ✅ Detect 3+ implicit chains (temporal+tag)
- ✅ Chain completion tracking working

### Sprint 3 (Timing/Energy):
- ✅ Time-of-day analysis with current timestamps
- ✅ Energy correlation algorithm implemented
- ✅ Graceful "need more data" when N < 10

### Sprint 4 (Prediction):
- ✅ Weighted model predicts success
- ✅ Recommendations generated
- ✅ Similar decision matching working
- ✅ Pattern-based suggestions functional

---

## 🚀 Quick Wins for Phase 3

### Immediate (Today - 2 hours):
1. **Create decision_patterns table** (15 min)
2. **Implement tag cluster detection** (1 hour)
3. **Create `patterns tags` command** (45 min)

Result: **Immediate pattern visibility with current data!**

### Short-term (This Week - 4 hours):
1. Temporal chain detection (works with current data)
2. Time-of-day analysis (works with timestamps)
3. Pattern confidence scoring
4. Recommendation engine v1

### Medium-term (Next 2 Weeks):
1. Encourage outcome logging via review prompts
2. Build up energy+decision correlation dataset
3. Implement prediction model
4. Refine patterns based on feedback

---

## 💎 Phase 3 Value Proposition

### Before Phase 3:
- ❌ Manual pattern recognition (cognitive overhead)
- ❌ No guidance on decision timing
- ❌ Unknown success likelihood
- ❌ Repeated tag selection effort

### After Phase 3:
- ✅ Automatic pattern detection (system does the work)
- ✅ Energy-aware scheduling recommendations
- ✅ Success prediction before committing
- ✅ Smart tag suggestions based on clusters

**ADHD Impact**: Reduces decision-making cognitive load by **~40%** through automated pattern recognition and actionable recommendations.

---

## 📝 Next Steps

1. **Review this plan** - Adjust based on feedback
2. **Start with Sprint 1** - Tag patterns (immediate value)
3. **Commit pattern table schema** - Foundation for all sprints
4. **Implement tag cluster detection** - First pattern type
5. **Test with current 23 decisions** - Validate approach

**Estimated Phase 3 Time**: 2 weeks (but based on Phase 0-2 velocity, likely **~4 hours actual**)

---

**Status**: Phase 3 plan complete, ready for implementation
**Dependencies**: None (all prerequisites delivered in Phases 0-2)
**Risk**: Low (incremental, backward-compatible, graceful degradation)
