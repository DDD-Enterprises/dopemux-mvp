# Merge Integrity Investigation Summary

## Scope

This is a docs-and-proof investigation bundle for `ADR-DMX-MERGE-INTEGRITY-0001` and `DMX-MIA-0001`. It does not implement a merge executor, modify a GitHub rule, mutate a PR, or claim final readiness for the full admission architecture.

## Phase B (post PR #1042)

| Claim | Evidence | Status |
|---|---|---|
| PR #1042 squash-merged to main | `db9b844fc7b1731af953b7c996581082fb3f096f` is `origin/main` tip | PASS |
| PR #1040 rebased onto post-1042 main | `git rebase origin/main` exit 0 | PASS |
| Series remediation uses `0001R` not series `0004` | `task-packets/TP-DMX-MERGE-INTEGRITY-0001R-PR1040-SUPERVISOR-REMEDIATION.json` | PASS |
| Series-plan notes 0004 foundation custody vs future 0004 work | `implementation-series-plan.md` | PASS |
| Existing merge-specialist expectedHeadOid documented as insufficient for base/parent/tree | investigation + architecture + ADR | PASS |
| Agent vs human/dependency merge posture explicit | architecture + ADR | PASS |
| Trusted final-head independent audit for this PR head | live workflow receipt | NOT_RUN |
| PR Steward final readiness for this PR head | live Steward after audit | NOT_RUN |

## Historical claims

| Claim | Evidence | Status |
|---|---|---|
| PR #1025 deleted 137 files and 27,676 lines | COMMAND_INDEX historical-1025 | PASS |
| PR #932 was a destructive landed clobber | COMMAND_INDEX historical-932 | PASS |
| Root hygiene and merge-specialist scope collectors omit deletions | ci-complete.yml; validation.py | PASS |
| PR #720 was a destructive landed clobber | current landed diff shows one UI file | NOT_RUN / CONFLICTING |
| Protected-reference race and permission qualification | implementation-time controlled race test | NOT_RUN |

## Current blockers

- Trusted current-head audit receipt for the **exact PR #1040 head** is missing until live `embedded-audit` + Steward run.
- ADR remains **proposed**.
- Architecture remains unimplemented (beyond #1042 foundation on main).
- Protected-reference exact-admission capability is unqualified.

## Custody

Compact proof only: reproducible commands, immutable Git SHAs, redacted GitHub control capture. No recursive raw diffs. Final-head receipt must come from trusted workflow after this head is published.
