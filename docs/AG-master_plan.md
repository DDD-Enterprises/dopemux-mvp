# Dopemux Master Engineering Plan

## 1. Executive Context
**Status:** Post-Audit Stabilization
**Goal:** Transition from a fragile hybrid state to a robust, unified architecture.
**Owner:** Antigravity System (Handoff Ready)

This document details the exact engineering tasks required to fix debt, stabilize the stack, and evolve the "Memory Stack". Use the "Context" and "Hints" to execute without needing to re-read the entire history.

---

## 2. Work Stream Inventory

### Stream A: Validation (Immediate)
**Goal:** Verify the fixes made in the recent audit session.

- [ ] **Frontend Verification**
    - **Context**: The `adhd-engine` now runs on `localhost:8095` (Host), while `adhd-dashboard` is a React app served via `backend.py` on `:8097`.
    - **Task**: 
        1. Open `http://localhost:8097` in browser.
        2. Check "System Health" widget. It pulls from `http://localhost:8095/health`.
        3. Check "Memory" tab. It relies on Redis key `dopemux:events` which `task-orchestrator` writes to.
    - **Hint**: If unrelated CORS errors appear, check `backend.py` CORS middleware.

- [ ] **PAL Host Stability**
    - **Context**: PAL was migrated from Docker to `uv run` on Host (PID tracked).
    - **Task**: Leave `scripts/start-all.sh` running for >1 hour. Check `ps aux | grep pal_http_wrapper` to ensure it hasn't crashed.
    - **Verification**: `curl http://localhost:3003/health` must return 200 OK.

- [ ] **Postgres Mirror Activation**
    - **Context**: `services/working-memory-assistant` has a "Postgres Mirror" feature currently disabled.
    - **Task**:
        1. Open `services/working-memory-assistant/.env`.
        2. Set `ENABLE_MIRROR_SYNC=true`.
        3. Ensure `POSTGRES_URL` points to the containerized Postgres (`localhost:5455`).
    - **Verification**: `docker logs dopemux-working-memory` should show "Mirror sync active".

### Stream B: Architecture Cleanup (Next Sprint)
**Goal:** Remove "Zombie" code and files identified in the Audit.

- [ ] **MetaMCP Deprecation**
    - **Target**: `src/dopemux/mcp/broker.py` & `src/dopemux/mcp/router.py`.
    - **Context**: This custom broker logic is legacy. We want to use `litellm` (Port 4000) or standard `mcp-client`.
    - **Action**:
        1. Refactor `src/dopemux/cli.py` commands (`plan`, `chat`) to use `mcp-client` for tool discovery.
        2. Delete `src/dopemux/mcp/` directory once zero references remain.
    
- [ ] **Research Service Consolidation**
    - **Context**: We have `gptr-mcp` (Stock Fork) and `dopemux-gpt-researcher` (Custom). We picked Custom.
    - **Action**:
        1. Delete `docker/mcp-servers/gptr-mcp` directory.
        2. Delete `docker/mcp-servers/exa` directory (redundant).
        3. Remove commented-out services from `docker/mcp-servers/docker-compose.yml`.

- [ ] **Service Directory Pruning**
    - **Target**: `services/adhd_engine/services/`.
    - **Context**: This is a nested duplicate of the root `services/`.
    - **Action**: `rm -rf services/adhd_engine/services/` after verifying `start-all.sh` only references root services.

### Stream C: Containerization (DevOps)
**Goal:** Unify the runtime. Move "Host" services back to "Docker".

- [ ] **ADHD Engine Containerization**
    - **Target**: `services/adhd_engine/Dockerfile`.
    - **Issue**: `python-bidi` and other glue libs caused build failures, forcing a move to Host.
    - **Action**:
        1. Create new `Dockerfile` based on `python:3.11-slim`.
        2. Use `uv export` to generate a rigorous `requirements.txt` that pins binary wheels.
        3. Update `docker-compose.yml` to uncomment `adhd-engine` and bind port `8095:8095`.

### Stream D: Historical Backlog (Debt Repayment)
**Goal:** Close items left open in previous sessions (`task.md` history).

- [ ] **Test Suite Stabilization**
    - **Context**: `pytest` fails with collection errors in `roast-engine` and `serena` due to missing `__init__.py` or path issues.
    - **Task**: Run `pytest` recursively. Fix `ModuleNotFoundError` by adding `sys.path` hacks or `conftest.py` adjustments.
    
- [ ] **Contract Tests for Orchestrator**
    - **Context**: `task-orchestrator` APIs drift often.
    - **Task**: Create `tests/contract/test_orchestrator_api.py`. Test `/health`, `/tasks/create`, `/status`. 

- [ ] **V1-C Schema Hardening**
    - **Context**: `chat-audit` pipeline outputs need strict JSON validation.
    - **Task**: Implement Pydantic models in `src/chat_audit/schemas/` for `Claim`, `Conflict`, and `Synthesis`. Enforce them in `run.py`.

### Stream E: Memory Stack Evolution ("Brain" Roadmap)
**Goal:** Implement Phase 2 & 3 of the `Dope-Memory` Spec.

- [ ] **Reflection Pulse (Phase 2)**
    - **File**: `services/working-memory-assistant/reflection/pulse.py` (New).
    - **Spec**: Trigger a "Reflection" job if user is idle for >20min. Summarize the session from `work_log_entries` table.
    - **Store**: Write to new `reflection_cards` table in SQLite.

- [ ] **Causal Graph (Phase 3)**
    - **File**: `services/working-memory-assistant/graph/edges.py`.
    - **Spec**: Use LLM to analyze `work_log_entries` and propose "Caused By" edges.
    - **Store**: Sync these edges to Postgres (AGE Graph DB) via `dope-query`.

- [ ] **DopeQuery Rename**
    - **Context**: `conport-kg` is now `dope-query`.
    - **Action**: `mv services/conport_kg services/dope-query`. Update `pyproject.toml` name to `dope-query`.

### Stream F: Codebase Gaps (Grep Findings)
**Goal:** Fix specific code-level TODOs found in `src/`.

- [ ] **Vector Store Performance**
    - **Location**: `src/dopemux/extraction/hybrid_vector_store.py` (L651).
    - **Task**: "Implement ScaNN". Swap generic cosine similarity for `scann` library for faster retrieval.
    
- [ ] **Hooks Integration**
    - **Location**: `src/dopemux/hooks/claude_code_hooks.py` (L215).
    - **Task**: "Implement dopemux trigger command". Replace placeholder print with actual `subprocess.run(["dopemux", "trigger", ...])`.

- [ ] **Orchestrator Drift**
    - **Location**: `services/dopecon-bridge`.
    - **Task**: Grep for "TODO" status map. Map `TODO` string to `TaskStatus.PENDING` enum explicitly to prevent `KeyError`.

---

## 3. Verification Commands

| Component | Command | Success Criteria |
|-----------|---------|------------------|
| **Full Stack** | `./scripts/start-all.sh --verify` | All "Health Check" lines show ✅ 200 OK |
| **PAL** | `curl http://localhost:3003/health` | `{"status": "ok"}` |
| **ADHD Engine** | `curl http://localhost:8095/docs` | Swagger UI HTML response |
| **Task Orch** | `docker logs dopemux-mcp-task-orchestrator` | "Connected to PAL" (No connection refused) |
| **Tests** | `pytest tests/integration/` | Pass with no collection errors |
