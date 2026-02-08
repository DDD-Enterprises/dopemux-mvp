---
id: f6-completion
title: F6 Completion
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: F6 Completion (explanation) for dopemux documentation and developer workflows.
---
# F6: Abandonment Tracking - Implementation Complete

**Feature**: F6 - Abandonment Tracking (Phase 2 Analytics)
**Status**: ✅ Complete
**Date**: 2025-10-04
**Implementation Time**: ~3 hours (estimated from planning + implementation)
**Test Coverage**: 19/19 tests passing (100%)

## Overview

F6 adds temporal analysis to detect uncommitted work that's been idle for extended periods. It provides ADHD-friendly, guilt-free reminders to finish or archive abandoned work, with intelligent action suggestions based on work characteristics.

## Implementation Summary

### Files Created (2)
1. **services/serena/v2/abandonment_tracker.py** (265 lines)
   - AbandonmentTracker class: Time-based abandonment scoring
   - calculate_abandonment_score(): Score = days_idle / 14 (capped at 1.0)
   - classify_severity(): Maps scores to none/stale/likely/definitely
   - generate_message(): GUILT-FREE messaging with emoji indicators
   - suggest_action(): Recommends commit/archive/delete based on context
   - get_abandonment_summary(): Statistics across all abandoned work

2. **tests/serena/v2/test_abandonment_tracker_f6.py** (370 lines)
   - 19 comprehensive tests (100% passing)
   - Score calculation testing: 7-day, 14-day, 28-day scenarios
   - Severity classification testing: All 4 levels validated
   - Messaging testing: ADHD-friendly, guilt-free validation
   - Action suggestion testing: Commit/archive/delete logic
   - Integration testing: Full workflow validation
   - Statistics testing: Summary generation

### Files Modified (2)
1. **services/serena/v2/untracked_work_detector.py** (+4 lines)
   - Import AbandonmentTracker
   - Initialize abandonment_tracker in **init**
   - Calculate abandonment score in detect() (Step 3.75)
   - Add abandonment_data to detection result

2. **services/serena/v2/mcp_server.py** (+309 lines)
   - Added get_abandoned_work_tool (100 lines)
   - Added mark_abandoned_tool (67 lines)
   - Added get_abandonment_stats_tool (73 lines)
   - Tool registrations (3 tools)
   - Dispatcher routing (3 routes)

## Technical Decisions

### Time-Based Scoring: 7-14 Day Window
**Decision**: Score = days_idle / 14, considered abandoned at 7+ days (score ≥ 0.5)
**Rationale**:
- 7 days exceeds typical ADHD context-switching patterns (2-3 days)
- 14-day normalization reaches 1.0 at two-week mark (sprint boundary)
- Balances recency bias with genuine abandonment detection

**Implementation**:
- Capped at 1.0 to prevent over-penalization of very old work
- Uses git_detector.py first_change_time as authoritative source
- No negative impact on confidence_score (additive context only)

### Severity Classification: Four Levels
**Decision**: none (<0.3), stale (0.3-0.5), likely (0.5-0.7), definitely (0.7+)
**Rationale**:
- Progressive escalation from gentle nudge to clear action needed
- Matches ADHD working memory patterns (4-7 days = getting stale)
- Provides actionable distinctions without overwhelming user

**Implementation**:
- Emoji indicators: ⚪ none, 🟡 stale, 🟠 likely, 🔴 definitely
- Messaging intensity scales with severity
- Action urgency maps to severity level

### GUILT-FREE Messaging: Supportive Language
**Decision**: No blame, shame, or penalty language - only supportive choices
**Rationale**:
- ADHD-specific: Shame triggers paralysis, not action
- Framing as choices ("finish or archive?") empowers decision-making
- Emoji indicators provide visual cues without emotional weight

**Implementation**:
- Message templates use "might want to", "time to decide", "want to finish?"
- No words: abandoned, forgot, ignored, neglected (except in technical classification)
- Positive framing: "completing old work builds momentum"

### Action Suggestion Engine: Context-Aware Recommendations
**Decision**: Suggest commit/archive/delete based on file count, severity, and work type
**Rationale**:
- File count indicates intentionality (8 files = real work, 2 files = experiment)
- New files suggest deliberate feature work worth committing
- Severity + context determines urgency level

**Implementation**:
```python
if severity == "definitely_abandoned":
    if file_count > 5:
        return {"action": "commit", "urgency": "high"}  # Substantial work
    else:
        return {"action": "archive", "urgency": "medium"}  # Small experiment

if stats.get("new", 0) > 0:
    return {"action": "commit", "rationale": "new files = intentional work"}
```

### No Negative Confidence Penalty
**Decision**: Abandonment score is additive context, not confidence reducer
**Rationale**:
- Prevents false negatives (old but important work still detected)
- Abandonment provides temporal dimension, not replacement signal
- Allows user to decide whether age matters for their workflow

**Implementation**:
- abandonment_data added to detection result alongside confidence_score
- Tools expose abandonment separately for optional action
- Pattern learning can observe abandonment patterns without forcing penalty

### ADHD Optimizations: Max 10 Results, Visual Progress
**Decision**: Limit get_abandoned_work to 10 results, sort by severity
**Rationale**:
- Matches F1-F5 ADHD limits (prevents overwhelm)
- Severity sorting surfaces most urgent work first
- Forces prioritization over exhaustive lists

**Implementation**:
- `limit = min(limit, 10)` in get_abandoned_work_tool
- Sorted descending by days_idle (oldest first)
- Statistics tool provides overview without listing all items

## Performance Results

### Test Execution
- **Total Tests**: 19
- **Pass Rate**: 100%
- **Execution Time**: 0.15s (150ms)
- **Coverage**: Score (4 tests), Severity (4 tests), Messaging (4 tests), Actions (3 tests), Integration (2 tests), Statistics (2 tests)

### Time-Based Scoring Accuracy
- **7-day score**: 0.5 (exactly at abandonment threshold) ✅
- **14-day score**: 1.0 (reaches maximum) ✅
- **28-day capping**: 1.0 (not 2.0, prevents over-penalization) ✅
- **No time data**: 0.0 with "none" severity (graceful handling) ✅

### Severity Classification Precision
- **none range**: 0.0-0.29 correctly classified ✅
- **stale range**: 0.3-0.49 correctly classified ✅
- **likely range**: 0.5-0.69 correctly classified ✅
- **definitely range**: 0.7-1.0 correctly classified ✅

### Messaging Quality (ADHD Validation)
- **No guilt words**: "abandoned", "forgot", "ignored" absent from user messages ✅
- **Emoji consistency**: ⚪🟡🟠🔴 match severity levels ✅
- **Choice framing**: "want to finish or archive?" present ✅
- **Supportive tone**: "might want to", "time to decide" validated ✅

## Integration Points

### With F1-F4 (Untracked Work Detection)
- **Location**: untracked_work_detector.py:122-123 (Step 3.75)
- **Method**: Calculate abandonment after F5 pattern boost, before threshold check
- **Data Flow**: git_detection → calculate_abandonment_score → add to result
- **Non-Invasive**: Abandonment doesn't affect confidence or threshold logic

### With F5 (Pattern Learning) - Future Enhancement
- **Designed Integration**: Abandoned patterns → pattern_learner.learn_from_outcome()
- **Use Case**: Detect risky patterns (user frequently abandons .py files in experiments/)
- **Status**: Schema designed, integration pending (F5 learning loop not yet implemented)
- **Benefit**: Predict future abandonment based on pattern similarity

### With MCP Server (Tool Exposure)
- **Tools**: get_abandoned_work, mark_abandoned, get_abandonment_stats
- **Registration**: Lines 960-1017 (tool schemas)
- **Dispatcher**: Lines 1151-1156 (routing)
- **Response Format**: JSON with ADHD guidance and emoji indicators

### With ConPort (Future)
- **Event Logging**: mark_abandoned can log to pattern_events category
- **Action Tracking**: Record commit/archive/delete choices for learning
- **Status**: ConPort client integration pending (schema ready)

## Code Metrics

### Lines of Code (Total: 944)
- **Production Code**: 574 lines
  - abandonment_tracker.py: 265 lines
  - untracked_work_detector.py: +4 lines
  - mcp_server.py: +309 lines (tool implementations + registrations)
- **Test Code**: 370 lines
  - test_abandonment_tracker_f6.py: 370 lines

### Complexity Analysis
- **AbandonmentTracker**: Low complexity (simple time math, threshold checks)
- **Action Suggestion Logic**: Medium complexity (branching on file count + severity)
- **Integration**: Low complexity (single method call in detect() flow)
- **Overall**: Maintainable, well-tested, clearly documented

## Validation Gates (from Zen Planning)

### Gate 1: F6 Foundation ✅ PASSED
- [x] Time-based scoring working (7/14/28 day tests passing)
- [x] Severity classification accurate (all 4 levels validated)
- [x] GUILT-FREE messaging validated (no shame words present)
- [x] Action suggestions context-aware (file count + severity logic tested)
- [x] Tests passing (19/19)

**Decision**: ✅ PROCEED to F7 or finalize Phase 2

## Next Steps (From Planning)

### Immediate (Week 4-5): F7 - Metrics Dashboard
1. Create metrics_dashboard.py
2. Aggregate F1-F6 analytics (detection stats, pattern probabilities, abandonment rates)
3. Visualize trends over time (matplotlib or text-based)
4. Add MCP tools: get_metrics_dashboard, get_metric_history

### Future Enhancements
1. **ConPort Integration**: Connect abandonment_tracker to ConPort for event logging
2. **F5 Feedback Loop**: Feed abandoned patterns back to pattern_learner
3. **Risky Pattern Detection**: Learn "I always abandon .py files in experiments/"
4. **Action Outcome Tracking**: Did committing abandoned work improve productivity?

## Lessons Learned

### What Worked Well
1. **Thinkdeep Analysis**: Zen thinkdeep extracted F6 requirements efficiently (4 steps)
2. **ADHD Design Validation**: Guilt-free messaging tested explicitly, not assumed
3. **Test-First Severity**: All 4 severity levels tested before messaging validation
4. **F5 Pattern Reuse**: MCP tool structure from F5 applied cleanly to F6

### Issues Encountered
1. **Thinkdeep Step 5 Timeout**: Final step timed out, but steps 1-4 provided sufficient info
   - **Learning**: Don't over-rely on final synthesis step, extract incrementally
   - **Impact**: None - implementation proceeded successfully

### Future Improvements
1. Add time-decay to abandonment score (older work less urgent than recent)
2. Implement user feedback loop (track whether suggestions were helpful)
3. Add "snooze" option for work user wants to keep but not act on immediately
4. Consider context-switching cost (abandoned work during hyperfocus vs distraction)

## Dependencies

### Zero New Dependencies ✅
- Uses existing: pathlib, datetime, logging, json
- Integrates with: GitWorkDetector, UntrackedWorkDetector (existing)
- Future: ConPort MCP client (already planned)

### Version Compatibility
- Python: 3.11+
- pytest: 8.4.1+
- No breaking changes to F1-F5 interfaces

## Feature Comparison: F5 vs F6

| Aspect | F5: Pattern Learning | F6: Abandonment Tracking |
|--------|---------------------|-------------------------|
| **Signal Type** | Spatial (file patterns) | Temporal (time idle) |
| **Data Source** | File extensions, directories, branches | first_change_time |
| **Scoring** | Probability (frequency-based) | Score = days_idle / 14 |
| **Confidence Impact** | +0.15 boost (max) | None (additive context) |
| **Persistence** | ConPort custom_data (designed) | Current session only |
| **ADHD Feature** | Pattern recognition for confidence | Guilt-free reminders |
| **Integration Point** | Step 3.5 (before threshold) | Step 3.75 (after F5 boost) |
| **MCP Tools** | 2 (stats, patterns) | 3 (list, mark, stats) |
| **Lines of Code** | 563 production + 429 test | 574 production + 370 test |

---

**Completion**: All 7 tasks completed
**Status**: ✅ Ready for F7 implementation or Phase 2 finalization
**Decision ID**: Will be logged as ConPort Decision #144

## F6 MCP Tool Examples

### get_abandoned_work
```json
{
  "tool": "get_abandoned_work",
  "params": {
    "min_days_idle": 7,
    "min_score": 0.5,
    "limit": 10
  },
  "response": {
    "abandoned_work": [
      {
        "work_name": "Feature: Authentication refactor",
        "days_idle": 10,
        "score": 0.71,
        "severity": "definitely_abandoned",
        "message": "🔴 This has been sitting for 10 days - time to decide: commit, archive, or delete?",
        "suggested_action": {
          "action": "commit",
          "rationale": "6 files changed - looks like real work worth saving",
          "urgency": "high"
        },
        "files": ["auth.py", "session.py", "jwt.py", ...]
      }
    ]
  }
}
```

### mark_abandoned
```json
{
  "tool": "mark_abandoned",
  "params": {
    "work_name": "Feature: Authentication refactor",
    "action_taken": "commit"
  },
  "response": {
    "success": true,
    "feedback": "🎉 Great! Completing old work builds momentum. Your authentication refactor is now committed.",
    "pattern_logged": true
  }
}
```

### get_abandonment_stats
```json
{
  "tool": "get_abandonment_stats",
  "response": {
    "total_abandoned": 3,
    "by_severity": {
      "likely_abandoned": 1,
      "definitely_abandoned": 2
    },
    "avg_days_idle": 12.3,
    "oldest_work": {
      "work_name": "Experiment: Redis caching",
      "days_idle": 18
    },
    "suggested_actions": {
      "commit": 2,
      "archive": 1
    }
  }
}
```
