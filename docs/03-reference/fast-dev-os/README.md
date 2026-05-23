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
| [`PROJECT_CONSTITUTION.md`](PROJECT_CONSTITUTION.md) | Mission, scope, non-goals, vocabulary, boundaries vs governance | doctrine |
| [`THREAD00_CURRENT_OPERATING_LEDGER.md`](THREAD00_CURRENT_OPERATING_LEDGER.md) | Snapshot of current branch / PRs / packets / blockers at HEAD `<SHA>` | snapshot |
| [`UNKNOWN_CONFLICTING_STALE.md`](UNKNOWN_CONFLICTING_STALE.md) | UNRESOLVED authority/path drift; carries forward AGENTS.md §10 known dangers | register |
| [`PR_LEDGER.md`](PR_LEDGER.md) | Snapshot of `gh pr list --state open` cross-referenced with chat-context-v2 PR map | snapshot |
| [`PACKET_LEDGER.md`](PACKET_LEDGER.md) | Snapshot derived from `task-packets/INDEX.md` + v2 corpus TP citation graph | snapshot |
| [`PROOF_LEDGER.md`](PROOF_LEDGER.md) | Index of `proof/**/PROOF.json` with verdict and commit SHA columns | snapshot |
| [`evidence-notes.md`](evidence-notes.md) | Provenance of chat-context-v2 corpus citations (external evidence base) | reference |

## Subsequent packets in this series

The Fast Dev OS doctrine layer is built across three Task Packets (this is packet 1 of 3):

- **TP-DMX-FDOS-004-AUTHORITY-REFRESH** (this packet) — operational ledgers + project constitution.
- **TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK** — reusable prompts under `prompts/` (Codex / Claude Code / Gemini / Grok / Jules / Copilot + report / audit / acceptance templates).
- **TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES** — reusable templates under `proof/` and root (TASK_PACKET_TEMPLATE, PROOF_BUNDLE_TEMPLATE, PR_BODY_TEMPLATE, VALIDATION_COMMAND_LIBRARY, RUNTIME_DEPENDENCY_CONES).

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
