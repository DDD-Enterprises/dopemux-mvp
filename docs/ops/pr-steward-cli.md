---
id: pr-steward-cli
title: PR Steward CLI
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Versioned CLI contract for dopemux pr-steward.
---
# PR Steward CLI

`dopemux pr-steward` is the versioned operator surface for PR Steward.

## Help

```bash
python -m dopemux.cli pr-steward --help
python -m dopemux.cli pr-steward --contract-version
```

## Intake

```bash
python -m dopemux.cli pr-steward intake --repo OWNER/REPO --pr 123 --out out/pr/123
```

This delegates to the existing check-only `tools.pr_steward.intake` engine and
preserves its exit behavior: `0` for `READY`, `2` for blocked or failed intake.

## Bridge

```bash
python -m dopemux.cli pr-steward bridge --artifact-dir out/pr/123 --out out/pr/123/bridge
```

The bridge expects `MERGE_READINESS.json`, `REVIEW_ITEM_LEDGER.json`,
`THREAD_DISPOSITIONS.json`, and `CI_TRIAGE.json`. It writes
`ACTION_PLAN.json` and `REPAIR_PACKET.md`.

## Gate

```bash
python -m dopemux.cli pr-steward gate \
  --head-sha HEAD \
  --required-class FINALIZATION \
  --merge-readiness out/pr/123/MERGE_READINESS.json \
  --audit-proof proof/TP/PROOF.json \
  --format json
```

The gate calls packaged Python `steward_gate` code. Missing artifacts, stale
timestamps, SHA mismatch, unsupported class, or nonpassing audit status exits
with code `2`.

## Audit

```bash
python -m dopemux.cli pr-steward audit --proof proof/TP/PROOF.json --format json
```

The audit command reads a proof bundle and reports embedded-audit status. It is
read-only.

## Doctor

```bash
python -m dopemux.cli pr-steward doctor
```

`doctor` currently fails closed and points to TP-DMX-STEWARD-DOCTOR-303, where
scaffold skew and config schema checks are implemented.
