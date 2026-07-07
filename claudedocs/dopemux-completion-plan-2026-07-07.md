# Dopemux Completion Plan — Fix & Build to Done

**Date**: 2026-07-07 · **Anchored to**: PR #1009 (11 commits, branch `claude/focused-mahavira-5bd29b`)
**Source audits**: `service-audit-2026-07-04.md`, `mcp-fleet-canonical-audit-and-target-design-2026-07-03.md`, `adhd-surfaces-deep-dive-2026-07-04.md`, `runtime-proof-chronicle-mirror-2026-07-07.md`

This plan takes Dopemux from "audited + P0/P1/P2 fixes shipped" to "every plane wired, proven, and dead weight gone." It is organized by plane, each item tagged **[DONE]** / **[IN-FLIGHT]** / **[TODO]** / **[DECISION]** with effort (S ≤0.5d, M 1–2d, L 3–5d) and acceptance criteria. Phases are ordered by dependency: later phases assume earlier ones landed.

---

## Where we are (shipped this cycle)

| Plane | Shipped | Evidence |
|---|---|---|
| Memory spine | chronicle mirror (P0), Phase 1.1 promotion contract (+4 event types), PM `from_phase`/`blocker.cleared` | consumer path **runtime-PROVEN** 0→1 |
| ADHD | ignition (default-start, event-field fix, health-check port), honesty layer (prior), notifier + WMA capability ports | unit + arch tests; runtime pending |
| Untracked-work | lite probe at `dopemux start` + SessionStart hook H5; `work.untracked_*` in contract | 8 tests; F001 rescue owned by Codex |
| MCP fleet | quarantine runtime half (exa retired, desktop-commander default-off), CLI drift fixes | 203 gate tests |
| Dead code | ~43 KLoC removed across 2 graveyard commits | package imports verified |

**The through-line finding**: Dopemux's problem was never capability — it was *wiring* and *twins*. Most features existed; they were stranded behind stream mismatches, naming-inversion twins, and unwired services. This plan finishes the wiring and kills the twins.

---

## Phase A — Prove the runtime (close the NOT_RUN ledger) · ~1 day

- **[IN-FLIGHT] A1** Rebuild `dopecon-bridge` from branch; log a real ConPort decision → full production path fills the chronicle. *Acceptance*: `work_log_entries` row with `source_adapter=conport` from a genuine `/kg/decisions` call (not injection). **S**
- **[IN-FLIGHT] A2** Start `adhd-engine` from branch; verify listener starts, `/api/v1/state` responds, `native_hook_activity` events promote to signal. *Acceptance*: engine healthy on :3025; log shows "ADHD Event Listener started"; `/api/v1/state` returns non-default after activity. **S**
- **[TODO] A3** End-to-end acceptance test (the fleet audit's Phase-5 gate): fresh worktree → `dopemux mcp up` → all planes green → decision logged → mirrored → recapped → retrieved. Codify as `tests/e2e/test_memory_spine_e2e.py` (skip-gated on docker). **M**
- **[TODO] A4** Heartbeat rate-limiting: `raw_activity_events` hit 24,539 spam rows. Add drop/rate-limit for `session-active`/heartbeat types at the capture source. *Acceptance*: heartbeat rows bounded per session. **S**

## Phase B — Memory spine to canonical · ~1 week

- **[TODO] B1** Wire `task.created` emitter — the Phase 1.1 contract has the handler but no producer (no PM create route today). Add emission at the PM create path when one exists, or at task-orchestrator item creation. **M**
- **[TODO] B2** Instance identity per-request: `dope-memory` + `conport` should reject identity-less requests rather than defaulting to `A`/`default` (fail-closed per governance). Compose passes `DOPE_MEMORY_INSTANCE_ID`. **M**
- **[TODO] B3** Skill-layer mirror receipts: `/decision`, `/caveat`, `/followup` append the dope-memory mirror receipt (Trinity Rule 1 beyond the gated CLI). **S**
- **[TODO] B4** Flip `ENABLE_DOPECONTEXT_INDEX=true` after curated entries exist — completes Trinity Rule 2 (chronicle → dope-context retrieval). *Acceptance*: a logged decision is retrievable via dope-context within N minutes. **M**
- **[DECISION] B5** ConPort append-only enforcement (INV-MEM-002/003/004): one migration (REVOKE + trigger) or delete the invariants from doctrine. Currently fiction. **M**

## Phase C — ADHD plane to live · ~1 week

- **[TODO] C1** Verify the June signal-loop series at runtime (deferred all session): read `976f4a957`/`db3977af7` diffs, confirm profile seeding + hyperfocus latch + activity fusion actually fire once the engine runs (Phase A2 unblocks this). **M**
- **[TODO] C2** Wire `native_hooks` PostToolUse → engine `/external-activity` — the first always-on real signal source (routes exist server-side). *Acceptance*: engine attention state changes in response to real tool activity. **M**
- **[DECISION] C3** interruption_shield activation: canonical home already decided (`services/adhd_engine/domains/interruption-shield/`). Wire as an optional engine domain plugin (DND/Slack-status/notification-filter on attention state) or leave shelved. **L**
- **[TODO] C4** Desktop-notification port validation: confirm `DesktopNotificationChannel` fires on host (macOS) for hyperfocus/overwhelm findings; self-disables in-container. **S** (Phase A2 unblocks)
- **[TODO] C5** ADHD-aware recap consumer: dope-memory now annotates `memory_recap` with `adhd_state`; add the consumer-side adaptation (fewer cards when scattered) in the TUI/CLI recap surface. **S**

## Phase D — Held-surface decisions (verify-then-act) · ~1 day total

Each needs one verifying look, not a fleet audit. The three deep-dive reports conflicted on these:

- **[DECISION] D1** `services/adhd-dashboard` — reports split 357 LOC vs 3.5K LOC. Verify actual size + whether any frontend consumes it. Live TUI + React ui-dashboard already exist → likely DELETE, but confirm. **S**
- **[DECISION] D2** `services/session_intelligence` (snake, F-NEW-6) — "canonical salvage" (unified Serena+ADHD session awareness) vs "delete, overlaps attention_monitor." Verify wiring + overlap. **S**
- **[DECISION] D3** `services/voice-commands` — held as ADHD-adjacent. Verify vs live `src/dopemux/voice/` (brand enforcement, different thing). Likely DELETE. **S**
- **[TODO] D4** `services/dopemux-gpt-researcher` relocation — it hosts the **live** extraction backend imported at `cli.py:4328`; the MCP twin is dead but the backend must move to `src/dopemux/extraction/` (or a kept path) before the twin dir can die. **M**

## Phase E — MCP fleet single-source-of-truth (fleet audit P1) · ~1 week

- **[TODO] E1** Unified catalog: merge `mcp_catalog.yaml` + `src/dopemux/mcp/registry.yaml` + services/registry MCP slice into one schema-validated catalog (canonical writer: dopemux). **L**
- **[TODO] E2** Codegen from catalog: `.mcp.json`, global/Codex config, compose env blocks, health-probe lists, doctrine docs — with the existing drift-test pattern widened. **M**
- **[TODO] E3** `dopemux mcp ensure` (idempotent, `--fast`): daemon → compose up required → recreate off-compose `pal-mcp-server` → orchestrator singleton → capability probe. H3 SessionStart hook calls `ensure --fast`. **L**
- **[TODO] E4** Command↔tool-surface drift gate: CI fails when a `.claude/command` references a tool no server exposes (today: 6 broken ConPort refs). **M**
- **[DECISION] E5** ConPort single-surface: retire the upstream-wrapper path, rewrite wrappers/commands against the real 17-tool surface; execute packets 106/107/201/202 (JSON-RPC parity, kill GET-mutation, product context, relationship write API). **L**
- **[DECISION] E6** Serena single-surface ADR: deployed=upstream wrapper is documented reality; archive the 45-tool local candidate or promote via ADR+proof. Keep 6 write tools out of default profile. **M**
- **[TODO] E7** Loopback-bind the remaining 0.0.0.0 listeners (conport/dope-memory/serena/gptr) — closes the standing exposure family. **S**

## Phase F — Final hygiene & proof · ~2–3 days

- **[TODO] F1** Regenerate doctrine docs from the catalog; mark aspirational ADHD automation as such everywhere it's still overclaimed. **M**
- **[TODO] F2** Qdrant collection GC keyed to `git worktree list`; Voyage cost guard on dope-context. **M**
- **[TODO] F3** Delete remaining dead config surfaces (`.claude/claude_config.json` writer, `wire_claude_mcp.py`) so no tool resurrects retired servers. **S**
- **[TODO] F4** Proof bundles per phase per AGENTS.md §8/§9; merge PR #1009. **S**

---

## Critical path (do in this order)

1. **Phase A (runtime proof)** — unblocks everything; A1/A2 in-flight now.
2. **Merge PR #1009** after A1/A2 — it's the foundation the rest builds on.
3. **Phase D decisions** — cheap, removes ambiguity, shrinks surface before deeper work.
4. **Phase E1–E3 (catalog + ensure)** — the fleet audit's insight: this must precede any config rewrite, or sync tools keep regressing reality.
5. **Phases B/C in parallel** — independent planes, highest user-visible value.
6. **Phase F** — rides on the catalog + CI gates so fixed things stay fixed.

## Effort roll-up

| Phase | Effort | Blocking? |
|---|---|---|
| A — runtime proof | ~1 day | unblocks all |
| B — memory canonical | ~1 week | after A |
| C — ADHD live | ~1 week | after A2, parallel with B |
| D — held decisions | ~1 day | independent |
| E — fleet SSOT | ~1 week | after D |
| F — hygiene/proof | ~2–3 days | last |

**Total to "done": ~4–5 focused weeks**, front-loaded so the highest-leverage, already-proven pieces (memory spine, ADHD ignition) land first.

## Invariants to hold throughout

- Every new event stream: ≥1 publisher ↔ ≥1 consumer (the disease that emptied the chronicle).
- Every service: real healthcheck = capability probe, loopback bind, identity-required requests.
- No build-then-strand: SERVICE_CATALOG tier review + fleet `lifecycle:` field enforced at PR time.
- Fail-closed on protection/identity; fail-open on advisory/telemetry.
