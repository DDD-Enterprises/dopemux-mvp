---
id: fast-dev-os-unknown-conflicting-stale
title: Fast Dev OS — UNKNOWN / CONFLICTING / STALE Register
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Register of unresolved authority/path drift, conflicts, and stale-risk claims that must be carried forward (not silently smoothed) into Fast Dev OS day-to-day operation.
---
# Fast Dev OS — UNKNOWN / CONFLICTING / STALE Register

> **This register must never be silently emptied.** When you resolve an entry, document the resolution and move it to the changelog at the bottom — do not simply delete it.

## Relationship to governance

This register **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md) (which itself defines the `UNKNOWN` / `CONFLICTING` / `OBSERVED` / `RECOMMENDED` vocabulary) plus [`AGENTS.md`](../../../AGENTS.md) §10 (known dangers). It **does not override** either source.

## Snapshot metadata

```yaml
snapshot:
  taken_at: '2026-05-23T02:35:00Z'
  repo_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  ledger_class: register
  refresh_policy: manual-per-session and on-resolution
  taken_by: 'TP-DMX-FDOS-004-AUTHORITY-REFRESH (initial authoring)'
```

## §1 — AGENTS.md §10 known dangers (CARRIED FORWARD AS UNRESOLVED)

Cited verbatim from `AGENTS.md §10`. These are repo-level dangers that Codex/agent work must respect.

| ID | Class | Description | Source | Resolution status |
|----|-------|-------------|--------|-------------------|
| AGENTS-§10-1 | UNKNOWN/CONFLICTING | `dopecon-bridge` exposes broad surfaces that can look authoritative, but it is only bridge/proxy/event transport. | AGENTS.md §10 | UNRESOLVED — preserve as adapter/proxy boundary only |
| AGENTS-§10-2 | CONFLICTING | Task-orchestrator runtime authority is conflicted across `services/task-orchestrator/app/main.py`, `services/task-orchestrator/task_orchestrator/app.py`, and Docker wiring. | AGENTS.md §10 | UNRESOLVED — see `codex-authority-refresh.md` Task Orchestrator row |
| AGENTS-§10-3 | CONFLICTING | Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`. | AGENTS.md §10 | UNRESOLVED — see `codex-authority-refresh.md` dope-memory row |
| AGENTS-§10-4 | UNKNOWN | Agent responsibilities are duplicated across multiple families, and agent authority is UNKNOWN. | AGENTS.md §10 | UNRESOLVED — see `codex-authority-refresh.md` agents row |
| AGENTS-§10-5 | CONFLICTING | `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language. | AGENTS.md §10 | UNRESOLVED — see `codex-refresh-gap-register.md` |
| AGENTS-§10-6 | CONFLICTING | MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets. | AGENTS.md §10 | UNRESOLVED |

**Do not silently resolve these.** Any work that purports to close one of these must be explicit in its packet body and produce runtime/source evidence.

## §2 — Cross-packet PR/TP conflicts (advisory; from chat-context-v2 corpus)

Source: [`/Users/hue/Downloads/dopemux-chat-context-v2/04_reconciled/CROSS_PACKET_CONFLICTS.md`](../../../../Downloads/dopemux-chat-context-v2/04_reconciled/CROSS_PACKET_CONFLICTS.md) (external evidence base; see [`evidence-notes.md`](evidence-notes.md)).

The chat-context-v2 reconciliation pass detected 6 PR conflicts and 8 TP conflicts where multiple chat sessions gave different normalized status claims for the same artifact. Most were classified as TIMELINE_PROGRESSION (auto-resolvable by trusting the latest packet); a few are true contradictions requiring live validation.

| Artifact | Class | Conflict | Resolution per chat reconciliation |
|----------|-------|----------|------------------------------------|
| PR #603 | TIMELINE_PROGRESSION | OPEN → OTHER → MERGED across chat packets 017→018→019 | Use latest (MERGED). Live-validate against `gh pr view 603`. |
| PR #605 | TIMELINE_PROGRESSION | OTHER → OPEN → MERGED across packets 018→019→020 | Use latest (MERGED). Live-validate. |
| PR #606 | TRUE_CONTRADICTION_OR_REGRESSION | BLOCKED in packet 018, MERGED in packet 020 | LIVE-VALIDATE required to determine truth. |
| PR #665 | TIMELINE_PROGRESSION | OPEN → MERGED | Use latest (MERGED). |
| PR #663 | TIMELINE_PROGRESSION | OPEN → MERGED | Use latest. |
| PR #568 | TIMELINE_PROGRESSION | MERGED + ACTIVE | Use latest. |
| TP-RTE-V3-CONSENT-004 | TIMELINE_PROGRESSION | PROPOSED → IMPLEMENTED → ACCEPTED_MERGED | Use latest. |
| TP-RTE-WALKER-006 | TIMELINE_PROGRESSION | similar | Use latest. |
| TP-RTE-BATCH-005 | TIMELINE_PROGRESSION | similar | Use latest. |
| TP-DT-CLAUDE-ADAPTER-0001 | TIMELINE_PROGRESSION | PROPOSED → ACCEPTED | Use latest. |
| TP-DMX-COCKPIT-SAFE-ACTIONS-001 | TIMELINE_PROGRESSION | similar | Use latest. |
| TP-DMX-COCKPIT-RUNTIME-RENDER-001 | TRUE_CONTRADICTION_OR_REGRESSION | conflicting status claims | LIVE-VALIDATE. |
| TP-DT-CLAUDE-RUNNER-ASSEMBLY-0001 | TRUE_CONTRADICTION_OR_REGRESSION | conflicting | LIVE-VALIDATE. |
| TP-DT-CLAUDE-PREFLIGHT-0001 | TRUE_CONTRADICTION_OR_REGRESSION | conflicting | LIVE-VALIDATE. |

**Truth posture**: all of the above are **chat-derived**. Treat as advisory until live `gh pr view <N>` or `task-packets/INDEX.md` lookup confirms the current state.

## §3 — Fast Dev OS layer-local risks

Recorded during this packet's authoring.

| ID | Class | Description | Mitigation in this layer |
|----|-------|-------------|--------------------------|
| FDOS-RISK-SCHEMA | UNKNOWN | `dopetask-canonical-spec.json` `execution.agent` enum is `{gemini, codex, vibe, shell}` — does not include `claude_code` or `jules`. | Plan uses `execution.agent: "codex"` for schema compliance; operator may run via Claude Code in practice. Future TP-DMX-FDOS-SCHEMA-EXTEND deferred. |
| FDOS-RISK-OVERLAP | UNKNOWN | `docs/03-reference/governance/codex-authority-refresh.md` already exists. Risk of duplicating its content here. | Every fast-dev-os doc includes "Relationship to governance" section pointing back and stating "operationalizes, not overrides." |
| FDOS-RISK-EXTERNAL-EVIDENCE | UNKNOWN | `/Users/hue/Downloads/dopemux-chat-context-v2/` is outside the repo; reviewers won't have it. | `evidence-notes.md` documents provenance + selection criteria; critical excerpts inlined where needed. |
| FDOS-RISK-FDOS-002 | RESOLVED | TP-DMX-FDOS-002-IMPLEMENTER-PROMPTS declared as `depends_on` of TP-FDOS-003 but never existed. | PR #668 cleanup patch (`66b05840d`) cleared the phantom dependency. Disposition: NEVER-EXISTED (full evidence in TP-FDOS-003 PROOF.json `refresh_log`). |
| FDOS-RISK-SNAPSHOT-STALENESS | STALE-RISK | PR/PACKET/PROOF ledgers are static markdown snapshots; they go stale on next merge. | Every snapshot ledger carries explicit `snapshot:` metadata block. Generator script enhancement deferred. |
| FDOS-RISK-PR-668-CREEP | RESOLVED | PR #668 refresh must not include fast-dev-os scaffolding. | Refresh respected: only TP-003 JSON depends_on patch + PROOF.json refresh_log added; zero fast-dev-os scaffolding leaked in. |
| FDOS-RISK-DOC-NAV | UNKNOWN | New docs may be invisible if not registered in repo's nav system. | TP-FDOS-004 allowlist includes `docs/INDEX.md` and `docs/docs_index.yaml` single-line additions. `docs/00-MASTER-INDEX.md` deferred (intrusive). |

## §4 — Cross-packet open questions (multi-packet UNKNOWNs from v2 corpus)

Source: [`/Users/hue/Downloads/dopemux-chat-context-v2/04_reconciled/RECONCILED_MASTER_LEDGER.md`](../../../../Downloads/dopemux-chat-context-v2/04_reconciled/RECONCILED_MASTER_LEDGER.md) §5.

The chat-context-v2 reconciliation found multi-packet UNKNOWNs (questions multiple chat sessions independently flagged). These are **priority resolution targets** — independent recurrence is signal.

| UNKNOWN (truncated) | First flagged in | Recurrences |
|---------------------|-------------------|-------------|
| dope-context migration branch identity | chat packet 061 | multiple |
| DopeContext current implementation location and schema | packet 057 | multiple |
| Current Dopemux UI stack technology | packet 058 | multiple |
| RIGUP/dNh CRM repo path/name | packet 047 | multiple |
| Current Textual/Bubbletea/Sampler maintenance status | packet 058 | multiple |
| Uberslicer UBERSLICER_ONLY_REPO physical location | packet 052 | multiple |
| Final file count for dopamine engine package: 11 vs 12/13 | packet 051 | multiple |

These are advisory and reflect chat-session-local uncertainties. Live validation against current repo is the resolution path.

## §5 — Resolution changelog

When an entry is resolved, log it here (do not delete from above):

| Date | Entry | Resolution |
|------|-------|------------|
| 2026-05-23 | FDOS-RISK-FDOS-002 | Cleared via PR #668 refresh commit `66b05840d`. Full evidence in `out/chatgpt-project-upload-set/.../PROOF.json` `refresh_log`. |
| 2026-05-23 | FDOS-RISK-PR-668-CREEP | Refresh kept scope tight; zero fast-dev-os scaffolding in PR #668 final diff. |

## Truth posture

This register is **chat-derived + repo-authored**. Cells marked CARRIED FORWARD AS UNRESOLVED come from `AGENTS.md §10` (authoritative). Cells from `chat-context-v2` are advisory. New layer-local risks were recorded by TP-DMX-FDOS-004. Always check live repo evidence before treating any entry as settled.
