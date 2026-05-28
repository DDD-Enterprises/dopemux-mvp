# Auditor Report — TP-DMX-PR-GATE-009

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-PR-GATE-009 — Stabilize required PR gate job
**Status**: PASS_WITH_RISKS (all MEDIUM findings resolved; HIGH finding out of TP scope)

---

## Scope

Files reviewed:

- `.github/workflows/ci-complete.yml` (ci-summary job gate addition)
- `tests/ci/test_pr_gate.py`
- `docs/ops/pr-gate-runbook.md`

---

## Findings

### F-009-HIGH-EXT-1 — code-quality job summary uses `$?` from echo (OUT OF SCOPE)

**Severity**: HIGH
**Status**: OUT_OF_SCOPE

The code-quality job's ADHD-friendly summary step uses `$?` which reflects the
exit code of the immediately preceding `echo` command, not the pre-commit
invocation. This is a pre-existing issue in the code-quality job (not in
ci-summary) and does not affect gate correctness: `ci-summary` reads
`needs.code-quality.result` (the job's overall exit status), which IS correct.

**Action**: Spawned as separate follow-up task. Not blocking TP-009.

---

### F-009-MED-1 — `needs.*.result` not defaulted on workflow cancellation

**Severity**: MEDIUM
**Status**: RESOLVED

The gate initially used inline GA expressions directly in `[ ]` comparisons.
On edge-case workflow cancellation, `needs.X.result` could theoretically be
empty, making the comparison ambiguous.

**Fix applied**: Captured each required job's result into a named variable with
a `|| 'missing'` fallback before the comparison:

```bash
code_quality="${{ needs.code-quality.result || 'missing' }}"
gate_tests="${{ needs.tests.result || 'missing' }}"
extractor_smoke="${{ needs.extractor-smoke.result || 'missing' }}"
gate_ok=true
[ "$code_quality"    != "success" ] && gate_ok=false
[ "$gate_tests"      != "success" ] && gate_ok=false
[ "$extractor_smoke" != "success" ] && gate_ok=false
```

This also eliminates the `_gate_ok` underscore-prefix style issue and improves
readability of the blocked message line.

---

### F-009-MED-2 — test used `re.search` — passed on first match only

**Severity**: MEDIUM
**Status**: RESOLVED

`test_gate_checks_success_not_non_failure` used `re.search(pattern, script)`
with a `(code-quality|tests|extractor-smoke)` alternation — a single match
would pass even if only one of the three required jobs used `!= "success"`.

**Fix applied**: Replaced with `test_gate_checks_each_required_job_uses_success_comparison`:
- Asserts each required job's `needs.X.result` is referenced in the gate script
- Asserts `len(re.findall(r'!= "success"', script)) >= 3`

---

### F-009-MED-3 — `test_advisory_extractor_full` passed vacuously

**Severity**: MEDIUM
**Status**: RESOLVED

The test scanned for `extractor-full.result` with `!= ` in the same line,
then checked if `exit 1` appeared within 5 lines. Since `extractor-full.result`
never appears in the gate script at all, the loop body never executed.

**Fix applied**: Replaced with a direct absence assertion:
```python
assert "needs.extractor-full.result" not in _GATE_SCRIPT
```

---

### F-009-LOW-1 — `[ ] && cmd` style inconsistency

**Severity**: LOW
**Status**: ACCEPTED_RISK

The gate uses `[ cond ] && gate_ok=false` while the rest of ci-summary uses
`if [ ]; then fi`. The pattern is functionally correct: bash's `set -e` is
explicitly exempt for non-final members of `&&` lists (bash manual). Accepted
as the named-variable refactor maintains the same idiom but improves clarity.

---

### F-009-LOW-2 — `_gate_ok` underscore prefix

**Severity**: LOW
**Status**: RESOLVED

Renamed to `gate_ok` (no underscore) as part of the F-009-MED-1 fix.

---

## Remaining Risks

- Branch protection truth is UNKNOWN — operator must verify `ci-summary`
  (display: "📊 CI Pipeline Summary") is registered as a required status check
  in the `main` branch protection rule.
- `code-quality` job's `$?` summary issue is pre-existing and out of TP-009
  scope; spawned as separate follow-up.
- `mypy` not run — `tests/ci/` contains only YAML-parsing structural tests;
  no new typed Python source files.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/ci/ (17 tests) | PASS |
| pytest prior suites (200 tests: copilot_repair + pr_action_bridge + audit) | PASS |
| Gate blocks on code-quality.result != success | PASS |
| Gate blocks on tests.result != success | PASS |
| Gate blocks on extractor-smoke.result != success | PASS |
| extractor-full.result absent from gate section | PASS |
| needs.*.result || 'missing' fallback present | PASS |
| gate_ok (no underscore prefix) | PASS |
| exit 1 on gate failure | PASS |
| PR Gate: BLOCKED message present | PASS |
| PR Gate: CLEAR message present | PASS |
| UNKNOWN branch protection caveat in code | PASS |
| advisory carve-out documented in code | PASS |
| No branch protection mutation | PASS |
| No pull_request_target introduced | PASS |
| No new secrets or elevated permissions | PASS |
| No trailing whitespace in gate script | PASS |
| No trailing whitespace in runbook | PASS |
| mypy | NOT_RUN (no typed source files) |
