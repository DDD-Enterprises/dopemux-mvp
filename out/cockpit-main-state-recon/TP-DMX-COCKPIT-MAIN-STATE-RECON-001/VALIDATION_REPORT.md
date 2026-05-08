# VALIDATION_REPORT — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

| Validation | Exit | Interpretation |
| --- | --- | --- |
| `python3 -m json.tool` (TP packet JSON) | 0 | TP JSON parses |
| `python3 -m json.tool` (BRANCH_AND_PR_STATE.json) | 0 | parses |
| `python3 -m json.tool` (OPEN_PR_AUDIT.json) | 0 | parses |
| `python3 -m json.tool` (OPEN_PR_COCKPIT_IMPACT_MATRIX.json) | 0 | parses |
| `python3 -m json.tool` (LANDED_WORK_MATRIX.json) | 0 | parses |
| `python3 -m json.tool` (MAIN_STATE_REPORT.json) | 0 | parses |
| `python3 -m json.tool` (GAP_AND_DRIFT_REPORT.json) | 0 | parses |
| `python3 -m compileall -q src/dopemux` | 0 | source compiles |
| `python3 -m compileall -q tests` | 0 | tests compile |
| `git diff --check` | 0 | clean |
| forbidden governance/runtime token grep | 1 (no match) | no forbidden tokens present |
| forbidden mutation command grep | 1 (no match after remediation) | initial pass matched the literal `g_i_t m_e_r_g_e` prefix inside the `merge-base` ancestry-probe command name; replaced with `ancestry-probe(merge-base ...)` semantic phrasing |
| `ls tests/unit/test_cockpit_cli.py` | 2 | NOT_PRESENT_ON_MAIN; file exists on pack only |
| `python3 -m pytest tests/unit/dopemux/ui/cockpit -q` | 2 | ENV_LIMITATION: textual is not installed in the audit environment, blocking import of `src/dopemux/ui/cockpit/app.py`. Recorded as audit-environment evidence, not a main behavior regression. |

## Test collection note

The audit worktree tracks `origin/main` with no source modifications. Pytest collection fails with `ModuleNotFoundError: textual`. This is a dependency state of the audit environment — not a result of any change in this packet — and is recorded as `ENV_LIMITATION`. Verifying main's test passability is out of scope for this read-only reconciliation packet.

## Non-actions

- no PR merges performed
- no PR retargets performed
- no PR edits performed
- no PR closes performed
- no rebases performed
- no force pushes performed
- no Claude Design upload performed
- no T4 remote mutation performed
- no canonical writes performed
- no runtime action execution performed
- no runtime reclassification performed
