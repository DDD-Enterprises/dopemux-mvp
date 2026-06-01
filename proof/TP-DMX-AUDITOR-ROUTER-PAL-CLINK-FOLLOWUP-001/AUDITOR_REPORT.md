# Auditor Report — TP-DMX-AUDITOR-ROUTER-PAL-CLINK-FOLLOWUP-001

Verdict: `PASS_WITH_RISKS`

Embedded review performed via `mcp__pal__codereview` (expert model `gpt-5.2`, `review_type=full`),
conducted by the Claude Code agent (`opus`). This mirrors the established repo convention for
embedded audits on this series (see `proof/TP-DMX-PAL-CLINK-RUNNER-003/PROOF.json`). It is **not**
an independent cross-vendor PAL-clink run; no audit-safe external CLI was available in this
environment (the same sandbox constraint documented in the PR #713 audit).

## Scope

Remediates two defects found by the read-only audit of merged PR #713
(`claudedocs/pr713-auditor-router-pal-clink-audit-2026-05-30.md`):

- **F2** — `build_pal_clink_embedded_audit_object` could emit `auditor_model="unknown"` under a
  non-`SKIPPED` status, violating `schemas/proof/embedded_audit.schema.json` `allOf[1]`. This was
  the external clink auditor's own required fix on PR #713, shipped unactioned.
- **F8** — three security-hardening tests used `from auditor_router.pal_clink …` (missing the
  `tools.` prefix) and failed under canonical pytest; they were also never collected by the
  required CI Unit Tests job.

## Fix

- Guard at the single choke-point: when the resolved auditor model is `"unknown"` (no audit-safe
  underlying CLI) and the status would be non-`SKIPPED`, emit a schema-valid `SKIPPED` embedded
  audit instead. `SKIPPED` remains blocking in `tools/pr_steward/classifier.py`
  (`BLOCKING_AUDITS`), so fail-closed behavior is preserved. The original status is recorded in
  `skip_reason` and a blocking marker is prepended to `remaining_risks`.
- Corrected the 3 import paths and added regression coverage (`assert_schema_valid` on the
  unproven/unknown-model path, across statuses, plus a proven-route-unaffected case).

## Review outcome (pal/codereview gpt-5.2)

All five requested checks validated: schema-validity of both branches, fail-closed preservation,
no regression to existing (proven-route) normalize callers, contained blast radius, correct test
additions. No correctness blockers. Observability suggestions (embed original status in
`skip_reason`; prepend blocking marker to `remaining_risks`; explicit SKIPPED-field assertions in
the builder test) were adopted. One suggestion (key the guard off `underlying_cli` instead of the
resolved model) was declined with rationale: keying off `auditor_model == "unknown"` mirrors the
exact schema invariant and auto-corrects if `_embedded_audit_model` later maps a new CLI to a real
model. One pre-existing annotation nit was deferred as out of scope.

## Nonblocking Risks

- Embedded audit via codereview, not independent cross-vendor clink (env-constrained).
- F2 is latent (no production caller invokes `normalize_pal_clink_audit_output` yet).
- `tests/auditor_router/` is still not in the required CI Unit Tests job (tracked as F8 in the
  audit report; recommended follow-up).
