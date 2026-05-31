---
id: autoreview-loop
title: Autoreview Loop
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Offline autoreview loop contract for PR Steward, Action Bridge, Copilot
  repair packets, and independent embedded audit.
---
# Autoreview Loop

The autoreview loop is a read-only, deterministic governance lane:

1. PR Steward classifies a harvested PR fixture and emits check-only artifacts.
2. Action Bridge reads those artifacts from disk and writes `ACTION_PLAN.json`.
3. Copilot repair generation maps implementer-role actions into a bounded
   `CopilotRepairPacket` and renders the governed PR repair template.
4. Independent embedded audit emits a schema-valid proof object with redacted
   provenance.
5. PR Steward re-intake verifies the final harvested state.

The offline fixture in `tests/fixtures/autoreview/offline_pr/` exercises the
implemented path without live GitHub calls, posting, approval, merge, readiness
mutation, check mutation, or `tools.pr_merge` imports.

## Contract

- All stages preserve `mutation_performed: false`.
- Copilot authority remains `implementer-only`.
- The embedded-audit proof author is `independent-embedded-audit`, not PR
  Steward, Action Bridge, or the merge engine.
- Token values are never recorded; only redacted token availability provenance
  may be recorded.
- Supervisor-role and CI-role items are not rendered into the Copilot repair
  packet.

## Fixture Shape

`initial/harvest.json` contains a required failed check and produces
`NEEDS_IMPLEMENTER`.

`audit/PAL_CLINK_AUDIT_OUTPUT.json` contains a deterministic PASS verdict used by
`scripts/audit/run_embedded_audit.py` for offline proof generation.

`final/harvest.json` contains the same PR head SHA with the required check
passing and embedded audit status PASS, producing `READY`.

## Validation

Run:

```bash
pytest -q tests/integration/test_autoreview_loop.py
```

The test is intentionally offline. It proves wiring, deterministic artifacts, and
governance pins; it does not prove live GitHub behavior or live PAL clink
execution.
