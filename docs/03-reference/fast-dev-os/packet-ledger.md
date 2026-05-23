---
id: fast-dev-os-packet-ledger
title: Fast Dev OS — Packet Ledger (Snapshot)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Snapshot of Task Packets in `task-packets/` at the time this ledger was authored. Refresh via `find task-packets -name '*.json'` + `task-packets/INDEX.md`.
---
# Fast Dev OS — Packet Ledger

> **⚠️ SNAPSHOT — NOT LIVE TRUTH.** Run `find task-packets -name '*.json'` and read `task-packets/INDEX.md` for live state.

## Relationship to governance

This snapshot **operationalizes** [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md); it **does not override** that layer. When this snapshot and `task-packets/INDEX.md` conflict, `task-packets/INDEX.md` wins.

## Snapshot metadata

```yaml
snapshot:
  taken_at: '2026-05-23T02:33:00Z'
  repo_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  ledger_class: snapshot
  refresh_policy: manual-per-session
  refresh_commands:
    - 'find task-packets -name "*.json" -type f | sort'
    - 'cat task-packets/INDEX.md'
  taken_by: 'TP-DMX-FDOS-004-AUTHORITY-REFRESH (initial authoring)'
```

## Inventory at snapshot time (47 packets in `task-packets/`)

### Top-level `task-packets/` (legacy + active)

| Packet | Subsystem | Status (per INDEX.md) |
|--------|-----------|------------------------|
| TP-DMX-AGENTS-CODEX-ENDTOEND-0001 | Agent Guidance | Ready |
| TP-DMX-COMPOSE-RESTORE-001 | Infra | Ready |
| TP-DMX-MCP-DATA-ASSEMBLY-001 | MCP | (see INDEX.md) |
| TP-DMX-MCP-REPO-SCOPED-TASK-ORCHESTRATOR-001 | MCP | (see INDEX.md) |
| TP-DMX-REPAIR-TEST-WARNINGS-5374 | Tests | (see INDEX.md) |
| TP-DMX-REPAIR-TESTS-5374 | Tests | (see INDEX.md) |
| TP-DMX-REPOHYG-001..008 | Repo Hygiene | Ready (all 8) |
| TP-DMX-RTEAUDIT-001 / -110 | Repo Truth Extractor | Ready / (see INDEX) |
| TP-DMX-RTECANON-001 | RTE | Ready |
| TP-DMX-RTEINT-001 | RTE | Ready |
| TP-DMX-RTEOPUS-AUDIT-DOCS-001 | RTE | Active |
| TP-OPS-MAC-SCRUBBER-001 | Ops | (see INDEX) |
| DMX-COCKPIT-ARCHIVE-INTENT-001 | Cockpit | (see INDEX) |
| DMX-COCKPIT-PM-TEXTUAL-001 | Cockpit | (see INDEX) |
| DMX-COCKPIT-PMIMPL-PACK-001 | Cockpit | Ready |

### `task-packets/generated/` (29 packets)

| Packet | Subsystem | Status |
|--------|-----------|--------|
| TP-DMX-CODEX-REFRESH-001-AUTHORITY-MATRIX | Governance | MERGED (PR #662) |
| TP-DMX-CODEX-REFRESH-002-OPERATOR-RUNBOOK | Governance | MERGED (PR #666) |
| (TP-DMX-CODEX-REFRESH-003-PROOF-PACKET-TEMPLATES) | Governance | MERGED at `8e7a2283f` (PR #667) — present as commit content; separate JSON not surfaced in inventory |
| TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP | Fast Dev OS | AUTO-MERGE QUEUED (PR #668) |
| **TP-DMX-FDOS-004-AUTHORITY-REFRESH** | **Fast Dev OS** | **THIS PACKET** |
| TP-DMX-COCKPIT-DESIGN-PICKUP-001 | UI Cockpit | Active |
| TP-DMX-COCKPIT-INVENTORY-REGEN-001 | UI Cockpit | Active |
| TP-DMX-COCKPIT-MAIN-STATE-RECON-001 | UI Cockpit | Executed |
| TP-DMX-COCKPIT-MERGE-EXECUTE-001 | UI Cockpit | Blocked Preflight |
| TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001 | UI Cockpit | Active |
| TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001 | UI Cockpit | Active |
| TP-DMX-COCKPIT-RUNTIME-RENDER-001 | UI Cockpit | Active (chat-conflict — see UNKNOWN_CONFLICTING_STALE §2) |
| TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 | UI Cockpit | Active |
| TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 | UI Cockpit | Active |
| TP-DMX-DOCS-FORGE-001..004 | Docs | (see INDEX) |
| TP-DMX-DOCS-PUBLIC-AI-RTE-BASELINE-001 | Docs | MERGED (PR #660) |
| TP-DMX-MOBILE-TUI-SPEC-001 | UI Cockpit | Active (MERGED via PR #665) |
| TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001 | RTE | Active |
| TP-RTE-V3-CONSENT-004 | RTE | Active |
| TP-RTE-WALKER-006 | RTE | Active |
| TP-RTE-BATCH-005 | RTE | MERGED (PR #614) |
| TP-RTE-BATCH-E2E-006 | RTE | MERGED (PR #615) |
| TP-RTE-DOCS-CANON-008 | RTE | Active |
| TP-RTE-SAFE-INTROSPECTION-001 | RTE | Active |
| TP-RTE-STRICT-ATTESTATION-007 | RTE | MERGED (PR #616) |

## Planned next packets in DMX-FDOS series

| Packet | Status |
|--------|--------|
| **TP-DMX-FDOS-004-AUTHORITY-REFRESH** | THIS PACKET (in worktree) |
| TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK | PLANNED — depends on TP-FDOS-004 landing |
| TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES | PLANNED — depends on TP-FDOS-004 + 005 landing |
| (TP-DMX-FDOS-007-GITHUB-GATES) | DEFERRED to a future plan |
| (TP-DMX-FDOS-008-COCKPIT-PROOF-GATES) | DEFERRED |

## Cross-reference: chat-context-v2 TP conflicts

8 TPs have status conflicts in the chat-context-v2 corpus. See [`unknown-conflicting-stale.md §2`](unknown-conflicting-stale.md). Three are TRUE_CONTRADICTION_OR_REGRESSION requiring live validation: `TP-DMX-COCKPIT-RUNTIME-RENDER-001`, `TP-DT-CLAUDE-RUNNER-ASSEMBLY-0001`, `TP-DT-CLAUDE-PREFLIGHT-0001`.

## Phantom-dependency cleanup

`TP-DMX-FDOS-002-IMPLEMENTER-PROMPTS` was declared as a `depends_on` of TP-FDOS-003 but **never existed** (verified via `git log --all --remotes`, `gh pr list --state all`, `find`, `proof/`). Cleared via PR #668 refresh commit `66b05840d` (depends_on → `[]`, series.parent_tp_id → `null`).

## Truth posture

Status values are chat-derived from `task-packets/INDEX.md` at snapshot time. Always read `task-packets/INDEX.md` live before treating any status as current.
