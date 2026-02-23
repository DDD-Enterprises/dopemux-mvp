# Fix Spec — Pre-Run Must-Fix + Should-Fix

**Date**: 2026-02-22
**Findings**: F-01, F-02, F-03, F-12
**Target**: Unblock first `--phase ALL --routing-policy cost` extraction run

---

## F-01: Remove Phantom Step IDs from v3 Runner (CRITICAL)

### Problem
`run_extraction_v3.py:503-517` declares `REQUIRED_PROMPT_STEP_IDS` containing step IDs that have no corresponding prompt files or promptset.yaml entries:
- `Q11` in the Q set (line 512)
- `S4`, `S5` in the S set (line 517)

If the runner validates prompt file existence at startup, these cause a hard failure.

### Fix

**File**: `services/repo-truth-extractor/run_extraction_v3.py`
**Lines**: 512, 517

**Before** (line 512):
```python
    "Q": {"Q0", "Q1", "Q2", "Q3", "Q9", "Q11"},
```

**After** (line 512):
```python
    "Q": {"Q0", "Q1", "Q2", "Q3", "Q9"},
```

**Before** (line 517):
```python
    "S": {"S0", "S1", "S2", "S3", "S4", "S5"},
```

**After** (line 517):
```python
    "S": {"S0", "S1", "S2", "S3"},
```

### Verification
```bash
# After edit, grep to confirm no phantom IDs remain:
grep -n 'Q11\|S4\|S5' services/repo-truth-extractor/run_extraction_v3.py
# Should return zero matches
```

### Rationale
- promptset.yaml phase Q has steps: Q0, Q1, Q2, Q3, Q9 (5 steps). No Q11 exists.
- promptset.yaml phase S has steps: S0, S1, S2, S3 (4 steps). No S4 or S5 exists.
- Prompt files on disk: `PROMPT_Q0_*.md` through `PROMPT_Q9_*.md` (5 files), `PROMPT_S0_*.md` through `PROMPT_S3_*.md` (4 files). Confirmed via coverage map and promptset.yaml.

---

## F-02: Regenerate Coverage Map to Include S2, S3 (HIGH)

### Problem
`prompt_artifact_coverage_map.json` declares `prompt_count: 103` but promptset.yaml has 105 steps. Steps S2 (DECISION_DOSSIER) and S3 (ARCHITECTURE_PROOF_HOOKS) are missing from the map.

### Fix

**Command**:
```bash
cd /Users/hue/code/dopemux-mvp
python scripts/rewrite_repo_truth_extractor_v4_prompts.py
```

This script reads `promptset.yaml`, walks all phases/steps, and regenerates `prompt_artifact_coverage_map.json` deterministically.

### Verification
```bash
# After regeneration:
python -c "import json; d=json.load(open('services/repo-truth-extractor/promptsets/v4/prompt_artifact_coverage_map.json')); print(f\"prompt_count: {d['prompt_count']}\")"
# Expected: prompt_count: 105

# Verify S2 and S3 appear:
grep -c '"S2"\|"S3"' services/repo-truth-extractor/promptsets/v4/prompt_artifact_coverage_map.json
# Expected: 2 or more matches
```

### Rationale
The rewrite script is the canonical generator for this file (`generated_by: scripts/rewrite_repo_truth_extractor_v4_prompts.py`). It reads promptset.yaml and hashes each prompt file. Running it will pick up S2/S3 which were added to promptset.yaml after the last map generation.

### Risk
The rewrite script may also overwrite prompt files if it has a generation mode. **Check**: If the script has a `--coverage-only` or `--map-only` flag, use it. Otherwise, inspect the script to confirm it only writes the coverage map and doesn't modify prompt content. The script name includes "rewrite" so review before running.

**Safer alternative**: If the script also rewrites prompts, manually add S2/S3 entries to the JSON:

```json
// In phases.S array, add after S1 entry:
{
  "outputs": ["DECISION_DOSSIER_OPUS.md", "S2_DECISION_DOSSIER.md"],
  "prompt_file": "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_S2_DECISION_DOSSIER.md",
  "prompt_sha256": "<compute: sha256sum services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_S2_DECISION_DOSSIER.md>",
  "step_id": "S2"
},
{
  "outputs": ["ARCHITECTURE_PROOF_HOOKS.md", "S3_ARCH_PROOF_HOOKS.md"],
  "prompt_file": "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_S3_ARCHITECTURE_PROOF_HOOKS.md",
  "prompt_sha256": "<compute: sha256sum services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_S3_ARCHITECTURE_PROOF_HOOKS.md>",
  "step_id": "S3"
}
```

Then update `"prompt_count": 105` at bottom of file.

---

## F-03: Resolve R↔S Artifact Writer Ambiguity (HIGH)

### Problem
11 artifact names are registered in BOTH phase R and phase S in `artifacts.yaml`, each with different `canonical_writer_step_id` values. This creates writer authority ambiguity.

### Duplicated Artifacts

| Artifact Name | R canonical_writer | S canonical_writer | Authority Decision |
|---------------|-------------------|-------------------|-------------------|
| `CONTROL_PLANE_TRUTH_MAP.md` | R0 | S0 | **R0 owns** — S0 re-emits with synthesis context |
| `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md` | R1 | S0 | **R1 owns** — S0 re-emits with synthesis context |
| `EVENTBUS_WIRING_TRUTH.md` | R2 | S0 | **R2 owns** — S0 re-emits with synthesis context |
| `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md` | R3 | S0 | **R3 owns** — S0 re-emits with synthesis context |
| `TASKX_INTEGRATION_TRUTH.md` | R4 | S0 | **R4 owns** — S0 re-emits with synthesis context |
| `WORKFLOWS_TRUTH_GRAPH.md` | R5 | S0 | **R5 owns** — S0 re-emits with synthesis context |
| `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md` | R6 | S0 | **R6 owns** — S0 re-emits with synthesis context |
| `CONFLICT_LEDGER.md` | R7 | S0 | **R7 owns** — S0 re-emits with synthesis context |
| `RISK_REGISTER_TOP20.md` | R8 | S0 | **R8 owns** — S0 re-emits with synthesis context |
| `DOPE_MEMORY_SCHEMAS.json` | R1 | (C9 in C phase) | **R1 owns for R phase** |
| `DOPE_MEMORY_DB_WRITES.json` | R1 | (C9 in C phase) | **R1 owns for R phase** |

### Design Decision

**R-phase is the canonical writer for all shared artifacts.** S-phase is a synthesis layer that reads R-phase outputs and may produce enhanced/annotated versions, but the v4 norm promotion should only promote from R-phase canonical writers for these artifacts.

### Fix Options

**Option A (Recommended): Add comments + rename S-phase outputs**

In `artifacts.yaml`, rename S-phase entries to avoid collision:

```yaml
# For each of the 9 shared markdown artifacts in phase S, change:
# FROM:
- phase: S
  artifact_name: CONTROL_PLANE_TRUTH_MAP.md
  canonical_writer_step_id: S0

# TO:
- phase: S
  artifact_name: S_CONTROL_PLANE_TRUTH_MAP.md  # prefixed with S_
  canonical_writer_step_id: S0
```

This requires also updating:
1. `promptset.yaml` S0 outputs list
2. The S0 prompt file's Outputs section
3. Coverage map regeneration (F-02)

**Option B (Minimal): Add authority comment, accept dual registration**

Add a YAML comment block at the top of the S-phase artifact entries:

```yaml
# --- S-phase synthesis artifacts ---
# These artifacts share names with R-phase outputs.
# R-phase is the canonical source of truth.
# S-phase produces enhanced versions for the synthesis trace.
# The v4 runner promotes from R-phase canonical writers only.
# S-phase versions live in norm/by_step/S0/ but are NOT promoted to phase norm root.
```

This is safe because `sync_phase_from_v3` (v4 runner line 968-991) only promotes artifacts where the canonical_writer_step_id matches. Since R and S are different phases, each phase's norm root gets its own canonical. The ambiguity is cosmetic, not functional.

### Recommended: Option B

Option B is correct because the v4 runner already handles this correctly:
- Phase R promotes from R-phase canonical writers to `R_arbitration/norm/`
- Phase S promotes from S-phase canonical writers to `S_synthesis_trace/norm/`
- There is no cross-phase promotion collision

Add the comment block and document the design decision. No code changes needed.

### Verification
```bash
# Confirm no cross-phase collision in runner logic:
grep -n "canonical_writer" services/repo-truth-extractor/run_extraction_v4.py | head -20
# The promotion loop (line 968-991) operates per-phase, so R and S never collide
```

---

## F-12: Add v4-Level `--dry-run` Summary (MEDIUM)

### Problem
`--dry-run` passes through to v3 runner with no v4-level summary showing cost estimate, step count, or partition plan.

### Design

When `--dry-run` is passed to the v4 runner, **before** delegating to v3, print a v4 summary:

```
╔══════════════════════════════════════════════════╗
║  Repo Truth Extractor v4 — Dry Run Summary       ║
╠══════════════════════════════════════════════════╣
║  Run ID:          v4_20260222_143000              ║
║  Phase(s):        A (11 steps)                    ║
║  Total steps:     11                              ║
║  Routing policy:  cost                            ║
║  Batch mode:      disabled                        ║
║  Escalation hops: 2                               ║
║                                                    ║
║  Estimated cost:  ~$1.20 (sync) / ~$0.60 (batch)  ║
║  Est. tokens:     ~280K input / ~55K output        ║
║                                                    ║
║  Step breakdown:                                   ║
║    bulk (inventory):  2 steps  (~$0.05)            ║
║    extract:           7 steps  (~$0.85)            ║
║    synthesis:         0 steps  (~$0.00)            ║
║    qa (merge):        2 steps  (~$0.30)            ║
╚══════════════════════════════════════════════════╝

Delegating to v3 runner with --dry-run...
```

### Implementation

**File**: `services/repo-truth-extractor/run_extraction_v4.py`
**Location**: In `run_pipeline()`, after line 1232 (`v3_phases = ...`), before the v3 call block.

**New function to add** (before `run_pipeline`):

```python
def print_dry_run_summary(
    *,
    run_id: str,
    selected_phases: List[str],
    promptset: Dict[str, Any],
    routing_policy: str,
    batch_mode: bool,
    escalation_max_hops: int,
) -> None:
    """Print v4-level dry-run summary with step count and cost estimate."""
    # Cost-per-step estimates ($/step, sync mode)
    TIER_COSTS = {
        "bulk": 0.035,      # inventory/partition steps (*0 steps)
        "extract": 0.12,    # extraction steps (*1-*8)
        "synthesis": 0.30,  # R/T/X/Z/S steps
        "qa": 0.03,         # merge/QA steps (*9/*99)
    }
    STEP_TYPE_PATTERNS = {
        "bulk": lambda sid: sid.endswith("0") and not sid.endswith("10"),
        "qa": lambda sid: sid.endswith("9") or sid.endswith("99"),
        "synthesis": lambda sid: sid[0] in {"R", "T", "X", "Z", "S"},
    }

    total_steps = 0
    tier_counts: Dict[str, int] = {"bulk": 0, "extract": 0, "synthesis": 0, "qa": 0}

    for phase in selected_phases:
        steps = phase_steps(promptset, phase)
        for step in steps:
            step_id = str(step.get("step_id", ""))
            total_steps += 1
            if STEP_TYPE_PATTERNS["bulk"](step_id):
                tier_counts["bulk"] += 1
            elif STEP_TYPE_PATTERNS["qa"](step_id):
                tier_counts["qa"] += 1
            elif STEP_TYPE_PATTERNS["synthesis"](step_id):
                tier_counts["synthesis"] += 1
            else:
                tier_counts["extract"] += 1

    sync_cost = sum(tier_counts[t] * TIER_COSTS[t] for t in TIER_COSTS)
    batch_cost = sync_cost * 0.5

    phase_label = ", ".join(selected_phases) if len(selected_phases) <= 5 else f"{len(selected_phases)} phases"

    print(f"\n{'='*55}")
    print(f"  Repo Truth Extractor v4 — Dry Run Summary")
    print(f"{'='*55}")
    print(f"  Run ID:          {run_id}")
    print(f"  Phase(s):        {phase_label}")
    print(f"  Total steps:     {total_steps}")
    print(f"  Routing policy:  {routing_policy}")
    print(f"  Batch mode:      {'enabled' if batch_mode else 'disabled'}")
    print(f"  Escalation hops: {escalation_max_hops}")
    print(f"")
    print(f"  Estimated cost:  ~${sync_cost:.2f} (sync) / ~${batch_cost:.2f} (batch)")
    print(f"")
    print(f"  Step breakdown:")
    for tier in ["bulk", "extract", "synthesis", "qa"]:
        cost = tier_counts[tier] * TIER_COSTS[tier]
        label = {"bulk": "bulk (inventory)", "extract": "extract", "synthesis": "synthesis", "qa": "qa (merge)"}[tier]
        print(f"    {label:20s} {tier_counts[tier]:3d} steps  (~${cost:.2f})")
    print(f"{'='*55}\n")
```

**Call site**: In `run_pipeline()`, add after line 1232:

```python
    if dry_run:
        print_dry_run_summary(
            run_id=run_id,
            selected_phases=selected_phases,
            promptset=promptset,
            routing_policy=routing_policy,
            batch_mode=batch_mode,
            escalation_max_hops=escalation_max_hops,
        )
```

### Verification
```bash
python services/repo-truth-extractor/run_extraction_v4.py --phase A --dry-run --run-id test_dry
# Should print summary table, then delegate to v3 --dry-run
```

---

## Implementation Order

1. **F-01** (5 min): Edit 2 lines in run_extraction_v3.py
2. **F-02** (10 min): Regenerate coverage map
3. **F-03** (5 min): Add comment block to artifacts.yaml
4. **F-12** (20 min): Add `print_dry_run_summary` function + call site

## Post-Implementation Verification

```bash
# 1. Audit passes:
python scripts/repo_truth_extractor_promptset_audit_v4.py --repo-root .

# 2. Coverage map correct:
python -c "import json; print(json.load(open('services/repo-truth-extractor/promptsets/v4/prompt_artifact_coverage_map.json'))['prompt_count'])"
# Expected: 105

# 3. Dry-run works:
python services/repo-truth-extractor/run_extraction_v4.py --phase A --dry-run --run-id test_verify
```
