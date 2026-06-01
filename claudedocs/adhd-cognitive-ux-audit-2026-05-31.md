# ADHD / Cognitive / User-Facing Audit — Dopemux MVP

**Date:** 2026-05-31
**Branch:** `feat/autoreview-platform-series` (HEAD `63918aab1`)
**Mode:** READ-ONLY investigation (no repo changes). No Task Packet required (AGENTS.md §3 — non-repo-changing).
**Method:** Entry-point→reachability tracing (advisor-directed), 6 parallel surface auditors, targeted test run, runtime port/health probes. External validation via PAL pending (see §10).

---

## 1. Executive Summary

> **Headline verdict: The ADHD/cognitive *intelligence* layer is largely aspirational at runtime. The code exists and is often well-structured, but in a normal session it is either unreachable, fed no real input, or serves hard-coded defaults. The user-facing *presentation* layer compounds this by displaying those defaults as if they were real telemetry. The genuinely ADHD-compliant UX primitives that *do* exist are dead code. Several doctrine claims (auto-save every 30s, energy/break hooks, hyperfocus mandate) are false as written.**

This is not a "broken feature" report — it is a **"wired vs. aspirational"** report. Confidence: **high** on reachability/wiring findings (static trace + import-graph, cross-corroborated by 6 independent auditors; the engine's default-serving additionally **observed** via in-process drive, §9); **NOT_RUN** on full-stack live runtime (no Docker services started — itself the default operator reality, `enabled_in_smoke:false`). Externally validated (PAL `gpt-5.2` + design-premise research, §10).

What this means for an ADHD end-user **today**:
- Attention/energy/cognitive-load state shown anywhere is a **constant default** (FOCUSED / MEDIUM / focus 50% / 0 switches), not a measurement.
- "Hyperfocus protection," "break reminders," "energy-aware routing," and "auto-save every 30s" do **not** fire in a Claude/CLI session.
- The well-designed, doctrine-compliant UX (max-3 choices, gentle error framing, progressive disclosure) is **not reachable** from any command.

What genuinely works (don't lose this): manual context save/restore, task decomposition, the theme/accessibility system, the orchestrator TUI (real data), and honest "engine disconnected" degradation in the main dashboard.

---

## 2. Scope & Surfaces Audited

| # | Surface | Files / dirs |
|---|---------|--------------|
| A | ADHD engine service | `services/adhd_engine/` (FastAPI, port 8095) |
| B | In-process ADHD core | `src/dopemux/adhd/*`, `orchestrator/adhd_orchestrator.py`, `utils/adhd_optimizations.py`, `adhd_error_messages.py` |
| C | CLI & UX | `cli.py` (ADHD cmds), `ux/*`, wizards, profile detection, error UX |
| D | UI / TUI / dashboards | `ui/*`, `tui/*`, `ui-dashboard/` (React), `services/*-dashboard/` |
| E | Cognitive / memory / context | `services/working-memory-assistant/`, `services/session-manager/`, `adhd/context_manager.py`, ConPort/dope-memory |
| F | Duplication & docs-vs-reality | cross-cutting |

---

## 3. Reachability Map (the spine)

Verdicts: **LIVE** (reachable + functional) · **LIVE-INERT** (runs but no real input/effect) · **PARTIAL** · **DEAD** (no non-test caller) · **ORPHANED** (exists, not wired/deployed).

| Component | Verdict | Evidence |
|-----------|---------|----------|
| `adhd/attention_monitor.py` | **LIVE-INERT** | `cli.py:2473` starts it; buffers fed only by `simulate_activity()` (test-only, `attention_monitor.py:173`) → all-zero metrics |
| `adhd_engine` FastAPI service | **PARTIAL / always-default** | `compose.yml:426`; monitors loop empty `user_profiles` (`engine.py:864+`); serves FOCUSED/MEDIUM defaults |
| `monitor_daemon.py` (claude hooks) | **CONDITIONALLY-LIVE** | spawned by `ClaudeCodeHooks.start_monitoring()` (`claude_code_hooks.py:76`), writes `~/.dopemux/hook_status.json` — disjoint from the other two |
| `adhd/context_manager.py` (manual save/restore) | **LIVE** | `cli.py` (5 sites), `profile_commands.py`; real SQLite + JSON session store |
| `adhd/context_manager.start_auto_save()` | **DEAD/STUB** | `context_manager.py:398` — "In a real implementation, this would start a background thread"; no caller |
| `adhd/task_decomposer.py` | **LIVE (partial)** | `cli.py:2725,2970`; JSON `tasks.json` backend |
| `adhd/workflow_manager.py` | **DEAD** | only caller is `main_orchestrator.py` (itself dead) |
| `orchestrator/adhd_orchestrator.py` + `main_orchestrator.py` | **DEAD** (closed triangle) | no non-test importers |
| `adhd/rte_adapter.py` | **DEAD** | only `scripts/smoke_test_integration.py`; also has key-mismatch bug |
| `utils/adhd_optimizations.py` | **DEAD** | only via `integrations/leantime_bridge.py`, itself un-imported |
| `adhd_error_messages.py` | **DEAD** | 0 importers anywhere |
| `ux/interactive_prompts.py` (the real max-3 ADHD code) | **DEAD from CLI** | only `adhd_orchestrator`/`workflow_manager` (both dead) |
| `ux/progress_display.py` | **DEAD from CLI** | same dead chain |
| `ux/launcher_wizard.py`, `startup_hints.py`, `splash.py` | **LIVE** | `cli.py:115,684,974` |
| `ui/dashboard.py` (`dopemux dashboard`) | **LIVE (honest-degrading)** | `cli.py:5822`; explicit "engine disconnected" BLOCKER on down |
| `ui/cockpit/` (`dopemux cockpit`) | **LIVE (static-demo by design)** | `cli.py:3222`; `render.py:19-21` "NO WRITES" |
| `tui/app.py` orchestrator HUD | **LIVE (real data)** | `orchestrator_commands.py:1072`; SQLite/FS/GitHub |
| `ui-dashboard/` (React) | **DEAD — does not build** | missing `index.html`, `tsconfig`, `vite.config`; 3/4 components absent |
| `services/adhd-dashboard/` | **ORPHANED** | not a compose service (only a CORS host string); depends on dead engine |
| `services/monitoring-dashboard/` | **ORPHANED + unauth `0.0.0.0`** | `server.py:1561` |
| `services/working-memory-assistant/main.py` | **ORPHANED** | not in compose; manifest marks `authority_status: UNKNOWN`, forbidden for durable memory |
| `predictive_context_restoration.py`, `adhd_integration.py`, `adhd_engine_client.py` | **ORPHANED** | reachable only via orphaned WMA `main.py` |
| `services/adhd-notifier/` | **NOT DEPLOYED** | 0 compose service defs |
| 4 shell hooks (`check_energy/log_progress/save_context/track_file_edit.sh`) | **ORPHANED + mis-ported** | not dispatched by `native_hooks.py`; target port 8080 (=Leantime) |

---

## 4. Findings by Severity

### CRITICAL

**C1 — The cognitive engine is structurally always-default (both systems). [FAIL]**
Neither attention/cognitive system is fed real input at runtime:
- *In-process* `AttentionMonitor`: keystroke/error/context buffers are written **only** by `simulate_activity()` (documented "for testing", `attention_monitor.py:173`). In production all buffers stay empty → `keystroke_rate=0`, `focus_score=0` (`attention_monitor.py:294`); `_last_activity` is set at construction and never reset (`:89`), so state is `NORMAL` until 600s then **permanently `DISTRACTED`**.
- *FastAPI* `adhd_engine`: all 6 background monitors loop `for user_id in self.user_profiles.keys()` (`engine.py:864,964,1061,1201,1266`), but `user_profiles` is empty on cold start and nothing creates one (the would-be creators — `claude_brain`, `activity-capture` — POST to wrong route shapes / are undeployed). `PUT /activity/{user_id}` writes cache keys that `ActivityTracker` never reads (`routes.py:653-665` vs `activity_tracker.py:84-117`). Result: `current_attention_states`/`current_energy_levels` stay at default `FOCUSED`/`MEDIUM` indefinitely.

**Net: every attention/energy/cognitive-load value the platform can show is a constant default, never a measurement.**

> **OBSERVED (in-process drive, not inference):** Imported `ADHDAccommodationEngine()` directly and exercised the monitor assessment path. Result: `user_profiles={}`, `current_attention_states={}`, `current_energy_levels={}`; **zero activity-ingestion methods exist** (no `update_activity`/`record_activity`/`ingest_*`); calling `_assess_attention_state`/`_assess_current_energy_level` for a user logs `"ActivityTracker not initialized, using defaults"` and returns `AttentionState.FOCUSED` / `EnergyLevel.MEDIUM`. This upgrades the engine-half of C1 from static-inference to **observed**, and shows the default-serving holds even at the assessment level (seeding `user_profiles` alone would not fix it — there is no real activity feed).

**C2 — `status --attention` presents fabricated telemetry to the user. [FAIL]**
`cli.py:2668` instantiates a *fresh* `AttentionMonitor` per call; `__init__` has no path to reload persisted sessions; empty history → `_get_default_metrics()` (`attention_monitor.py:451`). Output is unconditionally `state=normal / focus=50.0% / duration=0.0 min / switches=0`, under the docstring "Retrieves high-fidelity telemetry from the active cockpit session." **Shipping fabricated focus numbers to an ADHD user is worse than showing none.**
*Severity note (external calibration, §10):* by a strict technical rubric this is **HIGH** (trust-breaking misleading UX, not integrity/security/data-loss); it is rated at the HIGH/CRITICAL boundary here because honesty-of-signal is the product's core promise. P0 regardless of label.

**C3 — `ui-dashboard` (React) is unbuildable. [FAIL]** *(Severity corrected to **HIGH** — see note.)*
`vite build` → `Could not resolve entry module "index.html"`. No `index.html`, `tsconfig.json`, or `vite.config.*`; `package.json main` points at a nonexistent file; 3 of 4 imported components (`CognitiveLoadGauge`, `PredictionPanel`, `TeamDashboard`) are absent (`App.tsx:41-45`). It is a partial scaffold, not a one-line fix. (Corroborates prior beta-readiness note "ui-dashboard build broken.")
*Severity note (external calibration, §10):* **downgraded CRITICAL→HIGH.** `ui-dashboard` is referenced only in `docs/planes/pm/_evidence/PM-INV-00.outputs/*` scan-dumps — **not** in `INSTALL.md`, `README`, or any user tutorial/how-to. Users are not directed to it, so it is an internal/unreleased scaffold, not an advertised shipping surface.

**C4 — "Auto-save every 30s" is unwired in every reachable, deployed path. [FAIL]**
The doctrine promise (global + `.claude/CLAUDE.md`) is not delivered anywhere live. `ContextManager.start_auto_save()` is an explicit stub (`context_manager.py:398-402`). The registered `Stop`/`PreCompact` hook is `native_hooks.py`, whose `_on_stop` does workflow gating only (`native_hooks.py:342`) — no context save, no ConPort write. The only genuine 30s timer (`session-manager/checkpoint_manager._auto_save_loop`) is undeployed. `save_context.sh` (the doc-cited mechanism) is orphaned, targets port 8080, and calls a nonexistent route.

### HIGH

**H1 — The doctrine-compliant ADHD UX is dead code. [FAIL]** The code that actually implements "max 3 options," progressive disclosure ("Show more options…"), and gentle problem/why/fix error framing — `ux/interactive_prompts.py` (`max_choices=3`, `:32`), `ux/progress_display.py`, `adhd_error_messages.py` — has **zero reachable callers**. The reachable wizard (`launcher_wizard.py`) instead lists all 12-13 roles in a scrolling viewport (no 3-cap, `:149`). Reachable errors are plain `console` lines, not ADHD-framed.

**H2 — 4 shell hooks orphaned AND mis-configured. [FAIL]** `.claude/hooks/{check_energy,log_progress,save_context,track_file_edit}.sh` are not dispatched (settings.json runs only `native_hooks.py`; it never references them). They also target `http://localhost:8080` — which is **Leantime** (`compose.yml:165`), not the engine (host 3025→8095) — and call routes (`/state`, `/save-context`) that don't exist as routed. Dead three ways over.

**H3 — Hyperfocus latch bug + unreachable in prod. [FAIL]** `_classify_attention_state` requires `_state_duration > 2700s` to return `HYPERFOCUS` (`attention_monitor.py:314`), but `_update_state_tracking` zeroes `_state_duration` whenever state changes (`:333`). Transitioning *into* HYPERFOCUS changes the state → resets the counter → next sample fails the gate → flickers back to FOCUSED. It **can never persist two consecutive samples**. (Moot in production anyway: `focus_score≡0` means FOCUSED/HYPERFOCUS are never reached.) The passing test (`test_attention_monitor.py:230`) sets `_state_duration` directly and bypasses the state machine — green test, broken feature.

**H4 — `TrendsPanel` renders fabricated DEMO sparklines as live telemetry. [FAIL]** In the otherwise-honest `dopemux dashboard`, the "📈 COGNITIVE TRENDS (last 2h/7d/24h)" panel defaults its 3 series to `DEMO_*` constants, has only `render()` (no updater), and is skipped by `action_refresh_all` (`ui/dashboard.py:372-399,497-505`). It shows invented trend lines permanently, even in live mode.

**H5 — Engine input loop broken at multiple points. [FAIL]** Beyond C1: `engine.zen_client` does not exist (only `pal_client`), so `/recommend-break` always hits the except-branch and returns null recommendations (`engine.py:125`, `routes.py:529`); the real activity writer `activity-capture` is undeployed and would 403 (sends no `X-API-Key`); background break recommendations are pushed to a Redis list nothing reads (`engine.py:1160` vs `routes.py:455`).

**H6 — Latent bugs in dead modules (would break on revival). [FAIL]** `adhd_orchestrator.py:65` calls `AttentionMonitor(project_path, config=...)` but `__init__` accepts only `project_path` → `TypeError`. `rte_adapter.py:72` reads `metrics.get("state","medium")` but the key is `"attention_state"` → energy always defaults `"medium"`, so the ADHD profile never drives RTE decomposition.

**H7 — Doctrine claims false/partial. [FAIL/PARTIAL]** See §7. "Hyperfocus warn 60 / mandate break 90" → code says reminder@90 / critical@120 and only *recommends* (never mandates), reachable only inside the running engine (`hyperfocus_guard.py:72`). "25-min sessions w/ auto break reminders" → real loop in engine, but unwired to Claude sessions; the 25-min `_adhd_checkpoint_loop` in `mcp/broker.py:801` is dead.

### MEDIUM

| ID | Finding | Evidence |
|----|---------|----------|
| M1 | **Service-dir naming inversion** (a trap): `adhd_engine/`(underscore)=real, `adhd-engine/`(hyphen)=1-file fragment; **inverted** for notifier: `adhd-notifier/`(hyphen)=real, `adhd_notifier/`(underscore)=shim | `compose.yml:429`; `adhd_notifier/mobile_push.py:1` |
| M2 | `adhd-notifier` **not deployed** (0 compose services) | `compose.yml` |
| M3 | **No canonical context writer** — 4 overlapping surfaces (context_manager / dope-memory / WMA main / engine ContextPreserver), none owns interruption-recovery end-to-end (confirms AGENTS.md §10 "Known Danger") | `runtime_authority_manifest.json:391,444` |
| M4 | adhd-engine ConPort URL mismatch: `config.py:36`/`conport_mcp_client.py:45` hardcode `:3010`; compose injects `:3005` → context writes likely miss ConPort | as cited |
| M5 | **8 dashboard surfaces**, only `cockpit` is CLI-canonical; rest unwired | §3 |
| M6 | WMA test suite has 5 collection ERRORS (`ModuleNotFoundError: dopemux`) incl. `test_predictive_restoration` — those tests prove nothing | `pytest --collect-only` |
| M7 | **Two attention systems use divergent state enums** (NORMAL/DISTRACTED vs TRANSITIONING/OVERWHELMED) — correctness trap if ever merged | `engine.py:973` vs `attention_monitor.py:35` |

### LOW / OBS

- **Secrets:** default `dev-key-123` (`adhd_engine_client.py:27`, compose), `WMA_SECRET_KEY`/`WMA_ENCRYPTION_KEY=dev-only-change-me` (`compose.yml:465`); `monitoring-dashboard` binds `0.0.0.0` unauth. *(Overlaps existing beta-readiness audit security backlog — cross-reference, don't double-count.)*
- Stale comment: `adhd/__init__.py:12` references `archived/attention_manager.py.archived` which does not exist.
- `voice.py` is a brand-voice **text/tone** engine (no audio TTS) despite the name — works as designed, but naming misleads.
- Help text is heavily themed ("cockpit/ritual/ignition/high-fidelity telemetry") — adds cognitive load for an ADHD audience.
- `get_today_data` instantiates a throwaway test-canary `IdempotencyStore()` in the production render path (`data_sources.py:40`).

---

## 5. What Actually Works (fair-credit ledger)

| Works | Evidence |
|-------|----------|
| Manual context save/restore | `context_manager.py` real SQLite + JSON, CLI-invoked |
| Task decomposition | `task_decomposer.py`, JSON-backed, CLI-reachable |
| Theme / accessibility system | `theme.py` real & applied; default `mint-mojo` muted palette is a defensible ADHD choice; NO_COLOR + ASCII fallback + plain/compact modes |
| Orchestrator TUI | `tui/app.py` renders real SQLite/proof/GitHub data |
| Honest degradation | `dopemux dashboard` shows explicit "ADHD Engine disconnected" BLOCKER; adhd-dashboard backend returns `status:"partial"` not 5xx |
| Boot UX | `splash.py`, `launcher_wizard` step status, `startup_hints` reach users |
| Engine cognitive math (if running) | real cognitive-load calc (`engine.py:441`), energy blending, `workspace_watcher` self-feed |
| Safe failure modes | clients return `None` / fail-open when engine/Redis/ConPort down — no crashes |

---

## 6. The Three Disconnected Attention Systems

```
(a) src/dopemux/adhd/attention_monitor.py   → writes <proj>/.dopemux/attention/*.json
        in-process; states NORMAL/DISTRACTED; fed only by simulate_activity() [test-only]
(b) services/adhd_engine (_attention_state_monitor)  → Redis, keyed by user_id
        states TRANSITIONING/OVERWHELMED; monitors iterate empty user_profiles
(c) src/dopemux/hooks/monitor_daemon.py     → writes ~/.dopemux/hook_status.json
        spawned by ClaudeCodeHooks.start_monitoring(); never read by (a) or status
```
No shared state; divergent enums; `status --attention` reads none of them at runtime. This is the root structural problem — pick one, feed it real signal, delete the others.

---

## 7. Claimed-vs-Actual (doctrine corrections needed)

| Claim (source) | Verdict | Reality |
|----------------|---------|---------|
| Hooks "automate auto-save, energy/break tracking" + 4 `.sh` active (`.claude/CLAUDE.md`) | **FALSE** | only `native_hooks.py` runs; workflow orchestration only |
| "Auto-save every 30s / 5min" (global+project) | **FALSE** | `start_auto_save` is a stub; no live timer |
| "Hyperfocus protection (warn 60 / mandate 90)" | **PARTIAL/FALSE** | code = reminder 90 / critical 120; only recommends; unreachable from Claude |
| "25-min sessions w/ auto break reminders" | **PARTIAL** | real in engine if deployed; unwired to Claude; broker loop dead |
| "Energy-aware task selection from ConPort metadata" | **PARTIAL** | engine computes internally; not consumed by any Claude-side picker |
| "Python ADHD Engine: energy/load/break/attention/routing/hyperfocus" | **PARTIAL (real but isolated)** | substantial code; runs only in its container; Claude-session signal path orphaned |
| INSTALL.md "6 background monitors" | **TRUE** | matches `engine.py:266-272` |
| `/dx:` help advertises implement/session/load/stats | **PARTIAL (known clobber)** | only `implement.md` present on this branch; per memory the dx command set was clobbered on `main` and is mid-restoration (PR #734). Verify post-merge before filing as pure vapor |

---

## 8. Improvement Roadmap (prioritized)

**P0 — Stop misleading the user (honesty first; cheap):**
1. Fix `status --attention` (C2): either reload persisted sessions / query the running daemon, or label output "no active monitoring data." Don't print defaults as telemetry.
2. Fix `TrendsPanel` (H4): wire to a real source or mark `[DEMO]` / hide in live mode.
3. Reconcile doctrine docs (§7): strike/flag the false auto-save, energy-hook, and hyperfocus-mandate claims in `.claude/CLAUDE.md` + global config.

**P1 — Decide the cognitive layer's fate (structural):**
4. Pick ONE attention system (§6), feed it a real signal source (the `monitor_daemon` already watches files — route its events in), delete the other two. Two divergent enums is a correctness trap.
5. Close the engine input loop: real `engine.update_activity()` on `PUT /activity`; seed/auto-create a default profile so monitors actually iterate; fix `zen_client`→`pal_client` (`routes.py:529`).
6. Wire or delete the dead ADHD-compliant UX (H1): route reachable prompts/errors through `interactive_prompts`/`adhd_error_messages`, or excise them so they stop implying capability.

**P2 — Hygiene / debt:**
7. Resolve service-dir naming inversion (M1) and document canonical dirs; remove the hyphen `adhd-engine/` fragment and underscore `adhd_notifier/` shim or make them redirect.
8. Pick a canonical dashboard (recommend Textual `tui/app.py`); restore-or-delete `ui-dashboard` + `services/adhd-dashboard` + `monitoring-dashboard`.
9. Resolve canonical context-writer (M3); fix ConPort port (M4); fix WMA test packaging (M6).
10. Remove default secrets `dev-key-123` / `dev-only-change-me`; fail-closed when unset (feeds existing beta-readiness security backlog).
11. Delete or revive the dead module triangle (`workflow_manager`/`adhd_orchestrator`/`main_orchestrator`/`rte_adapter`/`adhd_optimizations`/`adhd_error_messages`) — they carry latent bugs (H6).

---

## 9. Validation Performed (PASS / FAIL / NOT_RUN)

- **PASS** — Targeted ADHD/UI test suite: 119 tests pass (`.venv/bin/pytest`, exit 0). **Caveat:** they exercise `simulate_activity`/mocks/isolated functions, **not** production paths — they mask C1/C2/H3 entirely ("green tests ≠ wired").
- **PASS** — Python TUI/theme/voice modules import + instantiate cleanly (`.venv/bin/python`).
- **FAIL** — `ui-dashboard` `vite build` (missing entry/config/components).
- **FAIL** — WMA standalone test collection (5 `ModuleNotFoundError: dopemux`).
- **NOT_RUN** — Live runtime behavior of any service. Two distinct facts: (i) *structural* — the engine is `enabled_in_smoke:false` (`registry.yaml`), i.e. not in the default/smoke stack a normal user runs; (ii) *environmental* — in this audit env Docker was down, ports 8095/3025 not listening, 8080=adb→401. (i) supports "not running by default"; (ii) only supports "NOT_RUN here." All engine/service verdicts are static-trace + reachability based.
- **PASS (observed, in-process)** — Drove `ADHDAccommodationEngine()` directly (no Docker): empty profiles/state, zero activity-ingestion methods, assessment returns `FOCUSED`/`MEDIUM` with `"ActivityTracker not initialized, using defaults"`. Engine default-serving is **observed**, not just inferred.
- **PASS (static)** — Import-graph/reachability claims, cross-corroborated by 6 independent auditors.

---

## 10. External Validation

**Assumption (flagged per advisor):** "externally validate" is read as **external-model validation** (PAL) of the audit's verdict + severity, plus a bounded research grounding of the load-bearing design premise.

**(a) Multi-model review (PAL consensus).** `gpt-5.2` (neutral, given the full report): central verdict **"largely fair and well-evidenced," confidence 8/10.** Endorsed the reachability findings as structural (independent of runtime) and endorsed P0 "fail honest" as the correct, low-cost first move (aligned with industry "explicit provenance" norms and the project's *existing* engine-disconnected pattern). Calibrations it raised, which I have adopted:
- **C2 severity** ("`status --attention` fabricated telemetry") is **trust-breaking misleading UX — more naturally HIGH than CRITICAL**, since CRITICAL usually denotes integrity/security/data-loss. I retain CRITICAL *framing* only because honesty-of-signal is the product's core promise for an ADHD audience; **treat C2 as HIGH/CRITICAL boundary** and prioritize it as P0 regardless of label.
- **"Not running by default"** should rest on `registry.yaml enabled_in_smoke:false` (structural — engine not in the default/smoke stack), **not** on "Docker was down in the auditor's env" (that only supports NOT_RUN-here). Corrected in §9/§11.
- **C3 severity** (`ui-dashboard` unbuildable) — same hinge as C2: the reviewer noted severity depends on whether users are *directed* to it. Verified post-review: `ui-dashboard` appears only in `_evidence` scan-dumps, not user docs → **downgraded CRITICAL→HIGH** (internal scaffold).
- `gemini-2.5-pro` (skeptical/against stance) was requested as an adversarial second voice but **failed with HTTP 429 (rate-limited)** — so external-model validation rests on one model (gpt-5.2) plus the adversarial self-challenge below.

**(b) Adversarial self-challenge (PAL challenge).** Weakest link identified: the **FastAPI engine's "serves defaults indefinitely" is inferred from static trace, NOT observed at runtime** (engine never started). A maintainer could stand up the complete stack (deployed `activity-capture` + seeded profiles) and show the engine computing real state — that would refute the *engine half* of C1. It would **not** refute the rest: the engine is `enabled_in_smoke:false` (a normal user doesn't run it), and `status --attention` + the in-process `AttentionMonitor` are CLI-local and broken independent of any deployment. **Verdict holds, precisely scoped:** "in the default configuration an end-user gets today, these features are inert / default-serving; the engine's full-stack behavior is the one NOT_RUN inference open to maintainer rebuttal."

**(c) Design-premise grounding (web research).** The audit critiques *wiring*, not the *concept*. External literature confirms the concept is sound: keystroke/typing dynamics (inter-key latency, typing speed, error frequency) are research-backed digital biomarkers for attention, stress, and cognitive fatigue ([Nature Sci Reports meta-analysis](https://www.nature.com/articles/s41598-022-11865-7), [keystroke dynamics as stress/alertness biomarkers](https://researchfeatures.com/keystroke-dynamics-digital-biomarkers-stress-alertness/), [cognitive-fatigue keystroke prediction](https://www.aijfr.com/papers/2025/5/1370.pdf)). **Implication:** the AttentionMonitor's *input model* is a defensible design — the fix is to feed it a real keystroke/event source and persist state, not to abandon the approach. (Caveat: those studies measure clinical cognitive decline / stress, not the specific FOCUSED/SCATTERED/HYPERFOCUS taxonomy here; thresholds would need empirical calibration, not the current hard-coded constants.)

---

## 11. Remaining Uncertainty / Risk

- **Weakest link (per adversarial self-challenge) — now CLOSED.** The engine's "serves defaults" was the one inferred-not-observed CRIT. It has since been **observed in-process** (§4 C1, §9): the assessment path returns `FOCUSED`/`MEDIUM` with no activity feed and there is no ingestion method. The residual unknown is narrower: whether a *fully-deployed* `activity-capture` + Redis stack could populate `user_profiles` and drive non-default assessments — but the in-process drive shows the assessment itself falls back to defaults when `ActivityTracker` is uninitialized, so a working end-to-end path would require code changes (wiring the activity store the assessment reads), not just deployment.
- All live-runtime verdicts are **NOT_RUN** (no services started). Starting the full compose stack could change PARTIAL→LIVE for the engine — but would not change the C1 "no real input feeds the in-process monitor" finding, which is structural, nor the fact the engine is `enabled_in_smoke:false`.
- `/dx:` command availability is entangled with the known palette-clobber restoration (PR #734) — re-verify post-merge.
- Dashboard duplication: the *intended* product UI among `ui-dashboard`/`tui`/`ui/dashboard.py` was not resolved from product docs — flagged, not asserted.
- `TMUX_ADHD_*` status-bar indicators (INSTALL.md): no live writer found, but not exhaustively traced.

---

## 12. Files / Authority

**Authority used:** runtime code (cli.py, attention_monitor.py, engine.py, routes.py, native_hooks.py, context_manager.py, rte_adapter.py), `compose.yml`, `settings.json`, `runtime_authority_manifest.json`, AGENTS.md §6/§10, targeted pytest + port probes. Per AGENTS.md Truth Order, runtime/source outranked the docstrings and doctrine docs that this audit found to be stale.

**Report path:** `claudedocs/adhd-cognitive-ux-audit-2026-05-31.md` (this file). No source files modified.
