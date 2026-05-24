---
id: fast-dev-os-templates-proof-readme
title: Fast Dev OS — Templates / Proof Bundle Skeleton
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Nav index for the templates-proof/ subdirectory — holds the canonical PROOF bundle skeleton (proof-bundle-template.json) for all Fast Dev OS packets.
---
# Fast Dev OS — Templates / Proof Bundle Skeleton

## Relationship to governance

This directory **operationalizes** [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md) and AGENTS.md §9 proof-and-finality contract; it **does not override** them.

## Lane

**L2** — the PROOF skeleton is referenced by every Fast Dev OS packet. Changes here propagate.

## Subdirectory naming

The original plan called for `docs/03-reference/fast-dev-os/proof/`. This packet uses **`templates-proof/`** instead to avoid name-collision confusion with the **repo-root `proof/`** directory (which holds the actual PROOF.json files emitted per packet). The `templates-proof/` name makes the intent explicit: these are templates *for* proof bundles, not proof bundles themselves.

## Files

| File | Purpose |
|------|---------|
| [`proof-bundle-template.json`](proof-bundle-template.json) | Schema-shaped skeleton for AGENTS.md §9-compliant PROOF.json bundles. Copy to `proof/<series>/<TP-ID>/PROOF.json` and fill each slot. |

## How to use

1. Copy `proof-bundle-template.json` to `proof/<series>/<TP-ID>/PROOF.json`.
2. Replace every `<...>` placeholder with the actual value for your packet.
3. For each `validations[]` entry, run the command and record the actual `exit_code` and `status` (PASS / FAIL / NOT_RUN — **never collapse NOT_RUN into PASS**).
4. Populate `codereview_status` and `precommit_status` after running PAL chains.
5. Populate `commit_sha`, `pr_url`, and `cleanup_status` after committing and opening the PR.
6. Enumerate `residual_risks` (with `RISK-ID` prefixes), `unknowns`, and `not_run` items honestly.

## AGENTS.md §9 required fields (cross-reference)

Every PROOF bundle MUST contain:

- `tp_path` / `tp_id` — packet identity
- `worktree_path` / `branch` / `base_branch` — git context
- `repo_identity_check` — verified repo binding result
- `slices_completed` — execution lifecycle slices with statuses
- `files_created` / `files_modified` — exact paths
- `allowlist_compliance` — result + expected vs actual counts
- `validations[]` — each with `command`, `exit_code`, `status`
- `codereview_status` — verdict + tool + model + issues
- `precommit_status` — verdict + tool + model
- `commit_sha` — 40-char SHA
- `pr_url` — GitHub PR URL or `null` with `pr_blocker` explanation
- `residual_risks` / `unknowns` — explicit lists
- `cleanup_status` — worktree disposition

If a value is genuinely unknown, use `null` and document why in `unknowns`. **Do not invent values.**

## Cross-references

- AGENTS.md §9 (canonical proof requirements): [../../../../AGENTS.md](../../../../AGENTS.md).
- Task Packet skeleton: [`../task-packet-template.json`](../task-packet-template.json).
- Annotated TP walkthrough: [`../template-task-packet.md`](../template-task-packet.md).
- PR body template: [`../template-pr-body.md`](../template-pr-body.md).
- Validation library: [`../validation-command-library.md`](../validation-command-library.md).
- Governance: [`../../governance/codex-authority-refresh.md`](../../governance/codex-authority-refresh.md).

## Truth posture

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence. Distinguish observed vs inferred vs proposed vs unknown.

> If you skip a validation, record it as `NOT_RUN` with reason. Silence ≠ PASS.
