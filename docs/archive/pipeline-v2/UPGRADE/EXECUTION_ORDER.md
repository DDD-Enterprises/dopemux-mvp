---
id: EXECUTION_ORDER
title: Execution Order
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Execution Order (explanation) for dopemux documentation and developer workflows.
---
# Optimized Execution Order: Flash → 5.2 → Opus

**Cost-optimized execution plan with model assignments.**

---

## Model Assignment Strategy

**Nuanced approach per phase characteristics:**

**Gemini Flash 3:**
- Home config (H1-H4) - strict redaction discipline
- Instruction/workflow planes (I1-I3, W1-W3) - JSON-only, no vibes
- Docs extraction (D0-CL) - mechanical, no judgment

**Grok-code-fast-1:**
- Code surfaces (A-F) - faster at code indexing/grep-like tasks
- Symbol maps, risk scans - when you need precise code parsing

**GPT-5.2 Extended:** Arbitration, truth maps, conflict resolution  
**Opus:** 2 runs for synthesis (architecture + migration)

**Rule:** Flash/Grok = evidence indexes. Only 5.2/Opus write "this is the architecture."

---

## Execution Order (Today)

### Phase 1: Home Config (Flash 3)
**15 min, $0.10**

```bash
export GEMINI_API_KEY=your_gemini_key
python UPGRADE/run_extraction.py --phases priority
```

Runs H1-H4 → 8 JSON outputs revealing hidden control plane

---

### Phase 2: Docs Tier 0/1 Partitions (Flash 3)
**45 min, $0.80**

Run D0, then D1/D2 for priority partitions only:
- P1_CONTROL_PLANE (docs/custom-instructions, .claude/, .dopemux/)
- P2_CORE_ARCH (docs/architecture/, docs/adrs/)
- P3_PLANES_ACTIVE (docs/trinity/, docs/memory/, docs/workflows/)

Skip lower-tier partitions for now (P10-P17).

---

### Phase 3: Merge + QA + Clusters (Flash 3)
**10 min, $0.15**

```bash
# After D1/D2 complete for Tier 0/1
python UPGRADE/run_extraction.py --phases docs
```

Runs D3, M1, QA, CL.

---

### Phase 4: GPT-5.2 Arbitration
**20 min, $3-5**

Feed ALL extracted JSON to GPT-5.2 Extended Thinking (desktop app):

**Inputs:**
- Home config (H1-H4 outputs)
- Instruction plane (I1-I3)
- Workflow surfaces (W1-W3)
- Doc claims/boundaries (D1/M1 outputs)
- Existing code surfaces (if current)

**Outputs requested:**
1. `CONTROL_PLANE_TRUTH_MAP.md`
2. `INSTRUCTION_TO_SERVICE_TRACE.md`
3. `WORKFLOW_CONSISTENCY_LEDGER.md`
4. `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
5. `TASKX_INTEGRATION_TRUTH.md`
6. `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
7. `EVENTBUS_WIRING_TRUTH.md`
8. `PORTABILITY_RISK_LEDGER.md`

---

### Phase 5: Opus Run #1 - Architecture Synthesis
**15 min, $2-3**

**Inputs:**
- All 5.2 truth maps
- Doc topic clusters
- Workflow graph
- Control plane surfaces

**Output:**
`ARCHITECTURE_SPEC.md` - subsystems, boundaries, contracts, dataflows

---

### Phase 6: Opus Run #2 - Migration Plan
**15 min, $2-3**

**Inputs:**
- Control plane truth map
- Portability risks
- Workflow consistency ledger

**Output:**
`MCP_TO_HOOKS_MIGRATION_PLAN.md` - what moves, what stays, invariants

---

## Cost Summary

| Phase                | Model     | Time      | Cost      |
| -------------------- | --------- | --------- | --------- |
| H1-H4                | Flash 3   | 15m       | $0.10     |
| I/W                  | Flash 3   | 25m       | $0.20     |
| D0-CL (Tier 0/1)     | Flash 3   | 55m       | $0.95     |
| **Subtotal (Flash)** |           | **95m**   | **$1.25** |
| GPT-5.2              | Extended  | 20m       | $3-5      |
| Opus #1              | Synthesis | 15m       | $2-3      |
| Opus #2              | Migration | 15m       | $2-3      |
| **Total**            |           | **~145m** | **~$10**  |

Compare to full extraction (all partitions, all code): ~$25-30

---

## Decision Point: Skip Code Extraction?

**Check existing surface files:**
```bash
ls -lhT *_SURFACE.json *_MAP.json ENTRYPOINTS.json
```

If timestamps show **Feb 15, 2026** → Skip code extraction, use existing  
If older → Run code phases (A-F)

---

## Flash API Setup

```bash
export GEMINI_API_KEY=your_gemini_key
export XAI_API_KEY=your_grok_key  # Fallback only

# Verify
python UPGRADE/run_extraction.py --dry-run --phases priority
```

**Runner auto-routes:**
- All phases → Gemini Flash 3
- If GEMINI_API_KEY missing → Falls back to Grok
- If Flash breaks JSON → Manually set XAI_API_KEY only

---

## Next Steps After Extraction

1. **Validate outputs:**
   ```bash
   jq '.artifact_type' extraction/*/*.json | sort | uniq -c
   ```

2. **Spot-check drift:**
   ```bash
   jq '.comparisons[] | select(.drift_detected == true)' extraction/h3/HOME_VS_REPO_DIFF_HINTS.json
   ```

3. **Prepare for 5.2:**
   - Zip all extraction/*.json
   - Open GPT-5.2 desktop app
   - Paste prompt requesting truth maps

4. **Prepare for Opus:**
   - Feed 5.2 outputs + clusters
   - Request architecture spec
   - Request migration plan

---

## Fallback to Grok (If Needed)

If Flash keeps breaking JSON-only:

```bash
# Temporarily swap keys
export GEMINI_API_KEY=""
export XAI_API_KEY=your_grok_key

# Run specific problematic phase
python UPGRADE/run_extraction.py --phases code
```

Runner will fall back to Grok for that run.
