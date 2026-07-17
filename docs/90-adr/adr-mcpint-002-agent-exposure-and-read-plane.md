---
id: adr-mcpint-002
title: 'ADR-MCPINT-002: Agent Exposure Model — Codex Full Parity (Sequenced) and the DCP Facade as Universal Read Plane'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Encodes gate G1 — generated Codex config reaches full fleet parity only after per-request identity and actor authentication land; the DCP read-only facade becomes the universal read plane for all agents without attribution.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpint-001
    - adr-mcpint-003
    - adr-mcpint-004
    - adr-mcpint-005
    - ADR-DCP-MCP-RO-0009
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR-MCPINT-002: Agent Exposure Model — Codex Full Parity (Sequenced) and the DCP Facade as Universal Read Plane

**Status**: Proposed
**Date**: 2026-07-16
**Owners**: @hu3mann (program DMX-MCPINT, root `af10eefd`)

## Context

Agent×MCP configuration divergence is total (runtime verification
`claudedocs/mcp-fleet-runtime-verification-2026-07-16.md`, register
`docs/03-reference/mcp/feature-register.yaml`):

- **Claude**: full fleet (per-worktree `.mcp.json` + global singletons), plus hook-side
  governance — PreToolUse attribution block, orchestrator enforcement
  (HOOK-ORCH-ENFORCEMENT; actor auth currently **dormant** behind
  `actor_authentication.enabled`), server-side proof-bundle complete-gate.
- **Codex**: **zero** MCP servers. The Codex renderer exists
  (`src/dopemux/mcp/fleet_catalog.py:167`) but is preview-only.
- **OpenCode**: pal-only. **Gemini**: zero. **Copilot**: unproven proxy.
- **ChatGPT**: governed separately by ADR-DCP-MCP-RO-0009 (accepted): opaque `target_id`,
  `PRIMARY_CHECKOUT_ONLY`, 21 routing gates, redaction.

The purpose-built answer exists and is dark: the **DCP read-only facade** — 12 tools,
registry_v2 exposure policy, `route_manifest` ALLOWED/DENIED real enforcement, 537/539
tests green — has no compose service, no catalog entry, no port (P0 claim 8; register
DCP-FACADE, DCP-REGISTRY-V2). Three of its 12 tools (`search_code_docs`,
`get_index_status` and the dope-context-backed path) return BLOCKED because the facade is
REST-only while dope-context speaks MCP JSON-RPC (register DCP-FACADE-DCTX-BRIDGE).

Two runtime facts constrain any exposure design:

1. **N2 workspace contamination**: the primary dope-memory container carries
   `DOPE_MEMORY_WORKSPACE_ID=dNh_CRM` — another repo's workspace id — so writes attribute
   to the wrong workspace; per-project twin containers (N5) make cross-project bleed
   systemic. Env-derived identity is proven unsafe; per-request identity
   (DMX-MEMSPINE-IDENTITY-005, SVCFIN-owned) is the fix.
2. **pal `:3003/mcp` is fiction** (P0 claim 11): PAL exposure to any agent must be
   docker-exec (pal-stdio), never the cataloged HTTP URL — repaired by ADR-MCPINT-001 /
   MCPINT-FND-CATALOG-001.

A cautionary precedent for binding discipline: the retired exa server was found Up and
**world-bound `0.0.0.0:3011`** (P0 claim 15) — loopback violations on unwatched surfaces
are real, not hypothetical (loopback repair owned by DMX-HYG-LOOPBACK-002).

**Gate G1 was answered by the user on 2026-07-16: full parity for Codex** — with mandatory
sequencing (below). This supersedes the plan-of-record's interim posture ("writes stay
Claude-only until G1 says otherwise", plan D.4) — G1 has now said otherwise.

## Decision

### 1. Codex: full parity, mandatorily sequenced

The generated `.codex/config.toml` (sole producer: the ADR-MCPINT-001 generate pipeline;
packet MCPINT-IMP-CODEX-002) exposes the **full fleet** — the same server set Claude gets,
transport-corrected (pal via docker-exec).

**Mandatory sequencing — both preconditions land BEFORE the write-capable Codex config
ships:**

1. **DMX-MEMSPINE-IDENTITY-005** (SVCFIN): per-request workspace/instance identity with
   fail-closed writes on the memory spine (the N2 class of contamination becomes
   impossible, not just unlikely).
2. **Orchestrator `actor_authentication.enabled`** turned on (HOOK-ORCH-ENFORCEMENT):
   every task-orchestrator transition and note carries an authenticated actor, so Codex
   writes are attributable under the same proof-bundle governance as Claude's.

Until both land, the generated Codex config contains the **read plane only** (facade +
read-safe singletons). The `agents:` matrix value in catalog v2 records the target state
(`codex: full`); the generator enforces the precondition gate — shipping the write-capable
config with either precondition unmet is a CI-blockable contract violation.

### 2. The DCP facade: universal read plane for agents without attribution

`services/dcp-readonly-facade` is deployed (packet MCPINT-IMP-FACADE-001) as the primary —
for reads, the only — MCP surface for **OpenCode, Gemini, Copilot, and ChatGPT**, and for
Codex until its parity preconditions land:

- **Builds on ADR-DCP-MCP-RO-0009**: registry_v2 exposure policy (operator-authored,
  outside the repo), `route_manifest` ALLOWED/DENIED enforcement, opaque target ids,
  `PRIMARY_CHECKOUT_ONLY` binding, capability states, redaction rules — all incorporated
  by reference, not re-decided.
- **Compose entry is loopback-bound** (`127.0.0.1`), never `0.0.0.0` (the exa lesson,
  P0 claim 15). Remote exposure (ChatGPT) remains governed by 0009's security invariant.
- **The 3 BLOCKED dope-context-backed tools stay deferred** until a REST→JSON-RPC bridge
  exists (DCP-FACADE-DCTX-BRIDGE; note its TOOL_CONTRACT calls this its own "G1", distinct
  from MCPINT gate G1). BLOCKED is the correct fail-closed answer; the facade must not
  grow a bespoke dope-context client to dodge the bridge decision.
- Facade `search_progress` stays fail-closed behind `progress_readonly_safe` until
  ConPort's auto-fork-on-GET hazard lands its fix (COPT-107; ConPort surface owned by
  DMX-ARCH-CONPORT-SURFACE-002).

### 3. Exposure matrix (initial v2 values)

| Agent | Reads | Writes | Vehicle |
|---|---|---|---|
| claude | full | full | `.mcp.json` + global singletons (generated) |
| codex | full (facade + read-safe singletons → full at parity) | **gated on IDENTITY-005 + actor-auth** | generated `.codex/config.toml` |
| opencode | facade + read-safe singletons | none | generated `opencode.jsonc` |
| gemini | facade | none | generated fragment |
| copilot | facade | none | generated proxy yaml |
| chatgpt | facade (per 0009) | none | remote, 0009 security invariant |

"Read-safe singletons" = serena (subject to the read-only default profile decided by
DMX-ARCH-SERENA-SURFACE-003 — the P0 snapshot shows 11 write tools incl.
`execute_shell_command` live today, register SERENA-WRITE-LANE), dope-context, pal-stdio
(docker-exec). ConPort admin tools (`fork_instance`, `promote`, `promote_all`) are excluded
from every non-Claude row (placement map §3).

### Invariants

- No agent without enforced actor attribution ever holds a write-capable MCP config.
- Write acceptance is enforced at **runtime** (per-request identity + actor proof at the
  receiving service), never by config distribution alone — a generated config must not be
  the mechanism that makes writes possible, only the mechanism that makes them reachable.
- The facade is the only cross-plane read projection for non-attributed agents; adding a
  second read door for any of them supersedes this ADR.
- All facade and singleton bindings are loopback-only on this host.
- Exposure changes are catalog `agents:` edits flowing through the generate pipeline —
  never hand-edits to agent configs (ADR-MCPINT-001 invariant).

### Non-goals

- Deciding the Serena write-lane profile (owner: DMX-ARCH-SERENA-SURFACE-003).
- Deciding ConPort surface consolidation or COPT-107 (owner: DMX-ARCH-CONPORT-SURFACE-002).
- Re-deciding ChatGPT remote exposure mechanics (owner: ADR-DCP-MCP-RO-0009).
- Building the REST→JSON-RPC bridge (its own follow-on packet once transport design is
  agreed).

## Alternatives Considered

- **G1(a) — facade + read-safe singletons only (the triage REC).** Rejected by user
  decision: it leaves Codex permanently second-class in a fleet where Codex executes
  loaded packets; its governance property (no unattributed writes) is retained anyway via
  the sequencing preconditions rather than by permanent denial.
- **G1(c) — facade + a narrow TO-wrapper write lane for Codex.** Rejected: a half-measure
  needing a new wrapper packet and its own auth story; once IDENTITY-005 + actor-auth
  exist, the narrow lane is redundant with full parity.
- **Ship Codex full parity immediately, harden later.** Rejected: N2 is live proof that
  unattributed/misattributed writes actually occur; shipping writes first inverts
  fail-closed doctrine and would put unattributable events on the memory spine during the
  hardening window.
- **Per-agent bespoke configs (status quo).** Rejected: the audit's controlling finding —
  total divergence, zero shared source of truth — is exactly this alternative.

## Consequences

- **Packets**: MCPINT-IMP-FACADE-001 (deploy: compose loopback-bound, catalog active,
  registry-v2 target file, PRIMARY_CHECKOUT_ONLY, 12-tool smoke),
  MCPINT-IMP-CODEX-002 (generated configs + dry-run proof: Codex lists tools, executes a
  facade read, and a DENIED route is provably rejected), MCPINT-FND-CODEGEN-005 (renderers
  + per-target parity gates), MCPINT-FND-CATALOG-001 (facade catalog entry + pal transport
  truth). Cross-tree dependency: DMX-MEMSPINE-IDENTITY-005 (BLOCKS Codex write config;
  also blocks MCPINT-IMP-RECAP-003 per ADR-MCPINT-003).
- Codex's blindness ends in two steps (read plane now, parity at precondition-land) instead
  of one risky step.
- The facade gains a deployment vector, which means its 537-test suite finally guards a
  running surface; facade regressions become CI-visible (`/dcp:doctor`,
  `/dcp:denylist-check` skills already exist for this).
- Operating cost: one more compose service (facade) and a parity gate per agent target.
- Failure mode introduced: if IDENTITY-005 or actor-auth slips, Codex stays read-only
  indefinitely — this is the intended fail-closed direction, but it should be visible in
  the load-plan ledger as a tracked blocker, not silent.
- Copilot's proxy remains unproven until its generated config's dry-run lands
  (MCPINT-IMP-CODEX-002 scope covers analogous fragments).

## Migration Strategy

1. IMP-FACADE-001: deploy facade loopback-bound; smoke all 12 tools (3 expected BLOCKED).
2. FND-CODEGEN-005 + IMP-CODEX-002: generate read-plane configs for
   codex/opencode/gemini/copilot; commit as baseline; dry-run proofs.
3. On IDENTITY-005 + actor-auth landing: flip catalog `codex:` row's precondition gate,
   regenerate, commit — Codex write parity ships as a one-line catalog change plus
   regeneration.
4. Rollback: regenerate with the `codex:` row reverted to read-plane; facade can be
   compose-stopped without touching any other server.

## Verification

- P4/P6 proofs: Codex dry-run transcript (tool list + facade read + denied-route
  rejection); parity gates green per target; facade 12-tool smoke with 3 BLOCKED and 0
  unexpected states; `lsof` shows facade bound to 127.0.0.1 only.
- Negative test: attempt to generate a write-capable Codex config with
  `actor_authentication.enabled=false` → generator refuses (CI test).

## Validation

- **PAL consensus (2026-07-17, pal-stdio `consensus`, continuation
  `8f1682d6-6b8e-4976-82de-0e2290aa9c41`)**: **RUN — both models endorse** (two full
  verdicts, for/against stances).
  - `anthropic/claude-opus-4.1` (stance: for) — verdict: **sequencing sound, facade is the
    correct universal read plane** (confidence 8/10). The two-precondition gate is
    "non-negotiable given proven workspace contamination". Strongest missed failure mode:
    the **asymmetric transition** — if IDENTITY-005 lands but actor-auth stalls, schedule
    pressure will push for a "temporary" write wrapper; mitigation: explicit
    rollback/checkpoint criteria and transition monitoring (addressed: the wrapper is a
    named rejected alternative; precondition slippage must be a tracked ledger blocker per
    Consequences).
  - `openai/gpt-5` (stance: against) — verdict: **sequencing sound, facade prudent**
    (confidence 8/10) with the strongest objection: **"read-only ≠ safe"** — loopback is
    not an auth boundary (any local process can connect); reads need enforced per-request
    scoping, and writes need a **runtime** guard so config distribution alone can never
    enable them. Addressed in this ADR: the runtime write-guard is now an invariant;
    fed to packets: facade local-auth hardening option (UDS/bearer token) and
    read-scoping/rate-cap conformance tests → MCPINT-IMP-FACADE-001; E2E identity/actor
    propagation conformance as the actual parity flip condition → MCPINT-IMP-CODEX-002
    verification.
  - Consensus summary: no disagreement on the decision itself; both objections are
    hardening requirements on execution packets, not challenges to the architecture.
- ConPort `log_decision`: owed at acceptance.

## Cross-references

- ADR-MCPINT-001 (catalog v2 `agents:` matrix — the data this policy constrains),
  ADR-MCPINT-003 (implicit channels are Claude-only today), ADR-MCPINT-004 (event ingress
  identity), ADR-MCPINT-005 (shelved features).
- ADR-DCP-MCP-RO-0009 (accepted foundation for facade identity/resolution/redaction).
- `docs/03-reference/mcp/tool-placement-map.md` §3 (facade + admin-tool rows).
- Owners referenced, not decided for: DMX-ARCH-SERENA-SURFACE-003,
  DMX-ARCH-CONPORT-SURFACE-002, DMX-MEMSPINE-IDENTITY-005, DMX-HYG-LOOPBACK-002.
- Runtime evidence: P0 claims 7, 8, 11, 15; findings N2, N5.

---

*PAL consensus outcome recorded in the Validation section above (2026-07-17).*
