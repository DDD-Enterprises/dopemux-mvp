# TP-DCP-MCP-RO-0010 Auditor Report

**Auditor:** Claude Code CLI (Opus), independent of the Claude Sonnet subagent that implemented the code.
**Verdict:** PASS_WITH_RISKS (all risks non-blocking).

## Method
- Read `registry_v2.py`, `resolver_core.py`, `capability.py`, `registry_v2.schema.json`, and the new tests in full.
- Verified contract fidelity against ADR-DCP-MCP-RO-0009 (9 families, forbidden `task-orchestrator`, policy table, `PRIMARY_CHECKOUT_ONLY`, capability separation, opaque block reasons).
- **Executed** `_derive_roots` on this actual linked worktree → `project_root=[LOCAL_PATH_REDACTED]`, `worktree_root=workspace` (correct against genuine `.git` metadata).
- Parsed all 7 fixtures independently; confirmed each invalid case is rejected and the duplicate case now fails closed (`[]`).
- Purity scan of the three new modules (clean) and secret scan of all new files (zero secrets).
- `advisor()` second opinion (PAL external codereview NOT_RUN — OpenAI 401 / Google 429 provider outage).

## Findings
- **F-0010-LOW-1 (RESOLVED):** duplicate `target_id` hardened from keep-first to fail-closed (ambiguity blocks).
- **F-0010-INFO-1 (ACCEPTED_RISK):** `project_root` trust deferred to 0011/0012 (per-service identity re-validation).
- **F-0010-INFO-2 (ACCEPTED_RISK):** submodule/symlinked-`.git` derivation reasoned (fail-closed), not live-tested.
- **F-0010-LOW-2 (ACCEPTED_RISK):** PAL external codereview NOT_RUN (provider outage); mitigated by Opus audit + advisor.

## Fixes applied (this reviewer)
1. Duplicate `target_id` fails closed (drop first + poison id).
2. Stray v1 `projects` key alongside v2 `targets` warns.
3. Discard `validate_workspace` raw error explicitly (`_err` → `_`).

## Result
Deterministic, fail-closed, faithful to ADR-DCP-MCP-RO-0009. No runtime/network/backend code introduced. See `AUDIT.md` for the full narrative and `PROOF.json` for machine-readable validation.
