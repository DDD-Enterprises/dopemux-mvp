---
id: rte-operator-quickstart-debut
title: RTE Operator Quickstart — Trigger a Real Run Today
type: operator-quickstart
owner: claude
date: 2026-05-22
audit: rte-pre-debut-2026-05-22
audit_branch_head: 748d3c9a681f346e645042cba05ff311d7007f05
status: empirically-validated (F8 retry confirmed live run path)
---

# RTE Operator Quickstart — Trigger a Real Run Today

This is the single-page reference for an operator who wants to run RTE against a real repo right now. Validated end-to-end during the 2026-05-22 audit ($0.27 actual spend on Phase A against a 5-file fixture).

---

## Prerequisites

1. **Python env** with `openai` package installed:
   ```bash
   pip install openai readchar python-dotenv
   ```
   (RTE soft-imports `openai`; missing it produces `AMBIGUOUS_PROVIDER_BLOCK` — see audit F8R-MED-1.)

2. **API keys** in env. Required for the `balanced_grok_openrouter` lane:
   ```bash
   export OPENROUTER_API_KEY=...
   export XAI_API_KEY=...
   ```
   Optional (for other lanes): `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`.

3. **Consent env**:
   ```bash
   export DPMX_LIVE_OK=1
   ```

---

## Three-step real run

### Step 1 — Dry-run cost preview (FREE)

```bash
cd /path/to/your/repo
python /path/to/dopemux/services/repo-truth-extractor/run_extraction_v5.py \
  --print-cost-preview --phase A --dry-run \
  --routing-policy balanced_grok_openrouter \
  --run-id $(date +%Y%m%d_cost_probe) \
  --output-root /tmp/rte-cost-preview
```

Read the `summary.estimated_cost_usd` field. If you're comfortable with that number ×2 (safety margin), proceed.

### Step 2 — Bounded live run

```bash
python /path/to/dopemux/services/repo-truth-extractor/run_extraction_v5.py \
  --phase A --execute \
  --routing-policy balanced_grok_openrouter \
  --partition-workers 1 \
  --run-id $(date +%Y%m%d_first_run) \
  --output-root /path/to/extraction-output
```

**Optional spend cap** (recommended): `--max-cost-usd 0.50`. NOTE: cost cap requires a `--pricing-manifest` file with rows covering every model the lane uses. If you hit `Pricing config missing route coverage for ...`, either add the rows or run without `--max-cost-usd` on a known-small corpus.

**Forced serial execution**: `--partition-workers 1` is enforced automatically when `--max-cost-usd` is set, and recommended even without (avoids spend-ledger race per audit FA-5-MED-1).

### Step 3 — Inspect the outputs

```bash
# Per-phase outputs:
cat /path/to/extraction-output/runs/<run-id>/A_repo_control_plane/qa/A0_QA.json | jq

# Spend ledger:
cat /path/to/extraction-output/runs/<run-id>/spend_ledger.json | jq '.models'

# Resume proof (if interrupted):
cat /path/to/extraction-output/runs/<run-id>/RESUME_PROOF.json | jq

# Per-step prompt that was sent:
cat /path/to/extraction-output/runs/<run-id>/A_repo_control_plane/raw/A0__A_P0001.TRACE.md
```

---

## Safety: what NOT to do today

Per the audit (and P5 §4.1), the validated bounded lane is **direct python invocation**, NOT the `dopemux rte ...` CLI. Avoid until further notice:

- **`dopemux rte run`** — known to flow through the CLI subprocess which has its own quirks (`extractor_preflight` issues TWO subprocess calls per `--auth-doctor` per FA-1-MED-1).
- **`dopemux upgrades run ...`** — DEPRECATED. The CLI labels this a legacy compatibility alias. Some docs (`docs/03-reference/extraction-wizard.md:197`) still reference it incorrectly — audit FA-10-HIGH-1 / F4-CRIT-2 residual.
- **`dopemux prescan ...`** — DOES NOT EXIST. Doc reference at `docs/03-reference/extraction/prescan-pipeline.md:302` is wrong. Per audit FA-10-HIGH-2 / F4-HIGH-3.
- **`--home-scan-mode full`** — no consent gate; can walk `.ssh/`, `.aws/`, `.kube/` into prompts. Per audit FA-2d-HIGH-1.
- **Running on a repo with `_SECRET_NAMED_` env-style files** — secrets like `AWS_SECRET_ACCESS_KEY=...` or `DATABASE_PASSWORD=...` in Makefiles / scripts will leak into the published proof bundle (audit FA-4-HIGH-1, runtime-confirmed in F8). Pre-screen your corpus.

---

## Safe introspection (read-only, $0 cost)

These commands are validator-safe per audit F7 (12/13 introspection paths verified zero-side-effect):

```bash
# Phase taxonomy + dependency graph:
python run_extraction_v5.py --list-phases --run-id any --output-root /tmp/out

# Cost preview:
python run_extraction_v5.py --print-cost-preview --phase A --dry-run --run-id any

# Doctor (refuses without DPMX_LIVE_OK=1):
python run_extraction_v5.py --doctor --run-id any --output-root /tmp/out

# Print config / run order / phase routing:
python run_extraction_v5.py --print-config --phase A --dry-run --run-id any
python run_extraction_v5.py --print-run-order --run-id any
python run_extraction_v5.py --print-phase-routing --phase A --run-id any
```

**KNOWN GOTCHA (audit FA-7-MED-1):** `--status --run-id <typo>` (text mode) creates a `telemetry/TERMINAL_TIMELINE.jsonl` under the typo'd run-id. Use `--status-json` instead — it's fully readonly.

---

## When things go wrong

### Preflight `AMBIGUOUS_PROVIDER_BLOCK`
- Run `pip install openai` (the # 1 cause)
- Verify keys with direct curl: `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/chat/completions ...`

### `Pricing config missing route coverage`
- Drop `--max-cost-usd` OR
- Add the model_id to a custom `--pricing-manifest` JSON file

### `Live LLM call blocked in test context`
- Set `RTE_ALLOW_LIVE_LLM_IN_TESTS=1`
- This shouldn't normally fire; if it does, your env has `PYTEST_CURRENT_TEST` set somehow

### COST_ABORTED
- Resume is **intentionally disabled** for cost-aborted runs (FA-5-OBS-3). Start a new run with a higher cap.

---

## Audit pointers

For deeper context on any aspect:

- All findings: `~/.claude/projects/-Users-hue-code-dopemux-mvp/memory/rte_audit_findings_FA*.md`
- SLO budget: `~/.claude/projects/-Users-hue-code-dopemux-mvp/memory/rte_audit_slo_budget.md`
- Audit branch: `audit/rte-pre-debut-2026-05-22` at `/Users/hue/code/dopemux-mvp-audit-rte-debut`
- F8 live-run artifacts: see `rte_audit_findings_FA8_RETRY_and_FA_OPT_EMPIRICAL.md`

---

## Validated reference run (2026-05-22)

| Metric | Value |
|--------|-------|
| Corpus | 5 files (golden_repo_min + planted F4 PoC fixtures) |
| Phase | A only (`balanced_grok_openrouter`) |
| Wall time | 227.6 seconds |
| Routes used | `openrouter/openai/gpt-5.3-codex`, `openrouter/openai/gpt-5.4`, `xai/grok-4.20-beta-0309-non-reasoning`, `xai/grok-4.20-beta-0309-reasoning` |
| Models served | `openai/gpt-5.3-codex-20260224`, `gpt-5.4-2026-03-05`, `grok-4.20-0309-reasoning` (alias drift tolerated by RTE) |
| Tokens | 51,174 input + 9,859 output = 61,033 total |
| Cost | **$0.2715** |
| Output | 14 norm artifacts, 30 QA artifacts, 1 RESUME_PROOF.json, 1 spend_ledger.json |
