---
id: RUNBOOK-EXTRACTION-RTE-V5-BILLING-DRILL
title: Repo Truth Extractor v5 Billing Verification Drill
type: runbook
owner: '@hu3mann'
date: '2026-04-01'
author: '@codex'
prelude: Single-partition spend verification drill for comparing v5 cost estimates
  against provider-side billing or export data.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_extraction_v5.py
  - services/repo-truth-extractor/lib/spend_ledger.py
last_review: '2026-04-01'
next_review: '2026-07-01'
---
# Repo Truth Extractor v5 Billing Verification Drill

This drill is a cheap sanity check, not a precise reconciliation system.

## Goal

Compare:

- the v5 dry-run cost preview
- the runtime spend ledger
- the cost-abort artifact when the run stops on cap
- the provider-side billing or usage export

for a single controlled partition.

## Controlled setup

Use one small phase and one isolated run root.

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --phase A \
  --dry-run \
  --print-cost-preview \
  --run-id rte_billing_probe \
  --output-root /tmp/rte-billing-drill
```

Review `/tmp/rte-billing-drill/runs/rte_billing_probe/A_repo_control_plane/inputs/COST_PREVIEW.json`.

Then execute the same small run with an explicit cap and the same run root:

```bash
DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py \
  --phase A \
  --run-id rte_billing_probe \
  --execute \
  --max-cost-usd 1.0 \
  --output-root /tmp/rte-billing-drill
```

## Compare these artifacts

- `runs/rte_billing_probe/spend_ledger.json`
- `runs/rte_billing_probe/COST_ABORT.json` when the cap is hit
- `runs/rte_billing_probe/A_repo_control_plane/inputs/COST_PREVIEW.json`
- provider-side billing, usage export, or console view for the same time window

Observed runtime behavior:

- `--max-cost-usd` is enforced before projected submit/call work and after actual runtime accumulation
- unknown model ids use the recorded conservative fallback policy rather than optimistic zero-cost handling
- batch submit and async submit reserve estimated spend at submit time
- if a breach occurs after a provider response, the current partial output is retained and the run is marked `COST_ABORTED`
- `If a run enters COST_ABORTED, resume is not allowed. Start a new run.`

`Batch cost accounting is conservative reservation accounting and not authoritative provider billing truth.`

## Record the discrepancy

Capture:

- run id
- phase
- provider and model route used
- preview estimate
- ledger estimate
- provider-reported usage or billed amount
- absolute delta
- percentage delta

Suggested note format:

```text
run_id=rte_billing_probe
phase=A
preview_estimate_usd=<value>
ledger_estimate_usd=<value>
provider_reported_usd=<value>
delta_usd=<value>
delta_percent=<value>
notes=<fallback pricing used|step override present|comparison disabled>
```

## Acceptable variance

Use this as the operator threshold for the current baseline implementation:

- `<= 20%` variance: acceptable for the current best-effort preview path
- `> 20%` variance: investigate before trusting the preview for larger live runs

Reasons for variance include:

- fallback baseline pricing for unknown model ids
- step-level route overrides
- retries
- submit-time reservation versus observed usage at finalize/watch
- provider-side billing granularity differences
- batch vs sync execution differences

## Fail-closed recommendation

If the drill exceeds the variance threshold, do not treat the current preview as
budget authority for broad live rollouts. Keep caps conservative and record the
discrepancy with the run artifacts.
