# TP-DMX-EVIDENCE-GATE-VERIFY-001 Summary

**Executor:** Antigravity (Claude Sonnet 4.6 Thinking)  
**Branch:** `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`  
**HEAD SHA:** `8be0675579f501582c74e14a409343ac6384edb3`  
**Dirty State:** dirty (M src/dopemux/tmux/cli.py + 6 untracked)  
**Runtime Process Checks:** ✅ Performed (`docker ps`, `curl`)  
**Executed:** 2026-06-06

---

## Verdict

**READY_FOR_NEXT_PACKET**

All 12 gates have statuses. No stop conditions triggered. No secrets printed. No source/config/docs edited. No commits made. No forbidden files touched.

---

## Gate Results

| Gate | Status | Key Evidence | Next Action |
|------|--------|-------------|-------------|
| VG-001 | ✅ VERIFIED | `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exists at correct path. Misspelling only in advisory/archive contexts. | Monitor upload-set for drift to misspelled variant. |
| VG-002 | ✅ VERIFIED | jpicklyk Docker MCP container live on 3001/tcp (stdio). Dopemux FastAPI (port 8000) returns CURL exit 7 — not running. Two-surface split confirmed. | Document fate of app/main.py before factory automation. |
| VG-003 | ✅ VERIFIED | All 43 services/ dirs inventoried and classified: A=compose-wired, B=standalone-not-in-compose, C=utility-library, D=UI-stub, E=empty/dead, F=meta-only. Naming duplicates identified. | Reconcile naming duplicates; prune dead dirs. |
| VG-004 | ⚠️ STILL_UNKNOWN | server.py binds 0.0.0.0:8098 (not 1561) with no auth middleware. Container NOT running. Unauthenticated exposure is *conditional* on deployment, not currently active. | Flag as SEC-001 (MEDIUM). Add auth before any deployment. |
| VG-005 | ✅ VERIFIED | `collect_truth_split()` (line 523) is a REAL implementation. Always-PASS stubs exist only in test `monkeypatch` (test isolation). Production gate at line 1411 calls real logic. Prior evidence pack claim was incorrect. | Concern resolved. No TP-RTE-S7-DRIFT-FIX-001 prerequisite from this gate. |
| VG-006 | ⚠️ STILL_UNKNOWN | `LIVE_WRITE_READY` is an enum VALUE in DCP schemas (vocabulary) but not assigned anywhere in code/config/runtime. K-46 open item. All DCP docs confirm undefined+blocking. | Dedicated packet needed to define proof criteria and authorization. |
| VG-007 | ⚠️ STILL_UNKNOWN | DCP-RED-MERGE-SEAM-0001 is schema-defined and task-packet documented. TP-DCP-0003.md has a manual git diff guard. No compiled runtime enforcement (import guard, pre-commit hook, CI check) found. | Add pre-commit hook or CI check to block DCP Core imports of queue_drain/batch_resolve_and_merge. |
| VG-008 | ⚠️ STILL_UNKNOWN | services/agents/ has 15 prototype Python files, no Dockerfile/compose/src-import path. Tests import from `dopemux.agent_orchestrator` (src/), not services/agents/. No live production caller found. | Confirm whether src/ re-exports services/agents/ code. If dead, archive. |
| VG-009 | ✅ VERIFIED | .mcp.json: `type=stdio`. Wrapper launches jpicklyk v3.8.0 Docker. Container confirmed live (3001/tcp). HTTP singleton (8000) not running. stdio is sole active transport. | Document Dopemux FastAPI TO is not deployed. |
| VG-010 | ✅ VERIFIED | `dope_memory_main.py` is the canonical entry point, configured via Dockerfile.dope-memory (CMD ["python", "dope_memory_main.py"]) on port 3020 and run inside the container. WMA FastAPI `main.py` is not wired into compose/docker. | None. Verification complete. |
| VG-011 | ✅ VERIFIED | `conport_kg` and `conport_kg_ui` are inactive/superseded. `dopecon-bridge` routes only load API proxy routes to `conport_client`, not `conport_kg`. `mcp-integration-bridge` is not configured or running in `compose.yml`. | None. Recommend pruning legacy services/conport_kg/ and conport_kg_ui/. |
| VG-012 | ✅ VERIFIED | .claude/hooks/ ADHD Engine integration is REAL: check_energy.sh, save_context.sh, log_progress.sh, prompt_analyzer.py all curl localhost:8080. NOT a stub. ADHD Engine container NOT currently running — hooks degrade gracefully. | Start ADHD Engine if operator support depends on it. Run docker ps -a | grep adhd to check stopped state. |

**Summary:** 8 VERIFIED · 4 STILL_UNKNOWN · 0 CONFLICTING · 0 BLOCKED (12 gates total)

---

## High-Risk Findings

### SEC-001 — MEDIUM: monitoring-dashboard unauthenticated bind
- **File:** `services/monitoring-dashboard/server.py:1563`
- **Code:** `uvicorn.run("server:app", host="0.0.0.0", port=8098)`
- **Finding:** FastAPI app has no authentication middleware on dashboard API endpoints. `auth_required=True` only applies to *monitored downstream services*, not the dashboard itself.
- **Risk condition:** Container NOT currently running. Risk activates on deployment.
- **Action:** Add API key or restrict to 127.0.0.1 before deployment.

### SEC-002 — LOW: ADHD Engine hooks unauthenticated
- **File:** `.claude/hooks/check_energy.sh:18`
- **Finding:** `curl -s localhost:8080/api/v1/state` with no authentication token.
- **Risk:** Local port spoofing could inject false energy state.
- **Action:** Add shared secret to ADHD Engine hook calls if port 8080 is network-accessible.

### VG-007 — Process gap: DCP-RED-MERGE-SEAM-0001 docs-only
- **Finding:** The merge seam prohibition is schema-vocabulary + process discipline only. No runtime-compiled guard exists.
- **Action:** Pre-commit hook or CI check to block DCP Core imports of red-line files.

---

## Key Evidence Pack Corrections

| Prior Evidence Pack Claim | Actual Status | Evidence |
|--------------------------|---------------|---------|
| "S7 collect_truth_split always-PASS stub" | INCORRECT — function is real implementation | `validate_pre_live_gate_v25.py:523`, test monkeypatches are test isolation only |
| "monitoring-dashboard binds 0.0.0.0:1561" | INCORRECT — actual port is 8098 | `server.py:1564` |
| "all components runtime_process_verified: false" | PARTIALLY CORRECTED — docker ps performed; jpicklyk TO and 8 MCP containers confirmed live | `docker ps` output |

---

## Changed Packet Ordering

Per Section 13 decision logic:

- VG-004: monitoring-dashboard is **NOT actively exposed** (container not running) → security finding flagged but does not require immediate blocking packet
- VG-005: S7 is **real enforcement** → TP-RTE-S7-DRIFT-FIX-001 prerequisite concern resolved
- VG-012: ADHD hooks are **real and wired** → not dead; engine liveness concern noted but not blocking

**→ Next packet: `TP-RTE-SP-PHASE-CONTRACT-001`**

Rationale: VG-004 concern is conditional (not live); VG-005 resolved; VG-012 real-but-engine-down; VG-006/VG-007 are open but scoped (schema + process gaps, not factory blockers for SP contract work).

Recommend also scheduling **TP-DMX-MONITORING-DASHBOARD-SECURITY-001** before any factory run that starts the monitoring-dashboard container.

---

## No-Write Confirmation

| Invariant | Status |
|-----------|--------|
| Source files edited | ✅ NO |
| Docs/configs edited | ✅ NO |
| Commits made | ✅ NO |
| Dopetask execution | ✅ NO |
| Task-Orchestrator writes | ✅ NO |
| ConPort writes | ✅ NO |
| dope-memory writes | ✅ NO |
| dope-context writes | ✅ NO |
| dopecon-bridge writes | ✅ NO |
| GitHub mutation | ✅ NO |
| Merge automation | ✅ NO |
| queue_drain.py touched/invoked | ✅ NO |
| batch_resolve_and_merge.py touched/invoked | ✅ NO |

---

## Recommended Next Packet

**Primary:** `TP-RTE-SP-PHASE-CONTRACT-001`

**Secondary (schedule before dashboard deployment):** `TP-DMX-MONITORING-DASHBOARD-SECURITY-001`

**Do NOT proceed to `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` yet** — VG-007 (DCP-RED-MERGE-SEAM-0001 docs-only enforcement) needs hardening first.

---

## Proof Artifact Paths

- `proof/TP-DMX-EVIDENCE-GATE-VERIFY-001/VERIFICATION_GATES_REPORT.json`
- `proof/TP-DMX-EVIDENCE-GATE-VERIFY-001/SUMMARY.md`
- `proof/TP-DMX-EVIDENCE-GATE-VERIFY-001/NO_WRITE_CONFIRMATION.md`

---

## Embedded Audit Request

See `proof/TP-DMX-EVIDENCE-GATE-VERIFY-001/AUDIT_REQUEST.md` for the embedded audit prompt. AGY/Sonnet or Claude Code Sonnet should audit this report before the next packet is authorized.
