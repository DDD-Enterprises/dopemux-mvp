# TP-DMX-ACTIONBRIDGE-CLI-102 Validation Output

## CI Review

- `gh pr checks 755 --watch=false`: PASS. All reported checks were pass or skipping.
- `gh pr checks 756 --watch=false`: PASS. All reported checks were pass or skipping.

## TDD Red

`pytest -q tests/pr_action_bridge/test_cli.py`

Result before implementation: FAIL.

Expected missing-entrypoint failures were observed:

- `No module named tools.pr_action_bridge.__main__`
- missing `scripts/pr-action-bridge`
- missing `tools/pr_action_bridge/cli.py`

## Focused Packet Validation

`python -m json.tool task-packets/generated/TP-DMX-ACTIONBRIDGE-CLI-102.json`

Result: PASS.

`python -m compileall -q tools/pr_action_bridge/__main__.py tools/pr_action_bridge/cli.py scripts/pr-action-bridge tests/pr_action_bridge/test_cli.py`

Result: PASS.

`pytest -q tests/pr_action_bridge/test_cli.py`

Result: PASS.

```text
.....                                                                    [100%]
```

## Claude Review Repair

`git merge --no-edit origin/main`

Result: PASS after resolving `task-packets/generated/TP-DMX-ACTIONBRIDGE-CLI-102.json`
to keep the current narrowed `compileall` validation command.

`/path/to/worktree/scripts/pr-action-bridge --artifact-dir artifacts --out out --generated-at 2026-01-01T00:00:00Z`

Run from `/tmp/pr-action-bridge-wrapper-proof-cwd`, with `artifacts/` populated from
`proof/TP-DMX-ACTIONBRIDGE-CLI-102/input/`.

Result: PASS.

```text
wrote out/ACTION_PLAN.json
wrote out/REPAIR_PACKET.md
# REPAIR_PACKET
```

`! git check-ignore -q proof/TP-DMX-ACTIONBRIDGE-CLI-102/PROOF.json`

Result: PASS. The TP102 proof bundle is now included in the tracked proof ledger
allowlist instead of requiring `git add -f`.

`git diff --check`

Result: PASS.

## Replay Artifact Generation

`python -m tools.pr_action_bridge --artifact-dir proof/TP-DMX-ACTIONBRIDGE-CLI-102/input --out proof/TP-DMX-ACTIONBRIDGE-CLI-102/output --generated-at 2026-01-01T00:00:00Z`

Result: PASS.

```text
wrote proof/TP-DMX-ACTIONBRIDGE-CLI-102/output/ACTION_PLAN.json
wrote proof/TP-DMX-ACTIONBRIDGE-CLI-102/output/REPAIR_PACKET.md
```

## Known Out-Of-Scope Failures

`python -m compileall -q tools scripts tests`

Result: FAIL. Existing files outside the TP102 allowlist fail compilation:

- `scripts/migration/switchover.py`
- `scripts/partition_function.py`
- `scripts/submit_loop_context.py`

`pytest -q tests/pr_action_bridge`

Result: FAIL. Existing compiler tests fail outside the TP102 allowlist:

- `TestSourceItemId.test_unresolved_thread_cross_refs_thread`
- `TestUnknownBlockerAndSequentialIds.test_unknown_blocker_emits_supervisor_action`
- `TestUnknownBlockerAndSequentialIds.test_ids_stay_sequential_when_unknown_blocker_between_known`

## CI Remediation

Initial PR #758 CI failed in `Audit Proof Validator (--all)` because
`proof/TP-DMX-ACTIONBRIDGE-CLI-102/PROOF.json` was missing top-level `embedded_audit`.

Added an explicit `embedded_audit` object with `status=SKIPPED`, plus
`proof/TP-DMX-ACTIONBRIDGE-CLI-102/AUDITOR_REPORT.md`, because no external embedded audit
route ran during this packet.

`python scripts/audit/validate_audit_proof.py proof/TP-DMX-ACTIONBRIDGE-CLI-102/PROOF.json`

Result: PASS.

```text
PASS  proof/TP-DMX-ACTIONBRIDGE-CLI-102/PROOF.json

Result: 1/1 PASS
```
