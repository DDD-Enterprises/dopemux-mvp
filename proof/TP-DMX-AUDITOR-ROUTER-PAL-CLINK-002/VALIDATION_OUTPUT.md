# Validation Output

Status: `PASS_TARGETED_TESTS_WITH_SCOPE_CONFLICT`

## Scope Conflict: Missing Auditor Router Baseline

Expected predecessor runtime from `TP-DMX-AUDITOR-ROUTER-001` was not present on `origin/main`.

Observed missing baseline surfaces:

- `tools/auditor_router/**`
- `tests/auditor_router/**`
- `scripts/auditor-preflight`

This packet therefore implemented the minimal auditor-router baseline required for PAL clink classification tests to pass.

Impact:

- This is broader than a pure PAL clink extension.
- `scripts/auditor-preflight` remains `NOT_RUN / BLOCKED` because the packet validation references it but the allowlist does not permit creating it.
- No claim is made that the full CLI wrapper contract is complete.

## P1 Review Thread Fixes

PR #713 review identified two PAL clink safety gaps:

- Prompt safety checked only `default_codereviewer.txt` basename. Fixed by requiring the canonical relative prompt path `systemprompts/clink/default_codereviewer.txt` and rejecting absolute, parent-traversal, or dot-path forms.
- Mutation flag detection missed equals-form coupled flags. Fixed by detecting unsafe `--flag=value` forms including `--permission-mode=bypassPermissions`, `--approval-mode=yolo`, `--mode=autopilot`, and mutation flags such as `--allow-all=true`.

## PASS

- `python -m json.tool task-packets/generated/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002.json` exited 0.
- `python -m json.tool schemas/proof/auditor_route.schema.json` exited 0.
- `python -m json.tool schemas/proof/embedded_audit.schema.json` exited 0.
- `python -m jsonschema -i task-packets/generated/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exited 0 with a jsonschema CLI deprecation warning.
- `python -m compileall -q tools tests` exited 0.
- `pytest -q tests/auditor_router/test_pal_clink.py` exited 0: `29 passed`.
- `pytest -q tests/auditor_router` exited 0: `33 passed`.
- `python -m tools.auditor_router.preflight --help` exited 0.
- `python -m tools.auditor_router.preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_chosen_when_direct_auth_required --out /tmp/auditor-route-pal-clink --packet-id TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002` exited 0 and selected `pal-mcp-clink AVAILABLE`.
- `python -m json.tool /tmp/auditor-route-pal-clink/AUDITOR_ROUTE.json` exited 0.
- `python -m json.tool /tmp/auditor-route-pal-clink/ROUTE_PROBE_OUTPUTS.json` exited 0.
- `python -m tools.auditor_router.preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_not_chosen_when_direct_available --out /tmp/auditor-route-direct-wins --packet-id TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002` exited 0 and selected `claude-code-cli AVAILABLE`.
- `python -m json.tool /tmp/auditor-route-direct-wins/AUDITOR_ROUTE.json` exited 0.
- `python -m jsonschema -i /tmp/auditor-route-direct-wins/AUDITOR_ROUTE.json schemas/proof/auditor_route.schema.json` exited 0 with a jsonschema CLI deprecation warning.
- `python -m tools.auditor_router.preflight --out /tmp/auditor-route-live --packet-id TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002` exited 0 and selected repo-local `pal-mcp-clink AVAILABLE` by static config inspection.
- `git diff --check` exited 0.
- `pre-commit run --files $(cat proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/CHANGED_FILES.txt)` exited 0. Hooks passed or skipped as not applicable.

## FAIL / BLOCKED

- Historical PAL-CLINK-002 result: `scripts/auditor-preflight --help` exited 127 because the wrapper was not allowlisted in that packet.
- Follow-up resolution: `TP-DMX-AUDITOR-ROUTER-WRAPPER-003` adds `scripts/auditor-preflight` and validates wrapper help plus fixture smokes. Resolved blocker: `WRAPPER_BLOCKED_BY_ALLOWLIST`.
- External blocker recorded after PR #713 review work: `BLOCKED_BY_GITHUB_WORKFLOW_DISPATCH_500`.

## NOT_RUN

- Real PAL MCP clink execution: `PAL_CLINK_AUDIT_OUTPUT.json` was not captured. Blocker: `PAL_CLINK_AUDIT_OUTPUT_MISSING`.
- PR Steward live integration: out of scope.
- Host-side authenticated CLI/PAL execution: out of scope for router preflight.

## Status Terms

Use `PASS_TARGETED_TESTS_WITH_SCOPE_CONFLICT` for this branch. Do not call this `PASS`, `READY`, or `MERGE_READY`.

## Local PR #713 Review Fix Validation

Generated: 2026-05-26T12:01:41.823532Z

```text
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 33 passed
pytest -q tests/auditor_router -> exit 0, 37 passed
python -m tools.auditor_router.preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_no_configs_found --out /private/tmp/auditor-route-pr713-fallback --packet-id TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002 --allow-fallback -> exit 0
```

## Local PR #713 Schema-Compatible Finding Fix Validation

Generated: 2026-05-26T22:06:50Z

Patched the active PR #713 review blocker where normalized PAL clink findings emitted a `blocking` property not allowed by `schemas/proof/embedded_audit.schema.json`. The router now preserves the raw `blocking=true` signal for FAIL classification but omits it from emitted embedded-audit findings.

```text
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 33 passed
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router -> exit 0, 37 passed
python -m json.tool schemas/proof/embedded_audit.schema.json -> exit 0
python -m json.tool proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/PROOF.json -> exit 0
python -m json.tool proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/review_bundle/PROOF.json -> exit 0
git diff --check -> exit 0
pre-commit run --files $(git diff --name-only) -> exit 0
```
