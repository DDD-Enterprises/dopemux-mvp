---
id: TP-DMX-START-AUDIT-CRIT-FIX-001
title: Fix CRIT bugs from dopemux start audit 2026-06-06
type: bugfix
owner: '@hu3mann'
author: claude-sonnet-4-6
date: '2026-06-06'
branch: claude/modest-cartwright-340c04
status: draft
---
# Task Packet: TP-DMX-START-AUDIT-CRIT-FIX-001 · CLI · Start Audit CRIT Bug Fixes

════════════════════════════════════════════════════════════

## Objective

Fix four confirmed CRIT bugs in `src/dopemux/cli.py` (dangerous-mode shadowing, two
unguarded post-launch crashes) and repair five test-mock failures in the new
`tests/integration/test_start_crit_gaps.py` contract test file.

────────────────────────────────────────────────────────────

## Evidence Base

All bugs confirmed by:
- Direct code inspection (Stage 1 read-only audit, 2026-06-06)
- PAL gpt-5.2 codereview (CONFIRMED CRIT for all four)
- RED-phase pytest runs: all 5 bug tests fail at the exact expected lines

| Bug ID   | Location          | Failure mode                                              |
|----------|-------------------|-----------------------------------------------------------|
| GAP-C1   | cli.py:5914       | Duplicate `_activate_dangerous_mode` — no-confirm version shadows interactive |
| GAP-C2   | cli.py:2518       | `save_instance_state_sync()` — no try/except, crashes post-launch |
| NEW-C4a  | cli.py:2472       | `claude_hooks.start_monitoring()` — no try/except, crashes post-launch |
| NEW-C4b  | cli.py:2475       | `AttentionMonitor.start_monitoring()` — no try/except, crashes post-launch |

────────────────────────────────────────────────────────────

## Scope

IN:
* Remove duplicate `_activate_dangerous_mode()` at cli.py:5914 (and the paired
  duplicate `_deactivate_dangerous_mode()` at cli.py:5928 and
  `_check_dangerous_mode_expiry()` at cli.py:5944 — same shadowing root cause)
* Add `try/except Exception` guard around `save_instance_state_sync()` at cli.py:2518
* Add `try/except Exception` guard around `claude_hooks.start_monitoring()` at cli.py:2472
* Add `try/except Exception` guard around `attention_monitor.start_monitoring()` at cli.py:2475
* Fix five test-mock failures in `tests/integration/test_start_crit_gaps.py`:
  - GAP-C3 test: fix `httpx` mock (imported locally in cli.py — use module-level patch)
  - GAP-H1 test: fix RoutingConfig mock path + LaunchdServiceManager mock path
  - GAP-H3 happy path test: fix `start_simple_proxy` mock path and env var assertion
  - GAP-H4 tests (×2): fix RoutingConfig mock path and altp/litellm interaction

OUT:
* GAP-C3 production fix (change `"0.0.0.0"` to `"127.0.0.1"` in `--alt-routing` path)
  — requires separate security decision and deprecated-flag review; deferred
* GAP-H1–H7 new HIGH-gap tests that need further mock investigation
* Any cli.py refactoring beyond the minimal guard additions
* Any other file not listed under "Files to Touch"

────────────────────────────────────────────────────────────

## Invariants (Must Remain True)

1. `_activate_dangerous_mode()` must call `click.confirm()` twice and not set any
   env var if the user declines either prompt.
2. `dopemux start` must exit cleanly (exit_code 0) even if ConPort is unreachable
   after Claude is launched.
3. `dopemux start` must exit cleanly (exit_code 0) even if `claude_hooks.start_monitoring()`
   or `AttentionMonitor.start_monitoring()` raises.
4. The exception handlers added for C2/C4 must log a WARNING (not silently pass)
   so operators can diagnose the failure.
5. All existing tests in `tests/integration/test_start_command.py` must continue
   to pass after the changes.
6. The dangerous-mode env vars set by the surviving `_activate_dangerous_mode()`
   at line 3875 must be identical in name and value to what the current passing
   test `test_dangerous_mode_sets_env_vars_after_both_confirmations` asserts.
7. No new module-level imports introduced — keep changes minimal.

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Plan (Numbered)

### Phase A — Production bug fixes (src/dopemux/cli.py)

1. **GAP-C1**: Delete the duplicate function block starting at line 5914:
   - `_activate_dangerous_mode() -> None:` (lines 5914–5925)
   - `_deactivate_dangerous_mode() -> None:` (lines 5928–5941)
   - `_check_dangerous_mode_expiry() -> bool:` (lines 5944–EOF of that block)
   Remove only those three duplicate definitions. The authoritative versions remain
   at lines 3875, 3948, and 5944 (their first occurrence). Verify call sites still
   resolve to the interactive version after deletion.

2. **GAP-C2**: Wrap `save_instance_state_sync(...)` at line 2518 in a try/except:
   ```python
   try:
       save_instance_state_sync(
           state,
           workspace_id=str(project_path.resolve()),
           conport_port=3004,
       )
       console.logger.info("[text.dim]✅ Instance state saved for crash recovery[/text.dim]")
   except Exception as exc:
       logger.warning("Instance state save failed (ConPort may be down): %s", exc)
   ```

3. **NEW-C4**: Wrap monitoring hook calls at lines 2472 and 2475 in try/except:
   ```python
   try:
       claude_hooks.start_monitoring(str(project_path))
   except Exception as exc:
       logger.warning("claude_hooks.start_monitoring failed (best-effort): %s", exc)

   try:
       attention_monitor = AttentionMonitor(project_path)
       attention_monitor.start_monitoring()
   except Exception as exc:
       logger.warning("AttentionMonitor.start_monitoring failed (best-effort): %s", exc)
   ```

### Phase B — Test mock fixes (tests/integration/test_start_crit_gaps.py)

4. **GAP-C3 test**: Fix the httpx mock — `httpx` is imported locally inside
   `_alt_routing_setup()`, not at cli.py module level. Patch it at
   `"dopemux.cli.httpx"` only after verifying the local import path, or mock
   `subprocess.Popen` at `"dopemux.cli.subprocess.Popen"`.

5. **GAP-H1 test**: Fix the RoutingConfig mock — currently patching
   `dopemux.routing_config.RoutingConfig.load_default` but the cli.py path imports
   via `from .routing_config import RoutingConfig` and calls `RoutingConfig.load_default()`.
   Patch `dopemux.cli.RoutingConfig` (the name in cli.py's namespace).
   Fix LaunchdServiceManager similarly: patch `dopemux.cli.LaunchdServiceManager`
   or `dopemux.launchd_services.LaunchdServiceManager.get_instance`.

6. **GAP-H3 test**: Fix `start_simple_proxy` mock — patch `dopemux.cli.start_simple_proxy`.
   Verify the env var actually set in the grok path and update assertion accordingly.

7. **GAP-H4 tests**: Fix RoutingConfig mock path (same as step 5). Verify the
   `UnboundLocalError: config_data` at cli.py:1328 — this is a pre-existing bug
   in the `--altp` subscription-mode path where `config_data` is referenced before
   assignment. Document it in the test; do NOT fix the production bug in this TP
   (out of scope).

### Phase C — Verification

8. Run the RED tests to confirm they now PASS:
   ```
   python -m pytest tests/integration/test_start_crit_gaps.py \
     -k "decline or crash or graceful" --tb=short -v
   ```

9. Run the full existing start-command suite to confirm no regressions:
   ```
   python -m pytest tests/integration/test_start_command.py --tb=short -v
   ```

10. Run the full new gap test file:
    ```
    python -m pytest tests/integration/test_start_crit_gaps.py --tb=short -v
    ```

────────────────────────────────────────────────────────────

## Files to Touch

* `src/dopemux/cli.py` — delete 3 duplicate function blocks; add 3 try/except guards
* `tests/integration/test_start_crit_gaps.py` — fix 5 test mock paths/assertions

If additional files are needed, stop and request approval.

────────────────────────────────────────────────────────────

## Exact Commands to Run

```
# Verification (run in this order)
python -m pytest tests/integration/test_start_crit_gaps.py -k "decline or crash or graceful" --tb=short -v
python -m pytest tests/integration/test_start_command.py --tb=short -v
python -m pytest tests/integration/test_start_crit_gaps.py --tb=short -v
python -m pytest tests/ -x --ignore=tests/e2e -q   # smoke pass
```

────────────────────────────────────────────────────────────

## Output Capture Rules (Verbatim)

Implementer must return:
* `git diff --stat`
* `git diff`
* Output of all four pytest commands above, verbatim with exit codes
* Confirmation that `_activate_dangerous_mode` is defined exactly once after the fix

────────────────────────────────────────────────────────────

## Rollback

```bash
git diff src/dopemux/cli.py tests/integration/test_start_crit_gaps.py
git restore src/dopemux/cli.py tests/integration/test_start_crit_gaps.py
```

Both files are uncommitted. Restore is instant and non-destructive.

────────────────────────────────────────────────────────────

## Stop Conditions

Stop and report a blocker when:
* Deleting the line-5914 block would remove the ONLY occurrence of any of the three
  functions (verify with grep before deleting)
* Any invariant fails after the change
* The existing `test_start_command.py` tests regress
* The diff touches files outside the allowlist

────────────────────────────────────────────────────────────

## Embedded Audit

Required: yes — this packet touches a security-sensitive surface (`_activate_dangerous_mode`).

Auditor: PAL codereview (continuation_id from Stage 1 review available) OR
         inline self-review against the 7 invariants above.

Minimum: verify each invariant holds against the actual diff before declaring done.

────────────────────────────────────────────────────────────

## Model Routing

- cheap_read: VERIFY_WITH_VENDOR_DOCS (haiku / sonnet-low)
- investigation: VERIFY_WITH_VENDOR_DOCS
- planner_strong: claude-sonnet-4-6 (this session — advisory governance only)
- implementer_standard: claude-sonnet-4-6 (this session)
- judge_strong: VERIFY_WITH_VENDOR_DOCS
- self_audit: PAL codereview / advisor()

Escalate to strong model if:
- The duplicate-deletion touches more lines than the three named function blocks
- Any test regression cannot be explained
- A new security surface is discovered in the dangerous-mode code

────────────────────────────────────────────────────────────

## PR Steward Readiness

Not applicable yet — no commit or PR opened. File this section after implementation.
