---
id: rte-live-certification-gates
title: Rte Live Certification Gates
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-16'
last_review: '2026-04-16'
next_review: '2026-07-15'
prelude: Rte Live Certification Gates (reference) for dopemux documentation and developer
  workflows.
---
# RTE Live Certification Gates

`CERTIFICATION_RESULT.json` is the machine-readable split-gate result emitted by the RTE runtime when evidence is available.

Gate meanings:

- `canonical_runner_correctness`: static/internal validation of the canonical RTE runner and its certification writer.
- `live_provider_readiness`: live provider probe evidence from doctor or provider-preflight output.
- `artifact_contract_stability`: presence and shape of the core evidence artifacts (`PROOF_PACK.json`, `COVERAGE_ROLLUP.json`, `RESUME_PROOF.json`, `RUN_DASHBOARD.json`, `STEP_METRICS.json`, `FAILURE_INDEX.json`).
- `operator_topology_resilience`: doctor or topology evidence for the operator/control surface.

Status meanings:

- `PASS`: evidence was exercised and the gate passed.
- `FAIL`: evidence was exercised and the gate failed.
- `UNKNOWN`: the gate was not exercised, or the evidence was insufficient to prove it.

The operator summary report is `reports/rte-production-certification-status.json`. It should mirror the split-gate model and must not collapse unknown gates into a single overall GO claim.
