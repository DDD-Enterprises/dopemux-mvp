# V5 Extractor — Complete Plan Checklist

Source: `purring-puzzling-coral.md` (V5 Extraction Engine Live Run Readiness & Prompt Optimization)

**Legend**: `[ ]` pending | `[~]` in progress | `[x]` done | `[!]` blocked
**Tool key**: `CX` = Codex Desktop | `CC:O` = Claude Code Opus | `CC:S` = Claude Code Sonnet | `GC` = Gemini CLI

---

## Phase A — Safety Gates (Must Complete Before Live Run)

### A0. Resolve Bundle Conflicts `CX GPT-5.4-mini`
- [ ] Resolve 47 conflict markers in `model_map.yaml`
  - Accept HEAD for model IDs (`grok-4-1-fast-reasoning`)
  - Accept pr321 for lane_class assignments (`BULK_DOCS_GENERAL` for R/S)
- [ ] Resolve 11 conflict markers in `run_extraction_v5.py`
  - Accept HEAD for auth sequence
  - Accept pr321 for sampling logic
- [ ] Verify: `grep -c "<<<<<<" model_map.yaml run_extraction_v5.py` → both return 0

### A1. Hard Cost Ceiling `CX GPT-5.4`
- [ ] Add `--max-cost-usd` CLI flag to `run_extraction_v5.py`
- [ ] Wire into prescan cost estimator (`lib/prescan/cost_estimator.py`)
- [ ] Abort before batch submission if projected cost exceeds budget

### A2. Dual Live-Consent Guard `CX GPT-5.4-mini`
- [ ] Require both `--execute` AND `DPMX_LIVE_OK=1` env var for live API calls
- [ ] Add guard at all `batch_clients.submit()` and `_execute_live_batch()` call sites

### A3. Fix Batch Result Parsing `CX GPT-5.4-mini`
- [ ] Count discarded JSON lines in `lib/batch_clients.py` `fetch_results()` (~L154-176)
- [ ] Log every discard with content
- [ ] Abort if >5% loss: `BatchCorruptionError`

### A4. Per-Phase Spend Accumulator `CX GPT-5.4`
- [ ] Create new `lib/spend_ledger.py` with `SpendLedger` class
- [ ] Track `input_tokens`, `output_tokens`, `estimated_cost_usd` per phase
- [ ] Write to `{run_dir}/spend_ledger.json` after each phase
- [ ] Check against `--max-cost-usd` before starting next phase

### A5. Prescan Model Routing Optimization `CX GPT-5.4-mini`
- [ ] Route dedup/discover/feasibility passes to `gpt-5-nano` in `lib/prescan/grok_passes.py`
- [ ] Keep Grok 4.20 for optimize pass only

### A6. Enable Batch API by Default `CX GPT-5.4-mini`
- [ ] Change `--batch-mode` default to `True` in `run_extraction_v5.py`
- [ ] Add `--no-batch` flag for explicit opt-out

### A7. Integration Test `CX GPT-5.4`
- [ ] Create `tests/test_live_integration_pilot.py`
- [ ] 1 real batch submission (1 partition, `gpt-5-nano`)
- [ ] Mark with `@pytest.mark.live`

### Phase A Verification
- [ ] `python validate_pre_live_gate_v25.py`
- [ ] `pytest services/repo-truth-extractor/tests/ -k "not live"`
- [ ] `dopemux audit wizard --dry-run`

---

## Phase B — Deep Prompt Audit & Optimization

### TIER 1 — Structural Fixes

#### Pass 1: Input Scope Dedup + Boilerplate Extraction `CX GPT-5.4-mini`
- [ ] Deduplicate every Inputs section using `PHASE_SCOPE_HINTS` (53 prompts)
- [ ] Create shared `PROMPTSET_RULES.md` (Evidence + Determinism + Anti-Fabrication)
- [ ] Replace 35-40 line boilerplate blocks with single-line references (128 prompts)
- [ ] Modify rewrite script to prevent re-triplication
- [ ] Verify: zero duplicate paths in any Inputs section
- [ ] Verify: no prompt Inputs > 30 lines

---

### TIER 2 — Extraction Procedure Rewrites

#### Pass 2: Phase A Extraction Procedures (15 prompts) `CX GPT-5.4`
- [ ] A1: Replace generic template with concrete file/pattern instructions
- [ ] A2: Replace generic template with concrete file/pattern instructions
- [ ] A3: Replace generic template with concrete file/pattern instructions
- [ ] A4: Replace generic template with concrete file/pattern instructions
- [ ] A5: Replace generic template with concrete file/pattern instructions
- [ ] A6: Replace generic template with concrete file/pattern instructions
- [ ] A7: Replace generic template with concrete file/pattern instructions
- [ ] A8: Replace generic template with concrete file/pattern instructions
- [ ] A9: Replace generic template with concrete file/pattern instructions
- [ ] A10: Replace generic template with concrete file/pattern instructions
- [ ] A11: Replace generic template with concrete file/pattern instructions
- [ ] A12: Replace generic template with concrete file/pattern instructions
- [ ] A13: Replace generic template with concrete file/pattern instructions
- [ ] A99: Replace generic template with concrete file/pattern instructions
- [ ] Verify: `grep -c "domain-specific patterns" promptsets/v4/prompts/PROMPT_A*.md` → all 0

#### Pass 3: Phase C+W Extraction Procedures (25 prompts)

**Batch 3A** (C1-C9 core) `CX GPT-5.4`
- [ ] C1: Name uvicorn/gunicorn/click/typer/Dockerfile CMD/console_scripts patterns
- [ ] C2: Name .publish()/.emit()/.subscribe()/@event_handler + retry/DLQ config
- [ ] C3: Rewrite extraction procedure
- [ ] C4: Rewrite extraction procedure
- [ ] C5: Rewrite extraction procedure
- [ ] C6: Rewrite extraction procedure
- [ ] C7: Name @app.get()/@router.get() + response_model + Depends() + HTTPException
- [ ] C8: Name threading.Thread/asyncio.create_task/random/uuid/datetime.now
- [ ] C9: Rewrite extraction procedure

**Batch 3B** (C10-C17 extended) `CX GPT-5.4-mini`
- [ ] C10: Fix scope triplication
- [ ] C11: Fix scope triplication
- [ ] C12: Fix scope triplication
- [ ] C13: Already good — skip or minor touch-up
- [ ] C14: Already gold standard — skip
- [ ] C15: Already gold standard — skip
- [ ] C16: Fix scope triplication
- [ ] C17: Fix scope triplication

**Batch 3C** (W1-W5 workflows) `CX GPT-5.4`
- [ ] W1: bash scripts, Makefiles, GH Actions, tmux YAMLs, runbook docs
- [ ] W2: Rewrite extraction procedure
- [ ] W3: Rewrite extraction procedure
- [ ] W4: set -euo pipefail, trap ERR, retry decorators, rollback steps
- [ ] W5: Rewrite extraction procedure
- [ ] Verify: `grep -c "domain-specific patterns" promptsets/v4/prompts/PROMPT_C*.md PROMPT_W*.md` → all 0

#### Pass 4: Phase R/B/G/E Extraction Procedures (26 prompts)

**R-phase** (11 prompts) `CX GPT-5.4`
- [ ] R0-R10: Replace 12-step boilerplate with domain-specific synthesis contracts
- [ ] Each must name upstream artifacts to consume, conflict signals, output table format

**B-phase** (5 prompts) `CX GPT-5.4-mini`
- [ ] B0-B3, B9: Add FastAPI Depends(), .claude/settings.json permissions, AGENTS.md, HTTPException(403)

**G-phase** (6 prompts) `CX GPT-5.4-mini`
- [ ] G0-G4, G9: Expand G4 with auth patterns; add env var reads, hardcoded credentials, .gitignore

**E-phase** (8 prompts) `CX GPT-5.4-mini`
- [ ] E0-E6, E9: Add docker compose, make targets, uv run, tmux new-session patterns

---

### TIER 3 — Schema Depth Upgrades

#### Pass 5: Item-Level Schema Expansion (20 prompts)

**Top 5 — Novel schema design** `CC:O (Opus)` ← OPUS TASKS
- [x] **C2 Eventbus**: Add `event_name`, `retry_policy` (none|fixed|exponential), `dlq_target`, `ordering_guarantee` (none|fifo|key_based), `payload_schema_ref`, `is_async`
- [x] **C7 API**: Add `http_method` enum, `path_template`, `request_body_schema`, `response_codes[]`, `auth_required`, `rate_limited`
- [x] **A5 Hooks**: Add `hook_type` enum (git_hook|claude_hook|fastapi_event|github_action|signal_handler), `trigger`, `handler_path`, `is_blocking`
- [x] **C1 Entrypoints**: Add `entrypoint_type` enum (uvicorn|gunicorn|cli|script|docker_cmd|console_script), `port`, `startup_args[]`, `health_check_path`
- [x] **C8 Risk Scans**: Add `risk_type` enum per output, `severity` enum with thresholds, `affected_symbol`, `mitigation_present`

**Items 6-20 — Template-based expansion** `CX GPT-5.4`
- [ ] W1 Workflows: `trigger_type` enum, `step_count`, `rollback_supported`, `sla_seconds`
- [ ] W4 Failure Modes: `failure_mode_type` enum, `recovery_strategy`, `is_documented`
- [ ] G4 Security: `secret_type` enum, `exposure_risk`
- [ ] B3 Bypass: `bypass_type` enum, `severity`, `mitigating_controls`
- [ ] E2 Env Loading: `env_var_name`, `default_value`, `required`, `consumer_services`
- [ ] D2: Domain-specific typed fields
- [ ] R7: Domain-specific typed fields
- [ ] T1: Domain-specific typed fields
- [ ] X1: Domain-specific typed fields
- [ ] C6: Domain-specific typed fields
- [ ] H7: Domain-specific typed fields
- [ ] M1: Domain-specific typed fields
- [ ] R5: Domain-specific typed fields
- [ ] S7: Domain-specific typed fields
- [ ] A13: Domain-specific typed fields

---

### TIER 4 — New Prompt Creation (8 prompts)

**Opus-assigned (novel security domain)** `CC:O (Opus)` ← OPUS TASKS
- [x] **G5_AUTH_FLOW_SURFACE**: Create prompt (G-phase, CE lane, `AUTH_FLOW_SURFACE.json`)
  - Targets: Depends(get_current_user), JWT decode, OAuth2PasswordBearer, HTTPBearer, permission checks
  - All 9 required sections
- [x] **R11_SECURITY_RISK_SYNTHESIS**: Create prompt (R-phase, BULK_DOCS_GENERAL lane, `SECURITY_RISK_SYNTHESIS.md`)
  - Aggregates G4+G5+B1-B3 into security truth memo
  - All 9 required sections

**Codex-assigned (template-based)** `CX GPT-5.4`
- [ ] C18_OBSERVABILITY_SURFACE: logging.getLogger, structlog, Counter/Gauge/Histogram, /health, /metrics, OpenTelemetry
- [ ] C19_ERROR_HANDLING_PATTERNS: try/except, bare except:, reraise vs swallow, unhandled IO
- [ ] G6_DEPENDENCY_HEALTH_SURFACE: pyproject.toml deps, requirements*.txt, uv.lock, unpinned deps
- [ ] C20_STATE_MANAGEMENT_SURFACE: self.xxx mutations, module globals, SQLite writes, Redis set/get
- [ ] C21_PERFORMANCE_SURFACE: time.sleep in async, N+1 queries, sync requests in async def, unbounded loops
- [ ] G7_TECHNICAL_DEBT_REGISTER: TODO/FIXME/HACK/XXX, deprecated decorators, CHANGE_ME, large commented blocks

**Registration for ALL new prompts**:
- [x] Add G5 to G-phase in `promptset.yaml`
- [ ] Add G6, G7 to G-phase in `promptset.yaml`
- [x] Add R11 to R-phase in `promptset.yaml`
- [ ] Add C18, C19, C20, C21 to C-phase in `promptset.yaml`
- [x] Register G5 + R11 artifacts in `artifacts.yaml`
- [ ] Register C18-C21, G6, G7 artifacts in `artifacts.yaml`
- [x] Add G5 + R11 model routing in `model_map.yaml`
- [ ] Add C18-C21, G6, G7 model routing in `model_map.yaml`

---

### TIER 5 — Depth Improvements + Verification

#### Pass 7: Partial-Coverage Domain Enhancements (4 prompts) `CX GPT-5.4`
- [ ] C7 API: Add request/response schemas, error codes, auth deps (if not done in Pass 5)
- [ ] M1 DB Schema: Add column types, NOT NULL, FKs, indexes, constraints
- [ ] C2 Events: Add retry policy, DLQ, ordering, payload schema (if not done in Pass 5)
- [ ] W1 Workflows: Add duration, recovery, rollback, idempotency, trigger (if not done in Pass 5)

#### Pass 8: Verification & Integration Tests `GC Gemini Flash`

**8A — Contract verification** (zero LLM cost)
- [ ] Run `scripts/repo_truth_extractor_promptset_audit_v4.py` on full promptset
- [ ] Add checks: no "domain-specific patterns", no scope duplicates, all new artifacts registered

**8B — Spot-check live extraction**
- [ ] Run A + C1-C8 + G against test fixture
- [ ] Verify: no unauthorized fields, reasonable item counts, real file references, stable IDs

**8C — Cross-phase dependency validation**
- [ ] Build artifact dependency graph from promptset.yaml
- [ ] Verify no broken edges

**8D — Token budget audit**
- [ ] Sum before/after token costs
- [ ] Target 25-35% reduction in A/C/H phases

---

## Execution Order & Dependencies

```
A0 (conflicts) ──┐
                  ├──→ A1-A7 (safety gates, parallel) ──→ A-Verify
                  │
Pass 1 (dedup) ──→ Pass 2 (A procs) ──┐
                  → Pass 3 (C+W procs) ├──→ Pass 5 (schemas) ──→ Pass 7 (depth)
                  → Pass 4 (R/B/G/E)  ┘    Pass 6 (new prompts) ──→ Pass 8 (verify)

INDEPENDENT NOW (no upstream deps):
  - Pass 5 top 5 (Opus schema expansion) ← can start immediately
  - Pass 6 G5 + R11 (Opus new prompts)   ← can start immediately
```

---

## Cost & Effort Summary

| Pass | Tier | Tool | Model | Effort |
|------|------|------|-------|--------|
| A0 | Pre | Codex | GPT-5.4-mini | 0.5 sess |
| A1-A7 | Pre | Codex | GPT-5.4 / mini | 1 sess |
| 1 | T1 | Codex | GPT-5.4-mini | 1 sess |
| 2 | T2 | Codex | GPT-5.4 | 1.5 sess |
| 3 | T2 | Codex | GPT-5.4 / mini | 2 sess |
| 4 | T2 | Codex | GPT-5.4 / mini | 1.5 sess |
| 5 | T3 | Claude + Codex | Opus (5) + GPT-5.4 (15) | 2 sess |
| 6 | T4 | Claude + Codex | Opus (2) + GPT-5.4 (6) | 2 sess |
| 7 | T5 | Codex | GPT-5.4 | 1 sess |
| 8 | T5 | Gemini CLI | Flash | 0.5 sess |
| **Total** | | | | **~13 sess** |

**Minimum viable before live run**: A0 + A1-A7 + Pass 1 + Pass 2 + Pass 3 (~7 sessions)
**Full optimization**: All passes (~13 sessions)
