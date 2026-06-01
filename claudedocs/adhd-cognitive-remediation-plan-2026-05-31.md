# DMX-ADHD-COGNITIVE-REMEDIATION — Comprehensive Plan

**Date:** 2026-05-31 · **Branch base:** `feat/autoreview-platform-series` (audit HEAD `63918aab1`)
**Ambition (user-selected):** **Full build** — make the entire cognitive-intelligence layer genuinely functional, plus all honesty/consolidation/hygiene work.
**Inputs:** the audit (`claudedocs/adhd-cognitive-ux-audit-2026-05-31.md`), the in-repo signal inventory, and the external design-research brief (12 evidence-based principles).
**Status:** comprehensive plan — to be PAL-validated, then formalized via analyze→tracer→planner, then loaded into task-orchestrator as a work tree.

---

## 0. Guiding decisions (the disposition spine)

"Full build" = build the **real capability**, not preserve the mess. Every audit finding gets exactly one disposition:

| Disposition | Meaning | Examples |
|-------------|---------|----------|
| **BUILD** | Implement for real | real signal pipeline, engine input loop, calibration, predictive restoration |
| **WIRE** | Already built but dead — connect it | `interactive_prompts` (max-3), `adhd_error_messages`, `progress_display` |
| **CONSOLIDATE** | Multiple overlapping → one canonical | 3 attention systems → 1; 4 context writers → 1; 3 event APIs → 1 |
| **REBUILD** | Broken scaffold → make it work | `ui-dashboard`, hyperfocus/break enforcement |
| **DELETE** | Dead, superseded, or harmful | dead orchestrator triangle, duplicate dirs, orphaned/mis-ported hooks |
| **HARDEN** | Works but unsafe/unhonest | secrets, `0.0.0.0` dashboard, fail-honest UX, privacy |

**Canonical authorities (resolves audit "no canonical writer" + AGENTS.md §6/§10 Known Dangers):**
- **Attention/energy/cognitive state →** the FastAPI `services/adhd_engine` (it owns the real assessment math, ConPort link, monitors). The in-process `AttentionMonitor` and `monitor_daemon` are **KEPT-until-live, then deleted** *after* T4 proves the engine ingests real signal (consensus fix — don't remove the only currently-running capture path before the replacement works). `monitor_daemon`'s file-watch capture logic is **migrated into `native_hooks`** before deletion, not discarded.
- **Event backbone →** `ADHDEventEmitter` (Redis stream `dopemux:events`). `src/dopemux/event_bus.py` and the `workspace_watcher`/`external_activity` third API are reconciled onto it. **Capture must survive engine-down** (`enabled_in_smoke:false`): buffer-and-replay (disk/Redis queue), not naked synchronous HTTP — PAL tracer finalizes transport.
- **Context preservation →** ONE writer (candidate: engine `ContextPreserver` ConPort-backed, OR `context_manager`; **PAL analyze decides** — see T5). The working manual `context_manager` stays authoritative as fallback until the chosen writer is proven.
- **Operator identity →** a deterministic single-operator `user_id` must be resolved FIRST (the engine is keyed by `user_id` but the CLI has no auth identity). This is **T4-00, a gating dependency** for all per-user state/calibration (consensus fix — was an open question).
- **Engine stays cognitive-only** (AGENTS.md §6): operator/cognitive state + recommendations + hooks. No task/PM authority writes. This is a hard constraint on every track.

**Privacy invariant (research principle 11/12), applies to all tracks:** local-only by default, no telemetry egress, log *derived state transitions* only — never keystroke content or file contents; one-command kill switch + data wipe.

---

## 1. Track map & phasing

```
T1 Honesty layer ───────────────────────┐ (front-load; ships trust; bridges until T4 real)
T2 Wire dead ADHD UX ────────────────────┤ Phase 1 (low-risk wins)
T6 Hygiene (naming/secrets/dead-code) ───┘
        │ (T2 salvage must precede T3/T6 dead-code delete)
T3 Consolidate attention → ONE ──────────┐
T4 Real activity-signal pipeline ────────┤ Phase 2 (structural core — analyze/tracer heavy)
T5 Context canonical writer + autosave ──┘
        │
T7 Dashboards + enforcement + notifier ──── Phase 3 (depends on T4 real data)
```

Phasing is a *dependency order*, not a scope cut — all tracks are in scope (full build).

---

## 2. Tracks → work packets (TPs)

### T1 — Honesty layer  *(disposition: REBUILD presentation; HARDEN docs)*
The UI must never present defaults as measurement. Bridges the gap until T4 makes signals real.
- **T1-01** Confidence-band UX primitive: shared renderer for `measured / inferred / low-confidence / calibrating / unavailable` (principle 7/8). Used by status + dashboards.
- **T1-02** `status --attention` (`cli.py:2668`): replace always-default output with the confidence-band primitive; when no live monitoring data → "no active monitoring data," not `normal/50%/0`.
- **T1-03** `TrendsPanel` (`ui/dashboard.py:372`): gate DEMO sparklines behind `--demo`; show "calibrating / no data" in live mode; include it in `action_refresh_all`.
- **T1-04** Doctrine doc corrections: `.claude/CLAUDE.md` + global config — mark auto-save-30s, energy/break hooks, hyperfocus-mandate, 25-min as **"planned, not yet wired"** until the relevant track lands; remove the false "active" framing.
- **Accept:** no surface displays a fabricated number; docs match runtime; primitive unit-tested for each state.

### T2 — Wire the already-built ADHD UX  *(disposition: WIRE)*
The doctrine-compliant UX exists but is reachable only via the dead orchestrator triangle. Rewire to a LIVE entry point (call directly from CLI; do **not** revive `MainOrchestrator`).
- **T2-01** Route reachable CLI choice prompts through `ux/interactive_prompts.py` (`max_choices=3` + progressive disclosure "Show more…").
- **T2-02** Wire `adhd_error_messages.py` into `error_handling.py` so reachable errors use gentle problem/why/fix framing.
- **T2-03** Wire `ux/progress_display.py` where progress is rendered.
- **Accept:** at least the launch/profile/wizard flows use max-3 + gentle errors; the modules have non-test callers; salvage complete so T3/T6 can delete the dead triangle.

### T3 — Consolidate attention → ONE system  *(disposition: CONSOLIDATE + DELETE)*
- **T3-01** Designate `adhd_engine` canonical; **unify state enums** (reconcile NORMAL/DISTRACTED vs TRANSITIONING/OVERWHELMED into one taxonomy).
- **T3-02** Repoint `status --attention` to read engine state (via a local cache the engine writes, or HTTP when running; honest "unavailable" when engine down — honest degradation already exists in `ui/dashboard.py:154`).
- **T3-03** DELETE the dead orchestrator triangle (`workflow_manager`, `adhd_orchestrator`, `main_orchestrator`, `rte_adapter`, `adhd_optimizations`) — **after** T2 salvage. These are unambiguously dead and safe to remove now.
- **T3-04** DELETE in-process `AttentionMonitor` + `monitor_daemon` — **only after T4-03/04 prove the engine ingests real signal** (consensus fix: don't remove the only running capture path before its replacement is live). Migrate `monitor_daemon`'s file-watch capture into `native_hooks` (T4-02) first. Fix/remove the latent bugs (hyperfocus latch, `config=` TypeError, `"state"` key mismatch) by deletion.
- **Accept:** exactly one attention system; one enum; `status` reads it; dead modules gone; import graph clean; no capture gap during cutover.

### T4 — Real activity-signal pipeline  *(disposition: BUILD — the core)*
Apply research principles 1–5. Wire the real signal end-to-end.
- **T4-00 (GATE)** Resolve deterministic operator `user_id` for the single-operator CLI (machine/install-scoped id, content-free). **Blocks T4-03/04/05** — per-user state/baselines cannot be stored or keyed without it.
- **T4-01** Reconcile the 3 event APIs → `ADHDEventEmitter` canonical; **fix the `EventType`→`EventTypes` ImportError** killing `workspace_watcher` + `external_activity`; fix `/record-progress` emitting `claude_tool_completed` with no listener handler. Define the **buffer-and-replay** transport so capture survives engine-down (disk/Redis queue; tracer finalizes HTTP-POST vs Redis-XADD).
- **T4-02** Signal capture: emit real activity from `native_hooks` (PostToolUse/PostToolUseFailure/PreToolUse/UserPromptSubmit) → `POST /api/v1/activity/{user}` (fix `log_progress.sh` port 8080→8095 and register, OR emit directly in `native_hooks._on_post_tool_use`; native_hooks is a per-event subprocess → IPC required, content-free payload only).
- **T4-03** Close the input loop: fix the `routes.py:671-674` stub to call assessment + write `current_energy_levels`/`current_attention_states`; **seed a default profile** at startup/first-activity so monitor loops + the `user_id in user_profiles` gate are non-empty.
- **T4-04** Real assessment: `_assess_*` consumes real activity (`ActivityTracker.get_recent_activity` fed from captured signal) instead of defaults; fuse weak signals (cadence, edit:nav ratio, error/undo rate, switch freq, time-of-day) — principle 4.
- **T4-05** Per-user baseline calibration (principle 1): relative percentile baselines over first N≈5–10 sessions; "calibrating" state; **replace hard-coded thresholds** (45-min hyperfocus, 10-min distracted) with relative ones.
- **T4-06** Boundary detection (principle 2): commit/test/build/file-close breakpoints drive state changes, not wall-clock.
- **T4-07** Correctness: fix hyperfocus latch (separate accumulated-focus clock from post-transition state clock); enforce idle≠distracted (≥2 corroborating signals — principle 3).
- **Accept:** with a session running, `GET /state` reflects real, changing activity; calibration gates classification; thresholds are per-user; integration test drives activity→state (not mocks).

### T5 — Context preservation: canonical writer + real auto-save + restoration  *(disposition: CONSOLIDATE + BUILD)*
- **T5-01** Pick ONE canonical context writer (PAL analyze decides among engine `ContextPreserver` / `context_manager` / WMA / dope-memory). Demote/retire the others to non-authoritative.
- **T5-02** Real auto-save: replace `ContextManager.start_auto_save()` stub; wire `native_hooks` Stop/PreCompact to persist context (and/or fix+register `save_context.sh` port). Make the doc claim true or strike it.
- **T5-03** `predictive_context_restoration.py`: make real (currently orphaned) and wire to the canonical writer, or DELETE if T5-01 supersedes it.
- **T5-04** Fix ConPort URL mismatch (engine `3010` vs compose `3005`); resolve WMA orphan/manifest-forbidden status.
- **Accept:** one canonical writer; auto-save observably persists on Stop/PreCompact; restoration round-trips; ports correct.

### T6 — Hygiene  *(disposition: DELETE + HARDEN)*
- **T6-01** Service-dir naming: keep `adhd_engine/` (real) + `adhd-notifier/` (real); delete `adhd-engine/` fragment + `adhd_notifier/` shim; document the (now removed) inversion trap.
- **T6-02** Secrets: remove `dev-key-123` + `dev-only-change-me` defaults; fail-closed when unset in non-dev. (Feeds existing beta-readiness security backlog — coordinate, don't double-fix.)
- **T6-03** Dead-code deletion (post-T2 salvage): dead triangle, stale `__init__.py:12` archived-ref comment.
- **T6-04** Orphaned hooks: consolidate `check_energy/log_progress/save_context/track_file_edit.sh` into `native_hooks` or delete; remove the 8080(=Leantime) mis-port.
- **Accept:** no duplicate/orphan ADHD dirs; no default secrets; clean hook surface.

### T7 — Dashboards + enforcement + notifier  *(disposition: RETIRE-default + BUILD-minimal)*
Depends on T4 (real engine data) **and T8 (validated signal)** — consensus: don't ship surfaces/notifications on an unproven pipeline. **Scope guard: no multi-rule policy engine; single opt-in breakpoint-deferred accommodation only.**
- **T7-01** Dashboard decision (PAL analyze): canonical = Textual `tui/app.py` (real data, LIVE). **Default RETIRE** `ui-dashboard` + `services/adhd-dashboard` + `services/monitoring-dashboard`. React rebuild is a **separate, explicitly-justified project**, not in this remediation (consensus: it's an internal scaffold, not user-directed).
- **T7-02** Hyperfocus/break accommodations (principles 5/6/9): opt-in, dismissible, snoozeable, deferred-to-breakpoint; wire `HyperfocusGuard` to a reachable surface; no auto-modals/shame/streaks (principle 10). **Blocked by T8 validation + T1-04 doc honesty** (don't ship enforcement copy that diverges from docs).
- **T7-03** Deploy `adhd-notifier` (add to compose) wired to engine recommendations; honor privacy invariant. Blocked by T8.
- **T7-04** Canonical dashboard renders real engine state via the confidence-band primitive (T1-01).
- **T7-05** Secure `monitoring-dashboard` (`0.0.0.0` unauth) — or retire it (default retire per T7-01).
- **Accept:** one canonical dashboard showing real data with confidence bands; ONE opt-in breakpoint-deferred accommodation; notifier deployed behind T8; no unauth exposure; React rebuild explicitly out of scope.

### T8 — Signal validation, safety rails & observability  *(disposition: BUILD — consensus-added)*
The riskiest assumption (both reviewers) is that content-free tool-hook telemetry can reliably infer ADHD states. This track makes the pipeline *correct-enough, observable, and privacy-safe*, not just *wired*. **Gates T7.**
- **T8-01** Anti-regression end-to-end wiring test: start engine → emit a synthetic `native_hooks` event → assert `GET /state` *changes* AND the UI renders the right confidence band. Directly prevents the audit's "green tests ≠ wired" failure.
- **T8-02** Privacy/schema enforcement test: lint/test asserting activity payloads contain only event-type + timings + coarse counters — never filenames, prompt text, or code content (principle 11).
- **T8-03** Offline/engine-down buffering + replay: define and test capture behavior when the engine isn't running (buffer to disk/Redis, replay on reconnect) — without it, real users see "unavailable" most of the time.
- **T8-04** Ground-truth-lite calibration loop: optional, low-friction self-report at breakpoints ("focused last 10 min? y/n/skip") storing only aggregate calibration deltas — validates whether per-user baselines help or hurt.
- **T8-05** Event-backbone observability: metrics on `ADHDEventEmitter`/stream (events emitted/consumed/dropped, assessment latency) + a one-command **kill-switch** + data-wipe (principle 11/12).
- **Accept:** the wiring test fails if the loop breaks; privacy test blocks content leakage; capture survives engine-down; calibration measurable; backbone observable + killable.

---

## 2.6 Architecture decisions (PAL analyze — RESOLVED, gpt-5.2)

| # | Decision | Verdict | Resolution (file:line grounding) |
|---|----------|---------|----------------------------------|
| 1 | Operator identity (T4-00) | ADOPT-WITH-CHANGES | Persisted **random UUID** at `~/.dopemux/operator_id` (0600), content-free — **NOT** machine-id/path hash (fingerprinting risk). Resolve in CLI layer. **Also unify the engine's wrong use of `settings.workspace_id` as `user_id`** (`engine.py:296-303,335-339`; `routes.py:1489` default `"default"`). |
| 2 | Signal transport (T4-01/02) | ADOPT-WITH-CHANGES | **Redis XADD → `dopemux:events`** is canonical (`event_emitter.py:75`); the stream already buffers while the consumer is down. native_hooks XADDs content-free events; engine drains via consumer group. `/activity` stub (`routes.py:667-675`) is NOT the primary path. Add local JSONL spool only as a fallback if Redis itself may be down. |
| 3 | Canonical context writer (T5-01) | ADOPT-WITH-CHANGES | Keep `context_manager` canonical (`context_manager.py:248`); wire native_hooks Stop/PreCompact → `ContextManager.save_context(force=True)`; **harden engine `/save-context` to metadata-only** — it currently accepts `prompt_hint`+`files` (`routes.py:1628-1686`) → content leak; demote engine ContextPreserver to advisory. |
| 4 | Enum unification (T3-01) | ADOPT-WITH-CHANGES | Canonical enum in `services/adhd_engine/core/models.py`. Set = **`FOCUSED, TRANSITIONING, SCATTERED, OVERWHELMED, HYPERFOCUSED`**. Remove/alias `NORMAL` (inconsistently referenced `engine.py:1431` vs matrix `engine.py:534-560`); ban ad-hoc `"normal"` strings (`context_manager.py:37`). |
| 5 | §6 boundary | **REJECT+alternative — NEW CRITICAL** | Cannot "confirm" — **the engine ALREADY violates §6**: writes task-like `TODO` progress to ConPort (`engine.py:1401-1414`), exposes `/tasks*` (`routes.py:841-872`), `/unfinished-work` returns file paths (`routes.py:1710-1773`, PII leak). → new **T4-08**. |

**New track item — T4-08 (§6 compliance + privacy hardening) — disposition HARDEN, BLOCKS T7:**
- Strip or dev-flag the engine's task/PM-authority surfaces (`/tasks*`, `/unfinished-work`); replace ConPort `log_progress_entry` "TODO" writes (`engine.py:1404`) with **content-free recommendation events** (`recommendation_type`, `urgency`, `timestamp` — no descriptions/paths).
- Privacy schema guard on ALL event/context payloads: reject `prompt`, `file_path`, `tool_response`, `files` fields (also covers `native_hooks` storing truncated tool_input/response, `native_hooks.py:312-316`). This is the enforcement mechanism behind T8-02.
- **Accept:** engine emits only cognitive state + content-free recommendation hints; no task/PM truth; no path/content in any persisted payload; §6 verified.

## 2.7 Wiring map (PAL tracer — activity→state→consumer)

The exact hop-by-hop status the T4 packets must implement. **EXISTS / BROKEN / MISSING** + function + file:line:

```
[Claude PostToolUse] → native_hooks._on_post_tool_use  (native_hooks.py:282)   EXISTS — dispatched, but only records WorkflowKernel history; emits NO activity
   ↓  (MISSING)
[native_hooks → Redis XADD "dopemux:events"]  via ADHDEventEmitter.emit (event_emitter.py:~110)   MISSING — native_hooks has zero engine/Redis wiring today
   ↓
[ADHDEventListener consume] (event_listener.py:147)   BROKEN/PARTIAL — consumes stream but updates NO state dict; only pokes detectors/surfaces findings
   ↓  (MISSING handler)
[NEW handler → _assess_attention_state / _assess_current_energy_level] (engine.py:973,874)   writes current_* (engine.py:946,998)
   ↓  (gate)
[gate: user_id in engine.user_profiles] (engine.py:864,1201)   MISSING — user_profiles empty; _load_user_profiles loads only Redis adhd:profile:* (engine.py:254) → must SEED a default profile for the operator UUID
   ↓
[GET /api/v1/attention-state/{user_id}] (routes.py:398) / GET /state / `status --attention`   EXISTS — but returns .get(user_id, FOCUSED) default until the loop above lands
```

**`user_id` threading defect (must fix in T4-00):** engine binds `AttentionCalibrator(user_id=settings.workspace_id)` (engine.py:296) and `event_listener.start(user_id=settings.workspace_id)` (engine.py:335); routes default to `"default"`/`"default_user"` (routes.py:1489). The resolved operator UUID must replace `workspace_id`-as-user consistently end-to-end.

**Resulting precise T4 packet steps:** T4-00 UUID resolver + thread it; T4-01 fix `EventType`→`EventTypes`, confirm `ADHDEventEmitter` canonical; T4-02 emit content-free activity from native_hooks (post/pre tool, prompt, failure) via XADD; T4-03a seed default profile at startup; T4-03b add listener activity-handler that calls assessment + writes `current_*` (and make `/activity` emit, not stub); T4-04 `_assess_*` consume real activity via `ActivityTracker.get_recent_activity` (activity_tracker.py:65).

## 3. Dependency DAG (BLOCKS)

```
T1-01 ──▶ T1-02, T1-03, T7-04            (confidence-band primitive first)
T2-01/02/03 ──▶ T3-03, T6-03             (salvage UX before deleting dead triangle)
T4-00 (identity GATE) ──▶ T4-03, T4-04, T4-05   (no per-user state without user_id)
T4-01 ──▶ T4-02 ──▶ T4-03 ──▶ T4-04 ──▶ T4-05 ──▶ T4-06/07   (pipeline order)
T3-01/02 ──▶ T3-03                       (designate+repoint before delete)
T4-03 + T4-04 ──▶ T3-04                  (engine ingests real signal BEFORE deleting legacy monitor/daemon — no capture gap)
T4-02 ──▶ T3-04                          (migrate monitor_daemon capture into native_hooks before deleting it)
T4-03 ──▶ T3-02                          (engine real before status reads live data; T1-02 covers honest-interim)
T4-01 ──▶ T5-02, T5-03                   (event backbone before autosave/restoration)
T4-04 ──▶ T8-01..05                      (real signal before validation/observability)
T8 (validation) + T4-04 + T1-04 ──▶ T7  (no surfaces/notifications on unproven pipeline; no copy/doc divergence)
T5: context_manager stays fallback until T5-01 writer proven
T6-01/02/04 ── independent (parallel)
```

Phase 1 = {T1, T2, T6-01/02/04}. Phase 2 = {T3, T4, T5, T8}. Phase 3 = {T7, T6-03}.

---

## 4. Cross-cutting acceptance & guardrails
- **AGENTS.md §6:** engine never writes task/PM truth; verify per TP touching the engine.
- **Honest signal everywhere:** no bare cognitive numbers; confidence bands only (principle 7).
- **Privacy:** content-free logging, local-only, kill switch (principle 11/12).
- **Tests exercise real paths:** every BUILD/WIRE TP adds at least one test on the production path (the audit's "green tests ≠ wired" trap must not recur).
- **Each repo-changing TP** conforms to `dopetask-canonical-spec.json`, runs the Codex PAL chain (`analyze → planner → codereview → precommit`; risky tracks add `thinkdeep/challenge`), and emits the AGENTS.md §8 proof bundle.

---

## 5. Open questions for PAL analyze/tracer (deliberately deferred)
1. Canonical context writer (T5-01): engine `ContextPreserver` vs `context_manager` — which owns durable session-restore? (analyze)
2. Signal transport (T4-02): HTTP POST to `/activity` vs direct `xadd` to `dopemux:events` from native_hooks — latency/coupling tradeoff. (tracer)
3. Dashboard canonical (T7-01): rebuild React vs standardize on Textual TUI. (analyze)
4. Default-profile identity (T4-03): what `user_id` does a single-operator CLI use? (tracer — the engine is keyed by user_id but the CLI has no auth identity.)
5. Enum unification (T3-01): target attention-state taxonomy. (analyze)

---

## 6. Validation status
- [x] **PAL consensus** on plan + dispositions — gpt-5.2 (neutral, 8/10) + gpt-5.1-codex (against, 6/10). Both validated direction; refinements ADOPTED: keep-monitor-until-live (T3-04 resequenced), identity gate (T4-00), new T8 validation/observability track, T7 trimmed to RETIRE-default + blocked on T8, transport=buffer-and-replay, context_manager fallback. Riskiest assumption (signal→state inference reliability) mitigated by T8.
- [x] **PAL analyze** (gpt-5.2) — 5 decisions resolved (§2.6); surfaced NEW §6 violation → T4-08. Identity=persisted UUID; transport=Redis XADD; context_manager canonical; enum in engine models; engine §6-noncompliant today.
- [x] **PAL tracer** (precision) — hop-by-hop wiring map (§2.7): native_hooks emit=MISSING, listener-handler=BROKEN, default-profile=MISSING, user_id-threading=defect. Yields precise T4 packet steps.
- [x] **PAL planner** (gpt-5.2) — finalized 8 epics + 39 leaf TPs + BLOCKS DAG; granularity confirmed commit-sized.
- [x] **Load-plan JSON** authored: `docs/ops/load-plans/load_plan-DMX-ADHD-COGNITIVE-REMEDIATION.json` (durable).
- [x] **LOADED + VERIFIED in task-orchestrator** — root `2cd264b3-6268-4860-b6d6-23df81a68a4d`; 8 epics + 39 leaves (47 children) + 39 BLOCKS deps, atomic, zero failures. DAG enforced (verified: T4 ready={T4-00,T4-01}, rest correctly blocked with satisfied=false chains). Tag `dmx-adhd-cognitive-remediation`; no collision with existing trees.
- [ ] (execution-time) Each leaf authors a canonical dopetask TP + runs the AGENTS.md §5 PAL chain + §8 proof bundle when picked up.

**First-wave ready (13 unblocked leaves):** T1-01, T1-04, T2-01, T2-02, T2-03, T3-01, T4-00, T4-01, T5-01, T6-01, T6-02, T6-03, T6-04.
