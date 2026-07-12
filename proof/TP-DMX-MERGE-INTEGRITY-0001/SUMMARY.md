# Merge Integrity Investigation Summary

## Scope

This is a docs-and-proof investigation bundle for `ADR-DMX-MERGE-INTEGRITY-0001` and `DMX-MIA-0001`. It does not implement a merge executor, modify a GitHub rule, mutate a PR, or claim final readiness.

## Verified Claims

| Claim | Evidence | Status |
|---|---|---|
| PR #1025 deleted 137 files and 27,676 lines | `git diff --name-status --find-renames 7f904d78e01702d2d21b0ac953eb3b8611dda971 8af764b142587ea4421b5a361c5892e804537793` | PASS |
| PR #932 was a destructive landed clobber | `git diff --name-status --find-renames c45b2c8e7a995b3d47537367d909fafaa7ac12cf 559d7e2fa6ba5335763a57a1fe0dbe79b0e1dfa1` | PASS |
| Root hygiene and merge-specialist scope collectors omit deletions | `.github/workflows/ci-complete.yml`; `src/dopemux_pr_merge_specialist/validation.py` | PASS |
| Existing merge-specialist merge binds expected head only | `src/dopemux_pr_merge_specialist/merge.py`; `src/dopemux_pr_merge_specialist/github_api.py` | PASS |
| Current GitHub controls and single-owner CODEOWNERS posture | `GITHUB_CONTROL_CAPTURE.json` | PASS |
| PR #720 was a destructive landed clobber | current landed diff shows one UI file; causal story requires more evidence | NOT_RUN |
| Final-head independent audit | trusted post-commit workflow depends on unmerged PR #1042 | NOT_RUN |
| Protected-reference race and permission qualification | implementation-time controlled race test required | NOT_RUN |

## Current Blockers

- This PR remains a draft and is not merge-ready.
- No trusted current-head audit receipt exists.
- PR #1042 has not landed, so its fail-closed audit/Steward behavior is not repository truth on `main`.
- Protected-reference exact-admission capability is unqualified.
- PR #720/#734 remains a conflicting historical report, not an accepted replay fixture.

## Custody

The committed proof records reproducible commands, immutable Git SHAs, and a redacted GitHub control capture. It intentionally does not contain recursive raw diffs or copied source trees. A trusted workflow must produce the final-head receipt after the candidate commit exists.
