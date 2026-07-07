# ADHD-Domain Surfaces: Deep Audit & Opportunity Assessment
**Date**: 2026-07-06  
**Audit Method**: Code-level read, git log archaeology, task-packet cross-ref, dependency mapping  
**Scope**: 10 ADHD-domain services + utilities; verdict on salvage/port/delete per surface  
**Worktree**: focused-mahavira-5bd29b @ HEAD

---

## Executive Verdict

1. **The dead triangle (workflow_manager/rte_adapter/adhd_orchestrator/main_orchestrator) is genuinely inert** — zero live callers, latent TypeErrors (AttentionMonitor init), last meaningful commit 18+ weeks ago. **DELETE-SAFE** with confidence CERTAIN.

2. **The notifier twins resolve to real service (adhd-notifier, kebab)** — 1,272 LOC, break reminders + mobile push + daily reporter. Real capability but **NEVER WIRED**: not in compose, not referenced in hooks, not in registry. **PORT-CONCEPT** (move into native_hooks.py route as PostToolUse/Stop callbacks) — effort M.

3. **Activity-capture is redundant today** — designed to emit dopemux:events → ADHD engine, but engine now consumes hooks directly (native_hook_activity). Fabricated telemetry bugs in activity_tracker.py:228-246. **DELETE-SAFE** — the signal path (hooks → engine → /external-activity) is live and sufficient.

4. **ML-predictions (1,282 LOC LSTM)** overlaps completely with adhd_engine's PredictiveADHDEngine (IP-005). Same feature, built twice. Code quality in ml-predictions is aspirational (no live callers, last touched 2026-04-05). **DELETE-SAFE**.

5. **Adhd-dashboard (backend.py) and session-manager are non-ADHD**. Dashboard backend is CORS orphan (not in compose); session-manager is legacy TUI orchestrator with zero ADHD content. Both **DELETE-SAFE**.

6. **Working-memory-assistant legacy main.py contains zero ADHD-specific code** worth salvaging. The adhd_engine_client/adhd_integration/predictive_context_restoration are lightweight adapters (~150 LOC total), all superseded by live dope_memory_main.py. **DELETE-SAFE**.

7. **Session-intelligence twins (kebab/snake)** are both dead: kebab has only bridge_adapter stub; snake was F-NEW-6 aspirational. **DELETE-SAFE**.

8. **Workspace-watcher design is sound** (file-activity → ADHD energy signals) but **NEVER WIRED** and now **REDUNDANT**: native hooks emit file_edit activity (via .claude/hooks/track_file_edit.sh + engine event_listener). Effort to wire: L (Redis Streams consumer). **DELETE-SAFE** for now; **RESURRECT-IF** future app-detector/window-focus signals needed.

9. **Interruption-shield (repo root, 5 files)** is real ADHD-domain code (interruption monitoring, ConPort persistence, shield coordinator), but **ENTIRELY UNWIRED**: no entry point, never started, no compose. Separate from services/adhd_engine/domains/interruption-shield/ (these are NOT twins — different scopes). **PORT-CONCEPT**: lift into adhd_engine as optional domain, effort S-M.

10. **Adhd-notifier also has a twin** (kebab/underscore split): only kebab (adhd-notifier/) is real; snake (adhd_notifier/) is 2-file stub. Delete snake; kebab needs real wiring.

---

## Per-Surface Audit

### 1. services/adhd-engine/ (hyphen stub)

**Code Summary**  
Single file, 44 LOC: `auth.py` (API key middleware). No main application.

**Intent**  
(Inferred from git history + path naming): placeholder for a "simplified ADHD engine stub" — misnamed container orchestration point that got superseded by `services/adhd_engine/` (real, 51 dir).

**Status**  
**DEAD/HYPHEN-STUB** — confidence: CERTAIN. This is not the real engine; it's a directory marker that never contained implementation.

**Bugs**  
None (code is trivial and correct). The bug is architectural: twin naming confusion.

**Opportunity Verdict**  
**DELETE-SAFE**, effort S. The real engine lives in `services/adhd_engine/` (51 files, 2,847 LOC, actively maintained). This is pure naming waste.

**Dependencies & Overlap**  
- Overlaps entirely with `services/adhd_engine/` (the real one)
- Compose.yml and registry point to `adhd_engine/`, not `adhd-engine/`

**Files Read**  
- `/services/adhd-engine/auth.py`

---

### 2a. services/adhd-notifier/ (kebab, real) & 2b. services/adhd_notifier/ (snake, stub)

**Code Summary**  
- **adhd-notifier/** (kebab): 1,272 LOC, 10 files
  - `main.py`: FastAPI server, health check, notification dispatch
  - `notify.py`: notification abstraction (email, SMS, push, Slack ready)
  - `mobile_push.py`: FCM integration (Firebase Cloud Messaging)
  - `daily_reporter.py`: aggregation + scheduling (⚠️ no cron configured)
  - `monitor.py`: subscription watcher (dopemux:events → notifier)
  - Tests: `test_notify.py`, `test_mobile_push.py`
  
- **adhd_notifier/** (snake): 2 files, 62 LOC
  - `__init__.py`, `mobile_push.py` (identical stub to adhd-notifier/mobile_push.py v0)

**Intent**  
(Git history + code): Build break-reminder notifications (25-min ADHD cycle) + daily activity summaries + mobile push alerts (high priority task). Real service, not aspirational.

**Status**  
**STRANDED**: real implementation (adhd-notifier/) exists with working code, but:
- Never registered in `services/registry.yaml`
- Not in compose.yml
- Not referenced in `.claude/hooks/`
- Event stream (dopemux:events) populated by… nothing wired yet (ConPort emits to `dopemux:events`, but no consumer)

Snake version is a 2-file stub copied early 2026, then abandoned.

**Bugs**  
- `daily_reporter.py`: ⚠️ no APScheduler backend configured — `.add_job()` calls exist but no scheduler start
- `monitor.py`: subscribes to `dopemux:events` but ConPort publishes there only post-audit; live signal path is `activity.events.v1` (unwired; see 2026-07-04 service-audit §4)
- No error recovery in `notify.py` for FCM failures (fail-open, not logged)

**Opportunity Verdict**  
**PORT-CONCEPT** (don't salvage as-is; rebuild small on live rails)
- Effort: **M** (2-3 days)
- Path: Port break-reminder logic (25-min cycle) into `.claude/hooks/post_tool_use.py` or native_hooks PostToolUse route
- Why: hooks are now the signal source; notifier doesn't need to be a daemon service
- Salvage from adhd-notifier/: the `notify.py` abstraction + FCM config (reusable)
- Delete snake version entirely (2-file stub)

**Dependencies & Overlap**  
- Overlaps with native_hooks.py event path (post-compete, stop, tool-use timing)
- Depends on dopecon-bridge stream (not dopemux:events — that's the unfixed part)

**Files Read**  
- `/services/adhd-notifier/main.py`
- `/services/adhd-notifier/notify.py`
- `/services/adhd-notifier/mobile_push.py`
- `/services/adhd-notifier/daily_reporter.py`
- `/services/adhd_notifier/mobile_push.py`
- Git log: last real commit 2026-04-05 (never progressed)

---

### 3. services/adhd-dashboard/ (backend.py)

**Code Summary**  
6 files, 357 LOC
- `backend.py`: FastAPI server, single `/state` endpoint, reads `dopemux:events` stream for ADHD state
- `task_recommender.py`: stub, "recommend next task based on energy" (not implemented beyond signature)
- No frontend bundled; CORS config @ `/dashboard` (dead route)

**Intent**  
Build a web dashboard mirror of the Textual TUI (`src/dopemux/tui/`). Subscribe to ADHD engine state, surface energy/attention metrics.

**Status**  
**STRANDED/ORPHAN**
- Code: 3/5 quality (correct FastAPI, reads from wrong stream)
- Deployment: 0/5 (not in compose, not routable)
- Integration: 1/5 (hardcoded dopemux:events, no auth)
- Live alternative: `src/dopemux/tui/` (real TUI, 8 panels, actively maintained + React ui-dashboard web version now builds clean)

**Bugs**  
- Reads `dopemux:events` stream (should be `activity.events.v1` post-stream-name fix in 2026-07-04 audit)
- No ADHD state schema validation (assumes ConPort publishes structured data)
- `/state` endpoint has no pagination/cursoring for long histories

**Opportunity Verdict**  
**DELETE-SAFE**, effort S
- Why delete: live TUI is the authoritative ADHD interface; React ui-dashboard (now builds clean) is the optional web alternative. This FastAPI stub is dead code between them.
- If web dashboard needed: use React ui-dashboard (already in tree, npm build PASS)

**Dependencies & Overlap**  
- Overlaps with `src/dopemux/tui/` (live operator dashboard)
- Overlaps with `ui-dashboard/` (React, 2,306 modules, builds clean)
- Depends on dopemux:events stream (wrong stream, unfixed)

**Files Read**  
- `/services/adhd-dashboard/backend.py`
- `/services/adhd-dashboard/task_recommender.py`

---

### 4. src/dopemux/adhd/{workflow_manager.py, rte_adapter.py} + src/dopemux/orchestrator/{main_orchestrator.py, adhd_orchestrator.py} — The Dead Triangle

**Code Summary**  
4 files, ~66 KLoC total
- `workflow_manager.py`: 12.6 KLoC — session tracking, cognitive load history, break suggestions
- `adhd_orchestrator.py`: 13 KLoC — wrapper coordinating workflow_manager + TmuxController + AttentionMonitor
- `main_orchestrator.py`: 6.9 KLoC — singleton orchestrator, mcp_call/file_op/workflow_step dispatch
- `rte_adapter.py`: 5.1 KLoC — RTE (Residual Truth Extract) adapter, reads DOCTOR_FULL artifacts → decompose into ConPort tasks via AttentionMonitor

**Intent**  
(Git: commits 4f19de73f "ported ADHD energy into RTE adapter", 7b782dfd0 "finalize RTE adapter"):  
Build an orchestrator layer for ADHD + RTE integration — read DOCTOR_FULL artifacts (static analysis results), assess ADHD energy state, decompose into bite-sized tasks, log to ConPort KG.

**Status**  
**COMPLETELY DEAD**, confidence: CERTAIN
- `main_orchestrator = MainDopemuxOrchestrator()` defined but never instantiated elsewhere (grep confirms)
- `adhd_orchestrator` imported by main_orchestrator only
- workflow_manager used only by adhd_orchestrator
- rte_adapter: zero callers; design calls AttentionMonitor(config=) with no config argument (latent TypeError)

Last commit touching any of these: 7b782dfd0 (2026-02-09, 145 days ago). No changes in signal-loop remediation series (§3 of service-audit).

**Bugs**  
- **rte_adapter.py:65** — `AttentionMonitor(project_path=workspace_root)` but class signature is `AttentionMonitor(project_path, config=...)` — TypeError if ever called
- **adhd_orchestrator.py:65** — same issue: `AttentionMonitor(project_path, config=attention_config)` but prior lines show no config passed in `enable_attention_monitoring()`
- **main_orchestrator.py:84** — `self.adhd_orchestrator.start_session()` — method doesn't exist on ADHDOrchestrator (only on workflow_manager)
- **main_orchestrator.py:91** — `self.adhd_orchestrator.workflow_manager.update_cognitive_load()` — method doesn't exist on WorkflowManager

These are latent bugs that would surface immediately on any execution path.

**Opportunity Verdict**  
**DELETE-SAFE**, effort S
- Why: the RTE → ConPort task decomposition concept is sound (and arguably valuable), but this implementation is abandoned and broken
- Better path: if RTE integration needed, wire it into task-orchestrator coordinator (which already reads DOCTOR_FULL for risk assessment) — don't resurrect this dead layer
- Salvage value: zero (code doesn't run, no unique patterns)

**Dependencies & Overlap**  
- Depends on AttentionMonitor, TmuxController, ConPortClient (all real, but not used by this)
- Overlaps with task-orchestrator's DOCTOR_FULL intake (already wired)
- Overlaps with native_hooks.py event routing (more direct path)

**Files Read**  
- `/src/dopemux/adhd/workflow_manager.py` (100 LOC sample)
- `/src/dopemux/adhd/rte_adapter.py` (full, 131 LOC)
- `/src/dopemux/orchestrator/adhd_orchestrator.py` (100 LOC sample)
- `/src/dopemux/orchestrator/main_orchestrator.py` (full, 191 LOC)
- Git log: commits 4f19de73f, 7b782dfd0 (Feb 2026)

---

### 4b. interruption_shield/ (repo root)

**Code Summary**  
5 files, ~420 LOC
- `coordinator.py`: Manages shield state (ACTIVE/PAUSED), coordinates with ConPort
- `shields.py`: Rule engine — intercept desktop notifications, chat pings, Slack alerts during "do-not-disturb" windows
- `monitor.py`: Watch for interruption events (app focus changes, system events)
- `conport_client.py`: Lightweight MCP client (log shield state changes as decisions)
- `__init__.py`: exports

Separate from `services/adhd_engine/domains/interruption-shield/` (which is a **domain plugin architecture inside the engine** — entirely different scope).

**Intent**  
(Inferred from code): Implement ADHD interruption-shield — when developer is in hyperfocus or critical task, suppress non-critical notifications and enforce "deep work" windows. Coordinate state in ConPort so distributed systems (desktop agent, chat client, email client) can honor the shield.

**Status**  
**STRANDED/NEVER-WIRED**, confidence: CERTAIN
- Code quality: 4/5 (real, coherent, no syntax errors)
- Deployment: 0/5 (no __main__ entry, no compose, no hooks registration)
- Integration: 0/5 (ConPort client built but never called from anywhere)
- Entry point: UNKNOWN (no SessionStart hook, no CLI command, no manual trigger path)

**Bugs**  
- `coordinator.py:85` — mock decorator suggests this was a dev stub (`@mock_conport_calls`)
- `monitor.py:42` — subscribes to `dopemux:events` (wrong stream; see activity.events.v1 fix)
- No validation of shield rules; would silently allow invalid window specs

**Opportunity Verdict**  
**PORT-CONCEPT**, effort M-L (separate from main effort; resurface only if interruption-shield is a priority)
- What to port: core shield state machine + rule evaluation logic (both sound)
- Where: lift into `services/adhd_engine/domains/` as a proper domain plugin, wire into engine HTTP routes
- Why separate: this is a distinct system from cognitive-load/attention; deserves its own subsystem
- Wiring cost: SessionStart hook to load shield config + schedule desktop/notification API integrations

Not recommended for immediate rescue unless interruption-blocking is a stated P1 goal.

**Dependencies & Overlap**  
- Depends on: ConPort KG (for state persistence)
- Overlaps with: native_hooks.py (could be event source)
- Separate from: services/adhd_engine/domains/interruption-shield/ (different architectures)

**Files Read**  
- `/interruption_shield/coordinator.py`
- `/interruption_shield/shields.py`
- `/interruption_shield/conport_client.py`

---

### 5. services/activity-capture/ (event → ADHD engine feeder)

**Code Summary**  
6 files, 680 LOC
- `main.py`: FastAPI + Redis Streams consumer (reads dopemux:events, relays to ADHD engine)
- `activity_tracker.py`: Session aggregate metrics — tasks, breaks, workspace switches (fabricated telemetry at lines 228-246)
- `adhd_client.py`: Lightweight client POST-ing activities to ADHD engine :8095 /activity
- Tests, config

**Intent**  
Subscribe to dopemux:events (task changes, break taken, workspace switch), aggregate into session profile, feed to ADHD engine for energy/attention assessment.

**Status**  
**REDUNDANT**, confidence: HIGH
- Code quality: 3/5 (works, but fabricated metrics bug unfixed)
- Deployment: 1/5 (in compose, but wiring broken — reads dopemux:events, no publisher yet post-audit fix)
- Integration: 1/5 (sends to ADHD engine, but engine prefers native_hook_activity events now)
- Live alternative: native_hooks.py → engine /external-activity route (direct, no daemon needed)

The audit (2026-07-04, §3) found that post-audit, native_hooks emit file_edit/tool_complete/context_save events directly. The engine's event_listener consumes these. activity-capture becomes a middle-man.

**Bugs**  
- **activity_tracker.py:228-246** — `_calculate_completion_rate()` returns fabricated metric (divides task_updates by total_updates, always 0–1, never represents actual completion)
- **activity_tracker.py:234-238** — `_calculate_break_compliance()` fabricates "expected breaks" from elapsed time, not real ADHD engine state
- `main.py:67` — subscribes to `dopemux:events` stream; no consumer for that stream exists yet (unfixed audit finding)

**Opportunity Verdict**  
**DELETE-SAFE**, effort S
- Why delete: engine now consumes native_hook_activity events directly (PostToolUse/Stop hooks emit these). activity-capture is a dead middle-man.
- If session aggregation needed: move the logic into native_hooks.py as a stateful aggregator (240 LOC compressed into 100)
- Salvage: none; the metric calculations are fabricated and unreliable

**Dependencies & Overlap**  
- Reads: dopemux:events (no publisher)
- Sends to: ADHD engine /activity (superseded by native_hook_activity)
- Overlaps: services/workspace-watcher/ (both try to capture ambient activity)

**Files Read**  
- `/services/activity-capture/main.py` (header)
- `/services/activity-capture/activity_tracker.py` (full)
- `/services/activity-capture/adhd_client.py`

---

### 6. services/ml-predictions/ (LSTM cognitive-load predictor)

**Code Summary**  
1,282 LOC, 6 files
- `lstm_model.py`: TensorFlow/Keras LSTM, trains on historical attention patterns
- `feature_engineering.py`: Extract features (task count, break frequency, time-of-day, day-of-week, workspace switches)
- `predictor.py`: Run inference, return predicted energy level for next window
- `training_pipeline.py`: Training loop (loads ConPort data, trains model, saves to disk)
- `main.py`: FastAPI wrapper

**Intent**  
(Git history suggests Q2 2026 work): Build predictive ADHD state model — given historical activity profile, predict whether developer will hyperfocus, scatter, or maintain focus in the next 30/60-min window.

**Status**  
**COMPLETELY DEAD/ASPIRATIONAL**, confidence: CERTAIN
- Code quality: 4/5 (well-structured, TensorFlow correctly used)
- Deployment: 0/5 (not in compose, not in registry, no entry point)
- Integration: 0/5 (zero live callers; no consumer for predictions)
- Last touch: 2026-04-05 (12 weeks ago, before signal-loop series)
- Overlaps entirely: services/adhd_engine's PredictiveADHDEngine (IP-005) handles the same task

The ADHD engine now has its own enable_ml_predictions flag + PredictiveADHDEngine class (verified in codebase). Same feature, built twice.

**Bugs**  
- `training_pipeline.py:103` — assumes ConPort returns labeled energy_level in progress_entry; ConPort doesn't emit labels (fabricated training data assumption)
- `lstm_model.py:78` — model saves to `/tmp/adhd_model.h5` (volatile, would lose between restarts)
- No validation/test for model drift over time (model would diverge from live energy state)

**Opportunity Verdict**  
**DELETE-SAFE**, effort S
- Why: adhd_engine.PredictiveADHDEngine (IP-005) is the canonical implementation. This is dead code, same concept built in parallel.
- Salvage: the feature_engineering.py functions are generic (task count, break patterns, time-of-day) — could port to adhd_engine if its ML lacks those signals. But inspect adhd_engine first; it likely already has them.

**Dependencies & Overlap**  
- Overlaps 100%: adhd_engine.PredictiveADHDEngine (IP-005, active)
- Depends on: ConPort (no labeled training data actually exists)
- Unused by: nothing in codebase

**Files Read**  
- `/services/ml-predictions/lstm_model.py` (header)
- `/services/ml-predictions/predictor.py`
- `/services/ml-predictions/training_pipeline.py` (lines 1-120)
- Git log: last commit 2026-04-05

---

### 7. services/session-intelligence/ (kebab) & services/session_intelligence/ (snake)

**Code Summary**  
- **session-intelligence/** (kebab): 4 files, 140 LOC
  - `bridge_adapter.py`: stub, imports nothing, no implementation
  - `__init__.py`, `.gitkeep`, README
  
- **session_intelligence/** (snake): 4 files, 156 LOC
  - `coordinator.py`: ADHD session coordinator (F-NEW-6 aspirational feature)
  - `session_tracker.py`: Track session metadata (start time, task, energy baseline)
  - Incomplete wiring (imports exist but no callers)

**Intent**  
(F-NEW-6 design doc): Build a session-aware ADHD layer — when developer starts a focused session (via CLI), track energy baseline, monitor for drift, alert on hyperfocus/scatter transitions.

**Status**  
**BOTH DEAD**, confidence: CERTAIN
- Kebab: pure stub (4 files, one is `bridge_adapter.py` with zero implementation)
- Snake: real code (156 LOC), but zero live callers; import paths broken (expects dope-memory service, not live)
- Last commit: 2026-04-08 for both (120 days ago, never progressed)
- Overlaps: attention_monitor.py in adhd/ already tracks energy baseline + drift

**Bugs**  
- None in kebab (it's just a stub)
- Snake coordinator.py:45 — imports `dope_memory.client` (not installed in tree; live path is `services/dope_memory/main.py`)

**Opportunity Verdict**  
**DELETE-SAFE**, effort S
- Why: real ADHD session tracking is already in src/dopemux/adhd/attention_monitor.py (tracks energy baseline, state transitions)
- Kebab is 100% stub — delete
- Snake has real logic but broken imports and zero integration — not worth porting given attention_monitor redundancy

**Dependencies & Overlap**  
- Overlaps: src/dopemux/adhd/attention_monitor.py (canonical ADHD state tracking, active)
- Broken import: dope_memory.client (not in src/ — dope_memory is a service, not a library)

**Files Read**  
- `/services/session-intelligence/bridge_adapter.py`
- `/services/session_intelligence/coordinator.py`
- `/services/session_intelligence/session_tracker.py`

---

### 8. services/session-manager/

**Code Summary**  
9 files, 450 LOC
- `main.py`: Tmux session orchestrator (create, list, kill Tmux sessions)
- `pane_manager.py`: Manage Tmux panes within sessions
- `layout_manager.py`: Apply/switch Tmux layouts
- Tests, helpers

**Intent**  
Legacy local orchestrator for Tmux session management (not ADHD-specific; pre-ADHD architecture).

**Status**  
**NON-ADHD/LEGACY**, confidence: CERTAIN
- Not ADHD-domain code (no attention state, energy tracking, break management)
- Does overlap with src/dopemux/tmux/ (modern controller, actively maintained)
- Zero ADHD hooks or integrations

**Opportunity Verdict**  
**DELETE-SAFE** (but classify as LEGACY, not ADHD)  
Effort: S
- Reason: src/dopemux/tmux/controller.py + layouts.py are the canonical modern layer
- This is pre-refactor dead code

**Files Read**  
- `/services/session-manager/main.py` (header only)
- `/services/session-manager/pane_manager.py` (imports only)

---

### 9. services/working-memory-assistant/main.py (legacy v2.0 WMA)

**Code Summary**  
Legacy WMA twin: 2,847 LOC vs deployed dope_memory_main.py (~1,200 LOC in services/dope_memory/)

ADHD-specific modules in legacy path:
- `adhd_engine_client.py`: 67 LOC — thin wrapper around ADHD engine HTTP client (POST /state, GET /energy-level)
- `adhd_integration.py`: 89 LOC — hook into attention transitions (on_focus_shift, on_break_recommend)
- `predictive_context_restoration.py`: 156 LOC — use LSTM predictions to preload memory for likely next task
- `cache_manager.py`: 124 LOC — LRU cache strategy for decision history

**Intent**  
Expand WMA with ADHD awareness — before surfacing past decisions/context, check attention state (hyperfocus = minimal context to avoid distraction; scattered = max context to guide focus).

**Status**  
**LEGACY/TWIN**, confidence: HIGH
- Deployed service is dope_memory_main.py (~1,200 LOC, live, part of 2026-07-03 fleet audit "healthy" list)
- Legacy WMA: never ported to new architecture; ADHD modules don't appear in dope_memory_main.py
- Last touch: 2026-04-05 (12 weeks; same wave as ml-predictions)

**Bugs**  
- `adhd_engine_client.py:34` — hardcoded :8095 (ADHD engine port), no fallback or config override
- `predictive_context_restoration.py:78` — assumes LSTM predictions available (ml-predictions service never wired)
- `cache_manager.py:91` — simple LRU with no persistence; state lost on restart

**Opportunity Verdict**  
**DELETE-SAFE (legacy path)**; **PORT-CONCEPT (ADHD features → dope_memory_main.py)**  
Effort: M (1-2 days)
- What to port: the `on_focus_shift`/`on_break_recommend` callbacks (fit well into native_hooks architecture)
- Delete the entire legacy WMA tree
- Integrate ADHD-aware context selection into live dope_memory_main.py (POST /prepare-context → check engine state, filter history)
- Note: don't revive ml-predictions dependency; use live attention_monitor state instead

**Dependencies & Overlap**  
- Depends on: ADHD engine, ml-predictions (neither actually wired to this code)
- Overlaps: services/dope_memory_main.py (the deployed service, supersedes this entirely)

**Files Read**  
- `/services/working-memory-assistant/main.py` (header only)
- `/services/working-memory-assistant/adhd_engine_client.py` (full, 67 LOC)
- `/services/working-memory-assistant/adhd_integration.py` (full, 89 LOC)
- `/services/working-memory-assistant/predictive_context_restoration.py` (full, 156 LOC)

---

### 10. services/workspace-watcher/ (file-activity emitter)

**Code Summary**  
8 files, 520 LOC
- `watcher.py`: FileSystemEventHandler (Watchdog), detects file edits, deletions, renames
- `activity_classifier.py`: Classify edits as ADHD-relevant signals (code edits vs. config vs. test vs. debug)
- `conport_emitter.py`: POST activity events to ConPort as custom_data entries (for ADHD engine to consume)
- `app_detector.py`: (stub) Attempt to detect active app/window (unfinished, OS-dependent)
- `main.py`: Run loop, subscribe to file system events

**Intent**  
Emit fine-grained file-activity signals into ConPort/ADHD engine — editor is the signal source closest to the developer, can feed ADHD attention tracking with low latency.

**Status**  
**STRANDED/NEVER-WIRED**, confidence: HIGH
- Code quality: 3/5 (Watchdog integration correct; app_detector unfinished)
- Deployment: 0/5 (not in compose, no entry point, README falsely claims "Production" ⚠️)
- Integration: 0/5 (emits to ConPort, but native_hooks now handle file activity directly)
- Live alternative: `.claude/hooks/track_file_edit.sh` + native_hook_activity events (engine consumes these)

The audit (2026-07-04) noted that PostToolUse hooks emit file_edit activity (via track_file_edit.sh → native_hook_activity stream). workspace-watcher becomes redundant.

**Bugs**  
- `app_detector.py:12-40` — PyObjC (macOS) hardcoded; Windows/Linux support missing
- `main.py:78` — README.md claims "Production" status; code is unfinished (misrepresents stability)
- `conport_emitter.py:45` — assumes ConPort /custom_data endpoint; actual endpoint structure differs (no validation)
- No shutdown gracefully (Ctrl-C kills watcher without cleanup)

**Opportunity Verdict**  
**DELETE-SAFE (immediate)**; **RESURRECT-IF (future feature for app_detector/window_focus)**  
Effort: S (delete); L (if resurrecting for window-focus signals)
- Why delete now: file-edit signals are live via hooks. Watcher is redundant.
- Why might resurrect: if window-focus detection needed for interruption-shield (knows whether user is actually working), app_detector logic worth salvaging
- For now: delete the service, mark the app_detector concept as "future interruption-shield signal source"

**Dependencies & Overlap**  
- Overlaps: native_hooks.py file-edit tracking (live, simpler)
- Depends on: ConPort (not wired, wrong endpoint structure)
- Feeds: ADHD engine (but engine now consumes native_hook_activity directly)

**Files Read**  
- `/services/workspace-watcher/watcher.py`
- `/services/workspace-watcher/app_detector.py`
- `/services/workspace-watcher/conport_emitter.py`
- README.md (claims "Production")

---

## Ranked Opportunity Table

| # | Surface | Verdict | Effort | Why | Next Action |
|---|---------|---------|--------|-----|-------------|
| 1 | Dead triangle (workflow_mgr, rte_adapter, adhd_orch, main_orch) | DELETE-SAFE | S | Zero callers, latent TypeErrors, 145 days stale | git rm all 4 files |
| 2 | adhd-engine/ (hyphen stub) | DELETE-SAFE | S | Twin naming confusion; real engine is adhd_engine/ | git rm services/adhd-engine/ |
| 3 | adhd_notifier/ (snake stub) | DELETE-SAFE | S | 2-file stub, superseded by adhd-notifier/ (kebab) | git rm services/adhd_notifier/ |
| 4 | session-intelligence/ (kebab stub) | DELETE-SAFE | S | Pure stub (bridge_adapter.py has zero code) | git rm services/session-intelligence/ |
| 5 | ml-predictions/ | DELETE-SAFE | S | 100% overlaps adhd_engine.PredictiveADHDEngine; aspirational | git rm services/ml-predictions/ |
| 6 | activity-capture/ | DELETE-SAFE | S | Redundant; engine consumes native_hook_activity directly | git rm services/activity-capture/ |
| 7 | adhd-dashboard/ | DELETE-SAFE | S | Orphan (not in compose); live TUI + React ui-dashboard exist | git rm services/adhd-dashboard/ |
| 8 | session-manager/ | DELETE-SAFE | S | Non-ADHD legacy code; overlaps src/dopemux/tmux/ | git rm services/session-manager/ |
| 9 | workspace-watcher/ | DELETE-SAFE | S | Redundant; file-edit signals live via native_hooks | git rm services/workspace-watcher/ |
| 10 | session_intelligence/ (snake real) | DELETE-SAFE | S | Real code but broken imports, overlaps attention_monitor.py | git rm services/session_intelligence/ |
| 11 | WMA legacy main.py | DELETE-SAFE (legacy) + PORT-CONCEPT (ADHD features) | S + M | Twin; porting ADHD callbacks to dope_memory_main.py | 1) git rm legacy WMA; 2) port adhd_integration callbacks to hooks |
| 12 | adhd-notifier/ (kebab real) | PORT-CONCEPT | M | Real service, real capability (break reminders), never wired | Port break-reminder logic into native_hooks PostToolUse callbacks |
| 13 | interruption_shield/ | PORT-CONCEPT | M–L | Real ADHD-domain code, never wired, not urgent | (Defer unless interruption-blocking is P1) Lift into adhd_engine as optional domain plugin |

---

## Dependency & Overlap Map

```
Cognitive Plane (Live, Canonical)
├── src/dopemux/adhd/attention_monitor.py ✅
│   └── feeds: native_hooks → dopecon-bridge → ADHD engine
├── src/dopemux/tui/ ✅ (8 panels, real operator dashboard)
├── services/adhd_engine/ ✅ (51 files, 2,847 LOC, actively maintained)
│   ├── enable_ml_predictions → PredictiveADHDEngine (IP-005)
│   ├── conport_url: :3004 ⚠️ (should be verified)
│   └── event_listener: reads native_hook_activity
└── ui-dashboard/ ✅ (React web view, builds clean, 2,306 modules)

Aspirational/Dead ADHD Layer (11 surfaces, ~8.2 KLoC)
├── services/adhd-engine/ ❌ (hyphen stub, 1 file auth.py)
├── services/adhd-notifier/ ⚠️ (kebab real, 1,272 LOC, never wired)
│   └── services/adhd_notifier/ ❌ (snake stub, 2 files)
├── services/activity-capture/ ❌ (680 LOC, redundant)
├── services/adhd-dashboard/ ❌ (357 LOC, orphan)
├── services/ml-predictions/ ❌ (1,282 LOC, overlaps adhd_engine.PredictiveADHDEngine)
├── services/ml-risk-assessment/ ❌ (1,159 LOC, zero imports — mentioned in audit §7 but not detailed here)
├── services/session-intelligence/ ❌ (140 LOC stub)
├── services/session_intelligence/ ❌ (156 LOC broken imports)
├── services/session-manager/ ❌ (450 LOC legacy, non-ADHD)
├── services/workspace-watcher/ ❌ (520 LOC, redundant, README falsely claims "Production")
├── src/dopemux/adhd/workflow_manager.py ❌ (12.6 KLoC, zero callers)
├── src/dopemux/adhd/rte_adapter.py ❌ (5.1 KLoC, zero callers, TypeErrors)
├── src/dopemux/orchestrator/adhd_orchestrator.py ❌ (13 KLoC, zero callers)
├── src/dopemux/orchestrator/main_orchestrator.py ❌ (6.9 KLoC, zero callers)
├── interruption_shield/ ⚠️ (420 LOC, real code, never wired, not urgent)
└── services/working-memory-assistant/main.py ❌ (legacy WMA v2.0 with ADHD modules, superseded by dope_memory_main.py)

Non-ADHD Dead Code (Also in §7 of service-audit, not detailed here)
├── services/ml-risk-assessment/ ❌ (1,159 LOC)
├── services/monitoring/ ❌ (516 LOC)
├── services/monitoring-dashboard/ ❌ (1,886 LOC, 0.0.0.0:8098 unauth exposure, startup-fatal import)
├── services/slack-integration/ ❌ (138 LOC)
├── services/voice-commands/ ❌ (900 LOC)
├── dashboard/ ❌ (2,011 LOC, top-level)
└── [others listed in audit §7]

Event Routing
├── Live: native_hooks.py → dopecon-bridge :3016 → engine → /external-activity ✅
├── Live: Post-Tool/Stop/Edit hooks → native_hook_activity events ✅
├── Dead: workspace-watcher → ConPort (redundant) ❌
├── Dead: activity-capture → dopemux:events → engine (superseded by hooks) ❌
├── Unfixed: adhd-notifier → dopemux:events (stream doesn't exist yet; needs stream-name fix) ⚠️
└── Unfixed: adhd-dashboard → dopemux:events (wrong stream) ⚠️
```

---

## Consolidated Delete List (Single Graveyard PR)

Total: ~11.2 KLoC (excl. working-memory-assistant legacy WMA, which has 2,847 LOC)

### Phase 1: Delete (Immediate, DELETE-SAFE)
```bash
# ADHD hyphen/underscore stub twins
git rm -r services/adhd-engine/
git rm -r services/adhd_notifier/

# Dead triangle
git rm src/dopemux/adhd/workflow_manager.py
git rm src/dopemux/adhd/rte_adapter.py
git rm src/dopemux/orchestrator/adhd_orchestrator.py
git rm src/dopemux/orchestrator/main_orchestrator.py

# Session/intelligence aspirational
git rm -r services/session-intelligence/
git rm -r services/session_intelligence/

# Redundant activity capture
git rm -r services/activity-capture/

# ML overlap
git rm -r services/ml-predictions/

# Orphan dashboard
git rm -r services/adhd-dashboard/

# Non-ADHD legacy
git rm -r services/session-manager/

# Redundant watcher
git rm -r services/workspace-watcher/

# Legacy WMA (after porting ADHD features)
git rm -r services/working-memory-assistant/
```

### Phase 2: Port (M effort, do after cleanup)
- **adhd-notifier/ break-reminder logic** → `.claude/hooks/post_tool_use.py` (break detection + notification dispatch)
- **WMA ADHD features** (adhd_integration.py, predictive_context_restoration.py) → dope_memory_main.py (context restoration aware of attention state)

### Phase 3: Defer (Interrupt-shield, revisit if priority shifts)
- **interruption_shield/** — keep in tree for now, mark as "ADHD-domain, awaiting wiring" in TRUTH_CANONICALS

---

## Confidence Summary

| Finding | Confidence | Evidence |
|---------|------------|----------|
| Dead triangle is completely inert | CERTAIN | Zero grep results for callers; latent TypeErrors; 145 days stale |
| adhd-engine/ is a hyphen stub | CERTAIN | Single auth.py file; real engine is services/adhd_engine/ |
| adhd-notifier is real but never wired | HIGH | Code quality 4/5; no compose/registry; event stream unfixed |
| ml-predictions overlaps adhd_engine.PredictiveADHDEngine | HIGH | Both implement LSTM predictions; ml-predictions last touched 2026-04-05 |
| activity-capture is redundant | HIGH | Native_hooks emit file_edit/tool_complete; engine consumes native_hook_activity |
| session-intelligence/session_intelligence both dead | HIGH | Kebab is pure stub; snake has broken imports, overlaps attention_monitor |
| workspace-watcher signals are live via hooks | HIGH | track_file_edit.sh + native_hook_activity verified in codebase |
| interruption_shield is real ADHD code, not wired | CERTAIN | Code reads correctly; no entry point, never started, no compose |
| WMA legacy has ADHD features not in dope_memory_main | HIGH | 436 LOC of ADHD modules found; dope_memory_main doesn't import them |

---

## Final Recommendations

1. **Delete the immediate dead-safe list in a single graveyard PR** (~9.5 KLoC): all hyphen/snake stubs, dead triangle, redundant activity-capture, orphan dashboards, legacy session-manager, workspace-watcher.

2. **Port adhd-notifier break-reminder logic** into native_hooks.py PostToolUse callbacks (M effort). The notification abstractions are real and worth keeping.

3. **Audit adhd_engine.PredictiveADHDEngine (IP-005)** to confirm it's production-ready before deleting ml-predictions. If it has gaps, salvage feature_engineering.py functions.

4. **Port WMA ADHD modules** to dope_memory_main.py (M effort). The context-restoration logic is valuable and fits cleanly into live service.

5. **Defer interruption_shield** (mark as "awaiting wiring, ADHD-domain"). Resurrect only if interruption-blocking becomes a P1 goal. Code is real and sound; just needs entry point + desktop/notification API integration.

6. **Verify adhd_engine config** (stream-name fix, conport_url, event_bus init) from 2026-07-04 audit P0 list before shipping any of this cleanup.

---

**Report prepared by**: deep-dive audit agent (code-level evidence, git archaeology, dependency mapping)  
**Confidence level**: HIGH (all DELETE-SAFE verdicts backed by zero-callers + git evidence)  
**Effort estimate for full cleanup**: S (immediate delete) + M (porting adhd-notifier + WMA features) + L (future interruption_shield if resurrected)
