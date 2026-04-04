---
id: repo-truth-extractor-user-guide
title: Repo Truth Extractor User Guide
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-03'
last_review: '2026-04-03'
next_review: '2026-07-02'
prelude: Repo Truth Extractor User Guide (how-to) for dopemux documentation and developer
  workflows.
---
# Repo Truth Extractor User Guide

## 1. Overview

The Repo Truth Extractor (RTE) is a deterministic, multi-phase extraction engine designed to produce machine-verifiable truth maps of complex software repositories. It uses a tiered routing system to balance cost, performance, and reasoning depth across different extraction tasks.

## 2. Architecture

RTE operates in distinct phases:

- **Phase A (Audit)**: Discovery of control-plane surfaces, configuration, and service boundaries.
- **Phase H (Hygiene)**: Scan and cleanup of stale state, os artifacts, and run debris.
- **Phase D (Discovery)**: Comprehensive inventory of documents and code artifacts.
- **Phase C (Collection)**: Extraction of structured data from discovered artifacts.
- **Phase W (Wiring)**: Identification of eventbus, memory, and service-to-service links.
- **Phase R (Reasoning)**: Synthesis of high-level architectural insights and risk registre.
- **Phase B (Boundaries)**: Formal mapping of security and authority boundaries.
- **Phase G (Governance)**: Compliance and policy enforcement check.
- **Phase E (Execution)**: Verification of runtime behavior and startup graphs.
- **Phase Q (Quality)**: Final validation and artifact reconciliation.

## 3. Configuration

### model_map.yaml
Defines the routing policy and model selection for each phase and step.

### artifacts.yaml
Defines the output schema and merge strategy for each extracted artifact.

## 4. Basic Usage

### Scanning for drift
```bash
dopemux upgrades run --phase ALL --dry-run
```

### Executing an extraction
```bash
dopemux upgrades run --phase A --execute
```

## 5. Resume and Reliability

RTE is designed to be resumed. If a run is interrupted, use the `--resume` flag:

```bash
dopemux upgrades run --phase C --execute --resume
```

## 6. Hygiene and Maintenance

Run hygiene before starting a new major extraction:

```bash
python services/repo-truth-extractor/extraction_hygiene.py scan
python services/repo-truth-extractor/extraction_hygiene.py apply --apply
```

## 7. Live Validation

Validation stages:

- `preflight`
- `provider_probe`
- `batch_pilot`
- `phase_slice`
- `full_phased`

### For paid stages, provide a pricing manifest so spend caps can be enforced:

```bash
dopemux upgrades validate-live \
  --promptset-root /abs/path/to/generated/promptset \
  --stage phase_slice \
  --provider openai \
  --pricing-manifest /abs/path/to/pricing_manifest.json
```

Live validation stages that would spend money still require explicit consent:

- `--execute` on the underlying runner path
- `DPMX_LIVE_OK=1`

Use the phase-scoped confidence ramp:

1. `preflight`
2. `provider_probe`
3. `batch_pilot`
4. `phase_slice`
5. `full_phased`

If `validate-live` exits immediately with an import-origin error, the command is not running from the current checkout. Reinstall with `pip install -e ".[dev]"` or rerun with `PYTHONPATH=src`.

## 8. Interpreting stdout quickly

`PHASE_START`:

- phase, run_id, inventory count, partition count, routing policy, tier defaults

`STEP_START`:

- step id, tier (`bulk|extract|qa|synthesis`), selected route (`provider/model`)

`ESCALATE` (only on trigger):

- reason, from route, to route, hop number

`STEP_DONE`:

- ok/failed counts, hop distribution, escalated partitions count
- sync vs batch counts
- final provider/model usage counts

## 9. Output structure

Run root:

```text
extraction/repo-truth-extractor/v4/runs/<RUN_ID>/
```

Per phase:

- `inputs/` deterministic inventory and partition plans
- `raw/` partition provider outputs and trace payloads
- `norm/` merged deterministic artifacts
- `qa/` validation and reliability artifacts
- `batch/` (only when batch mode is enabled)

Top-level run files include routing fingerprint, resume proof, and run manifest.

## 10. Common failure patterns

Auth/provider failure:

- Run preflight with `--auth-doctor`
- Verify provider key env vars are present

Schema gate failures:

- Check phase `qa/PHASE_FAILURE_ROLLUP.json`
- Check `qa/PHASE_REQUEST_META_INDEX.json` for failing step/partition IDs

Excessive escalations:

- Start with `--routing-policy balanced`
- Reduce phase scope to isolate one phase

Unexpected run size growth:

- Limit scope to targeted phase
- Use dry-run first
- Keep `--resume` enabled for retries

## 11. Engine fallback

Use v3 only when needed:

```bash
dopemux upgrades run --pipeline-version v3 --phase ALL --execute --run-id rte_v3_fallback_001
```

## 12. Recommended operator workflow

1. Promptset audit
2. Provider preflight
3. Dry-run targeted phase
4. Execute with `--resume`
5. Check status
6. Run doctor and reprocess plan
7. Archive run artifacts and QA outputs
