---
id: RUNNER_README
title: Runner Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Runner Readme (explanation) for dopemux documentation and developer workflows.
---
# Production Runner - Complete Features

Updated `run_extraction.py` with production-grade reliability:

## New Features

### 1. Retry Logic with Exponential Backoff
- **Max retries:** 3 attempts per API call
- **Base delay:** 5 seconds
- **Backoff:** 5s → 10s → 20s
- **Handles:** Rate limits (429), timeouts, network errors

### 2. Checkpoint/Resume
- **Auto-saves** progress to `.checkpoint.json`
- **Tracks:** Completed phases, failed phases, tokens, cost
- **Resume:** `python run_extraction.py --resume`
- **Skip completed:** Won't re-run successful phases

### 3. Cost Tracking
- **Real-time:** Shows cost per phase
- **Total:** Cumulative cost across all phases
- **Token counts:** Input/output tokens tracked
- **Pricing:** Grok rates ($0.50/$1.50 per 1M tokens)

### 4. Output Validation
- **JSON validation:** Checks output before saving
- **Warnings:** Alerts on invalid JSON (still saves for manual review)
- **File size:** Shows output size in KB

### 5. Error Handling
- **Graceful interrupts:** Ctrl+C saves checkpoint
- **Error recovery:** Failed phases logged to checkpoint
- **Summary on failure:** Shows what succeeded before crash

### 6. Progress Tracking
- **Per-phase:** Shows attempt number, tokens, cost
- **Overall:** Summary at end with totals
- **Time tracking:** Elapsed time displayed

---

## Usage

### Normal Run
```bash
export XAI_API_KEY=xai-your_key
python UPGRADE/run_extraction.py
```

### Resume After Failure
```bash
python UPGRADE/run_extraction.py --resume
```

### Custom Checkpoint Location
```bash
python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
```

### Dry Run (Test)
```bash
python UPGRADE/run_extraction.py --dry-run
```

---

## Checkpoint Format

Saved to `extraction/.checkpoint.json`:

```json
{
  "completed_phases": ["I1", "I2", "W1"],
  "failed_phases": [
    {
      "phase": "H2",
      "error": "Timeout",
      "timestamp": "2026-02-15T21:30:00Z"
    }
  ],
  "total_tokens": {
    "input": 45000,
    "output": 32000
  },
  "total_cost": 0.87,
  "started_at": "2026-02-15T21:00:00Z",
  "last_updated": "2026-02-15T21:30:00Z"
}
```

---

## Example Output

```
Phase I1: EXEC_I1_INSTRUCTION_INDEX.md
============================================================
  Input tokens (est): 8,200
  Calling Grok API (attempt 1/3)...
  Tokens: 8,156 in / 11,234 out
  Cost: $0.0208
  ✓ Saved: extraction/i1/LLM_INSTRUCTION_INDEX.json (145.2 KB)
  ✓ Phase I1 complete

...

EXTRACTION SUMMARY
============================================================

Completed phases: 21
Phases: ['A', 'B', 'C', 'D', 'D0', 'D3', 'E', 'F', 'H1', 'H2', 'H3', 'H4', 'I1', 'I2', 'I3', 'M1', 'QA', 'W1', 'W2', 'W3', 'CL']

Total tokens:
  Input:  287,456
  Output: 198,234

Total cost: $2.47

Time elapsed: 68.3 minutes

Outputs saved to: /Users/hue/code/dopemux-mvp/extraction/
```

---

## Benefits for Long Runs

✅ **Won't lose progress** - checkpoint saves every phase  
✅ **Survives rate limits** - automatic retry with backoff  
✅ **Cost transparency** - see exactly what you're spending  
✅ **Quick recovery** - resume picks up where it left off  
✅ **Validation** - catches JSON errors immediately  
✅ **Interrupt safe** - Ctrl+C saves state gracefully
