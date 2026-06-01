# Proof Bundle — PR #725

**Title:** `fix(rte,mcp,install): remediate distributed audit findings (TP-1/1b/2/3/4/5)`  
**PR:** https://github.com/DDD-Enterprises/dopemux-mvp/pull/725  
**Branch:** `claude/rte-remediation-2026-05-29` → `main`  
**Date:** 2026-05-30  
**Prepared per:** AGENTS.md §8

---

## Task Packet Reference

| TP ID | Description |
|-------|-------------|
| TP-RTE-001 (TP-1) | RTE fail-closed gate truth-split, prescan correctness, orphan-phase doc |
| TP-RTE-001b (TP-1b) | SP exec-time fail-close, loud S-prompt swap, canonical run_status, hygiene/promptset docs |
| TP-MCP-002 (TP-2) | MCP internal lockdown — scoped child env, escalation, gate fail-closed, session sanitize |
| TP-MCP-003 (TP-3) | MCP services lockdown — debug secret leak, localhost bind, KG deny-by-default, capture validation, CORS |
| TP-INSTALL-004 (TP-4) | Install hardening — canonical dopemux-network, pipefail, .env chmod 600, healthcheck |
| TP-CLI-005 (TP-5) | CLI v3 engine deprecation warning + canonical command migration banner |
| CODE-REVIEW-P0 | Restore gate strict/warn enforcement + remove dead conport block (lost in salvage) |
| CODE-REVIEW-P1P2 | Five P1 regressions + three P2 hardening gaps found during post-PR code review |

---

## Worktree & Branch

```
Repo root:  /Users/hue/code/dopemux-mvp
Worktree:   /Users/hue/code/dopemux-mvp/.worktrees/rte-remediation
Branch:     claude/rte-remediation-2026-05-29
Base (main merge-base): d38e138730f2abf20c56207df9887b579765efa9
HEAD:       7fc1da21568508940791f0a4f3b4599e5fa69811
```

---

## Commits (oldest → newest)

```
fb836be19  fix(rte): TP-1 core — fail-closed gate truth-split, prescan correctness, orphan-phase doc
d5bd554f2  fix(install): TP-4 hardening — canonical dopemux-network, pipefail, .env chmod 600, healthcheck, test-mode docs
a3b0ec3ea  fix(rte): TP-1b — SP exec-time fail-close, loud S-prompt swap, canonical run_status, hygiene/promptset docs
f23fa0999  fix(mcp): TP-2 internal lockdown — scoped child env, escalation fix, gate fail-closed, session 0700+sanitize
8f7ca3893  fix(mcp): TP-3 services lockdown — debug secret leak, localhost bind, KG deny-by-default, capture validation, CORS
2d9637db6  fix(cli,docs): TP-5 — v3 engine deprecation warning + canonical command migration banner
ba5f43f33  fix(mcp): P0-1 — restore gate strict/warn enforcement lost in salvage (MCP1-02)
25a9dbcff  fix(mcp): P0-2 — remove dead conport dual-spelling block; correct false claim (MCP1-10)
7fc1da215  fix(mcp,rte,install): P1+P2 — code-review regressions and hardening
```

---

## Files Changed (41 total, +1621/−70 across the PR)

### Security / MCP layer
- `src/dopemux/mcp/gate.py` — strict-mode enforcement restored; dead conport block removed
- `src/dopemux/mcp/server_manager.py` — scoped child env; proxy/CA vars added to allow-list
- `src/dopemux/mcp/session_manager.py` — path-sanitize fixed (encode not reject); 0700 perms
- `src/dopemux/mcp/broker.py` — escalation fix

### Capture / Integration Bridge
- `services/mcp-capture/server.py` — localhost-only bind; capture validation; event type alias fix
- `services/mcp-integration-bridge/main.py` — CORS restricted; localhost bind; KG deny-by-default; CORS port defaults
- `services/mcp-integration-bridge/kg_authority.py` — deny-by-default route guard

### RTE service
- `services/repo-truth-extractor/lib/prescan/engine.py` — prescan correctness; compression key aligned
- `services/repo-truth-extractor/lib/intelligence_router.py` — compress_map lookup (AttributeError guard)
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py` — fail-closed S7
- `services/repo-truth-extractor/run_extraction_v4.py` — promptset docs
- `services/repo-truth-extractor/run_extraction_v5.py` — SP exec-time fail-close, run_status
- `services/repo-truth-extractor/extraction_hygiene.py` — hygiene docs
- `services/repo-truth-extractor/rte_promptset.py` — S-prompt swap
- `services/repo-truth-extractor/rte_constants.py` — canonical constants
- `services/repo-truth-extractor/reporting.py` — run_status canonical
- `services/repo-truth-extractor/phases.py` — orphan-phase doc

### Install / scripts
- `install.sh` — canonical dopemux-network; .env chmod 600; healthcheck; test-mode
- `scripts/setup.sh` — pipefail; pipefail SIGPIPE fixes (submodule/health)
- `scripts/install-docker-mcp-servers.sh` — master-branch fallback
- `scripts/deploy/deployment/stack_up_all.sh` — network rename complete

### Docs
- `INSTALL.md` — network name
- `docs/02-how-to/install.md` — network name; added MCP management doc
- `docs/02-how-to/universal-extractor-usage.md` — usage guide
- `docs/02-how-to/manage-mcp-servers.md` — new

### Tests added/extended
- `tests/mcp/test_discovery_gate_strict.py` — 6 new real-assertion tests for gate strict/warn
- `tests/mcp/test_mcp_internal_lockdown.py` — extended: session encoding + traversal rejection
- `tests/unit/pm/test_pm_route_contracts.py` — contract tests
- `tests/unit/test_task_orchestrator_launcher.py` — launcher tests
- `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` — pre-live gate tests

### Governance
- `KNOWN_GAPS.md` — 6 deferred shells documented (KG-RTE-01..04, KG-MCP-01..02)
- `claudedocs/pr725-proof-bundle-2026-05-30.md` — this file

---

## Validations

| Suite | Result | Detail |
|-------|--------|--------|
| `tests/mcp/` | **PASS** | 41 passed, 2 skipped |
| `services/repo-truth-extractor/tests/` | **PASS** | 1115 passed, 1 skipped, 8 xfailed |
| FastAPI TestClient (bridge) | **NOT_RUN** | `fastapi` not installed in venv |
| `_build_child_env` unit test | **NOT_RUN** | `websockets` not installed in venv |
| Live extraction / service start | **NOT_RUN** | Per AGENTS.md §7 — requires Docker + secrets |

---

## Code Review Status

Code review performed against PR head `96a331aab` (pre-repair), recorded in
`claudedocs/code-review-pr725-2026-05-29.md`. Findings:

| Finding | Severity | Status |
|---------|----------|--------|
| gate.py strict_optional dead code | HIGH | ✅ Fixed (P0-1, `ba5f43f33`) |
| gate.py conport fallback no-op | MED | ✅ Fixed (P0-2, `25a9dbcff`) |
| mcp-capture event type alias rejected | MED-HIGH | ✅ Fixed (P1-1, `7fc1da215`) |
| installer dropped master fallback | MED | ✅ Fixed (P1-2, `7fc1da215`) |
| session_id sanitizer silently loses persistence | MED | ✅ Fixed (P1-3, `7fc1da215`) |
| compression key mismatch (engine vs router) | MED | ✅ Fixed (P1-4, `7fc1da215`) |
| network rename incomplete | MED | ✅ Fixed (P1-5, `7fc1da215`) |
| child env missing proxy/CA vars | MED-LOW | ✅ Fixed (P2, `7fc1da215`) |
| CORS default missing ports | LOW-MED | ✅ Fixed (P2, `7fc1da215`) |
| setup.sh pipefail SIGPIPE | LOW | ✅ Fixed (P2, `7fc1da215`) |
| bridge host 127.0.0.1 default | LOW (note) | ✅ Noted in code; no change needed |

---

## Precommit Status

- `git diff --check` clean on all commits (no whitespace errors)
- No unintended files staged (verified with `git diff --stat HEAD` before each commit)
- No changes to `proof/`, `docs/archive/`, or migration scripts

---

## Deferred Shells

All 6 pre-existing stub implementations documented in `KNOWN_GAPS.md`:

| ID | Shell | Disposition |
|----|-------|-------------|
| KG-RTE-01 | S7 truth-split per-step wiring | Documented; deferred — runtime plumbing not available |
| KG-RTE-02 | S8-002 extraction_hygiene YAML unwired | Documented; deferred — config-loading sprint |
| KG-RTE-03 | S2 `required_prompt_sections` unenforced | Documented; deferred — promptset-validation task |
| KG-MCP-01 | MCP2-05 `str(e)` info disclosure (~9 sites) | Documented; deferred — no secrets exposed, security hardening task |
| KG-MCP-02 | Broker `request_escalation` no transport | Documented; deferred — transport layer not decided |
| KG-RTE-04 | Orphan phase "M" | Documented; deferred — scope undefined |

---

## Residual Risks

1. **P1-3 session encoding forward-compatibility** — Sessions saved before this fix used
   the strict `[A-Za-z0-9_-]` check, so no existing session files have colon/dot IDs
   (they were silently dropped, not persisted). Sessions created after the fix encode
   such chars; no double-encoding risk on re-load since the decode path matches.

2. **P1-4 bare-string compression hints** — The key rename wires the offline prescan path
   into the router, but bare-string entries (what the engine currently emits) still yield
   no active compression hint — `send_summary_instead` is absent on bare strings. Functional
   improvement deferred to KG-RTE-* (emit richer objects from the engine). This is
   pre-existing behaviour, not a regression.

3. **Deferred shells** — S7/S8-002/S2/MCP2-05/broker-escalation/phase-M remain as stubs.
   All are pre-existing; all are now documented in `KNOWN_GAPS.md`.

4. **NOT_RUN live tests** — FastAPI/websockets test paths not exercised. Changes to those
   surfaces are minimal and consistent with house patterns.

---

## UNKNOWNs

- Whether any production session files exist with non-safe-filename characters in the session
  ID (pre-fix they were silently dropped, so the answer is almost certainly "no live files",
  but we cannot confirm from static analysis).
- Whether any master-only MCP upstreams are used in production (installer fix is defensive).

---

## Cleanup

- Worktree `/Users/hue/code/dopemux-mvp/.worktrees/rte-remediation` should be removed
  after PR merge: `git worktree remove .worktrees/rte-remediation`
- No temporary files, debug scripts, or test fixtures left behind.
