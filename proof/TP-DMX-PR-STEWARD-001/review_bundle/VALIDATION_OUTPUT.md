# Validation Output

Generated: `2026-05-26T06:56:15Z`

| Command | Exit Code | Result |
| --- | ---: | --- |
| `python -m json.tool task-packets/generated/TP-DMX-PR-STEWARD-001.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/merge_readiness.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/review_item_ledger.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/thread_dispositions.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/ci_triage.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/pr_state_snapshot.schema.json` | 0 | PASS |
| `python -m json.tool schemas/proof/embedded_audit.schema.json` | 0 | PASS |
| `python -m json.tool proof/TP-DMX-PR-STEWARD-001/PROOF.json` | 0 | PASS |
| `python -m compileall -q tools tests` | 0 | PASS |
| `pytest -q tests/pr_steward` | 0 | PASS, 8 passed |
| `python -m tools.pr_steward.intake --help` | 0 | PASS |
| `scripts/pr-steward --help` | 0 | PASS |
| `python -m tools.pr_steward.intake --fixture-dir tests/fixtures/pr_steward/ready_all_green --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-ready --strict` | 0 | PASS, emitted READY |
| `python -m json.tool /tmp/pr-steward-ready/MERGE_READINESS.json` | 0 | PASS |
| `python -m json.tool /tmp/pr-steward-ready/REVIEW_ITEM_LEDGER.json` | 0 | PASS |
| `python -m json.tool /tmp/pr-steward-ready/THREAD_DISPOSITIONS.json` | 0 | PASS |
| `python -m json.tool /tmp/pr-steward-ready/CI_TRIAGE.json` | 0 | PASS |
| `python -m json.tool /tmp/pr-steward-ready/PR_STATE_SNAPSHOT.json` | 0 | PASS |
| `test -f /tmp/pr-steward-ready/PR_STEWARD_SUMMARY.md` | 0 | PASS |
| `copilot --model claude-sonnet-4.6 --no-custom-instructions --disable-builtin-mcps --stream off --available-tools=__none__ -p "$(cat proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md)"` | 0 | PASS_WITH_RISKS |
| `git diff --check` | 0 | PASS |
| `pre-commit run --files $(git diff --name-only) || true` | 0 | PASS |

## Embedded Audit Caveat

The raw Copilot transcript is preserved at `artifacts/COPILOT_AUDIT_OUTPUT.md`. It returned `PASS_WITH_RISKS` and `Commit Readiness READY`, but includes inert tool-call shaped text and generated snippets that are not local proof. Local commands in this file are the validation authority.
