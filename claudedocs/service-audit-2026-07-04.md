# Dopemux Full-Service Audit — Planned vs Implemented, Effectiveness, and Integration Design

**Date**: 2026-07-04 · **Worktree**: `focused-mahavira-5bd29b` @ `8f71ab9af` (post-quarantine merge #1001)
**Method**: 6 parallel read-only cluster auditors (2 Sonnet on focus areas, 4 Haiku on mechanical clusters) + synthesis against the 2026-07-03 MCP fleet audit (`claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md`) and the 2026-05-31 ADHD audit. No files modified except this report + appendix. Runtime NOT probed (static wiring evidence only) — every reachability claim below is compose/registry/import-graph evidence.
**Companion**: `service-audit-2026-07-04-appendix-memory-spine.md` (full memory-spine agent report).

---

## 1. Executive summary

1. **The untracked-work tracker exists and was built well — then stranded.** Serena v2 "Feature 1: Untracked Work Detection" (`services/serena/untracked_work_detector.py`, `untracked_work_storage.py` (974 lines), `git_detector.py`, `batch_track_tool.py`, six MCP tools in `services/serena/mcp_server.py:1190-1255`) implements the complete lifecycle: detect uncommitted work with no matching ConPort task → confidence-scored → cross-session reminders (exponential backoff, quiet hours, snooze) → auto-track at ≥0.85 confidence into ConPort `progress_entry` → auto-close when a matching commit lands (≥80% file overlap vs last 5 commits). **It is unreachable at runtime**: the deployed Serena container builds `docker/mcp-servers/serena/` (wrapper only), and the session Serena is upstream OSS. Design 4/5, reachability 1/5.
2. **The ADHD layer made real progress since 2026-05-31 — honesty first, wiring second.** A 36-commit remediation series verifiably fixed the "fabricated telemetry" class (C2/H4/C3: `status --attention` now shows UNAVAILABLE; TrendsPanel labels demo data; React dashboard **builds clean — verified by actual `npm run build` PASS**). But the engine is still `enabled_in_smoke: false` (a default session runs no ADHD engine), its ConPort URL default still points at dope-context's port (`config.py` → :3010, a wrong-service write hazard), the event listener start is gated on a possibly-never-set `event_bus`, and no external activity source exists.
3. **The chronicle is empty by architecture, not by accident — and the root cause is now precise.** Three independent agents converged: (a) ConPort publishes `decision.logged` to Redis stream `dopemux:events` while dope-memory's consumer listens on `activity.events.v1` (≈4 one-line fixes); (b) the PM plane emits only `task.blocked/completed` + `workflow.phase_changed` with `from_phase` hardcoded `"unknown"` (`src/dopemux/pm/writes.py:325`), never `task.created/failed/assigned`; (c) no untracked-work event type is in the promotion allowlist (`services/working-memory-assistant/promotion/promotion.py:20-27`), and `eventbus_consumer.py:384` handles only `session.ended`.
4. **Shadow-twin syndrome and dead mass persist post-quarantine.** The #1001 quarantine fences only exa + desktop-commander out of *generated client configs*; compose still builds both, `DEFAULT_MCP_SERVICES` still lists desktop-commander, and the six non-catalog dead surfaces (mcp-client, mcp-integration-bridge, router, task-router, services/serena vendored tree, services/dopemux-gpt-researcher) are untouched — one (`mcp_commands.py:206`) can still *resurrect* the dead integration-bridge. Separately, ~8.2 KLoC of confirmed zero-import dead code sits in services/ (ml-predictions, ml-risk-assessment, intelligence, monitoring, monitoring-dashboard, slack-integration, voice-commands, top-level `dashboard/`) — one big aspirational drop from 2026-04-05.
5. **The live core is genuinely healthy.** dopecon-bridge (3 consumers), dope-context (loopback-bound), conport, gptr-mcp, task-orchestrator, the PM plane write-routing, `src/dopemux/tui/` (real operator HUD) + `src/dopemux/ui/` (render substrate), voice enforcement layer, profile analytics → all wired, consumed, recently maintained.
6. **Operational hazard**: the main checkout at `/Users/hue/code/dopemux-mvp` is stale (`dbe34fce5`, ancestor of the quarantine merge) — the fleet-catalog gate, its contract test, and the canonical fleet audit doc are unreachable from main's working copy. "Current state" depends on which worktree you stand in. `git pull` on main is the cheapest fix in this whole report.

---

## 2. Focus answer: the untracked-work tracker

### What was planned and built (Serena v2 Feature 1)
| Capability | Implementation | Evidence |
|---|---|---|
| Detect uncommitted work w/ no ConPort task | multi-signal confidence scoring + ConPort matcher | `services/serena/untracked_work_detector.py` |
| Persist w/ state machine | `detected → acknowledged → snoozed → converted_to_task → abandoned` | `untracked_work_storage.py:19-25` (ConPort custom_data `"untracked_work"`) |
| Cross-session reminders | exponential backoff, once-per-session cap, quiet hours, snooze 1h/4h/1d | `untracked_work_storage.py:632-714` |
| Auto-close on commit | ≥80% file overlap vs last 5 commits | `untracked_work_storage.py:418-536` |
| Auto-track | confidence ≥0.85 → ConPort `log_progress` | `untracked_work_storage.py:538-630` |
| Operator surface | 6 MCP tools: detect/track/snooze/ignore/get_config/update_config | `mcp_server.py:1190-1255, 1793-1822, 3338+` |

### Why you can't use it
Compose `serena` (compose.yml:538-562) builds `docker/mcp-servers/serena/Dockerfile`, which copies only `wrapper.py`/`info_server.py` — never `services/serena/`. The Serena MCP in sessions is upstream OSS (no untracked-work tools). SERVICE_CATALOG itself marks `services/serena` runtime authority "unknown".

### What actually runs today (two narrow slices, both in `dopemux start`)
- **Dirty-main protection**: `uncommitted_detector.py` → `main_worktree_detector.py` → `protection_interceptor.py` (cli.py:205-206, 1954). Bugs: **fail-open** on git failure (`uncommitted_detector.py:135-144` — "assuming no changes" silently disables protection, violates fail-closed doctrine); rename entries stored as literal `"old -> new"` strings (:169); stash count is repo-wide, not per-worktree (:183-184); NoneType crash path at `main_worktree_detector.py:109`.
- **Orphaned-worktree recovery**: `worktree_recovery.py` menu at cli.py:1928 (ADHD-conformant: max 3 options, 30s timeout).

### Recommended consolidation (cheap — Feature 1 has no LSP dependency, only git + ConPort)
1. Lift `git_detector.py` + `untracked_work_detector.py` + `untracked_work_storage.py` out of `services/serena/` into `src/dopemux/` (keep ConPort custom_data as canonical store).
2. Wire detection into the two live entry points: `dopemux start` (beside the recovery menu) and a SessionStart hook (H1–H4 pattern already exists in `.claude/hooks/`).
3. Add `work.untracked_detected` / `work.untracked_converted` to the promotion allowlist (`promotion/promotion.py:20`) — or emit via the already-wired `dopemux capture emit` — so untracked work reaches the chronicle.
4. Bridge the convert path to task-orchestrator `manage_items` so converted work enters the real task system, not just ConPort progress.
5. Fix the two live bugs in the existing slice (fail-open + NoneType) and quarantine the residue (workspace-watcher — whose README falsely claims "Production" — activity-capture, both session-intelligence twins, services/session-manager).

Also confirmed: **nothing anywhere detects "sessions without task packets"** — genuine gap if you want it; the SessionStart hook in step 2 is the natural home.

---

## 3. ADHD cluster (deep dive vs 2026-05-31 baseline)

### Verified fixed (direct evidence)
- **C2** fabricated `status --attention` telemetry → honest UNAVAILABLE banding (`cli.py:2711-2774`, `attention_monitor.py:128/482` `data_status` field).
- **H4** TrendsPanel fake sparklines → real mode prints "UNAVAILABLE no live trend data" (`ui/dashboard.py:385-395, 410-413`); demo data behind explicit `--demo` banner (:487-488); ADHDStatePanel makes a real `GET /api/v1/state` with provenance rows.
- **C3** React ui-dashboard unbuildable → **builds clean (npm run build PASS, 2306 modules)**; all 4 missing components exist. Residual: dual npm/pnpm lockfiles.
- **C4/H7** doctrine dishonesty → project CLAUDE.md now explicitly disclaims timers/auto-save/forced breaks as planned-not-observed.
- **M1** naming inversion → now documented as duplicate in SERVICE_CATALOG/TRUTH_CANONICALS (but stub dirs still on disk).

### Claimed fixed, unverified at runtime (commit + test evidence only)
Signal-loop series (~20 commits): profile seeding at startup, activity fusion into assessment, hyperfocus latch (`db3977af7`), per-user baselines, idle-forwarding guards + 241-line activity-loop test. Diffs unread; runtime NOT_RUN.

### Still broken / new findings
| Finding | Location | Severity |
|---|---|---|
| Engine excluded from default stack (`enabled_in_smoke: false`) — normal session gets no ADHD engine at all | `services/registry.yaml:192-199` | HIGH (gates everything else) |
| ConPort URL default = :3010 = **dope-context's port** — wrong-service write hazard, not just dead port | `services/adhd_engine/config.py` (corroborated system-adhdengine.md:204-205) | HIGH |
| Event listener start gated on `engine.event_bus` that init may never set — signal-loop series conditionally inert | system-adhdengine.md:185,196 | HIGH |
| task-orchestrator coordinator health-checks ADHD engine at `:8080` (= Leantime) | system-adhdengine.md:202 | MED |
| Dead triangle unchanged 5+ wks: `workflow_manager.py`, `adhd_orchestrator.py`, `main_orchestrator.py`, `rte_adapter.py` (zero live callers, latent TypeError bugs) | `src/dopemux/adhd/`, `src/dopemux/orchestrator/` | MED (delete or wire) |
| adhd-dashboard still compose-orphaned (exists only as CORS string, compose.yml:482/522); notifier twins unresolved | services/ | LOW |
| `interruption_shield/` (repo root) — NEW unaudited surface, 5 files, wiring unknown | repo root | follow-up |

### Highest-leverage ADHD wiring (in order)
1. Fix `event_bus` init → verify listener starts.
2. Fix conport_url 3010→3004 (or fail-closed env requirement).
3. Flip `enabled_in_smoke: true` — the single change that makes the whole remediation series real for a default session.
4. Wire `native_hooks.py` PostToolUse → engine `/external-activity` (routes `/log-intent`, `/save-context`, `/external-activity`, `/log-git-event`, `/state` already exist server-side) — first always-on signal source, no new services needed.
5. Delete the dead triangle + hyphen/underscore stub dirs.

---

## 4. Memory spine (chronicle) — root cause and fix

Design (Memory Trinity: ConPort canonical → dope-memory chronicle mirror → dope-context retrieval) validated as sound. Implementation ~75%:

- ✅ `error.encountered` wired (native_hooks → capture_client, shipped in #993 with Redis socket timeouts).
- ⚠️ `decision.logged` **built but blocked by a stream-name mismatch**: ConPort publishes to `dopemux:events`; dope-memory's EventBusConsumer subscribes to `activity.events.v1`. ≈4 one-line changes (ConPort + DopeconBridge publish targets) unblocks it.
- ❌ `task.*`/`workflow.phase_changed` partially emitted: PM plane sends `task.blocked/completed` + `workflow.phase_changed` on transitions only, `from_phase` hardcoded `"unknown"` (`src/dopemux/pm/writes.py:325`); `task.created/failed/assigned`, `blocker.cleared` never emitted; dope-memory mirror is best-effort with silently swallowed failures (`writes.py:400-418`).
- ❌ `eventbus_consumer.py:384` handles only `session.ended`; workspace-watcher/activity-capture event families have no consumer (moot while those services stay unwired).
- Peripheral debt: WMA legacy `main.py` vs deployed `dope_memory_main.py` twin trap; mcp-capture server implemented but registered nowhere; copilot transcript ingester implemented + consumed as a library but nothing schedules it.

**Chronicle fill sequence** (order matters): stream-name fix → PM event completeness (`task.created/failed`, real `from_phase`) → promotion allowlist additions (untracked-work types) → schedule copilot ingester (SessionEnd hook or cron) → then flip dope-context decision indexing (Trinity Rule 2) once curated entries exist.

## 5. MCP/integration plane

- **Live and healthy**: dopecon-bridge :3016 (consumers: conport, task-orchestrator, adhd-engine — the only multi-consumer event seam; candidate canonical event plane), dope-context :3010 (loopback-bound ✅), serena wrapper :3006, gptr-mcp :3009, conport, task-orchestrator.
- **Bugs**: dope-context healthcheck `|| exit 0` = always-pass (compose.yml:375 — contradicts the #993 "honest healthchecks" work; change to `|| exit 1`); `mcp_commands.py` drift — `DEFAULT_MCP_SERVICES` still includes quarantined desktop-commander (:36-48), `mcp down` list asymmetric to `up` (leaves dopecon-bridge/dope-memory/task-orchestrator/pal-stdio running, :135-138), start-all fallback resurrects dead integration-bridge (:206), script paths break from wheel installs (:110/:195); exa identity contradiction (catalog = exec-into-litellm stdio vs compose = dedicated :3011 HTTP container); compose.yml:605 comment mislabels exa as "Leantime Bridge".
- **Quarantine (#1001) is real but thin**: config-generation only; runtime fleet unchanged; six non-catalog dead surfaces untouched; orphan volumes remain (compose.yml:41-44).
- **Branch hazard**: main checkout stale at `dbe34fce5` → fleet-catalog gate/tests/audit doc unreachable from main's working copy; whether main's `mcp_catalog.yaml` carries the personality/lifecycle fields the contract test requires is UNKNOWN until reconciled.

## 6. Orchestration / PM plane

- **Authority routing works as documented** (PM_PLANE.md): Leantime = metadata, task-orchestrator = transitions, ConPort = progress/decisions, dope-memory = best-effort mirror. All four write paths verified wired.
- **Gaps**: event emission incompleteness (§4); `services/agents/` family (14 files) orphaned with authority explicitly UNKNOWN in AGENTS.md §6; orchestrator enforcement hooks dormant behind never-set `actor_authentication.enabled`; ConPort access split across :3004/:3005; `services/task-orchestrator/task_orchestrator/` legacy module still in tree beside canonical `app/main.py`; note the Python :8000 service is the PM workflow API — the canonical workflow MCP remains the Kotlin jar :7890 (fleet audit target: rename Python service → `workflow-api` to end the name collision).

## 7. Misc / intelligence cluster

- **Keep-and-invest**: `src/dopemux/tui/` (the real operator dashboard — Textual HUD, 8 orchestrator-data panels), `src/dopemux/ui/` (5.3 KLoC render substrate, most-wired surface; flag: 82KB `cockpit/runtime_contract.py`), `src/dopemux/voice/` (brand enforcement, live), `profile_analytics.py` (+`analytics.py` facade; live via `profile_commands.py:267`), `services/copilot_transcript_ingester` (live library; relocate under src/ — services→src import is a layering smell), `services/shared/mcp/pal_client.py` (sole live piece of a 4 KLoC tree).
- **Dead (~8.2 KLoC, zero imports, all last-touched 2026-04-05 except noted)**: services/intelligence (306), ml-predictions (1,282), ml-risk-assessment (1,159), monitoring (516), slack-integration (138, with unreachable-code bugs), voice-commands (900), top-level `dashboard/` (2,011), monitoring-dashboard (1,886 — **0.0.0.0:8098 unauth exposure still in tree** at `server.py:1563`, but startup-fatal import at `server.py:78` means it can't boot; deleting the dir retires both), `scorer.py` (16), `suggestion_engine.py` (61).

---

## 8. Cross-cutting patterns (why this keeps happening)

1. **Build-then-strand**: features get implemented to high quality in a service dir, then deployment moves elsewhere (Serena Feature 1, WMA main.py, dcp facade dir-as-pointer). *Countermeasure*: SERVICE_CATALOG tier review at PR time + the fleet catalog's `lifecycle:` field enforced by the contract test (already written — needs to land on main).
2. **Emit-without-consumer / consumer-without-emitter**: workspace-watcher emits events nothing reads; chronicle reads streams nothing writes to. *Countermeasure*: treat event streams as contract surfaces — a CI check that every subscribed stream has ≥1 publisher and vice versa.
3. **Fail-open as default reflex** (uncommitted detector, PM memory mirror, all hooks) contradicts the repo's fail-closed doctrine. Acceptable for hooks; not for protection features.
4. **Honesty debt gets fixed faster than wiring debt** — the ADHD series proves the team culture responds to "stop lying" findings; leverage that: every dashboard/status surface should carry `source/updated/data_status` provenance (the pattern `ui/dashboard.py` now uses).

## 9. Optimal interaction model

The 2026-07-03 fleet audit §6–7 already defines the target (one catalog + codegen, `dopemux mcp ensure`, authority labels, per-request identity, loopback binds, memory-spine wiring). This audit **confirms it and adds four service-layer amendments**:

1. **dopecon-bridge is the event plane** — it's the only seam with 3 live consumers. All promotable events (PM transitions, ConPort decisions, untracked-work detections, ADHD state changes) route through it on **one named stream contract** (`activity.events.v1`), ending the dopemux:events split.
2. **Untracked-work detection joins the session lifecycle**: SessionStart hook (detect + surface, max-3 ADHD menu) → ConPort custom_data (canonical) → capture event (chronicle) → optional task-orchestrator item (convert). This is the missing "ambient capture" leg of the Trinity.
3. **ADHD engine consumes hooks, not daemons**: PostToolUse/Stop → engine HTTP routes (already built) → engine assessment → surfaced only in `tui/` + `status` with provenance. Skip the watcher/capture services entirely — hooks are the signal source that actually exists.
4. **One dashboard family**: `tui/` = operator HUD (live), React ui-dashboard = optional web view (now builds), everything else in the dashboard namespace deleted.

## 10. Prioritized roadmap

**P0 — one-line-ish, high leverage (do first)**
- [ ] `git pull` the stale main checkout (unblocks the quarantine gate + audit doc visibility).
- [ ] Stream-name fix: ConPort/DopeconBridge publish → `activity.events.v1` (≈4 lines) → chronicle starts filling.
- [ ] dope-context healthcheck `|| exit 0` → `|| exit 1` (compose.yml:375).
- [ ] ADHD `config.py` conport_url :3010 → :3004.
- [ ] uncommitted_detector fail-open → fail-closed (:135-144) + NoneType guard (main_worktree_detector.py:109).

**P1 — the two focus features (≈ a packet each)**
- [ ] **Untracked-work rescue**: lift Feature 1 → `src/dopemux/`, wire `dopemux start` + SessionStart hook, promotion allowlist entries, orchestrator convert bridge (§2).
- [ ] **ADHD ignition**: event_bus init fix → verify listener → `enabled_in_smoke: true` → native_hooks PostToolUse → `/external-activity` (§3).

**P2 — event completeness + CLI drift**
- [ ] PM plane: emit `task.created/failed/assigned`, `blocker.cleared`; real `from_phase`; surface mirror failures (writes.py).
- [ ] `mcp_commands.py`: fix DEFAULT list, up/down asymmetry, dead-bridge fallback, wheel-safe paths.
- [ ] Schedule copilot ingester (SessionEnd hook or cron).
- [ ] Resolve exa identity (catalog vs compose) — wire-or-retire decision.

**P3 — dead-mass excision (single "graveyard" PR, ~12+ KLoC)**
- [ ] Delete/SYSTEM_ARCHIVE: the 8.2 KLoC misc set (§7) + router, mcp-client (+ orphan volumes compose.yml:41-44), task-router, services/serena vendored tree, services/dopemux-gpt-researcher, ADHD stub twins, dead triangle, workspace-watcher/activity-capture/session-intelligence ×2/session-manager (or honest lifecycle labels), scorer.py, suggestion_engine.py, WMA legacy main.py.
- [ ] Then: `services/agents/` authority decision, Serena single-surface ADR, ConPort endpoint unification, interruption_shield audit (still unaudited).

---

## Honesty ledger (NOT_RUN)
No runtime probing anywhere (docker state unknown; conport/dope-memory were down at session start). ADHD signal-loop commit diffs unread (claimed-fixed only). dcp facade 12-tool verification NOT re-confirmed this session. `.claude/settings.json` hook-dispatch grep for ADHD shell scripts not re-verified. interruption_shield/ unaudited. Two agent contradictions resolved by evidence strength: ui-dashboard build (verified PASS) supersedes "vite.config.ts missing"; `services/activity-capture` existence (direct ls) supersedes one agent's "no such dir".
