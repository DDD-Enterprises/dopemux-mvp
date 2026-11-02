---
id: adr-mcpint-002-amendment-runner-identity
title: 'ADR-MCPINT-002 Amendment: Verified Runner Identity on dope-memory and ConPort Replaces the Actor-Auth Precondition'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-01'
last_review: '2026-11-01'
next_review: '2027-02-01'
prelude: Proposed amendment to ADR-MCPINT-002. For dope-memory and ConPort, verified per-runner transport identity on HTTP writes with identity-required writes replaces the actor-auth precondition. Codex is admitted while the servers run in log mode, with its writes verified. Enforce follows once the 2A blockers clear. The orchestrator precondition stays and moves to Wave 2C.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpint-002
    - ADR-227
    - MACRO-DMX-RUNNER-MEMORY-2A-001
---
# ADR-MCPINT-002 Amendment: Verified Runner Identity Replaces the Actor-Auth Precondition for the Memory Servers

════════════════════════════════════════════════════════════

## Status

* **Proposed.** Not accepted. The accepted ADR file
  (`docs/90-adr/adr-mcpint-002-agent-exposure-and-read-plane.md`) is not edited by this
  document. Design 5.9 requires the operator to accept this amendment before the Codex memory
  config ships (how-to step 8).
* Drafted by `TP-DMX-RUNNERMEM2A-R2-W08-DOCS-ADR-001` (workstream W08 of
  `MACRO-DMX-RUNNER-MEMORY-2A-001-R2`) from the committed W01 to W07 and W10 changes. The
  operator chose this wording on 2026-11-01 ("Allow log mode (Recommended)",
  `proof/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/review_bundle/AMENDMENT_03.md`).

## Date

* 2026-11-01

## Owners

* Supervisor (DDD-Enterprises); drafted by the W08 implementer (Claude agent session).

────────────────────────────────────────────────────────────

## Context

ADR-MCPINT-002, Decision 1, gives Codex the full MCP fleet only after two preconditions:

1. DMX-MEMSPINE-IDENTITY-005: per-request workspace and instance identity, with fail-closed
   writes on the memory spine.
2. Orchestrator `actor_authentication.enabled`: every task-orchestrator transition and note
   carries an authenticated actor.

Its invariant is that no agent without enforced actor attribution holds a write-capable MCP
config, and that write acceptance is enforced at runtime by the receiving service, not by
config distribution.

Wave 2A (`docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md`, revision 2) built a
different runtime guard for the two memory servers:

* Both servers fill an omitted `workspace_id`, and an omitted `instance_id` where the row
  carries one, from their own binding, and reject an HTTP write whose `workspace_id` does not
  match the server's binding (or any write to a server with no binding), in every auth mode
  (W01, W02, W12; `services/working-memory-assistant/auth_identity.py:112-140`;
  `AMENDMENT_04.md`). A write can therefore never be stored under another workspace.
* Each server has an auth mode `off`, `log` or `enforce`. A write with a valid per-principal
  bearer token is stored with its verified principal (for example `runner:codex`); any other
  write is stored `unverified` and counted by caller. `enforce` rejects it with 401.
* Tokens live in the macOS keychain; the servers hold only SHA-256 hashes (W03).
* The stdio bridge sends the runner's token and fills the repo's ids (W04).
* The generator writes Codex's memory config only when a gate holds (W07).

The orchestrator is not part of Wave 2A. Upstream 4.0.0 is unreleased and moves to Wave 2C.

────────────────────────────────────────────────────────────

## Decision

For **dope-memory and ConPort only**:

1. **Replacement.** "Verified per-runner transport identity on HTTP writes, with
   identity-required writes" (Wave 2A design goals G1 and G2) replaces the
   `actor_authentication.enabled` precondition of ADR-MCPINT-002 Decision 1.
2. **Codex is admitted in `log` mode.** The generator writes `.codex/config.toml` for the
   memory servers when, for both servers, `/health` reports `auth_mode` of `log` or
   `enforce` and `identity_required_writes` true (ConPort also `auth_principal_column`
   `ok`), and a keychain token for `runner:codex` exists. `off` fails. In `log` mode every
   Codex write is verified as `runner:codex`, because the bridge always sends that token;
   writers without a token are still accepted and recorded `unverified`.
3. **Enforce follows.** `enforce` is switched on per server after the 2A blockers below
   clear, a smoke test passes, and the accepted-writer review is done.

For the **task orchestrator**: the actor-auth precondition **stays in force and moves to
Wave 2C**. Codex gets no orchestrator entry until then. The `full-sequenced` rows for the
orchestrator (and for serena, dope-context, gpt-researcher and pal-stdio) stay in the
preview only.

### What stays exactly as in ADR-MCPINT-002

* The DCP facade as the universal read plane, the exposure matrix rows for every other
  agent, the loopback-only invariant, and the catalog as the single source for generated
  configs.
* Write acceptance is a runtime decision at the receiving service. The gate decides only
  whether the generator writes a config.

### Blockers for `enforce` (not available in 2A)

From `W05_RETURN.md` open items 2 to 5, `AMENDMENT_02.md` and `AMENDMENT_03.md`:

* Container callers (`adhd_engine`, `claude_brain`, `dopecon-bridge`) cannot reach the
  keychain.
* Container ids are unknown.
* The bridge's progress route drops `instance_id` (red-lane file, not exempt).
* Claude Code stays on direct HTTP until Wave 2B.
* Other writers: `services/task-orchestrator`, `pm/adapters/conport.py`,
  `services/dope-memory/mcp_stdio_adapter.py`.

### Invariants

* Tokens are keychain-only; servers keep hashes; no token enters a tracked file or a log.
* A write is never labelled with a principal the server did not verify from a token, except
  local writers that record a self-asserted `internal:*` principal with a marker (W06).
* Servers bind to `127.0.0.1`.

### Non-goals

* The orchestrator, Wave 2B runner renderers, the installed-config doctor, and the Claude
  Code move to the bridge.
* Changing DMX-MEMSPINE-IDENTITY-005's own status. Whether the identity-required writes
  built in 2A close that packet is UNKNOWN and is the operator's call.

────────────────────────────────────────────────────────────

## Alternatives Considered

* **Keep both preconditions as written.** Rejected for the memory servers: the actor-auth
  precondition is an orchestrator feature and says nothing about who writes to dope-memory
  or ConPort.
* **Gate Codex on `enforce` only (design 5.7 as first written).** Rejected by the operator
  on 2026-11-01: `enforce` cannot be switched on in 2A, so Codex could never get a config.
  Codex's own writes are verified either way; `enforce` only adds rejection of tokenless
  writers.
* **Ship Codex without a token check.** Rejected: that is the status quo the ADR was
  written to prevent.

## Consequences

* Codex can write to both memory servers in 2A as `runner:codex`, and the stored principal
  proves it.
* Until `enforce`, any writer without a token still writes. The `log` period is the
  window to find and fix or accept them. `dopemux mcp doctor` does not report them (not
  built); the evidence is each server's `/health` (`auth_unverified_calls`).
* A token holder can write as that principal. A compromised runner using its own token, a
  second process of the same macOS user reading the keychain item or the ledger, and local
  writers forging their self-asserted principal are not protected against
  (design section 6).
* The gate reads `/health` at generation time only. Switching `enforce` off later does not
  withdraw an existing Codex config.
* Claude Code's direct HTTP writes carry no token and, after the image rebuild, need the
  bound ids in the tool call (W01 residual 1). This is a 2A limitation until Wave 2B.

## Migration Strategy

1. The operator runs the how-to steps in `docs/02-how-to/runner-memory-identity.md`.
2. The operator accepts this amendment (status becomes `accepted`, with a decision date)
   before step 8 writes the Codex config.
3. Wave 2B moves Claude Code and the other runners; Wave 2C handles the orchestrator and
   restates its precondition.

Rollback: set this document's status back to `proposed` or `rejected`, restore
`.codex/config.toml` (`git checkout -- .codex/config.toml`), and revoke
`runner:codex` (`dopemux auth revoke runner:codex --apply`).

## Verification

* Gate tests: `tests/unit/runner_memory_2a_r2_w07/test_generator_gate.py` and
  `tests/unit/test_mcp_commands_catalog.py` (W07 and its Amendment 03 round).
* Live Codex acceptance: how-to step 10, `NOT_RUN` until the operator runs it.
* Nothing in this amendment has been observed live.

## Notes

* Related: ADR-MCPINT-002 (amended), ADR-227 (the red-lane carve-out Wave 2A relied on),
  design RFC `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` sections 5.5, 5.7 and
  5.9, and `AMENDMENT_03.md` (the `log` mode ruling).
* The `actor_authentication.enabled` wording remains in
  `schemas/mcp/fleet-catalog.schema.json:148`, a schema description outside Wave 2A's
  write surface (`W07_RETURN.md` residual 6).
