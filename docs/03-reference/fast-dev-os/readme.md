---
id: fast-dev-os-readme
title: Fast Dev OS — Operational Doctrine Layer
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Index and landing page for the Fast Dev OS operational doctrine layer that implements the governance authority refresh in day-to-day Codex/operator workflows.
---
# Fast Dev OS — Operational Doctrine Layer

This directory contains the **operational doctrine** for the Dopemux Fast Dev OS — the day-to-day operator view of what the governance layer already mandates. It is a **risk-routed, proof-gated control system** sitting on top of the existing governance layer.

## Relationship to governance

This directory **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md); it **does not override** that layer. When this layer and the governance layer conflict, the governance layer wins.

The governance layer defines the *what* (authority boundaries, label vocabulary, proof rules). The Fast Dev OS layer defines the *how* (day-to-day operator workflow, snapshot ledgers, packet/prompt templates, risk lane selection).

## Files in this directory

| File | Purpose | Class |
|------|---------|-------|
| [`project-constitution.md`](project-constitution.md) | Mission, scope, non-goals, vocabulary, boundaries vs governance | doctrine |
| [`thread00-current-operating-ledger.md`](thread00-current-operating-ledger.md) | Snapshot of current branch / PRs / packets / blockers (HEAD SHA recorded in the file's `snapshot:` frontmatter block) | snapshot |
| [`unknown-conflicting-stale.md`](unknown-conflicting-stale.md) | UNRESOLVED authority/path drift; carries forward AGENTS.md §10 known dangers | register |
| [`pr-ledger.md`](pr-ledger.md) | Snapshot of `gh pr list --state open` cross-referenced with chat-context-v2 PR map | snapshot |
| [`packet-ledger.md`](packet-ledger.md) | Snapshot derived from `task-packets/INDEX.md` + v2 corpus TP citation graph | snapshot |
| [`proof-ledger.md`](proof-ledger.md) | Index of `proof/**/PROOF.json` with verdict and commit SHA columns | snapshot |
| [`evidence-notes.md`](evidence-notes.md) | Provenance of chat-context-v2 corpus citations (external evidence base) | reference |

## Canonical templates (reusable for future packets)

| File | Purpose | Class |
|------|---------|-------|
| [`template-task-packet.md`](template-task-packet.md) | Annotated walkthrough of the canonical TP shape (field-by-field) | template |
| [`task-packet-template.json`](task-packet-template.json) | Schema-valid skeleton TP (parseable by jsonschema) | template |
| [`template-pr-body.md`](template-pr-body.md) | Canonical PR body shape (required sections + Forbidden Phrases enforcement) | template |
| [`validation-command-library.md`](validation-command-library.md) | Reusable validation snippets (jsonschema, docs hygiene, git diff, frontmatter, anti-pattern grep) | reference |
| [`runtime-dependency-cones.md`](runtime-dependency-cones.md) | Cross-workstream collision matrix (which packets cannot parallelize) | reference |
| [`templates-proof/proof-bundle-template.json`](templates-proof/proof-bundle-template.json) | AGENTS.md §9-compliant PROOF.json skeleton | template |
| [`templates-proof/readme.md`](templates-proof/readme.md) | templates-proof subdirectory nav + AGENTS.md §9 reference | reference |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| [`prompts/`](prompts/readme.md) | Reusable executor prompt pack for multi-implementer routing (Codex / Claude Code / Gemini / Grok / Jules / Copilot) plus operator-side templates (report / audit / acceptance decision). See [`prompts/readme.md`](prompts/readme.md). |
| [`templates-proof/`](templates-proof/readme.md) | Canonical PROOF bundle skeleton with AGENTS.md §9 required fields. See [`templates-proof/readme.md`](templates-proof/readme.md). |

## Subsequent packets in this series

The Fast Dev OS doctrine layer is built across three Task Packets (this is packet 1 of 3):

- **TP-DMX-FDOS-004-AUTHORITY-REFRESH** (this packet) — operational ledgers + project constitution.
- **TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK** — reusable prompts under `prompts/` (Codex / Claude Code / Gemini / Grok / Jules / Copilot + report / audit / acceptance templates).
- **TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES** — reusable templates under `templates-proof/` and root (TASK_PACKET_TEMPLATE, PROOF_BUNDLE_TEMPLATE, PR_BODY_TEMPLATE, VALIDATION_COMMAND_LIBRARY, RUNTIME_DEPENDENCY_CONES).

## Truth posture

All chat-extract evidence cited here is **chat-derived** and **NEEDS_LIVE_VALIDATION** until checked against the live repo / GitHub / runtime state. The authority order from AGENTS.md §2 applies:

1. Active Task Packet
2. Runtime code / config / tests / compose / entrypoints
3. `TRUTH_*.md` / `docs/03-reference/truth/*`
4. `RULES.md` / `PROJECT.md` / `ARCHITECTURE.md` / `SYSTEM_BOUNDARIES.md` / `PM_PLANE.md` / `SERVICE_CATALOG.md` / `SYSTEM_*.md`
5. Historical / generated / advisory / uploaded / external docs (this layer is here)

Snapshot ledgers (`THREAD00_*`, `PR_LEDGER`, `PACKET_LEDGER`, `PROOF_LEDGER`) carry explicit `snapshot:` metadata (taken_at, repo_head, refresh_policy) so they cannot be mistaken for live truth.

## Snapshot refresh

Snapshot ledgers are refreshed **manual-per-session** by re-running the authority refresh procedure (see PROJECT_CONSTITUTION.md). A future TP (deferred) may add a generator script to automate refresh.

## Out of scope for this layer

- Runtime code / service code / tests / compose / dependencies — handled in other packets.
- Cockpit display surfaces — Cockpit is a display + gate + proof surface only; not part of this doctrine layer (see Phase 4 in the executive verdict).
- GitHub PR gates / CI enforcement — Phase 3 in the executive verdict (deferred).
