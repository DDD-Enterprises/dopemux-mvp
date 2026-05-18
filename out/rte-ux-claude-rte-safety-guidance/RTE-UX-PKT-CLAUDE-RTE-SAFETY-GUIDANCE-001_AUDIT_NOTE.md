---
id: RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001
title: RTE UX Claude RTE Safety Guidance Audit Note
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Audit note for the Claude and agent-facing RTE safety guidance packet.
---
# RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001 Audit

## What Changed

- Added a dedicated `REPO TRUTH EXTRACTOR SAFETY INVARIANTS` block to
  `.claude/PROJECT_INSTRUCTIONS.md`.
- Added a matching `RTE Safety Invariants` section to `AGENTS.md` so
  non-Claude agent-style work inherits the same rules.
- Created the packet file at
  `task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md`.
- Created this audit note and the proof JSON for the packet.

## What Did Not Change

- No `src/**` files were edited.
- No `services/**` files were edited.
- No `promptsets/**` files were edited.
- No `schemas/**` files were edited.
- No routing, pricing, provider, live-extraction, dispatch, or runtime behavior
  was changed.
- No provider calls were run.
- No live extraction, live preflight, network/provider validation, or
  account-specific checks were run.
- Follow-on packet work was not started.

## Authority Read

- `AGENTS.md`
- `.claude/PROJECT_INSTRUCTIONS.md`
- `.claude/brand-voice-guidelines.md`
- `docs/03-reference/governance/rules.md`
- `docs/03-reference/truth/truth-canonicals.md`
- `docs/03-reference/truth/truth-scope.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_MANIFEST.json`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_PACKET_SEQUENCE.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_ACCEPTED_SCOPE.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_VALUATION_MATRIX.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_DEFERRED_ITEMS.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_NO_RUNTIME_CHANGE_ATTESTATION.md`
- `proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json`
- `out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `.pre-commit-config.yaml`

## Runtime / Source Evidence Used For Guidance Only

- `src/dopemux/cli.py`: observed `dopemux rte` as the canonical operator command
  family, `validate-live` wiring, legacy/refusal surfaces, and live-run wrapper
  behavior.
- `services/repo-truth-extractor/run_extraction_v5.py`: observed the v5 runner,
  `DPMX_LIVE_OK` live-consent checks, pre-live validator integration, promptset
  preflight blocks, and first-live preset gate behavior.
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`: observed
  fail-closed blocker classes, route readiness, required API-key evidence, and
  sanitized JSON/text writes.
- `services/repo-truth-extractor/llm_runtime.py`: observed provider call guard
  behavior, payload redaction before provider calls, and redacted auth metadata.
- `services/repo-truth-extractor/output_safety.py`: observed output and provider
  payload sanitizers for secret-shaped values.
- `services/repo-truth-extractor/README.md`: observed documented live-run
  consent, first-live preset, live batch safety, provider cost warning, and
  comparison-lane separation.
- `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md`: observed RTE
  canonical command guidance, generated-artifact authority limits, and live
  validation consent requirements.
- `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md`: observed
  first-live runbook constraints, bounded-lane warning, validator-first flow, and
  route-readiness caution.

The runtime/source files above were read for grounding only. They were not
edited by this packet.

## Unknowns Preserved

- Exact Opus finding-ledger recovery is `UNKNOWN` because
  `out/rte-opus-uiux-claude-design-audit/` is absent in this worktree.
- Exact Opus recommendation-to-finding crosswalk is `UNKNOWN` without the source
  audit bundle.
- `CRIT-3` is preserved as valuation-derived, not independently recovered from
  a local Opus findings ledger.
- The exact titles for deferred `R-OPUS-12`, `R-OPUS-13`, `R-OPUS-16`,
  `R-OPUS-17`, and `R-OPUS-18` remain `UNKNOWN` in the local inputs.
- Broader repo-wide agent runtime authority remains `UNKNOWN` where no specific
  runtime path is verified.

## No-Runtime-Change Attestation

This packet changed guidance and proof artifacts only. It did not alter runtime,
provider, promptset, schema, routing, pricing, live-extraction, dispatch,
account, or validation behavior.

## Validation Results

- PASS: `python -m json.tool proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
- PASS: embedded Task Packet JSON payload validates against
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `git diff --check`
- PASS: `git status --short` and `git diff --name-only` scope review
- PASS: no `src/**` or `services/**` changes
- PASS: no `promptsets/**`, `schemas/**`, or
  `services/repo-truth-extractor/promptsets/**` changes
- PASS: no follow-on packet ids found outside excluded valuation, current
  task-packet, audit, and proof contexts
- PASS: `pre-commit run --files ...` on all touched files

## Proof Replay Cleanup (post-merge patch)

After PR #643 was squash-merged to `main` as
`0083f50a58ffa5e9d34eb3c9c620bf28076541e5`, an audit identified two replayability
issues in the original artifacts. A proof-only follow-up on branch
`codex/rte-claude-safety-proof-replay-cleanup` (from `origin/main`) patched
the following without changing runtime guidance:

- `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
  `validation_commands[1]` originally invoked the absent legacy schema
  reference with `Draft202012Validator`. It has been replaced with the
  canonical `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  path validated by `Draft7Validator`, matching the embedded task-packet
  `verify[1]` form and the schema's `$schema: draft-07/schema#`. The replay
  command now executes successfully against the merged tree.
- `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
  `rollback_plan` originally contained a pre-merge `<commit-sha>` placeholder.
  It now records that PR #643 is merged as squash commit
  `0083f50a58ffa5e9d34eb3c9c620bf28076541e5` and documents the concrete
  post-merge revert command.
- `task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md` Rollback Plan
  prose was updated to the same post-merge phrasing. The embedded task-packet
  JSON payload was not touched and still validates against the canonical
  schema.
- A `proof_replay_cleanup` block was added to `PROOF.json` recording the
  cleanup branch, the merged SHA, the patches applied, and the no-runtime,
  no-provider, no-live-extraction attestations.

The pre-squash local-branch HEAD `aa3f205072fb3ee5b935a0da72d83a56ffd8a56a`
referenced in some external notes is not present in this proof, audit, or
packet artifact text. No other artifact rollback text required correction.

This cleanup was proof and audit only. It did not change runtime, dispatch,
provider, promptset, schema, routing, pricing, live-extraction, validator,
or guidance semantics. No provider calls, live extraction, live preflight, or
network/provider validation were run.
