# Prompt build notes (MACRO-DMX-ROUTE-LEDGER-001-R4, W01, coordinator script, no model dispatch)

Subject: the MERGE commit `989fe4651c050ec23619e5208da17d6152b477b0` on `claude/route-ledger-001-8d8032` (parents `ad8a141c6a88ce05f865fb7d26d84ce0beeb4137` and `97b6d5040496e2271c41d24c339d039303bbe6b1`, the latter being origin/main with PR 1472). The seven audited content paths are byte-identical to the repair commit `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`. Diff base: `97b6d5040` (current origin/main). Earlier audited content head (R2): `93969e7a3ca2775c7b435e1ce1b6528ad2173c4a`.

## Sources
- The R3 coordinator-corrected prompt `proof/MACRO-DMX-ROUTE-LEDGER-001-R3/review_bundle/AUDIT_PROMPT.txt` (hard rules, INTENT, claims, Q1-Q13, output contract, embedded DELTA, PRIOR_FINDINGS and DIFF sections), changed only by the substitutions below.
- Diffs regenerated with `git diff` over the seven content paths and compared with R3's files.
- Gates: GATES_PRE_AUDIT.txt (literal output of the last lines of each command; trailing whitespace stripped and blank-line runs squeezed, which touches no audit input).

## Substitutions (a script; each anchor had to occur exactly once, otherwise STOP)
- FROZEN_CUMULATIVE.diff: `git diff 97b6d5040 989fe4651 -- <seven paths>`, 106228 bytes, sha256 4cc90ba80e8ba2f5b964e0cfa3718691f1686940078833a996d0e707b590dbcb; byte-identical (cmp) to R3's file.
- FROZEN_DELTA_SINCE_R2_AUDIT.diff: `git diff 93969e7a3 989fe4651 -- <seven paths>`, 10898 bytes, sha256 fd5ad264254193e2525c59036f747ed9de922497a4eeb3791e21fae116e5e512; byte-identical (cmp) to R3's file.
- substitution "SUBJECT base, head, counts, macro id": 1 occurrence replaced.
- substitution "IMPLEMENTER CLAIMS lead-in": 1 occurrence replaced.
- substitution "pre-commit claim": 1 occurrence replaced.
- substitution "limitation (xiii)": 1 occurrence replaced.
- substitution "claims header head": 1 occurrence replaced.
- substitution "claims file header head": 1 occurrence replaced.
- embedded DELTA section == FROZEN_DELTA_SINCE_R2_AUDIT.diff: True
- embedded DIFF section == FROZEN_CUMULATIVE.diff: True
- embedded PRIOR_FINDINGS section == PRIOR_FINDINGS_AS_CLAIMS.md: True

Nothing else in the prompt changed: the hard rules, INTENT, Q1-Q13 and the output contract are R3's text. The prompt contains no mention of the R3 audit runs or of any verdict. The string PASS_WITH_RISKS appears only as an allowed value of the output-contract enum.

## Sizes and hashes
AUDIT_PROMPT.txt is 136,451 bytes (limit 160,000). SHA256SUMS_INPUTS.txt lists the seven other files.

## Pattern scan (AKIA, xox, ghp_, sk-, a password/secret/api-key/bearer assignment, a private-key header)
Counts over the prompt, both diffs, the claims file and the gates file, in that order of patterns: 0 0 0 0 0 0 . The notes, the superseded record and the hash list were scanned after writing (see the closing scan in the W01 commit message). No `/Users/` path appears in the prompt.

## Not done
No auditor was run and nothing was sent anywhere in this workstream.
