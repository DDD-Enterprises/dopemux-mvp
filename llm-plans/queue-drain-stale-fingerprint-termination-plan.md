---
id: queue-drain-stale-fingerprint-termination-plan
title: Queue Drain Stale Fingerprint Termination Plan
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-29'
last_review: '2026-03-29'
next_review: '2026-06-27'
prelude: Queue Drain Stale Fingerprint Termination Plan (reference) for dopemux documentation
  and developer workflows.
---
# Plan: Fix Stale Fingerprint Causing Premature Queue-Drain Termination

## Context

PR #354 added stale fingerprint detection to `_create_global_fix_pr()`: if tests already pass
on `main`, return `-2` instead of launching Gemini (correct). But this introduced a regression:
when a fingerprint is stale, the 9 grouped PRs are NOT added to `global_fix_blocked` and fall
through to the normal tactic loop. In dry-run mode (`execute=False`), every PR unconditionally
hits `elif not execute: no_progress_ids.add(pr_id)`. With all 17 PRs in `no_progress_ids` after
pass 1, pass 2's `active_results` is empty → "All PRs processed" → drain exits after 2 of 3
passes. Separately, the stale pre-check (worktree rebuild + 2 pytest runs) repeats on every pass.

---

## Root Cause

**File**: `src/dopemux_pr_merge_specialist/queue_drain.py`

**Bug 1 — Premature termination** (line 2014–2016):
```python
elif not execute:
    # Dry-run: tactic won't change state, skip in future passes
    no_progress_ids.add(pr_id)
```
This catch-all adds every dry-run PR (including those needing APPLY_FIX) to `no_progress_ids`.
`active_results` at line 1882–1892 excludes `no_progress_ids` → pass 2 sees empty list → exits.

**Bug 2 — Repeated stale pre-check** (line 1847 called every pass):
`_handle_global_ci_blockers` has no memory of prior stale results. Each pass rebuilds the
worktree and runs 2 pytest invocations for a fingerprint already confirmed stale.

---

## Critical Files

| File | Lines | Role |
|------|-------|------|
| `src/dopemux_pr_merge_specialist/queue_drain.py` | 1551–1660 | `_handle_global_ci_blockers()` — stale detection |
| `src/dopemux_pr_merge_specialist/queue_drain.py` | 1820–1836 | per-pass state dicts init |
| `src/dopemux_pr_merge_specialist/queue_drain.py` | 1847–1858 | CI blocker check call site |
| `src/dopemux_pr_merge_specialist/queue_drain.py` | 1882–1892 | `active_results` filter |
| `src/dopemux_pr_merge_specialist/queue_drain.py` | 2012–2016 | dry-run `no_progress_ids` catch-all |

---

## Implementation Plan

### Fix 1 — Restrict the dry-run `no_progress_ids` catch-all (line 2012–2016)

The `elif not execute:` block at line 2014 fires for APPLY_FIX, MERGE, APPROVE, READY in
dry-run — all actionable tactics that WOULD change state if executed. Only terminal tactics
(DEFER, REQUEST_CHANGES, REQUEST_REVIEW) should reach `no_progress_ids`, since they won't
advance regardless of execute mode.

**Change** (line 2012–2016):
```python
# BEFORE:
elif tactic in ("DEFER", "REQUEST_CHANGES", "REQUEST_REVIEW"):
    no_progress_ids.add(pr_id)
elif not execute:
    # Dry-run: tactic won't change state, skip in future passes
    no_progress_ids.add(pr_id)

# AFTER:
elif tactic in ("DEFER", "REQUEST_CHANGES", "REQUEST_REVIEW"):
    no_progress_ids.add(pr_id)
# NOTE: In dry-run, actionable tactics (APPLY_FIX/MERGE/APPROVE/READY) are intentionally
# NOT added to no_progress_ids — they remain eligible for subsequent passes.
```

Effect: In dry-run mode, PRs needing APPLY_FIX/MERGE cycle through all 3 passes (showing
the same tactic each pass). Slightly verbose but correct — drain no longer exits prematurely.

### Fix 2 — Cache stale fingerprints across passes (lines 1831–1836 + 1551 + 1847)

**Step 2a** — Add `seen_stale_fingerprints` to per-drain state (line 1836):
```python
global_fix_blocked: Dict[int, int] = {}
seen_stale_fingerprints: set = set()   # new; persists across passes
```

**Step 2b** — Thread it through the call site (line 1847–1857):
```python
pass_blocked = _handle_global_ci_blockers(
    results,
    client,
    repo_root,
    seen_stale_fingerprints=seen_stale_fingerprints,   # new kwarg
    logger=lambda level, scope, message: _emit_live_run_event(...),
)
```

**Step 2c** — Update `_handle_global_ci_blockers` signature and body (line 1551–1660):
```python
def _handle_global_ci_blockers(
    results: List[PRResult],
    client: GitHubClient,
    worktree_dir: Path,
    seen_stale_fingerprints: Optional[set] = None,   # new param
    logger: Optional[Callable[[str, str, str], None]] = None,
) -> Dict[int, int]:
```

Inside the loop where `-2` is returned (line 1647–1652):
```python
elif new_pr_number == -2:
    _log(f"Remote CI fingerprint {fingerprint} is stale ...", "INFO")
    if seen_stale_fingerprints is not None:
        seen_stale_fingerprints.add(fingerprint)   # cache it
```

At the top of the per-fingerprint processing block (before calling `_create_global_fix_pr`),
skip already-stale fingerprints:
```python
if seen_stale_fingerprints and fingerprint in seen_stale_fingerprints:
    _log(f"Fingerprint {fingerprint[:8]} previously confirmed stale; skipping.", "INFO")
    continue
```

Effect: Pass 2 onward skips the worktree rebuild + pytest runs for already-stale fingerprints.
Saves ~30s per pass per stale fingerprint group.

---

## Verification

1. **Regression check** (dry-run, stale fingerprint present):
   ```bash
   dopemux pr-merge queue-drain --max-passes 3
   ```
   Expected: all 3 passes complete; no "All PRs processed" exit after pass 2; stale pre-check
   runs only once (pass 1) with "previously confirmed stale; skipping" on passes 2–3.

2. **Execute mode sanity** (ensure stale PRs still get APPLY_FIX):
   ```bash
   dopemux pr-merge queue-drain --execute --max-prs 1 --only <stale_pr_id>
   ```
   Expected: APPLY_FIX runs (rebase onto main picks up fix), validation passes.

3. **Unit tests** — add to `tests/pr_merge_specialist/test_queue_drain_integration.py`:
   - `test_stale_fingerprint_does_not_terminate_dry_run_early`: mock `_handle_global_ci_blockers`
     returning empty dict (stale) and verify drain completes all 3 passes with `execute=False`.
   - `test_stale_fingerprint_cached_between_passes`: mock `_create_global_fix_pr` returning -2
     and verify the pre-check is called only once across 3 passes.
