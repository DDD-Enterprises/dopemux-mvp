---
id: adr-task-orchestrator-claude-surface-integration
title: "ADR: Task Orchestrator Claude-Surface Integration"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Define the Claude-facing surface for task-orchestrator integration — schema config, slash commands, agent doc updates, hook coordination, and proof-bundle enforcement — as a sibling series to the existing DMX-ORCH-INTEGRATION runtime work.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-task-orchestrator-as-workflow-authority
    - adr-pm-plane-authority-boundaries
    - adr-conport-as-decision-progress-and-context-authority
    - adr-203-task-orchestrator-un-deprecation
    - adr-207-task-orchestrator-capabilities
---

# ADR: Task Orchestrator Claude-Surface Integration

════════════════════════════════════════════════════════════

## Status

* Proposed

## Date

* 2026-05-27

## Owners

* @hu3mann (Dopemux Workflow Plane / PM Plane / Integration Layer)

────────────────────────────────────────────────────────────

## Context

The Dopemux repo has adopted task-orchestrator as the canonical workflow authority via [adr-task-orchestrator-as-workflow-authority.md](./adr-task-orchestrator-as-workflow-authority.md) (status: `proposed`) and `AGENTS.md §6` ("Workflow transitions: task-orchestrator"). The upstream `ghcr.io/jpicklyk/task-orchestrator` v3 MCP is wired in via `.mcp.json`, and a runtime series — `DMX-ORCH-INTEGRATION` (root `32df1792`) — is loaded into the orchestrator with 19 children covering CLI, validators, MCP wrappers, workflow DSL, plugin/hook registry, context freshness, memory receipts, Task Packet Forge, intake/audit, transition preview, PR readiness, Kotlin proof envelope, TUI panels, T0/T1 automation, and final E2E proof.

The *Claude-facing surface* of that integration is missing.

**Evidence-backed pain points**:

* No `.taskorchestrator/config.yaml` exists at the repo root → zero schemas defined → zero gate enforcement → `guidancePointer` is permanently `null` for every work item.
* No `/dx:` slash commands target the orchestrator MCP — operators call `mcp__task-orchestrator__*` tools by hand.
* Claude-facing doctrine docs ([.claude/claude.md](../../.claude/claude.md), [.claude/modules/coordination/authority-matrix.md](../../.claude/modules/coordination/authority-matrix.md), [.claude/agents/project-manager.md](../../.claude/agents/project-manager.md), [.claude/modules/shared/superclaude-workflows.md](../../.claude/modules/shared/superclaude-workflows.md), [.claude/modules/shared/sprint.md](../../.claude/modules/shared/sprint.md)) **still state that ConPort owns task storage and that task-orchestrator was "removed"**, directly contradicting `AGENTS.md §6` and the existing workflow-authority ADR.
* Hooks don't surface orchestrator context at session start; agents don't know how to consume `guidancePointer`; the PAL chain mandated by `AGENTS.md §5` has no mechanical enforcement at the orchestrator layer.
* Cross-agent surfaces (`AGENTS.md` for Codex, `.github/copilot-instructions.md` for GitHub Copilot, `.claude/personas/*.agent.md` for personas) lack orchestrator operational guidance.

**Constraints**:

* `AGENTS.md §5` defines the PAL chain (`analyze → planner → codereview → precommit` minimum; risky variant adds `thinkdeep → challenge` rungs). The chain is mandated for non-trivial repo-changing work; it currently has no mechanical orchestrator enforcement.
* `AGENTS.md §9` (Proof and Finality) requires a proof bundle for every repo-changing TP. The bundle is not currently linked to orchestrator gates.
* `AGENTS.md §10` (Known Dangers) flags task-orchestrator runtime authority as conflicted across `app/main.py`, `task_orchestrator/app.py`, and Docker wiring — this surface is `UNKNOWN` until the runtime series resolves it.
* The runtime series `DMX-ORCH-INTEGRATION` is in flight and must not be blocked by Claude-surface work.

────────────────────────────────────────────────────────────

## Decision

The Claude-facing surface of task-orchestrator integration is owned by a dedicated sibling series — `DMX-ORCH-CLAUDE-SURFACE` — with explicit responsibility for six pillars:

1. **Schema config** at `.taskorchestrator/config.yaml` (workflow guide §3): work-item schemas, traits, default_traits, status_labels, schemas_metadata. Tags and types map work items to schemas; `guidancePointer` and `skillPointer` surface PAL chain guidance to agents.
2. **`/dx:` slash commands** wrapping the 13 task-orchestrator MCP tools with ADHD-shaped output (max 10 results, max 3 options, progressive disclosure, breadcrumb + gate status leading).
3. **Agent file updates** ([.claude/agents/project-manager.md](../../.claude/agents/project-manager.md), [developer.md](../../.claude/agents/developer.md), [architect.md](../../.claude/agents/architect.md), [researcher.md](../../.claude/agents/researcher.md)) plus a shared note-filling protocol doc at `docs/03-reference/orchestrator-note-filling-protocol.md` — linkable from every cross-agent surface.
4. **Doctrine reconciliation** in CLAUDE-facing modules per the Claude-Code companion regime (`.claude/claude.md` and `.claude/modules/shared/governance-principles.md`).
5. **PAL chain → required-notes mapping** per `AGENTS.md §5`: every chain stage (`analyze`, `planner`, `codereview`, `precommit`, plus risky-chain `thinkdeep` and `challenge-*` rungs) becomes a note key with a matching role-phase placement and `skill:` field that invokes the named PAL tool.
6. **Proof bundle as `complete`-gate** per `AGENTS.md §9`: the `proof-bundle` note (review-phase, `required: true`) holds the full bundle (TP path/ID, worktree path, branch, repo identity, slices, files changed, validations with exit codes, codereview status, precommit status, commit SHA, PR URL or blocker, residual risks, `UNKNOWN`s, cleanup status). Mechanical enforcement: `advance_item(trigger="complete")` fails if the note is unfilled.

Cross-agent applicability: `AGENTS.md` (Codex), `.claude/claude.md` (Claude Code), `.github/copilot-instructions.md` (Copilot), `config/instructions/agents.instructions.md` (Copilot custom-agent), `.claude/personas/*.agent.md` (personas) each receive an "Orchestrator Operations" section linked to the shared note-filling protocol doc.

Schema posture starts with **Option A — Soft gates, broad coverage (~6 schemas + `default` fallback, composed via traits)**: queue/work phases carry rich `description` + `guidance` + `skill` fields but `required: false`; only `proof-bundle` in `review` is `required: true`. Existing 19 `DMX-ORCH-INTEGRATION` TPs continue to advance freely (no retroactive blocking). Tighter postures (Option B hard gates) are reversible upward by editing trait definitions.

**Invariants**:

* `DMX-ORCH-CLAUDE-SURFACE` is a sibling series, not a child of `DMX-ORCH-INTEGRATION`. Cross-series dependencies are declared explicitly via `manage_dependencies` with `unblockAt` values matching the contract surface (most at `review`; runtime-deployment-dependent items at `terminal`).
* This ADR does NOT re-decide workflow authority (that is owned by [adr-task-orchestrator-as-workflow-authority.md](./adr-task-orchestrator-as-workflow-authority.md)).
* This ADR does NOT authorize runtime mutations to the orchestrator service itself (CLI, validators, MCP wrappers, Kotlin proof envelope, T0/T1 automation). Those remain owned by `DMX-ORCH-INTEGRATION`.
* `.taskorchestrator/config.yaml` is a contract-sensitive surface per `AGENTS.md §6`; schema/trait changes require canonical-writer inspection and ADR-or-decision linkage.

**Non-goals**:

* Resolution of `AGENTS.md §10` task-orchestrator runtime authority conflict (deferred to `DMX-ORCH-INTEGRATION` runtime work).
* Strict `actor_authentication.enabled: true` enforcement (workflow guide §10). Claim mechanism ships with self-reported actors; server-side authentication is an opt-in operator decision later.
* Multi-agent fleet `claim_item` selector mode beyond worktree-parallel pattern documentation.
* Cursor / Windsurf / other agent environments (covered by Bare-MCP escape hatch only).
* Self-modification ladder L3 (metric-triggered auto-action) and L4 (auto-PR with guardrails) — both require separate ADRs.

────────────────────────────────────────────────────────────

## Alternatives Considered

### Alternative 1 — Attach work to existing `DMX-ORCH-INTEGRATION` series

Add Claude-surface TPs as additional children under `32df1792` instead of a new sibling root.

* **Pros**: One unified series, easier `query_items(operation="overview")` view, simpler genealogy.
* **Cons**: Queue grows to ~35 items mixing runtime work (CLI, MCP wrappers, Kotlin proof envelope) with doctrine work (agent docs, slash commands, ADR updates). Different cadences, different reviewers, different blast radii. Operator decisions about prioritizing one vs the other become harder.
* **Why rejected**: Operator preference, plus the runtime series is supervised-only and supervisor-loaded; mixing it with autonomous-safe doctrine work would force the doctrine TPs to inherit a more conservative posture than they need.

### Alternative 2 — Skip ADR and proceed by convention

Document the integration in `.claude/claude.md` only; no ADR; rely on convention to maintain doctrine consistency.

* **Pros**: Faster to ship; no ratification review cycle.
* **Cons**: Doctrine drift recurs (Claude-facing modules already drifted out of sync with `AGENTS.md §6` and the workflow-authority ADR). Without a ratified ADR for the Claude-surface, the next person to touch CLAUDE.md re-introduces the old pattern. No genealogy linking schema config decisions back to a canonical source.
* **Why rejected**: The current drift is itself proof that "by convention" doesn't hold across multi-month timeframes and multiple contributors.

### Alternative 3 — Per-schema ADRs (one ADR per work-item schema)

Issue a separate ADR for each schema (`task-packet`, `feature-implementation`, `bug-fix`, etc.).

* **Pros**: Fine-grained traceability; each schema's design is independently citable.
* **Cons**: 6+ ADRs to write, review, and ratify before any code lands. Massive overhead for what is fundamentally one cohesive design.
* **Why rejected**: Premature decomposition. If a specific schema turns out to need its own ADR later (e.g., the audit-pack schema becoming a contract surface for RTE work), that ADR can be issued then as a refinement.

────────────────────────────────────────────────────────────

## Consequences

### Easier

* One coherent Claude-facing UX for orchestrator interaction (no more "what's the right MCP tool to call?" friction).
* Mechanical gate enforcement for proof bundles — `advance_item(trigger="complete")` fails closed when the bundle note is missing, removing a class of "shipped without proof" risk.
* PAL chain compliance becomes auditable via orchestrator notes — anyone can `query_notes(operation="list", role="review")` on a completed TP and read the chain artifacts.
* Cross-agent (Codex, Claude, Copilot) coverage with identical operational instructions via a single shared protocol doc — no inline-repeated text drifting.
* `guidancePointer` + `skillPointer` give agents (especially subagents launched via `SubagentStart` hooks) deterministic guidance about what to do next.

### Harder

* Doctrine reconciliation churn across ~10 files (CLAUDE.md, authority-matrix, superclaude-workflows, sprint, governance-principles, event-patterns, integration-bridge, project-manager agent, plus cross-agent surfaces). Touches contract-sensitive surfaces; requires canonical-writer review per `AGENTS.md §6`.
* `.taskorchestrator/config.yaml` becomes a new contract-sensitive surface. Schema changes require trait-aware review and propagate across all composing schemas.
* Hook coordination becomes more nuanced — `SessionStart` injects orchestrator state; `PostToolUse` may nudge note upserts; `Stop`/`PreCompact` triggers heartbeats on active claims. More moving parts to debug.

### Impossible / removed

* Removed: silent "claimed but completed without proof bundle" path (mechanical complete-gate).
* Removed: ambiguity about whether ConPort `progress_entry` or task-orchestrator owns workflow state (this ADR + the workflow-authority ADR jointly close that ambiguity).

### Operational consequences

* Each repo-changing TP-CS-NNN follows `AGENTS.md §4` Codex E2E Default: preflight → worktree → packet → validate → implement → codereview → precommit → push → PR → proof.
* PAL chain per `AGENTS.md §5` is enforced via note schemas — the chain is now an artifact, not just a process.
* Operator declares "DMX-ORCH-CLAUDE-SURFACE integration shipped" after Phase 5a (per plan §12); Phase 6 (manual retros) and Phase 7 (full L2, gated) follow as opt-in maturity work.

### Failure modes introduced or removed

* **Introduced**: Schema misconfiguration could block all work items from advancing (M11 risk). Mitigation: TP-CS-013 verification covers schema-load + tag-fallback + `AGENT_CONFIG_DIR` Docker path.
* **Introduced**: Hook misbehavior could noisily nag operators with note-fill suggestions. Mitigation: TP-CS-061 includes cooldown logic; all hooks are read-only suggestions, never auto-fills.
* **Removed**: "Did I remember to write the proof bundle?" — now mechanical.
* **Removed**: "What's the PAL chain status for this TP?" — now queryable via `query_notes(operation="list", role="review")`.

────────────────────────────────────────────────────────────

## Migration Strategy

Five phases plus a gated Phase 7 (full implementation plan at `/Users/hue/.claude/plans/on-a-new-branch-sleepy-robin.md`):

* **Phase 1 — Foundation**: this ADR (TP-CS-001) + promote workflow-authority ADR to `accepted` (TP-CS-002) + create `DMX-ORCH-CLAUDE-SURFACE` sibling series (TP-CS-003) + operator picks schema posture (TP-CS-010) + plugin assessment (TP-CS-100).
* **Phase 2 — Schema + read paths**: author `.taskorchestrator/config.yaml` (TP-CS-011) + verify load (TP-CS-013) + ship read-only `/dx:` commands (next, context, tree, blocked, search) + infrastructure docs.
* **Phase 3 — Doctrine reconciliation + cross-agent**: shared note-filling protocol doc ships first; then parallel updates to CLAUDE.md, authority-matrix, superclaude-workflows, sprint, governance, event-patterns, integration-bridge, AGENTS.md (Codex), copilot-instructions, agents.instructions, personas, agent files, how-to + memory, bare-MCP escape-hatch doc.
* **Phase 4 — Write paths + plugin + output style**: write commands (start, note, complete, block/resume/cancel/reopen, depends), new MCP tool wrappers (preview, complete-tree, backlinks, notes, claim, release), `/dx:implement` rewrite, hooks (session-start, post-edit-nudge, heartbeat), plugin decision + implementation, output style.
* **Phase 5a — Integration shipping close-out**: `/dx:packet` (cross-series-gated), series-state cleanup, plugin + output-style compat audit, final E2E verification.
* **Phase 6 — Self-improving L1+ (manual retros only)**: retrospective schema + `/dx:retro` command + how-to + self-modification ladder doc.
* **Phase 7 — Self-improving L2 maturation (CREATED + BLOCKED)**: 7 TPs for metric collector, anti-pattern detector, auto-triggers, action-feedback wiring, schema versioning, ConPort genealogy automation, action-category mapping. Gated by TP-CS-140 sentinel that goes `terminal` only when operator confirms ≥30 days elapsed and ≥2 manual retros completed. Cancel-cascade if operator decides L2 isn't worth pursuing.

**Rollback approach**: Each TP-CS-NNN ships as its own commit slice per `AGENTS.md §4`; reverting a single slice is straightforward. The `.taskorchestrator/config.yaml` is the only file whose change cascades to all in-flight items; rolling back to "no config" returns all items to schema-free advancement, which is the current state.

────────────────────────────────────────────────────────────

## Verification

How do we prove this ADR is correctly implemented?

* **Schema load**: `mcp__task-orchestrator__get_context(itemId="<any task-packet tagged item>")` returns a populated `schema` array and resolved `guidancePointer`.
* **PAL chain → notes**: `query_notes(operation="list", itemId=<TP id>, role="review")` on any completed TP-CS-NNN returns the four chain notes (`analyze`, `planner`, `codereview`, `precommit`) plus `proof-bundle`.
* **Complete-gate enforcement**: `advance_item(trigger="complete")` on a test item without `proof-bundle` filled returns a gate error citing the missing note.
* **Cross-agent floor**: Reading `AGENTS.md` in isolation (Codex CLI session) gives sufficient instruction to drive the MCP unaided. Same for `.claude/claude.md` (Claude Code), `.github/copilot-instructions.md` (Copilot).
* **Doctrine consistency**: `grep -r "no external orchestrators" .claude/` → zero matches; `grep -r "Task-Master" .claude/agents/` → zero matches; `grep -r "removed.*[Tt]ask-[Oo]rchestrator" .claude/` → zero matches.
* **Plan §11 verification suite**: All 20 verification steps in the plan file pass (schema load, item creation, slash commands, gate enforcement, cross-agent paths, self-improving metrics + anti-patterns + retro creation + action wiring + genealogy, claim lifecycle).
* **Proof bundle queryable**: For one shipped TP-CS-NNN, `query_notes(operation="get")` on its `proof-bundle` returns all fields from `AGENTS.md §9`.

Expected signals:

* `mcp__task-orchestrator__query_items(operation="overview")` shows both `DMX-ORCH-INTEGRATION` (existing) and `DMX-ORCH-CLAUDE-SURFACE` (new) as sibling roots.
* `mcp__task-orchestrator__get_blocked_items(includeAncestors=true)` correctly surfaces cross-series BLOCKS edges.
* `mcp__task-orchestrator__get_next_item(includeAncestors=true)` ranks unblocked items with ADHD scoring per Plan §5.

────────────────────────────────────────────────────────────

## Notes

* Full implementation plan with 68 TPs across Phases 1–7: `/Users/hue/.claude/plans/on-a-new-branch-sleepy-robin.md` (operator-approved).
* Related ADR (proposed): [adr-task-orchestrator-as-workflow-authority.md](./adr-task-orchestrator-as-workflow-authority.md) — should be promoted to `accepted` before this ADR is ratified (TP-CS-002).
* PAL audit findings applied: 9 HIGH, 7 MEDIUM, 4 LOW fixes plus PAL planner sequencing fixes and PAL challenge findings (Phase 5/6 split + Phase 7 gated creation).
* Hidden assumptions register: Plan §16 documents A1–A6 (existing TPs pick up schemas via tag-fallback, `.mcp.json` wrapper stability, ConPort/PAL availability for retros, cross-agent reading mechanics, upstream plugin compatibility, claim residuals).
* Open questions for operator review at execution time: Plan §16.1 Q1–Q4 (Phase 5 split confirmation, provisional ADR acceptance, runtime team estimate for TP-DMX-ORCH-005 terminal, minimal-vs-full schema authoring).
