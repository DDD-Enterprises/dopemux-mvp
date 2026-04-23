---
id: adr-001
title: ADR-001 - Workflow-Centric IA and Handoff Packet Authority Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
last_review: '2026-04-23'
next_review: '2026-05-23'
prelude: Architecture Decision Record for Round 2 operator shell redesign from service-centric to workflow-centric information architecture.
---

# ADR-001: Workflow-Centric IA and Handoff Packet Authority Model

**Status**: Proposed  
**Date**: 2026-04-23  
**Owners**: @hu3mann  
**Supersedes**: v1.0 service-centric 7-tab IA (SPEC.md §11.1)  
**Blocks**: any implementation decomposition or app-shell work that assumes packet or mode state.

## Context

v1.0 of the Dopemux TUI exposed seven top-level tabs keyed to services (`Tasks`, `Decisions`, `Memory`, `Search`, `Services`, `Events`, `Overview`). The revision brief (`01_REVISION_BRIEF_PM_IMPLEMENTER.md`) reframes the top surface around operator workflow, not service surface area, and requires a dual-mode shell with PM and Implementer as first-class modes, while preserving:
- terminal-native fixed-grid constraints,
- explicit authority labeling per pane,
- bridge/proxy segregation,
- write-confirm rules,
- closed chip vocabulary,
- no HTML/DOM/web framing.

A naive reading of "PM mode" and "Implementer mode" invites the creation of a unified PM record and a unified Implementer record inside `dopemux`, which would silently centralize authority that is in fact split across `task-orchestrator`, `leantime`, `conport`, `dope-memory`, and `dope-context`. The handoff artifacts (`PKT-*`, `PKB-*`) amplify this risk: if they are modeled as new canonical objects, `dopemux` becomes a task-state authority by accident.

## Decision

1. **Top-level IA is `[1]PM [2]Implementer [3]Overview [4]Services [5]Events`.** Tasks, Decisions, Memory, and Search are demoted to supporting views reached by `g o` / `g d` / `g m` / `g s` from PM or Implementer, or by `Enter` drill-down on a pane row. They do not appear in the mode strip.

2. **PM mode and Implementer mode are operator shells, not authority tiers.** Neither mode owns a canonical record. Each pane inside each mode shows an `authority:` header and every row carries an `SRC` tag identifying the canonical service for that slice. A "task" visible in PM mode and the same "task" visible in Implementer mode are the same composite view over split authorities, not two records and not one unified record.

3. **`PKT-*` (PM→Implementer) and `PKB-*` (Implementer→PM) are authored provenance envelopes, not new authority.** Authoring identity on the envelope is `dopemux`. Every field inside the envelope is tagged with the `SRC` of the canonical service that owns it (`leantime`, `task-orchestrator`, `conport`, `dope-memory`, `dope-context`). Reading an envelope never bypasses the `SRC` tags.

4. **`[H] send` is the only action that converts a draft envelope into a sent packet.** Send is human-only, dopemux-authored, and produces exactly two mirror writes: one `conport` progress/log entry and one `dope-memory` chronicle receipt chipped `[LOGGED]`. Send does not transition `task-orchestrator` state and does not mutate `leantime` metadata.

5. **Packet lifecycle**: sent packets remain active for 30 days, then archive to history/search. Pinned packets are exempt from auto-archive. Pin state is carried on the envelope and mirrored on the chronicle receipt. The archive reaper is owned by `dopemux` and runs daily.

6. **Supporting-view mocks (§4.4–§4.7) are authoritative for pane content and geometry only.** Their port numbers are illustrative only.

## Consequences

**Accepted**:
- `dopemux` gains an authoring store for envelopes (draft/sent/pinned/archived) and for reaper scheduling. This store is not a task store.
- The integration test matrix must prove that no `[H] send` invocation ever triggers a `task-orchestrator` transition or a `leantime` write.
- The UI must surface `authority:` and `SRC` everywhere without exception; absence of either is a rendering bug.

**Rejected alternatives**:
- *Unified PM record inside dopemux*: rejected — collapses authority, violates §3.3, makes rollback of packet state ambiguous.
- *Three top-level modes (PM, Implementer, Services)*: rejected — buries Overview and Events below operator shells, breaks monitor workflows.
- *Packet send auto-transitioning task-orchestrator state*: rejected — makes the operator's handoff gesture a silent workflow mutation, violates clarification 2.

**Citations**: SPEC.md §2.4, §3.3, §11.1, §11.4; locked clarifications 1–5; revision brief constraints 1–5.

## Implementation Notes

- Grid skeleton work (step 1) is not blocked by this ADR. Authority labeling (step 8) is.
- Mock `Source` implementations can proceed in parallel until the HTTP/RPC surface (U1) is finalized.
- Integration tests must validate that `[H] send` produces exactly two writes (ConPort + dope-memory) and no side effects in other services.
