# dope-context Metrics Tracking Guide

**Purpose**: Measure how often LLM automatically uses semantic search before/after enhancements

## Quick Start

### 1. Clear Baseline (Before Enhancement)
```
clear_search_metrics()
```

### 2. Use Claude Code Normally
Work on actual tasks for 1-2 hours, let metrics accumulate

### 3. Check Results
```
get_search_metrics()
```

## Understanding the Metrics

### Key Metrics

**total_searches**: How many times any search tool was called

**explicit_searches**: User explicitly said "find" or "search"
- Example: "Find the ConPort server implementation"

**implicit_searches**: LLM searched automatically without being asked
- Example: "How does ADHD engine track tasks?" → LLM searches first

**implicit_percentage**: TARGET >70% after enhancements

### Scenarios Tracked

- `explicit_search`: User said "find", "search", "locate"
- `understanding`: "How does X work?", "What is Y?", "Explain Z"
- `making_changes`: "Add", "modify", "update", "implement"
- `debugging`: "Why", "fix", "error", "not working"
- `review`: "Review", "pattern", "best practice"
- `impact_analysis`: "Depends on", "uses", "calls"
- `questions`: General code questions

### Sample Output

```json
{
  "total_searches": 45,
  "explicit_searches": 8,
  "implicit_searches": 37,
  "explicit_percentage": 17.8,
  "implicit_percentage": 82.2,
  "scenarios": {
    "understanding": 18,
    "making_changes": 12,
    "debugging": 5,
    "explicit_search": 8,
    "questions": 2
  },
  "tools": {
    "search_code": 38,
    "docs_search": 4,
    "search_all": 3
  },
  "sample_queries": {
    "understanding": [
      "How does ConPort track decisions?",
      "What is the ADHD engine architecture?",
      "Explain the two-plane design"
    ],
    "making_changes": [
      "Add logging to workspace detection",
      "Update tool descriptions",
      "Implement metrics tracking"
    ]
  }
}
```

## Benchmarking Workflow

### Phase 1: Baseline (Before Enhancement)

1. **Clear metrics**:
   ```
   clear_search_metrics()
   ```

2. **Work normally** for 1-2 hours on real tasks

3. **Record baseline**:
   ```
   get_search_metrics()
   ```

   Expected: ~20% implicit_percentage

### Phase 2: Enhanced (After Enhancement)

1. **Restart Claude Code** (loads new descriptions)

2. **Clear metrics**:
   ```
   clear_search_metrics()
   ```

3. **Work on SAME types of tasks** for 1-2 hours

4. **Record enhanced**:
   ```
   get_search_metrics()
   ```

   Target: >70% implicit_percentage

### Phase 3: Analysis

Compare:
- Baseline implicit%: ~20%
- Enhanced implicit%: ~70%+
- **Improvement**: 3.5x increase in automatic search usage

## Files Created

**Metrics Storage**: `~/.dope-context/search_metrics.json`

**Format**:
```json
[
  {
    "timestamp": "2025-10-04T14:23:45",
    "tool_name": "search_code",
    "query": "How does ConPort track decisions?",
    "workspace": "/Users/hue/code/dopemux-mvp",
    "top_k": 10,
    "scenario": "understanding",
    "explicit_search": false
  }
]
```

## Advanced Analysis

### Export to CSV
```python
from src.utils.metrics_tracker import get_tracker

# Export for spreadsheet analysis
get_tracker().export_for_analysis("metrics_baseline.csv")
```

### Time-Range Analysis
```python
# Only metrics after specific time
get_search_metrics(since_timestamp="2025-10-04T12:00:00")
```

### Manual Analysis
```python
import json
from pathlib import Path

metrics_file = Path.home() / ".dope-context" / "search_metrics.json"
with open(metrics_file) as f:
    metrics = json.load(f)

# Filter by scenario
understanding_queries = [
    m for m in metrics
    if m["scenario"] == "understanding"
]

print(f"Understanding queries: {len(understanding_queries)}")
for q in understanding_queries[:5]:
    print(f"  - {q['query']}")
```

## Success Criteria

✅ **SUCCESS**: implicit_percentage > 70%
- LLM searches automatically for most code tasks
- Users get relevant context without thinking about it

⚠️ **PARTIAL**: implicit_percentage 50-70%
- Good improvement, may need refinement
- Consider additional scenario examples

❌ **INSUFFICIENT**: implicit_percentage < 50%
- Enhanced descriptions not effective enough
- Consider RAG middleware as fallback

## Console Output

Each search logs to console immediately:
```
[METRICS] search_code | scenario=understanding | explicit=False | query=How does ConPort track decisions?...
```

Watch console during work to see real-time classification.

## Troubleshooting

**No metrics appearing**:
- Check `~/.dope-context/search_metrics.json` exists
- Verify imports in server.py
- Check console for `[METRICS]` logs

**Wrong scenario classification**:
- Check `metrics_tracker.py:classify_query()`
- Add keywords for better detection
- Scenarios are heuristic-based, not perfect

**Metrics not clearing**:
- Manually delete `~/.dope-context/search_metrics.json`
- Or call `clear_search_metrics()` again
