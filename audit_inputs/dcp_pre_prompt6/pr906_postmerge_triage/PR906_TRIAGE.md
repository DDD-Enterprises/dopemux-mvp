# PR #906 Post-Merge Review-Thread Triage — DCP 0005 Lane Engine

**Mode:** read-only implementation-evidence audit · **Date:** 2026-06-16
**Repo:** `DDD-Enterprises/dopemux-mvp` · **Auditor:** Claude Code (Opus 4.8)

## Verdict

```
PR906_TRIAGE_STATUS: BLOCKED
PROMPT6_READY: NO
NEXT_ACTION: create follow-up fix packet (2 small fail-closed fixes + tests)
             OR explicitly defer to 0007 with documented rationale; then bundle Prompt 6
```

Two unresolved, non-outdated, safety-relevant review threads remain on the merged
PR #906. Per the supervisor's own readiness gate (any unresolved non-outdated safety
thread ⇒ `prompt6_ready=false`), Prompt 6 cannot proceed until they are fixed or
explicitly classified/deferred.

## State (live GitHub + local main, outranks the stale bundle)

| Item | Value |
|------|-------|
| Repo root | `/Users/hue/code/dopemux-mvp` (worktree `trusting-williamson-6e4283`, branch == main content) |
| Current main SHA | `556ffff1b` (= `origin/main`, clean tree) |
| PR #906 state | MERGED 2026-06-17T01:30:37Z |
| PR #906 head SHA | `5b1b03a1002b` |
| PR #906 merge SHA | `02fa9b30ac0a` |
| PR #906 size | 5 files, +1752/-0 |
| #908 (0006 packet) | MERGED (docs) — but 0006 is now **implemented** on main |
| #909 (0007 packet) | MERGED (docs) — 0007 **not implemented** |

**Freshness correction vs. supervisor bundle:** main advanced **5 commits past** the
#906 merge. `02fa9b30a` (#906) is followed by `b460047eb` (**implements 0006 classifier
provenance hardening** — not just a docs packet) + 4 CLI/provenance hardening fixes.
`lane_engine.py` itself is **unchanged since the #906 merge**, so the two findings below
were not touched by the post-merge work.

## Thread classification (13 total)

| # | Path:Line | Resolved | Outdated | Class | Title |
|---|-----------|----------|----------|-------|-------|
| 0 | lane_engine.py | ✓ | ✓ | AUTO_APPLIED_OUTDATED | Use RouteDecision.is_runnable() for executability |
| 1 | lane_engine.py | ✓ | ✓ | AUTO_APPLIED_OUTDATED | Normalize input enums before lane matching |
| 2 | lane_engine.py:354 | ✓ | ✗ | AUTO_APPLIED | Strip mutating actions from non-runnable lanes |
| 3 | lane_engine.py | ✓ | ✓ | AUTO_APPLIED_OUTDATED | Route repo-changing inputs before read-only fallback |
| 4 | lane_engine.py | ✓ | ✓ | AUTO_APPLIED_OUTDATED | Route file-touching inputs out of evidence lane |
| 5 | lane_engine.py | ✓ | ✓ | AUTO_APPLIED_OUTDATED | Keep PR readiness from inheriting mutating requests |
| 6 | lane_engine.py:158 | ✓ | ✗ | AUTO_APPLIED | Fail closed on restored decisions with UNKNOWN fields |
| 7 | lane_engine.py:128 | ✓ | ✗ | AUTO_APPLIED | Block UNKNOWN proof requirements before execution |
| 8 | lane_engine.py:158 | ✓ | ✗ | AUTO_APPLIED | Block routes that carry stop conditions |
| 9 | lane_engine.py:354 | ✓ | ✗ | AUTO_APPLIED | Narrow mutating actions on passive lanes |
| 10 | lane_engine.py:248 | ✓ | ✗ | AUTO_APPLIED | Route public-behavior changes out of evidence |
| **11** | **lane_engine.py:70** | **✗** | **✗** | **MUST_FIX** | **Strip hard-forbidden actions from passive lanes** |
| **12** | **lane_engine.py:128** | **✗** | **✗** | **MUST_FIX** | **Block restored unknown markers before execution** |

## The two blockers

### [11] Strip hard-forbidden actions from passive lanes — STILL_VALID
`_MUTATING_ACTIONS` (lane_engine.py:70-80) omits **7** classifier `_ALWAYS_FORBIDDEN`
tokens: `call_connector`, `execute_dopetask`, `execute_runner`,
`mutate_task_orchestrator`, `run_destructive_command`, `touch_secrets`,
`write_github_state`. A passive *executable* lane runs `_strip_mutating_actions`
(line 352), which does not remove these. A restored `READ_ONLY` decision carrying e.g.
`execute_runner` in `allowed_actions` therefore keeps it on a `READ_ONLY_EVIDENCE` lane.

- **Reachability:** forged/restored `RouteDecision` only. `classify_route` always emits
  these in `forbidden_actions` (routing_classifier.py:440), so the trusted path is safe.
- **Fix:** for `_PASSIVE_LANES`, intersect with `_READ_ONLY_PROOF_SAFE_ACTIONS`
  (fail-closed allowlist) or union `_MUTATING_ACTIONS` with `_ALWAYS_FORBIDDEN`.

### [12] Block restored unknown markers before execution — STILL_VALID
`RouteDecision.unknowns` exists (routing_model.py:234) and round-trips through
`from_dict` (routing_model.py:384). Neither `is_runnable()` (routing_model.py:401-419,
post-0006) nor `_has_unknown_decision_contract` (lane_engine.py:118-129) checks
`decision.unknowns`. A restored decision with all enum fields known + `unknowns=[...]` +
`status=ALLOWED` + `red_lane_state=CLEAR` + valid `authority_class` is `is_runnable()`,
so `LOCAL_CODE_IMPLEMENTATION` becomes executable with mutating `allowed_actions` — even
though the sibling backend policy blocks `unknowns_present`.

- **Reachability:** forged/restored decision only (same threat class as [11]).
- **Fix:** add `bool(decision.unknowns)` to `_has_unknown_decision_contract`.

## Why these matter (and why they are not 0005 bugs)
The lane engine's contract (docstring line 8) is that it **trusts the classifier
decision as authoritative and never re-derives safety**. Under that contract a
*trustworthy* decision is handled correctly. Both findings are only reachable by
deserializing an **untrusted/forged** `RouteDecision` — exactly the "execution-eligibility
must be an unforgeable capability, not a serialized field" threat that **0007** is meant
to close. 0007 is currently **docs-only**. So these are genuine fail-closed
defense-in-depth gaps that become live the moment any execution surface trusts a restored
decision; they are cheap to close now (≈2 small edits + tests) and should not be carried
forward silently.

## Validation (PASS / FAIL / NOT_RUN)
- **PASS** `python -m compileall -q src/dopemux/dcp` (exit 0)
- **PASS** `pytest tests/unit/dcp/test_lane_engine.py tests/unit/dcp/test_routing_classifier.py` (129 passed)
- **NOT_RUN** full DCP suite — out of triage scope; targeted lane/classifier tests suffice and existing tests do **not** cover findings [11]/[12].

## Recommendation
Smallest correct path: a tiny follow-up fix packet against `lane_engine.py` closing both
gaps with reproduction tests (forged-decision fixtures), then assemble the Prompt 6
bundle on the resulting main. If the program prefers to route this to the 0007
implementation instead, classify [11]/[12] as `OUT_OF_SCOPE_FOLLOWUP → 0007` with that
rationale recorded — but do not leave them as bare unresolved threads.
