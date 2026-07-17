---
id: adr-mcpint-005
title: 'ADR-MCPINT-005: Shelved MCP Features (Combined Record)'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Formally shelves six planned-or-stubbed MCP features (Milvus semantic search, Zep, sprint auto-planning, multi-team coordination, the MCF fabric, and the memory semantic projection) with explicit revival conditions; records what G3/G4 deliberately kept OFF this shelf.
status: proposed
graph_metadata:
  node_type: ADR
  impact: low
  relates_to:
    - adr-mcpint-001
    - adr-mcpint-002
    - adr-mcpint-003
    - adr-mcpint-004
    - adr-memory-trinity-authority-and-interaction-model
    - adr-dope-context-as-search-and-retrieval-plane
---

# ADR-MCPINT-005: Shelved MCP Features (Combined Record)

**Status**: Proposed
**Date**: 2026-07-16
**Owners**: @hu3mann (program DMX-MCPINT, root `af10eefd`)

## Context

The P1 feature register (`docs/03-reference/mcp/feature-register.yaml`, 162 entries)
carries six entries with `status: shelved` and `decision: adr:adr-mcpint-005`. A shelf
without an ADR is how features become zombie backlog: re-proposed every audit, half-built
twice, deleted never. This ADR is the single durable record of **what** is shelved,
**why**, and **what would revive it** — one paragraph each, no re-litigation elsewhere.
Shelving here means: no packet, no catalog entry, no instruction-surface mention as
available capability; code stubs are inert and may be deleted by hygiene packets without
further decision.

## Decision

The following six features are SHELVED.

### 1. CONPORT-SEMSEARCH-MILVUS (including `mem.upsert`)

Vector semantic search and embedding-write inside ConPort (`mem.search`/`mem.upsert`,
Milvus + Voyage/OpenAI embeddings; stub verified at `src/conport/memory_server.py`
:905-930). Shelved because Milvus was never deployed and — decisively — semantic retrieval
is dope-context's plane: a second vector search inside the decision authority violates the
Memory Trinity boundary (adr-memory-trinity-authority-and-interaction-model,
adr-dope-context-as-search-and-retrieval-plane) and duplicates embedding spend. ConPort
semantic recall is already served by dope-context indexing ConPort projections
(DMX-MEMSPINE-DCINDEX-006 / Trinity Rule 2). **Revival condition**: a Trinity-boundary
revision ADR plus deployed vector infrastructure plus a demonstrated retrieval need that
dope-context provably cannot serve.

### 2. CONPORT-ZEP

Zep conversational-memory integration in ConPort — a config-only stub
(`src/conport/memory_server.py:113`), never implemented. Shelved for the same boundary
reason as #1 plus zero implementation to preserve: conversational memory is the chronicle
plane (dope-memory), not the decision plane. **Revival condition**: an explicit
conversational-memory requirement that neither dope-memory's chronicle/recap nor
dope-context recall satisfies, argued in its own ADR.

### 3. TO-SPRINT-AUTOPLAN

Task-orchestrator sprint auto-planning (`automate_sprint_planning`). Shelved because it is
genuinely unbuilt end-to-end and its hard dependency does not exist: ConPort has no sprint
API. **Revival condition**: a sprint API lands via the ConPort surface work (owner:
DMX-ARCH-CONPORT-SURFACE-002 — not requested from it here) *and* an operator actually asks
for automated sprint planning; both, not either.

### 4. TO-MULTITEAM

Multi-team coordination (`services/task-orchestrator/multi_team_coordination.py`, batched
comms ≤3/day) — dormant-by-design in a single-operator MVP. Shelved to formalize the
dormancy so audits stop counting it as stranded capability. **Revival condition**: a
second human operator/team actually onboards to this deployment; until a real second team
exists there is nothing to coordinate.

### 5. MCF-FABRIC (children escaped)

The full Memory Context Fabric orchestration layer
(capture→redact→dedup→route→promote→retrieve→inject; `context.recall`/`context.recap`;
proactive injection) — design-only, NO-GO (register MCF-FABRIC;
`claudedocs/memory-context-fabric-design-2026-07-04.md`). Shelved because the fabric
duplicates, in one new orchestrator, seams that now have narrower owners: injection is
ADR-MCPINT-003's closed channel list, ingress is ADR-MCPINT-004's door, retrieval is
dope-context. **Two children escaped the shelf and stay live**: TP-MCF-004 (SessionStart
recap) ships as MCPINT-IMP-RECAP-003 = ADR-MCPINT-003 block 2; TP-MCF-006 (ConPort graph
on active runtime) is `held` pending DMX-ARCH-CONPORT-SURFACE-002 outcomes. **Revival
condition**: the MEMSPINE spine is complete *and* the ADR-MCPINT-003 channel list is
demonstrated insufficient for a concrete recall need — argued as a superseding ADR to
ADR-MCPINT-003, not a resurrection of the fabric design as-is.

### 6. TP-MCF-005

Derived `memory_{hash}` semantic projection (`index_memory`/`search_memory` in
dope-context). Shelved on a **privacy NO-GO**: it ships private memory content to an
external embedding provider (Voyage). **Revival condition**: its own dedicated ADR with
either local/self-hosted embeddings or an explicit, operator-signed privacy waiver —
revival explicitly may not ride a routine packet.

### Deliberately NOT on this shelf

- **Serena ADHD/intel family** (F001, SERENA-ADHD-INTEL, SERENA-ADHD-CAPS,
  SERENA-ANALYTICS, SERENA-COMPLEXITY-BANDING): **unshelved by G3** — ships as the
  `dope-adhd` surface on adhd-engine (31 tools / 9 drops) per ADR-MCPINT-001 §5 and the
  placement map. Their earlier shelve-candidacy is void.
- **TO-PREDRISK**: **not shelved** — G4 chose the flag-gated 2-week pilot
  (MCPINT-IMP-RISK-005, ADR-MCPINT-003's sanctioned exception). It lands on this shelf
  only if the pilot is killed, via a one-line amendment here.
- **MCP-CAPTURE** is retired (deleted as a surface), not shelved — recorded in
  ADR-MCPINT-004; its dedup/audit ideas fold into `capture_client`.
- **claude_brain** is `held` (assess-or-shelve, placement map §3), pending its own
  register decision — listed here only so its absence is not read as an oversight; if no
  consumer emerges it joins this shelf by amendment.

### Invariants

- A shelved feature has no packet, no catalog presence, no instruction-surface presence,
  and its register entry stays `status: shelved` with `decision: adr:adr-mcpint-005`.
- Revival happens only through the named condition + an ADR (amendment or supersession),
  never through a packet quietly re-scoping it.
- Hygiene packets may delete shelved stubs' code without a new decision (the shelf record,
  not the stub, is the durable artifact).

### Non-goals

- Deleting code (owners: DMX-HYG-DEADSVC-001 and related hygiene packets).
- Re-deciding anything G3/G4 kept alive.

## Alternatives Considered

- **One ADR per shelved feature.** Rejected: six near-identical low-impact records bloat
  the ADR set; the register already carries per-entry state, this ADR supplies the
  rationale and revival conditions in one place.
- **Shelve implicitly (register-only, no ADR).** Rejected: register `status:` fields
  without a decision record are exactly how features got re-proposed across the 2026-07-03
  and 07-04 audits; the shelf needs an authority to point at.
- **Delete instead of shelve.** Rejected for these six: deletion is a hygiene action on
  code, not a decision state; two items (MCF, TP-MCF-005) have real future-revival shapes
  that deserve preserved rationale, and deletion without a record invites rebuild-by-
  amnesia (the BUILT-UNWIRED cycle).
- **Shelve the G3 family / TO-PREDRISK too** (the triage-time candidates): rejected by the
  user's actual gate answers — G3 unshelved the ADHD family into `dope-adhd`; G4 chose
  pilot-over-shelve.

## Consequences

- The register's 6 `shelved` entries gain their decision authority; the triage memo §3
  list is fully discharged.
- Audits and future planning passes treat these as CLOSED unless the named revival
  condition is met — reducing re-triage noise (the ADHD-audit "aspirational features
  re-counted every cycle" failure mode).
- Hygiene packets (DMX-HYG-DEADSVC-001 et al.) may prune the stubs (`memory_server.py`
  Milvus/Zep blocks, `multi_team_coordination.py`) citing this ADR — no per-file decision
  needed.
- Cost: revival friction is deliberately high (condition + ADR). That is the point; the
  program's dominant failure mode was capability built without a wiring decision.
- Packet linkage: no MCPINT-FND/IMP packet implements this ADR (it is a record);
  MCPINT-FND-REGISTER-GATE-006's contract test should assert the six entries remain
  `shelved`+`adr:adr-mcpint-005` so drift is CI-visible.

## Migration Strategy

None required — this ADR changes decision state, not runtime state. Register already
matches; the contract test (FND-REGISTER-GATE-006) locks it.

## Verification

- `tests/arch/test_feature_register_contract.py` (FND-REGISTER-GATE-006): the six ids
  carry `status: shelved`, `decision: adr:adr-mcpint-005`; F001/SERENA-ADHD-* do **not**.
- Docs-phase gate: no instruction surface advertises `mem.search`/`mem.upsert`, Zep,
  sprint auto-planning, multi-team tools, `context.recall`/`context.recap`, or
  `index_memory`/`search_memory` as available.

## Validation

- **PAL consensus**: NOT_RUN for this ADR — the Phase-2 consensus pass covers the
  load-bearing pair (ADR-001/ADR-002); this ADR receives consensus review at
  merge/acceptance. See the program note appended to ADR-MCPINT-001.
- ConPort `log_decision`: owed at acceptance.

## Cross-references

- ADR-MCPINT-001 (G3/G5 dispositions that kept things OFF this shelf), ADR-MCPINT-002,
  ADR-MCPINT-003 (channel list MCF would have duplicated; TP-MCF-004's landing place),
  ADR-MCPINT-004 (mcp-capture retirement; DMEM-EVENT-DEDUP absorption).
- adr-memory-trinity-authority-and-interaction-model,
  adr-dope-context-as-search-and-retrieval-plane (the boundary doctrine behind #1/#2/#6).
- `docs/03-reference/mcp/tool-placement-map.md` §3 (claude_brain HOLD; gptr dead-twin
  tools stay shelved with their home named).
- Register: CONPORT-SEMSEARCH-MILVUS, CONPORT-ZEP, TO-SPRINT-AUTOPLAN, TO-MULTITEAM,
  MCF-FABRIC, TP-MCF-005 (+ escaped children TP-MCF-004, TP-MCF-006).
- Triage memo: `claudedocs/mcp-feature-triage-2026-07.md` §3.
