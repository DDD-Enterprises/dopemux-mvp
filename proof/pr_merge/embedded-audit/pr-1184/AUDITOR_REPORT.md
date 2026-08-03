# Independent Embedded Audit — PR #1184

- Auditor: codex-cli
- Content head: `876cf3f1fd6f358c6500d61d40dfdad96587fc0f`
- Verdict: PASS

## Change Summary

F1 repaired. No blocking defect found.

## Authority Used

Bound commit, PR diff, validator/tests, governance policy.

## Analysis Performed

- Unmatched paths default L2.
- All three proof heads required; no fallback.
- Enumerated proof artifacts only; `evil.bin` and traversal fail.
- Git-derived `content_head..proof_head` delta must exactly match declared paths.
- Template exemption exact path only.
- `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` honored.
- L3 operator gate, L2/L3 one-final-audit remain preserved.
- Historical `SKIPPED` package proof accepted by schema/preflight.

## Validation Performed

PASS:

- `pytest -q -s tests/governance/test_validate_change_contract.py`
- Bound repair diff preflight: PASS, L2.
- Full PR diff whitespace check: PASS.
- Adversarial head-binding probe: FAIL with `proof_only_path_mismatch` plus escaped derived paths.
- Evil/traversal probes: FAIL closed.
- Missing proof head probe: FAIL closed.
- Pre-commit ref-range probe: PASS.

NOT_RUN:

- Full pre-commit suite.

## Remaining Uncertainty / Risk

Worktree contains untracked audit artifacts/caches, outside bound content head. `fsmonitor` IPC warning observed; Git reads still succeeded.

## Files Touched

None. Read-only audit.

## Git State

Bound source matches content head. No tracked modifications created.

## Rollback Plan

None required.

## Requested Next Step

Record audit PASS against bound head; create signed proof-only successor if governance requires it.