---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Repo Truth Extractor

Repo Truth Extractor is the canonical extraction service for dopemux.

## Engines

- `v5`: multi-phase partition runner with phase-recovery hardening and optional comparison lane.
- `v4` (default): schema-first prompt/artifact contracts with canonical-writer enforcement.
- `v3` (fallback): legacy execution engine maintained for compatibility.

## Canonical CLI

```bash
dopemux extractor list --engine-version v4
dopemux extractor run --engine-version v4 --phase ALL --dry-run
dopemux extractor status --engine-version v4 --run-id <RUN_ID>
dopemux extractor doctor --engine-version v4 --run-id <RUN_ID>
dopemux extractor promptset audit --engine-version v4
```

## Runner Entrypoints

- `services/repo-truth-extractor/run_extraction_v3.py`
- `services/repo-truth-extractor/run_extraction_v4.py`

## v3 Introspection and Async Batch Utilities

```bash
# Deterministic CLI introspection
python services/repo-truth-extractor/run_extraction_v3.py --print-run-order
python services/repo-truth-extractor/run_extraction_v3.py --print-phase-routing --phase Q --dry-run
python services/repo-truth-extractor/run_extraction_v3.py --print-phase-prompts ALL
python services/repo-truth-extractor/run_extraction_v3.py --tail-run-log --run-id <RUN_ID> --phase C --step C0 --tail-lines 100
python services/repo-truth-extractor/run_extraction_v3.py --show-provider-usage --run-id <RUN_ID>

# Async batch split mode (explicit)
python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-mode --batch-submit-only --run-id <RUN_ID>
python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-watch --run-id <RUN_ID>
```

Webhook notify mode for `--batch-watch` is controlled by:

- `DPMX_WEBHOOK_URL`
- `DPMX_WEBHOOK_SECRET`
- `DPMX_WEBHOOK_TIMEOUT_SECONDS`
- `DPMX_WEBHOOK_REQUIRED`
- `DPMX_WEBHOOK_AUTO_CONTINUE`
- `DPMX_LIVE_OK`

## v5 Runner

Entrypoint: `services/repo-truth-extractor/run_extraction_v5.py`

Output root: `extraction/repo-truth-extractor/v5/runs/`

### Basic usage

```bash
# Full run — all phases, canonical behavior
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id FULL_RUN \
  --phase ALL

# Single phase dry-run (inspect without executing)
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id INSPECT \
  --phase H \
  --dry-run
```

> ⚠️ **Cost warning**: Each run invokes provider APIs and may incur significant charges.
> A single accidental run cost $10 in March 2026. Never run without explicit authorization.
> Validate using `pytest -q services/repo-truth-extractor/tests/` instead of direct execution.

### Comparison lane

The comparison lane runs a secondary model alongside canonical steps **without altering
canonical outputs or pass/fail semantics**. It is disabled by default.

**CLI flags:**

| Flag | Description |
|------|-------------|
| `--compare-mode additional` | Enable comparison lane (required to activate) |
| `--compare-model <model>` | Model slug for comparison (e.g. `grok-4.20-beta`) |
| `--compare-provider <provider>` | Provider slug (e.g. `xai`) |
| `--compare-steps <step,step>` | Comma-separated eligible steps to compare |

**Eligible steps** (doc-heavy synthesis phases only):

`A9`, `B9`, `G9`, `H9`, `R9`, `S9`, `T9`, `W9`, `X9`

Requesting a step outside this list fails immediately with a clear error listing valid options.

**Example — compare H9 and A9:**

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id COMPARE_RUN \
  --compare-mode additional \
  --compare-provider xai \
  --compare-model grok-4.20-beta \
  --compare-steps H9,A9
```

**What happens:**
1. Canonical run completes normally — all existing behavior, routes, and artifacts unchanged.
2. After canonical completion for each selected step, the comparison lane executes the same
   partitions with the comparison model.
3. Comparison outputs are written to a separate tree and **never overwrite canonical files**.
4. A per-step summary (`COMPARE_SUMMARY_<STEP>.json` + `.md`) is written with side-by-side
   metrics: schema pass/fail, repair counts, latency, token/cost usage.

**Comparison artifact layout:**

```
extraction/repo-truth-extractor/v5/runs/<RUN_ID>/<phase_dir>/
  raw/
    <step>__<partition>.json          # canonical output (unchanged)
  raw/comparison/xai__grok-4.20-beta/
    <step>__<partition>.json          # comparison output (separate)
  COMPARE_SUMMARY_H9.json            # step-level side-by-side metrics
  COMPARE_SUMMARY_H9.md              # human-readable version
```

**Inspecting results:**

```bash
# Read the JSON summary for H9
cat extraction/repo-truth-extractor/v5/runs/COMPARE_RUN/H_home_entrypoints/COMPARE_SUMMARY_H9.json

# Read the markdown summary
cat extraction/repo-truth-extractor/v5/runs/COMPARE_RUN/H_home_entrypoints/COMPARE_SUMMARY_H9.md

# Grep comparison lane logs
grep "COMPARE_" logs/run_COMPARE_RUN.log
```

**Key log markers** (grep-friendly):

- `COMPARE_ROUTE_CHOSEN` — comparison route resolved
- `COMPARE_EXEC_START` — comparison partition execution starting
- `COMPARE_EXEC_DONE` — partition result recorded
- `COMPARE_VALIDATION_RESULT` — schema/repair outcome for comparison output
- `COMPARE_SUMMARY_WRITTEN` — summary files written
- `COMPARE_LANE_ERROR` — comparison failure (canonical run unaffected)

**Non-blocking failures:** If the comparison lane errors (network, model unavailable, schema
rejection), the canonical step remains PASS and the failure is recorded in the summary.
The run does not abort or downgrade.

**Resume behavior:** Comparison artifacts resume independently. An existing canonical
artifact does not skip the comparison, and vice versa.

**Full reference:** `extraction/repo-truth-extractor/v5/proofs/TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001/`

---

## Prompt Assets

- v3 prompts: `services/repo-truth-extractor/prompts/v3/`
- v4 promptset: `services/repo-truth-extractor/promptsets/v4/`
- v5 promptsets: `services/repo-truth-extractor/promptsets/v5/`
- legacy prompt archive: `services/repo-truth-extractor/archive/legacy_prompts/`

## Output Roots

- v3 runs: `extraction/repo-truth-extractor/v3/runs/`
- v3 doctor: `extraction/repo-truth-extractor/v3/doctor/`
- v4 runs: `extraction/repo-truth-extractor/v4/runs/`
- v4 doctor: `extraction/repo-truth-extractor/v4/doctor/`
- v5 runs: `extraction/repo-truth-extractor/v5/runs/`
- v5 proofs: `extraction/repo-truth-extractor/v5/proofs/`

Historical extraction outputs under old roots are preserved and read-only.
