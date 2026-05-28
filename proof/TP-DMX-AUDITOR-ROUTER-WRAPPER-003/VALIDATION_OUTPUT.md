# Validation Output

Status: `PASS_WITH_BLOCKERS`

## Objective

Add `scripts/auditor-preflight` as the missing wrapper for:

```bash
python -m tools.auditor_router.preflight "$@"
```

## PASS

- `pwd` exited 0: `/Users/hue/.codex/worktrees/693f/dopemux-mvp`.
- `git status --short --branch` exited 0 before proof creation on branch `codex/tp-dmx-auditor-router-pal-clink-002`.
- `git rev-parse HEAD` exited 0: `428fd7398f341ba429f39b216ac92733c6296d9c`.
- `python -m json.tool task-packets/generated/TP-DMX-AUDITOR-ROUTER-WRAPPER-003.json` exited 0.
- `python -m compileall -q tools tests` exited 0.
- `pytest -q tests/auditor_router` exited 0: `33 passed`.
- `python -m tools.auditor_router.preflight --help` exited 0.
- `scripts/auditor-preflight --help` exited 0.
- `scripts/auditor-preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_chosen_when_direct_auth_required --out /tmp/auditor-route-wrapper-pal --packet-id TP-DMX-AUDITOR-ROUTER-WRAPPER-003` exited 0 and selected `pal-mcp-clink AVAILABLE`.
- `python -m json.tool /tmp/auditor-route-wrapper-pal/AUDITOR_ROUTE.json` exited 0.
- `python -m json.tool /tmp/auditor-route-wrapper-pal/ROUTE_PROBE_OUTPUTS.json` exited 0.
- `scripts/auditor-preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_not_chosen_when_direct_available --out /tmp/auditor-route-wrapper-direct --packet-id TP-DMX-AUDITOR-ROUTER-WRAPPER-003` exited 0 and selected `claude-code-cli AVAILABLE`.
- `python -m json.tool /tmp/auditor-route-wrapper-direct/AUDITOR_ROUTE.json` exited 0.
- `git diff --check` exited 0.
- `pre-commit run --files $(git diff --cached --name-only)` exited 0.

## Resolved

- `WRAPPER_BLOCKED_BY_ALLOWLIST`: resolved by adding and validating `scripts/auditor-preflight`.

## FAIL / BLOCKED

- `BLOCKED_BY_GITHUB_WORKFLOW_DISPATCH_500`: manual PR Steward workflow dispatch for PR #713 failed via `gh workflow run` and direct REST API with HTTP 500 before this packet. This packet does not depend on workflow dispatch succeeding.

## NOT_RUN

- PAL MCP clink execution: out of scope.
- `PAL_CLINK_AUDIT_OUTPUT.json` capture: out of scope.
- Router logic changes: out of scope.
- Schema changes: out of scope.

## Remaining Blockers

- `MISSING_BASELINE_AUDITOR_ROUTER_ON_MAIN`
- `PAL_CLINK_AUDIT_OUTPUT_MISSING`
- `BLOCKED_BY_GITHUB_WORKFLOW_DISPATCH_500`
