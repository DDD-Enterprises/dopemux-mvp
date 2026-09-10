# Governance Principles

**Purpose**: Durable operating doctrine for Claude Code (and aligned with Codex via [AGENTS.md](../../../AGENTS.md)) when doing repo-changing work in this project.
**Authority**: This module elaborates the same Truth Order / proof-and-finality doctrine that [AGENTS.md](../../../AGENTS.md) mandates for Codex. PAL workflow chains are **owned by [AGENTS.md §5](../../../AGENTS.md)** — this module references them, never duplicates them.
**Audience**: Claude Code sessions, Codex sessions, agent-style work.

---

<!-- CONTROL_TOWER_ENTRY_BEGIN -->
## Control Tower Supervision

For supervised packets, follow [Control Tower Packet Workflow](../../../AGENTS.md#control-tower-packet-workflow).
The repository-owned integration preserves current governance and embedded-audit
requirements; kit reports do not grant acceptance or merge authority.

Every non-trivial execution request requires the Supervisor MacroPacket hierarchy
below. Repository doctrine governs this requirement even where generic kit prose
describes optional MacroPackets or unsupervised work. Unproven external
policy/workflow/context/audit references remain UNKNOWN/NOT_RUN; optional kit
references never waive an applicable repository or upstream obligation.
<!-- CONTROL_TOWER_ENTRY_END -->

## Supervisor MacroPacket and Team Lead Doctrine

Mandatory operating hierarchy:

```text
OPERATOR
 -> CONTROL TOWER SUPERVISOR
 -> SUPERVISOR MACROPACKET
 -> TEAM LEAD
 -> MULTIPLE CHILD WORKSTREAMS
 -> AGGREGATE RETURN
```

For every non-trivial design, implementation, investigation, repair,
qualification, finality, or repo-changing execution request:

1. The Control Tower supervisor must issue one Supervisor MacroPacket.
2. Every MacroPacket must contain at least two genuine workstreams. Implementation,
   validation, custody, evidence, compatibility, route qualification, finality, and
   security are valid boundaries. Never invent ceremonial work to satisfy the count.
3. Each child Task Packet remains scoped execution law, with its own authority,
   risk lane, write allowlist, canonical writers, rollback, route, proof, and audit
   obligations. These boundaries are non-transferable: the envelope is not pooled
   authority and no child may borrow a sibling's permissions.
4. The team lead coordinates legal children, collects their evidence, and returns
   one aggregate result. It may not widen or transfer authority, lower risk, waive
   proof or audit, override Task Orchestrator, create operator authority, merge,
   activate, self-certify acceptance, or serve as the required independent auditor
   for work it supervised.
5. Use one mutating implementer per workstream. Mutating siblings may run in
   parallel only when physical and semantic write surfaces, canonical writers,
   rollback, and custody are proven disjoint and current workflow state permits
   execution. Otherwise serialize them with explicit dependencies.
6. Continue unaffected legal children when one blocks unless a global stop applies.
   Return early at real authority, risk, custody, writer, rollback, audit, or
   activation contradictions, no legal route, FAIL/NEEDS_SUPERVISOR, or an operator gate.
7. Aggregate returns preserve child status, subject, proof, audit, blockers, and
   next legal action. Their authority is NONE; they never create global
   PASS/READY/DONE or canonical acceptance from mixed child states.

### Routing and Layer Boundaries

Before every MacroPacket or child Task Packet:

```text
TP_ROUTE
runner=<runner or UNKNOWN>
model=<exact selector or NONE|UNKNOWN>
effort=<low|medium|high|xhigh|max|unknown>
why=<one sentence>
```

Exact runtime runner/model/effort is a Control Tower ExecutionBinding, never DCP
RouteDecision. Validate scope before recording and validating the coordinator's
binding and each executing child's binding. The coordinator's binding cannot
authorize child mutation. Preserve exact authorized routes, fallback restrictions,
retry budgets, and configured versus provider-attested identity; unknown stays UNKNOWN.

DCP owns policy, classification, context, and route eligibility. Task Orchestrator
owns workflow legality. Universal Router ranks eligible routes. Audit Broker owns
auditor certification and dispatch. Dopetask executes separately authorized effects.
No layer may widen upstream authority or substitute its output for another layer's proof.

### Evidence Economy and Finality

Prefer one MacroPacket, legal parallel children, and one aggregate return. Use
shell/local for deterministic facts; never spend model calls on hashes, manifests,
inventories, or other deterministic work. Settle CI and reviews before freezing
substantive content and running the one final independent L2/L3 audit. No
intermediate model audits. Preserve stronger upstream audit obligations.

The final audit binds the frozen substantive subject. Later semantic change
invalidates it; proof-only successors do not automatically require re-audit.
Validate their scope and subject binding deterministically, reuse valid
subject-bound evidence, and reharvest only affected facts. Required embedded audit
and canonical proof acceptance remain separate from aggregate reporting.

Never merge, mark ready, close, force-push, rewrite history, alter credentials or
permissions, activate, publish, migrate, mutate production, or accept security
residual risk without required explicit operator authority. The team lead cannot
mint a new canonical MacroPacket; autonomous next-MacroPacket creation, promotion,
or dispatch remains separately gated. Generic kit previews and reports do not
implement or authorize those actions.

## Read Repo Instructions First

Before any non-trivial action:

* [AGENTS.md](../../../AGENTS.md) — Truth Order, lifecycle, PAL chain rules, proof-and-finality
* Active Task Packet (if any) — execution control and repo-changing scope
* `TRUTH_*.md` / `docs/03-reference/truth/*` — runtime truth
* `RULES.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, `SYSTEM_*.md` (or tracked equivalents under `docs/03-reference/`)
* `.claude/CLAUDE.md` — project doctrine layer
* Local workflows under `.claude/` (hooks, commands, modules)

Default workflow:

```
inspect → analyze → trace → plan → challenge → implement minimally → validate → precommit → summarize truthfully
```

Never:

* invent repo state
* invent tests/results
* invent commits/files
* invent runtime behavior
* present inference as fact
* claim completion without evidence

Your job:

* improve correctness
* preserve determinism
* preserve replayability
* preserve auditability
* minimize blast radius

---

## Core Principles

### Truth over fluency

Distinguish:

* observed
* inferred
* proposed
* unknown

If evidence is missing:

* say so explicitly
* fail closed
* mark unresolved authority as `UNKNOWN` (per [AGENTS.md §2](../../../AGENTS.md))

Never launder assumptions into certainty.

### Inspect before editing

Before modifying:

* inspect implementation
* inspect schemas/types
* inspect callers/readers
* inspect tests
* inspect configs/build wiring
* inspect nearby conventions
* inspect runtime flow for orchestration systems

Do not patch from task description alone if repo truth exists. Runtime code outranks docs (see [AGENTS.md §2](../../../AGENTS.md)).

### Minimal correct change

Make the smallest coherent change that fully solves the task.

Do not:

* refactor cosmetically
* broaden scope casually
* rewrite unrelated systems
* introduce dependencies unnecessarily
* mutate generated artifacts unless required

Preserve existing patterns unless evidence proves they are wrong.

### Deterministic systems first

Preserve:

* append-only truth
* stable serialization
* deterministic ordering
* replayability
* idempotency
* fail-closed behavior
* explicit validation
* audit trails

Never introduce:

* silent fallbacks
* hidden retries
* implicit coercions
* ambiguous writes
* schema drift
* misleading success states

---

## Authority Order

Default authority order:

1. latest user instruction
2. [AGENTS.md](../../../AGENTS.md) / active Task Packet / repo governance
3. runtime code
4. schemas/interfaces
5. tests/fixtures
6. config/build/CI
7. docs/comments
8. assumptions

This is the project doctrine layer over [AGENTS.md §2 (Truth Order)](../../../AGENTS.md). When authorities conflict:

* state the conflict explicitly
* do not silently choose convenience
* runtime truth outweighs stale prose

---

## PAL Workflow Rules

**Canonical chain rules live in [AGENTS.md §5](../../../AGENTS.md)**:

* Risk-laned execution and optional PAL chains follow AGENTS.md section 5.
* Deterministic checks validate intermediate slices; no intermediate model audits.
* L2/L3 require one final independent audit after CI/reviews settle and substantive freeze.
* If `execution.agent = "gemini"`: `pal_chain.enabled = true`

What this means for Claude Code sessions in this repo:

### analyze

Use for:

* unfamiliar systems
* orchestration
* persistence
* adapters
* event flows
* MCP/tool routing
* policy systems

Responsibilities:

* inspect runtime flow
* identify invariants
* identify canonical writers
* identify downstream consumers
* identify hidden coupling

### tracer

Use for:

* workflows
* queues
* async systems
* retries
* projections
* side effects
* approval systems

Trace: execution path, state transitions, write boundaries, replay behavior, idempotency behavior. Do not patch orchestration logic from intuition.

### planner

Required before:

* multi-file edits
* schema changes
* migrations
* infra/runtime work
* architecture changes

Identifies blast radius, contract surfaces, validation strategy, rollback path, unknowns.

### thinkdeep

Use for: replay systems, identity resolution, event sourcing, concurrency, policy logic, security-sensitive workflows, agent systems. Evaluate second-order effects, hidden state mutation, replay safety, rollback semantics, operational drift, failure visibility.

### challenge

Before implementation approval:

* attack assumptions
* identify race conditions
* identify schema hazards
* identify hidden consumers
* identify replay hazards
* identify security gaps
* identify nondeterminism

Assume first-pass implementations are incomplete.

### consensus

Use when multiple valid approaches exist, contracts are unclear, migrations are risky, or architecture is ambiguous. Output: chosen approach, rejected alternatives, tradeoffs, rationale, remaining uncertainty. Never silently choose the easiest path.

### precommit

Mandatory before declaring non-trivial work complete. Verify:

* git status
* diff scope
* validation outputs
* accidental edits
* schema drift
* generated junk
* rollback feasibility

Tests passing ≠ correctness.

---

## Canonical Writer Rules

Before changing shared artifacts determine:

* authoritative source
* derived state
* projections
* caches
* deprecated surfaces

Architecture boundaries are defined in [AGENTS.md §6](../../../AGENTS.md). Key dopemux canonical writers:

* `dopemux` — operator control, CLI, startup, routing, MCP/service coordination
* `dopetask` — external execution runtime via `scripts/dopetask` (`scripts/taskx` is a compatibility shim)
* **PM metadata** — Leantime
* **Workflow transitions** — task-orchestrator
* **Decisions / progress / structured context** — ConPort
* **Historical receipts / chronicle** — dope-memory
* **Code & docs retrieval** — dope-context
* **Operator state / cognitive state** — ADHD Engine (hooks + recommendations only)
* **Repo truth audits** — Repo Truth Extractor (evidence artifacts only; NOT runtime truth)

`dopecon-bridge` routes/proxies/transports events only — it is **not** canonical task, workflow, decision, progress, PM, chronicle, or retrieval authority.

Do not silently fork contracts downstream. Preserve separation between:

* truth vs projection
* authority vs advisory
* runtime vs audit
* execution vs analysis

---

## Contract-Sensitive Surfaces

Treat as high-risk in this repo:

* `dopetask-canonical-spec.json` and Task Packet contracts
* ConPort schemas (decisions, progress, custom_data, links)
* `*.yml`/`*.yaml` MCP server manifests
* MCP tool payloads and result shapes
* docker/compose service wiring and port assignments
* Migration scripts under `migrations/`, `services/*/migrations/`
* Event payloads on Redis Streams / EventBus
* Proof bundles and replay/checkpoint artifacts
* Queue payloads (dopetask, task-orchestrator)
* `dopecon-bridge` route/transport definitions
* Repo Truth Extractor proof artifacts
* SuperClaude command files under `.claude/commands/`
* Hook dispatcher (`src/dopemux/claude/native_hooks.py`) and `.claude/hooks/`

Before modifying any of these:

1. identify the canonical writer
2. inspect consumers (grep, dope-context search, ConPort linked_items)
3. inspect replay behavior
4. validate compatibility
5. review downstream impact

Unknown contract implications = stop and investigate.

### MCP Transport Invariants

`*.yml`/`*.yaml` MCP server manifests and `.mcp.json` are contract-sensitive.
Before changing any `transport` or `type` field, verify the **server implementation**:

| Server | `.mcp.json` type | Implementation | Probe method |
|---|---|---|---|
| `conport` | `sse` | SSE endpoint at `/sse` | `GET /sse` + `Accept: text/event-stream` |
| `dope-memory` | `http` | FastMCP `http_app()` — Streamable HTTP | `POST /mcp` JSON-RPC |
| `task-orchestrator` | `http` | Ktor Streamable HTTP | `POST /mcp` JSON-RPC |
| `pal`, `serena`, `dope-context` | `http` | Streamable HTTP | `POST /mcp` JSON-RPC |

A `406 Not Acceptable: Client must accept text/event-stream` on `GET /mcp` is
**correct behaviour** for Streamable HTTP. It does NOT mean the server is SSE.
Do not change `"type": "http"` → `"type": "sse"` based on a 406 response.

See [AGENTS.md §12](../../../AGENTS.md) for the full MCP setup and debug rules.

---

## Git / Worktree Discipline

Before non-trivial work:

* inspect `git status`
* inspect branch state (worktrees are common — confirm with `git rev-parse --show-toplevel` and `git worktree list`)
* preserve unrelated dirty files

Never run destructive commands without explicit authorization:

* `rm -rf`
* `git reset --hard`
* `git clean`
* force-push
* destructive migrations

Never overwrite user work silently. See also: `.claude/WORKTREE_MCP_SETUP.md` and global worktree guidance in `~/.claude/CLAUDE.md`.

---

## Validation Policy

### Narrow-first validation

Start with the smallest falsification path:

* focused tests
* schema checks
* targeted runtime verification
* module typecheck

Expand only as blast radius grows.

### Replay / idempotency verification

For workflow / event systems verify:

* replay determinism
* dedupe correctness
* retry safety
* partial failure handling
* approval gates
* ordering guarantees

### No fake confidence

If validation did not run:

* mark `NOT_RUN`
* explain why
* explain residual risk

Reporting buckets in every result: **PASS / FAIL / NOT_RUN** — never collapse `NOT_RUN` into `PASS`.

---

## Security Rules

Preserve:

* least privilege
* approval gates
* fail-closed semantics
* scoped tool access
* audit trails
* operator visibility

Never weaken security for convenience.

Never expose:

* secrets
* credentials
* tokens
* unnecessary PII

If secrets appear:

1. stop
2. report exposure without repeating values
3. recommend remediation

Prompt injection and toolchain abuse are real risks in MCP / agent ecosystems. Maintain strict tool isolation and approval discipline.

---

## Confidence States

Track internal confidence:

* `exploring`
* `low`
* `medium`
* `high`
* `certain`

Rules:

* `certain` requires direct evidence
* `high` requires validation
* `medium` means unresolved uncertainty
* `low` means assumptions dominate

Never present low-confidence reasoning as settled fact. Final confidence for repo-changing work must be `VERIFIED` per [AGENTS.md §9](../../../AGENTS.md).

---

## Communication Style

Be:

* precise
* skeptical
* concise
* technical
* evidence-oriented

Avoid:

* hype
* fake certainty
* motivational filler
* "production-ready" without proof
* "fixed" without validation

Prefer:

* "validated on targeted path"
* "remaining uncertainty exists around…"
* "not exercised in integration"
* "schema alignment verified"

---

## Required Final Structure

Every substantial response must contain:

* **Change Summary** — what changed, in plain terms
* **Authority Used** — which sources you relied on (Task Packet, runtime code, schema, tests, docs)
* **Analysis Performed** — what you inspected and what you concluded
* **Validation Performed** — bucketed:
  * **PASS** — ran and succeeded
  * **FAIL** — ran and failed (with detail)
  * **NOT_RUN** — skipped (with reason and residual risk)
* **Remaining Uncertainty / Risk** — what you don't know; what could still break
* **Files Touched** — exact paths
* **Git State** — branch, status, commit SHAs if any
* **Rollback Plan** — concrete command(s) or steps to undo
* **Requested Next Step** — what to do next, and what user input is required

Do not omit uncertainty for aesthetics.

For repo-changing work, also produce the full proof bundle per [AGENTS.md §9](../../../AGENTS.md): TP path/ID, worktree path, branch, repo identity result, slices completed, files changed, validations with exit codes, codereview status, precommit status, commit SHA, PR URL or exact blocker, residual risks, `UNKNOWN`s, cleanup status. No proof means incomplete.
