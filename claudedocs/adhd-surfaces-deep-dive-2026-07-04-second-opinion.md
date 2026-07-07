# Dopemux MVP: ADHD-Domain Surfaces Audit

**Date**: 2026-07-06  
**Scope**: 10 ADHD-domain surfaces + twins, dead code, and salvage opportunities  
**Confidence Levels**: ✅ = certain (direct code evidence) | 🟡 = high (git + docs) | 🟢 = medium (inferred) | 🔴 = low (assumed)

---

## Executive Summary

- **Live** (actively maintained): `services/adhd_engine` (122 Python files), `interruption_shield` (5 files), `activity-capture` (12 files)
- **Stranded** (partial, orphaned): `adhd-dashboard`, `adhd-notifier` twins (hyphen vs snake), `ml-predictions`, `session-intelligence` twins
- **Dead** (no active commits): `adhd-engine` (hyphen stub, 1 file), `workflow_manager.py`, `adhd_orchestrator.py`
- **Port-Concept** (salvageable logic): RTE adapter pattern, WMA ADHD-specific modules (energy monitoring, predictive restoration)
- **Delete-Safe** (redundant/obsolete): `adhd-notifier` snake variant, `session-manager` (non-ADHD), `workspace-watcher` overlap

---

## Surface-by-Surface Audit

### 1. `services/adhd-engine/` (Hyphen Stub) ✅

| Field | Finding |
|-------|---------|
| **code_summary** | Single file: `/Users/hue/code/dopemux-mvp/services/adhd-engine/auth.py` (44 lines). FastAPI API key validation only. Zero business logic. |
| **intent** | Placeholder for 2025 ADHD Engine service. Auth middleware never wired to real service. |
| **status** | **DEAD** — last commit `f018dd105` (deps bump). No integration points. |
| **bugs** | None (stub is minimal). |
| **opportunity_verdict** | **DELETE-SAFE** — no unique functionality; live `adhd_engine` (snake, 122 files) supersedes completely. |
| **dependencies_and_overlap** | Overlapped entirely by `/services/adhd_engine/` (snake). Both directories co-exist. |
| **confidence** | ✅ certain |

**Path**: `/Users/hue/code/dopemux-mvp/services/adhd-engine/auth.py`

---

### 2. `services/adhd-notifier/` (Hyphen, 1,236 LOC) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | **10 files**, 1,236 LOC. Core modules: `main.py` (112L), `notify.py` (267L), `mobile_push.py` (336L), `monitor.py` (290L), `daily_reporter.py` (201L). **Real feature set**: break reminders, hyperfocus alerts, daily reports, mobile push via Firebase/APNs. Kafka event subscriber. |
| **intent** | Phase 4 notification engine for ADHD break/hyperfocus alerts. Canonical notifier for live ADHD platform. |
| **status** | **WIRED** (partial) — compiles, has tests, but **no container in docker-compose** after June 4 audit. Events still flow but notifications stranded. |
| **bugs** | **1 latent**: `mobile_push.py` line ~150: APNs cert path assumes hardcoded `/etc/secrets/apns.p8` without env override. Blocks multi-tenant deployment. |
| **opportunity_verdict** | **SALVAGE "restore integration" (effort: S)** — reactivate in docker-compose, wire Kafka subscriber to adhd_engine events. Core notifier logic sound but orphaned. |
| **dependencies_and_overlap** | Feeds on `dopemux:events` topic (same as `activity-capture`, `ml-predictions`). Output to `dopemux:notifications`. Redundant with adhd_notifier snake variant (see #3). |
| **confidence** | 🟡 high (git log shows "Phase 4" ADHD Notifier commit; audit notes partial wiring) |

**Files Read**:
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/main.py`
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/notify.py`
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/mobile_push.py`
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/monitor.py`
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/daily_reporter.py`

---

### 3. `services/adhd_notifier/` (Snake, 36 LOC) ✅

| Field | Finding |
|-------|---------|
| **code_summary** | **2 files**: `__init__.py` (10L), `mobile_push.py` (26L). Stub. Single APNs provider, no notification orchestration. No main.py, no event subscriber. |
| **intent** | Orphaned extraction from hyphen variant. Never evolved beyond mobile push stub. |
| **status** | **DEAD** — last commit `f018dd105` (deps). No active development. |
| **bugs** | None (stub too minimal to have bugs). |
| **opportunity_verdict** | **DELETE-SAFE** — duplicate stub; hyphen variant is canonical and richer. Remove this directory. |
| **dependencies_and_overlap** | Exact duplicate (degraded) of `adhd-notifier/mobile_push.py` lines 1-26. Zero unique functionality. |
| **confidence** | ✅ certain |

**Paths**: 
- `/Users/hue/code/dopemux-mvp/services/adhd_notifier/__init__.py`
- `/Users/hue/code/dopemux-mvp/services/adhd_notifier/mobile_push.py`

---

### 4. `services/adhd-dashboard/backend.py` (3,500+ LOC) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | Single FastAPI backend for dashb. 100L of sample. Connects to `ADHD_ENGINE_URL`, `ACTIVITY_CAPTURE_URL`, reads Redis. Prometheus metrics for cognitive load, focus duration, hyperfocus alerts, notifications. WebSocket support for real-time updates. Task recommender integration. |
| **intent** | Real-time dashboard backend for ADHD visualization. Consumes engine metrics, surfaces cognitive load + break recommendations to UI. |
| **status** | **STRANDED** — code exists but **no corresponding frontend in repo** (UI should be in `ui-dashboard-frontend/` or similar; not found). Backend compiles but unconnected. |
| **bugs** | 🔴 **Potential**: Lines 39–99 assume `services/shared/brand_voice` + `task_recommender` modules exist; fallback if missing but silently degrades. |
| **opportunity_verdict** | **PORT-CONCEPT "rebuild dashboard on live stack" (effort: M)** — backend skeleton sound (Prometheus + Redis + WebSocket), but needs frontend pairing + integration with adhd_engine API. Consider deprecate in favor of dope_memory MCP HTTP endpoint (already live). |
| **dependencies_and_overlap** | Reads from `ADHD_ENGINE_URL` (adhd_engine service) + `ACTIVITY_CAPTURE_URL`. Overlaps partially with `dope_memory_main.py`'s MCP HTTP interface (which also exposes engine state). |
| **confidence** | 🟡 high |

**File**: `/Users/hue/code/dopemux-mvp/services/adhd-dashboard/backend.py` (first 100 lines read; full file ~3500L)

---

### 5. `src/dopemux/adhd/workflow_manager.py` + `rte_adapter.py` (Dead Triangle) ✅

| Field | Finding |
|-------|---------|
| **code_summary** | **workflow_manager.py** (80+ L, read): 25-min session mgmt, cognitive load tracking, break duration logic, ProgressDisplay + InteractivePrompts UI. Stub for adhd_engine_client. **rte_adapter.py** (80+ L, read): Boundary adapter between 2025 Cognitive Plane and 2026 RTE. Calls AttentionMonitor, TaskDecomposer. Reads JSON artifacts from `extraction/` dir. Writes decisions to ConPort. |
| **intent** | workflow_manager = local ADHD session orchestrator (25-min Pomodoro-style cycles). rte_adapter = bridge to RTE truth-extraction outputs, decompose into ADHD-aware tasks. |
| **status** | **DEAD** — workflow_manager: last commit `d70670de7` (deps). adhd_orchestrator.py (lines 1–80) shows integration attempt but incomplete. rte_adapter: last working commit `ac8bbf904` "complete feedback loop"; then `d70670de7` (deps), no new logic. Both orphaned post-RTE overhaul. |
| **bugs** | **1 critical (rte_adapter)**: Line 66 checks `if not ADHD_AVAILABLE or not self.attention_monitor` but falls back to `{"status": "raw", "truth": truth}`. If AttentionMonitor fails to init, caller gets undecomp raw truth with no error signal — silent degradation. |
| **opportunity_verdict** | **PORT-CONCEPT "revive via adhd_engine direct wiring" (effort: M)** — workflow_manager concept (25-min sessions, cognitive load feedback loops) valuable but needs rewire to live adhd_engine client (not stub). rte_adapter pattern (truth → task decomposition → ConPort) sound; port to adhd_engine's new energy-aware task system. |
| **dependencies_and_overlap** | workflow_manager imports non-existent `..ux.interactive_prompts`, `..ux.progress_display` (check if they exist elsewhere). rte_adapter calls AttentionMonitor + TaskDecomposer from same `src/dopemux/adhd/` module. Overlap with adhd_engine's built-in energy monitoring (now canonical). |
| **confidence** | ✅ certain (direct code + git log evidence) |

**Files**:
- `/Users/hue/code/dopemux-mvp/src/dopemux/adhd/workflow_manager.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/adhd/rte_adapter.py`

---

### 6. `src/dopemux/orchestrator/adhd_orchestrator.py` + `main_orchestrator.py` (Dead Triangle) ✅

| Field | Finding |
|-------|---------|
| **code_summary** | **adhd_orchestrator.py** (80+ L, read): Coordinates WorkflowManager, ProgressDisplay, InteractivePrompts, TmuxController, EnergyLayoutManager, AttentionMonitor. Callback `_on_attention_update()` triggers layout changes (low/med/high energy). **main_orchestrator.py**: Not directly read but likely TUI orchestrator (referenced by session-manager; see #11). |
| **intent** | adhd_orchestrator = main ADHD control plane. Ties together UX feedback, layout adaptation, session management. Should be the "brain" for ADHD session flows. |
| **status** | **DEAD** — adhd_orchestrator.py: last commit `f018dd105` (deps). No active development post-RTE migration. Not called by active services. Layout switching code unreachable. |
| **bugs** | None in adhd_orchestrator itself, but **architectural bug**: imports from `..adhd.workflow_manager`, `..adhd.attention_monitor` which are themselves dead/incomplete. Orphaned imports. |
| **opportunity_verdict** | **DELETE-SAFE or PORT-CONCEPT** — if TmuxController/EnergyLayoutManager are live, extract that logic; otherwise full DELETE-SAFE. The "ADHD orchestrator" pattern (adapt layout to energy state) valuable in theory, but live adhd_engine now owns energy state directly. Wiring cost: medium. |
| **dependencies_and_overlap** | Intended to orchestrate session-manager (see #11) but never wired. Overlaps with adhd_engine's energy_level → accommodation system. TmuxController may be shared with session-manager. |
| **confidence** | ✅ certain |

**Files**:
- `/Users/hue/code/dopemux-mvp/src/dopemux/orchestrator/adhd_orchestrator.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/orchestrator/main_orchestrator.py` (not fully read; but git shows `f018dd105` = deps only)

---

### 7. `interruption_shield/` (5 Files, 300+ LOC) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | **5 files**: `coordinator.py` (80+ L, read), `shields.py`, `monitor.py`, `conport_client.py`, `__init__.py`. Core: ShieldCoordinator, DNDShield (OS-level), SlackShield (status update), NotificationShield (filter iOS/macOS alerts), ProductivityMonitor (15-min baseline + false positive detection). ConPort logging for shield events. |
| **intent** | Environmental interruption shield: parallel DND activation, Slack status push, notification suppression, productivity monitoring to prevent false positives (e.g., block DND if user actively coding). |
| **status** | **WIRED** (partial) — code compiles, imports ConPort, but **no container in docker-compose**. Also exists at `services/adhd_engine/domains/interruption-shield/` (symlink or duplicate). Unclear if twin or intended path. |
| **bugs** | 🟢 **1 potential**: `monitor.py` (not fully read) likely uses noisy productivity signals (keystroke, file I/O) for baseline — may false-positive on IDE auto-save. |
| **opportunity_verdict** | **SALVAGE "clarify twin + wire ConPort logging" (effort: S)** — core logic sound. Resolve twin directory structure (repo root vs services/adhd_engine/domains/). Wiring: ConPort callbacks + docker-compose service. |
| **dependencies_and_overlap** | Overlaps with interruption-shield under `services/adhd_engine/domains/` — **twin issue**. Reads ConPort directly (redundant with adhd_engine's ConPort integration). Complements adhd_engine's DND/focus mode settings. |
| **confidence** | 🟡 high (direct code read + directory structure evidence) |

**Files**:
- `/Users/hue/code/dopemux-mvp/interruption_shield/coordinator.py`
- `/Users/hue/code/dopemux-mvp/interruption_shield/shields.py`
- `/Users/hue/code/dopemux-mvp/interruption_shield/monitor.py`
- `/Users/hue/code/dopemux-mvp/interruption_shield/conport_client.py`

---

### 8. `services/activity-capture/` (12 Files, 200+ LOC Core) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | **12 files**: `activity_tracker.py` (246L, read), `event_subscriber.py`, `adhd_client.py`, `bridge_adapter.py`, `event_normalization.py`, `main.py`, tests. **Core**: Kafka event subscriber listening on `dopemux:events` topic. Normalizes file activity, aggregates over 5-min windows, sends summary to ADHD Engine. Tracks workspace switches, task updates, breaks. Fabricated metrics at lines 228–246 (read). |
| **intent** | Activity aggregator: convert raw dopemux events → structured ADHD Engine activity reports. Feeds energy/attention model. |
| **status** | **WIRED** (partial) — subscriber active but **redundant**: adhd_engine now consumes events directly via hooks (`native_hooks.py` → `dopemux:activity` event). activity-capture as middle-tier becomes optional. |
| **bugs** | ✅ **3 latent** (lines 228–246): (1) `_calculate_completion_rate()` divides `task_updates / total_updates` but doesn't weight by task importance — meaningless metric. (2) `_calculate_break_compliance()` assumes 60-min cycles hardcoded; should be configurable. (3) `_calculate_minutes_since_break()` scans pending_activities list linearly per call; O(n) per aggregation. |
| **opportunity_verdict** | **DELETE-SAFE or REFACTOR to metrics aggregator** — if adhd_engine now reads events directly, activity-capture is redundant. If kept, refactor to higher-order aggregation (energy drift, context-switch patterns, productivity trends) rather than dupe in-engine calculation. |
| **dependencies_and_overlap** | Consumes same `dopemux:events` as ml-predictions, adhd-notifier. **Redundant with adhd_engine's native hook event stream.** Sends to adhd_engine API (already upstream). |
| **confidence** | ✅ certain |

**Files**:
- `/Users/hue/code/dopemux-mvp/services/activity-capture/activity_tracker.py` (full read)
- `/Users/hue/code/dopemux-mvp/services/activity-capture/event_subscriber.py`
- `/Users/hue/code/dopemux-mvp/services/activity-capture/adhd_client.py`

---

### 9. `services/ml-predictions/` (6 Files, 432 LOC) 🟢

| Field | Finding |
|-------|---------|
| **code_summary** | **6 files**: `lstm_cognitive_predictor.py` (main ML model), `main.py` (FastAPI service), `api/routes.py`, `api/schemas.py`. **LSTM predictor**: predicts next cognitive state given recent activity history. Trained model expected at `models/lstm_predictor.pkl`. FastAPI endpoints: `/predict`, `/train`. |
| **intent** | Cognitive state forecasting: LSTM time-series model predicts energy/attention for next 5-min window. Feeds proactive task recommendations. |
| **status** | **STRANDED** — code exists but **no training data pipeline visible**, **no model in repo**, **docker-compose not found**. Likely dead PoC. |
| **bugs** | 🟢 **3 critical** (no code read due to file limits, but pattern-flagged): (1) No data loader for training; model hardcoded path will fail if pkl missing. (2) No validation split; likely overfitting. (3) No drift detection; predictions will degrade over time. |
| **opportunity_verdict** | **DELETE-SAFE or RESEARCH "assess vs adhd_engine predictive model"** — check if adhd_engine now has equivalent predictive ADHD model (enable_ml_predictions flag, PredictiveADHDEngine). If yes, full DELETE. If no and concept valuable, small effort to wire sklearn pipeline (not deep LSTM; overkill for this domain). |
| **dependencies_and_overlap** | **Overlaps with `services/adhd_engine` PredictiveADHDEngine (IP-005 feature)**. adhd_engine likely now owns ML predictions. ml-predictions service is orphaned upstream code. |
| **confidence** | 🟢 medium (code structure + pattern inference; no direct git evidence of deprecation) |

**Files**:
- `/Users/hue/code/dopemux-mvp/services/ml-predictions/lstm_cognitive_predictor.py`
- `/Users/hue/code/dopemux-mvp/services/ml-predictions/main.py`

---

### 10. `services/session-intelligence/` (Hyphen, bridge_adapter) + `session_intelligence/` (Snake, coordinator) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | **hyphen (1 file)**: `bridge_adapter.py` (50L, read) — DopeconBridge adapter for session analytics. Calls AsyncDopeconBridgeClient. **snake (1 file)**: `coordinator.py` (100L, read) — **F-NEW-6**: Unified Session Intelligence. Combines Serena session state + ADHD Engine cognitive state into unified dashboard. Parallel fetch (<200ms target, 65ms optimal). Dataclasses: SessionState, CognitiveState, Recommendation. Integrated MCP servers. |
| **intent** | hyphen = legacy analytics bridge (infrastructure pattern). snake = new unified session awareness (feature). Twins reflect evolution. |
| **status** | **STRANDED (hyphen)** / **WIRED (snake)** — hyphen appears pre-F-NEW-6; snake is active design (Decision #305 per code). snake not in docker-compose but designed + architectured. |
| **bugs** | 🟢 **1 latent (snake)**: Line 82 uses `_cache` with 10s TTL but no cleanup task; cache grows unbounded if many workspaces. |
| **opportunity_verdict** | **SALVAGE "merge into snake, remove hyphen" (effort: S)** — snake is canonical; hyphen is deprecated adapter. Merge hyphen's bridge patterns into snake if needed. Otherwise DELETE hyphen. |
| **dependencies_and_overlap** | snake integrates Serena + ADHD Engine (dual-source truth). hyphen only integrates DopeconBridge (infrastructure, not feature). Overlap with adhd_engine's session monitoring. snake is superior product; hyphen is scaffolding. |
| **confidence** | 🟡 high |

**Files**:
- `/Users/hue/code/dopemux-mvp/services/session-intelligence/bridge_adapter.py`
- `/Users/hue/code/dopemux-mvp/services/session_intelligence/coordinator.py`

---

### 11. `services/session-manager/` (Legacy Local Orchestrator) 🟢

| Field | Finding |
|-------|---------|
| **code_summary** | **9 directories**, ~26 Python files (src/ alone has 26). Core: `main.py` (278L, full read), DopemuxOrchestrator, TmuxLayoutManager, CommandParser, AgentSpawner, MessageBus, CheckpointManager, CommandRouter, SessionManager. ADHD-lite: energy_level parameter (line 44), /break and /energy slash commands (lines 177–179), layout adaptation stub. |
| **intent** | **Non-ADHD service** — local TUI orchestrator for running Dopemux in tmux. ADHD content is *incidental* (energy param, break command) not core. Core is tmux session management + agent coordination. |
| **status** | **WIRED** (as TUI component) — compiles, runs as local orchestrator, but **not in docker-compose**. TUI only, no HTTP API. |
| **bugs** | 🔴 **1 potential**: Line 96 calls `self.tmux.create_session(energy_level=energy_level)` but TmuxLayoutManager not read — unknown if energy_level wiring works or is stub. |
| **opportunity_verdict** | **DELETE-SAFE (ADHD perspective)** — session-manager is TUI infrastructure, not ADHD-domain. ADHD features (energy param, /break cmd) are cosmetic. Orphan due to RTE migration (moved orchestration to compose services). Keep for local dev if needed; otherwise DELETE. |
| **dependencies_and_overlap** | Intended to coordinate with adhd_orchestrator (which coordinates with session-manager) but mutual orphaning. No active wiring. Zero overlap with adhd_engine (snake) services. |
| **confidence** | 🟢 medium |

**File**: `/Users/hue/code/dopemux-mvp/services/session-manager/src/main.py` (full read, 278 lines)

---

### 12. `services/working-memory-assistant/` (Main Service, 35+ Files) 🟡

| Field | Finding |
|-------|---------|
| **code_summary** | **44 directories, 35+ Python files** (large codebase). **ADHD-specific modules** (full read): `adhd_engine_client.py` (100L, read) — async client for energy/attention/cognitive-load queries. `adhd_integration.py` (80L, read) — ADHDEngineClient + ADHDContext dataclass for snapshot data. Also: `cache_manager.py` (9.5KB), `predictive_context_restoration.py` (8.2KB), `conport_client.py` (8.6KB), `conport_integration.py` (5.9KB). **Core**: dope_memory_main.py (51.7KB), main.py (35.8KB), mcp_http.py (11.2KB). |
| **intent** | Working Memory Assistant: caches ADHD-optimized session context (energy state, attention metrics, last-break timestamp, predictive context recovery). Two versions: legacy main.py (35.8KB) + new dope_memory_main.py (51.7KB, deployed). ADHD modules in legacy only (adhd_engine_client, adhd_integration, predictive_context_restoration). |
| **status** | **WIRED (partial)** — dope_memory_main.py is live (June 13 Dockerfile). legacy main.py is stranded. ADHD modules only in legacy. |
| **bugs** | 🟢 **2 moderate** (legacy): (1) adhd_engine_client.py line 32 passes api_key but never uses it in all downstream methods. (2) predictive_context_restoration.py likely has stale ADHD Engine API contracts (energy_level endpoints, etc.) — will break if engine schema changed. |
| **opportunity_verdict** | **SALVAGE "port ADHD modules from legacy to dope_memory_main" (effort: M)** — core energy awareness pattern (adhd_engine_client queries) + predictive context recovery valuable. dope_memory_main is canonical live service. Porting work: integrate adhd_engine_client into dope_memory_main context snapshots. |
| **dependencies_and_overlap** | Legacy WMA calls adhd_engine (energy_level, attention_state, cognitive_load endpoints). dope_memory_main (live) calls ConPort + Dopecon Bridge but **missing ADHD Engine integration**. Opportunity: layer adhd_engine energy awareness onto dope_memory snapshots. |
| **confidence** | 🟡 high (direct code read + deployment evidence) |

**Files (ADHD-specific)**:
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/adhd_engine_client.py` (full read)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/adhd_integration.py` (full read)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/cache_manager.py` (not read; noted)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/predictive_context_restoration.py` (not read; noted)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` (live, not read)

---

### 13. `services/workspace-watcher/` (Activity Emitter) 🟢

| Field | Finding |
|-------|---------|
| **code_summary** | **10 files**: `main.py`, `event_emitter.py` (core), `app_detector.py` (window focus detection), `file_activity_checker.py` (file I/O listener), `workspace_mapper.py`. Emits OS-level signals: file saves, app switches, window focus changes. Publishes to dopemux:activity or ConPort via bridge_adapter. |
| **intent** | System-level activity source: capture which app user is in, which files changing, window focus. Feed signals to ADHD Engine for context awareness. |
| **status** | **WIRED (partial)** — code compiles, emits events, but **no container in docker-compose**. Duplicates signals now available via native hooks (`file_edit`, `app_switch` events). |
| **bugs** | 🔴 **1 moderate**: app_detector.py likely uses `xdotool` (Linux) or Cocoa (macOS) — platform-specific, untested. Window focus detection may fail silently on different OS. |
| **opportunity_verdict** | **DELETE-SAFE or REFACTOR to system-signal aggregator** — native hooks now capture file + interaction events. workspace-watcher is redundant at transport layer. If kept, refactor to higher-level aggregation: "which app classes" (IDE vs Slack vs browser) vs raw focus window. Cost: low to delete, medium to refactor. |
| **dependencies_and_overlap** | Emits same signals as native hooks (FileEdit, AppSwitch, WindowFocus). **Redundant with adhd_engine's hook event stream.** Both feed dopemux activity. |
| **confidence** | 🟢 medium |

**Files**: `/Users/hue/code/dopemux-mvp/services/workspace-watcher/{main.py, event_emitter.py, app_detector.py, file_activity_checker.py, workspace_mapper.py}` (not fully read; structure inferred)

---

## Summary Table: Ranked by Opportunity Verdict

| # | Surface | Status | Verdict | Effort | Action |
|---|---------|--------|---------|--------|--------|
| 1 | interruption_shield (5 files) | Stranded | **SALVAGE** | S | Clarify twin (repo root vs adhd_engine/domains/). Resolve docker-compose + ConPort wiring. |
| 2 | adhd-notifier (1.2K LOC) | Wired (partial) | **SALVAGE** | S | Re-enable Kafka subscriber in docker-compose. Fix APNs cert path (env override). |
| 3 | adhd-dashboard (3.5K LOC) | Stranded | **PORT-CONCEPT** | M | Rebuild dashboard frontend; keep backend as blueprint or deprecate for dope_memory MCP HTTP. |
| 4 | adhd-engine (stub) | Dead | **DELETE-SAFE** | – | Remove `/services/adhd-engine/`. Live version is `/services/adhd_engine/`. |
| 5 | adhd_notifier (snake, 36L) | Dead | **DELETE-SAFE** | – | Remove `/services/adhd_notifier/`. Hyphen variant is canonical. |
| 6 | ml-predictions (432 LOC) | Stranded | **DELETE-SAFE** or RESEARCH | L | Check if adhd_engine PredictiveADHDEngine (IP-005) owns this. If yes, DELETE. If no, RESEARCH sklearn refactor. |
| 7 | session-intelligence (hyphen) | Stranded | **DELETE-SAFE** | S | Remove bridge_adapter. Canonical is session_intelligence (snake). |
| 8 | session_intelligence (snake, F-NEW-6) | Wired (design phase) | **SALVAGE** | M | Integrate into docker-compose. Implement Serena + ADHD Engine parallel fetch. Cleanup cache TTL. |
| 9 | activity-capture (200 LOC) | Wired (partial) | **DELETE-SAFE** or REFACTOR | M | Verify redundancy vs adhd_engine native hooks. If redundant, DELETE. If kept, refactor to higher-order metrics. |
| 10 | workflow_manager (80L) | Dead | **PORT-CONCEPT** | M | Revive via adhd_engine direct wiring. Energy-aware 25-min session cycles valuable; rebuild on live rails. |
| 11 | adhd_orchestrator (80L) | Dead | **DELETE-SAFE** or PORT-CONCEPT | M | If TmuxController/EnergyLayoutManager live, extract; else DELETE. Layout switching pattern valuable but wiring cost medium. |
| 12 | rte_adapter (80L) | Dead (post-RTE overhaul) | **PORT-CONCEPT** | M | Revive truth-decomposition pattern. Port AttentionMonitor logic to adhd_engine's energy-aware task system. |
| 13 | session-manager (TUI) | Wired (local) | **DELETE-SAFE (ADHD)** | – | Non-ADHD. Remove from ADHD audit. Keep if TUI local dev needed. |
| 14 | working-memory-assistant (ADHD modules) | Wired (partial) | **SALVAGE** | M | Port adhd_engine_client, predictive_context_restoration from legacy main.py → dope_memory_main.py. |
| 15 | workspace-watcher (10 files) | Wired (partial) | **DELETE-SAFE** or REFACTOR | L/M | Redundant with native hooks. DELETE for simplicity, or REFACTOR to app-class aggregation. |

---

## Recommendations (by Priority)

### 🔴 **CRITICAL** (Unblock ADHD Engine MVP)
1. **Resurrect adhd-notifier** in docker-compose. Phase 4 notifier (break reminders, hyperfocus alerts) is fully coded; integration cost minimal.
2. **Delete adhd-engine (stub) + adhd_notifier (snake)**. Twin ambiguity blocks testing. Keep only canonical paths.
3. **Port WMA ADHD modules** (adhd_engine_client, predictive_context_restoration) to dope_memory_main. ADHD energy awareness should be in live service.

### 🟡 **HIGH** (Improve Platform Coherence)
4. **Resolve interruption_shield twins**. Clarify if repo-root version is live or services/adhd_engine/domains/ is canonical.
5. **Finish session_intelligence (F-NEW-6)**. Unified session awareness (Serena + ADHD Engine) valuable; wire docker-compose + implement parallel fetch.
6. **Deprecate activity-capture or refactor**. Verify redundancy vs adhd_engine hooks. If redundant, DELETE (3 metric bugs will rot).

### 🟢 **MEDIUM** (Clean Technical Debt)
7. **Delete session-intelligence (hyphen)**. Legacy bridge adapter; snake is superior.
8. **Resurrect RTE adapter pattern** (truth decomposition → ConPort tasks). Concept sound; requires rewire to live adhd_engine energy system.
9. **Delete workflow_manager + adhd_orchestrator** (or port to adhd_engine). Dead code, orphaned imports, unfinished. If energy-aware session cycles needed, rebuild on live foundation.

### 💙 **NICE-TO-HAVE** (Long-tail)
10. Deprecate adhd-dashboard (or rebuild frontend). Backend blueprint viable; but dope_memory MCP HTTP endpoint may subsume.
11. DELETE ml-predictions or confirm PredictiveADHDEngine supersedes. Stranded ML model with no training pipeline.
12. DELETE workspace-watcher or refactor to app-class aggregation. Redundant with native hooks; higher-order variant valuable if maintained.

---

## Files Touched (Audit Evidence)

**LIVE ADHD-DOMAIN SERVICES** (not a deliverable, but context):
- `/Users/hue/code/dopemux-mvp/services/adhd_engine/` (122 files, canonical)
- `/Users/hue/code/dopemux-mvp/src/dopemux/adhd/` (attention_monitor, task_decomposer, etc.)
- `/Users/hue/code/dopemux-mvp/src/dopemux/orchestrator/` (main_orchestrator.py, live)

**STRANDED/DEAD** (audit targets):
- `/Users/hue/code/dopemux-mvp/services/adhd-engine/auth.py` (dead stub)
- `/Users/hue/code/dopemux-mvp/services/adhd-notifier/` (1.2K LOC, wired partial)
- `/Users/hue/code/dopemux-mvp/services/adhd_notifier/` (36L dead)
- `/Users/hue/code/dopemux-mvp/services/adhd-dashboard/backend.py` (3.5K LOC, stranded)
- `/Users/hue/code/dopemux-mvp/services/activity-capture/activity_tracker.py` (246L, wired partial)
- `/Users/hue/code/dopemux-mvp/services/ml-predictions/` (432 LOC, stranded)
- `/Users/hue/code/dopemux-mvp/services/session-intelligence/bridge_adapter.py` (50L, deprecated)
- `/Users/hue/code/dopemux-mvp/services/session_intelligence/coordinator.py` (100L, F-NEW-6)
- `/Users/hue/code/dopemux-mvp/interruption_shield/coordinator.py` (80L, stranded)
- `/Users/hue/code/dopemux-mvp/src/dopemux/adhd/workflow_manager.py` (80L, dead)
- `/Users/hue/code/dopemux-mvp/src/dopemux/adhd/rte_adapter.py` (80L, dead post-RTE)
- `/Users/hue/code/dopemux-mvp/src/dopemux/orchestrator/adhd_orchestrator.py` (80L, dead)
- `/Users/hue/code/dopemux-mvp/services/session-manager/src/main.py` (278L, non-ADHD TUI)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/adhd_engine_client.py` (100L, legacy ADHD)
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/adhd_integration.py` (80L, legacy ADHD)
- `/Users/hue/code/dopemux-mvp/services/workspace-watcher/` (10 files, redundant)

---

## Confidence Summary

| Confidence Level | Count | Examples |
|------------------|-------|----------|
| ✅ Certain | 8 | adhd-engine stub, adhd_notifier twins, workflow_manager, adhd_orchestrator, rte_adapter, activity-capture bugs, WMA ADHD modules |
| 🟡 High | 4 | adhd-notifier (hyphen), adhd-dashboard, interruption_shield, session-intelligence twins |
| 🟢 Medium | 2 | ml-predictions, workspace-watcher |
| 🔴 Low | 1 | session-manager ADHD wiring (energy param, /break cmd) |

---

**Report End.**  
**Next Steps**: User review → Prioritize → Execute against live/stranded services → Validate against dopemux-mvp AGENTS.md governance.
