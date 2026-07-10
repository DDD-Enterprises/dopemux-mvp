# PR #1031 CI Failure Analysis

**Head analyzed:** `e2c684eaa0686c99f558a60b73119c6cfe27b4f9`  
**Timestamp:** 20260710T040712Z  
**Packet:** TP-DMX-MCP-RUNTIME-006R2

---

## Workflow 1: Complete CI Pipeline

| Field | Value |
|---|---|
| workflow | Complete CI Pipeline (ADHD-Optimized) |
| run | 29067426650 |
| job | Unit Tests / Code Quality & Linting |
| headSha | e2c684eaa0686c99f558a60b73119c6cfe27b4f9 |

### Causal error A — Unit Tests

| Field | Value |
|---|---|
| step | Run fast unit gate |
| command | `uv run --frozen pytest tests/unit ... -n auto --maxfail=1` |
| exit code | 2 |
| first causal error | `test_reuses_running_singleton_with_http_env` |
| message | `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER: :7890 occupied by unlabeled container` |
| root cause | Docker stub in `tests/unit/test_task_orchestrator_http_singleton.py` does not answer `docker inspect` for `dopemux.project_root` / `.Name`. Packet 005 launcher `refuse_foreign_port_owner` treats unlabeled fixed-port occupant as block. Stub returns a generic cid for all `docker ps` without ownership labels. |
| downstream | CI summary fails because `gate_tests=failure` |
| local reproduction | `pytest -q tests/unit/test_task_orchestrator_http_singleton.py` |
| files implicated | `tests/unit/test_task_orchestrator_http_singleton.py` (stub); launcher script unchanged |
| proposed narrow fix | Extend docker stub to emit project_root label (and harmless name) so ownership check passes for the simulated healthy singleton |
| confidence | high |

### Causal error B — Code Quality root hygiene

| Field | Value |
|---|---|
| step | Enforce repo root hygiene |
| command | root-hygiene against changed files |
| exit code | 1 |
| first causal error | top-level directory `proofs` is not allowlisted |
| files | `proofs/mcp-runtime/dnh-crm-e2e/20260710T034241Z/*` |
| root cause | Packet 006/006R introduced intentional proof path `proofs/` but policy only allowed `proof/` |
| proposed narrow fix | Add `proofs` to `config/repo_hygiene/root_hygiene_policy.json` |
| confidence | high |

---

## Workflow 2: docs

| Field | Value |
|---|---|
| workflow | docs |
| run | 29067426635 |
| step | pre-commit on PR range |
| exit code | 1 |

### Causal error C — markdown-location-guard

| Field | Value |
|---|---|
| hook | markdown-location-guard |
| file | `proofs/mcp-runtime/dnh-crm-e2e/20260710T034241Z/SUMMARY.md` |
| root cause | exclusion regex allows `proof/` but not `proofs/` |
| proposed narrow fix | extend exclusion to `proofs/` in `.pre-commit-config.yaml` |
| confidence | high |

### Causal error D — root-hygiene (docs job)

Same as Causal error B (shared policy).

---

## Review items (parallel track)

| ID | Path | Class | Fix |
|---|---|---|---|
| R1 | `port_leases.py` | MUST_FIX | per-worker/pid/test unique pytest registry path |
| R2 | `test_mcp_docker_inspect.py` | MUST_FIX | restore prior coverage + keep compose tests |
| R3 | `.claude/claude_config.json` | MUST_FIX | revert PR delta to base |
| R4 | `task_orchestrator_identity.py` | MUST_FIX | root+id mismatch → CONFLICT; normalize IDs |
| R5 | Codex usage limit | INFO | no code action |

---

## Also present on base PR #1030

Same unit-test stub failure and `proofs/` hygiene failure exist on #1030 head. Fixes on #1031 stack will still leave #1030 blocked until base merges or is separately remediated; stack merge order remains #1030 then #1031.
