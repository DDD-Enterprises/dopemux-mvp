---
id: SERVICE-REPO-TRUTH-EXTRACTOR-README
title: Repo Truth Extractor README
type: reference
owner: '@hu3mann'
date: '2026-03-26'
author: '@codex'
prelude: Service reference and operator entrypoint summary for Repo Truth
  Extractor.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_extraction_v5.py
  - services/repo-truth-extractor/run_extraction_v3.py
  - src/dopemux/cli.py
last_review: '2026-03-26'
next_review: '2026-06-26'
---
# Repo Truth Extractor

Repo Truth Extractor is the canonical extraction service for dopemux.

## Engines

- `v5`: multi-phase partition runner with phase-recovery hardening and optional comparison lane.
- `v4` (default): schema-first prompt/artifact contracts with canonical-writer enforcement.
- `v3` (fallback): legacy execution engine maintained for compatibility.

## Canonical CLI

```bash
pip install -e ".[dev]"
dopemux upgrades run --pipeline-version v5 --phase ALL --dry-run
dopemux upgrades preflight --pipeline-version v5 --auth-doctor
dopemux upgrades validate-live --promptset-root /abs/path/to/generated/promptset
dopemux extractor validate --output-dir /abs/path/to/generated/promptset
```

## Validation Prerequisites

`dopemux upgrades validate-live` now fails closed if the active `dopemux` import does not come from this checkout.

Use one of:

```bash
pip install -e ".[dev]"
PYTHONPATH=src python -m dopemux.cli upgrades validate-live --promptset-root /abs/path/to/generated/promptset
```

Local scanner/toolchain check:

```bash
python scripts/check_validation_toolchain.py
```

Expected local tools:

- Python scanners from the repo `dev` extra: `pip-audit`, `bandit`, `semgrep`
- External binary on `PATH`: `gitleaks`

If `gitleaks` is missing, install it separately before running live validation.

## Runner Entrypoints

- `services/repo-truth-extractor/run_extraction_v5.py`
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

Operational output root: `extraction/repo-truth-extractor/v3/runs/`

The v5 runner is the active execution engine, but it still writes run artifacts,
doctor outputs, and telemetry under the `v3` extraction tree. Validation and
monitoring should therefore inspect `extraction/repo-truth-extractor/v3/`.

### Basic usage

```bash
# Full run — all phases, canonical behavior
dopemux upgrades run \
  --pipeline-version v5 \
  --run-id FULL_RUN \
  --phase ALL \
  --promptset-root /abs/path/to/generated/promptset

# Single phase dry-run (inspect without executing)
dopemux upgrades run \
  --pipeline-version v5 \
  --run-id INSPECT \
  --phase H \
  --dry-run \
  --promptset-root /abs/path/to/generated/promptset
```

> ⚠️ **Cost warning**: Each run invokes provider APIs and may incur significant charges.
> A single accidental run cost $10 in March 2026. Never run without explicit authorization.
> Validate using `pytest -q services/repo-truth-extractor/tests/` instead of direct execution.

### Live batch safety

Live batch operations are phase-scoped by default.

- Supported live batch providers: `openai`, `gemini`, `xai`
- `openrouter` remains sync and escalation only for this milestone
- Live batch submit/watch/retrieve requires both:
  - `--execute`
  - `DPMX_LIVE_OK=1`
- `--phase ALL --batch-mode --execute` is rejected unless `--allow-multi-phase-live-batch` is also present

Example:

```bash
DPMX_LIVE_OK=1 dopemux upgrades run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --batch-mode \
  --batch-provider openai \
  --batch-submit-only \
  --max-partitions-per-step 3 \
  --run-id BATCH_D_SUBMIT \
  --promptset-root /abs/path/to/generated/promptset
```

Retrieve or watch uses the same consent gate:

```bash
DPMX_LIVE_OK=1 dopemux upgrades run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --batch-watch \
  --run-id BATCH_D_SUBMIT \
  --promptset-root /abs/path/to/generated/promptset
```

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
   metrics: schema pass/fail, repair counts, and mean latency.

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
- FL_INT standalone prompts: `services/repo-truth-extractor/prompts/phase_fl_int/`
- external generated promptsets: pass via `--promptset-root`
- legacy prompt archive: `services/repo-truth-extractor/archive/legacy_prompts/`

## FL_INT Standalone Post-Processing

`FL_INT` is a bounded v1 post-processing flow that runs after an existing completed extraction.
It does **not** modify the default phase graph, upstream prompts, or upstream extraction artifacts.

Entrypoint: `services/repo-truth-extractor/run_fl_int.py`

### Scope

- fixed step order: `F0 -> F1 -> F2 -> F4 -> L0 -> L1 -> L3 -> L4`
- required upstream norm inputs: `D`, `C`, `R`
- optional upstream norm input: `X`
- explicit `--run-root` only; no implicit latest-run lookup

### Basic usage

```bash
# Inspect the standalone post-pass without calling providers
python services/repo-truth-extractor/run_fl_int.py \
  --run-root /abs/path/to/completed/run \
  --dry-run \
  --pretty

# Execute the standalone post-pass against an existing run
python services/repo-truth-extractor/run_fl_int.py \
  --run-root /abs/path/to/completed/run \
  --routing-policy cost \
  --pretty
```

### Output layout

Default output root:

```text
<RUN_ROOT>/postprocess/fl_int_v1/
```

This directory contains:

- `FL_INT_INPUT.json`
- `DESIGN_CLAIMS_RAW.json`
- `DESIGN_CLAIMS_CLASSIFIED.json`
- `DESIGN_CONTRADICTIONS.json`
- `CANONICAL_DESIGN.md`
- `CANONICAL_DESIGN_META.json`
- `FEATURE_CANDIDATES_RAW.json`
- `FEATURE_CANDIDATES_NORMALIZED.json`
- `FEATURE_MERGE_LOG.json`
- `FEATURE_LEDGER_ROUTING.json`
- `MASTER_FEATURE_LEDGER.json`
- `FL_INT_MACHINE_SUMMARY.json`

Reference: `docs/03-reference/extraction/fl-int-postprocess.md`

## Output Roots

- v3 runs: `extraction/repo-truth-extractor/v3/runs/`
- v3 doctor: `extraction/repo-truth-extractor/v3/doctor/`
- v4 runs: `extraction/repo-truth-extractor/v4/runs/`
- v4 doctor: `extraction/repo-truth-extractor/v4/doctor/`
- v5 runtime artifacts: `extraction/repo-truth-extractor/v3/runs/`
- v5 proofs: `extraction/repo-truth-extractor/v5/proofs/`

Historical extraction outputs under old roots are preserved and read-only.
