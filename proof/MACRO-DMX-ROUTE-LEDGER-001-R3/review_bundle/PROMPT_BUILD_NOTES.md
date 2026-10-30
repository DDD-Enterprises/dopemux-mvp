# Prompt build notes (MACRO-DMX-ROUTE-LEDGER-001-R3, W01)

Subject: commit 4fcdc97615d7a736cd1199bb854bf63fcdbf39f0, branch claude/route-ledger-001-8d8032. Base 93050d135ffc2592000c1d0edef82b2912935525. Earlier audited content head 93969e7a3ca2775c7b435e1ce1b6528ad2173c4a.

## Sources
- Template: proof/MACRO-DMX-ROUTE-LEDGER-001-R2/review_bundle/AUDIT_PROMPT_TEMPLATE.txt (hard rules, SUBJECT, INTENT, claims, Q1-Q11, output contract kept word for word except as listed below). The R2 AUDIT_PROMPT.txt was read for the shape of the filled-in fields.
- Claims file: PRIOR_FINDINGS_AS_CLAIMS.md, written from proof/MACRO-DMX-ROUTE-LEDGER-001-R2/review_bundle/GROK_ADJUDICATION.md (finding id, severity and claim only; no verdict, no adjudication column) plus the repair status read from the delta diff and the repair commit.
- Diffs: FROZEN_CUMULATIVE.diff and FROZEN_DELTA_SINCE_R2_AUDIT.diff, produced by `git diff` over the seven content paths, written byte-exact, inserted into the prompt unchanged (the prompt's DIFF section holds the cumulative diff; DELTA_SINCE_PRIOR_AUDIT holds the delta).
- Gates: GATES_PRE_AUDIT.txt (literal output). The prompt's validation claim is a summary of it.

## Deviations from the R2 template
1. Hard rule 5: the R2 sentence "There is no predecessor audit of this change set" is replaced, because one exists; the new text says the earlier findings are untrusted claims and the auditor must judge the whole cumulative diff.
2. SUBJECT: base, head and macro id filled in. Counts: 5 commits touch the seven files (8 commits in the range base..head), 7 files. The R2 sentence naming four commits is extended to five and points at the DELTA section.
3. VALIDATION_SUMMARY: 55 of 55 tests; `claude plugin validate` stated as passing with two warnings (manifest author, directory icon) plus one README marketplace-install advice line. The task framing said "one README marketplace-install warning"; the literal gate output shows that line as advice and shows the two other warnings, so the prompt states what the gate printed. Live session, markdownlint: NOT_RUN. The implementer-transcript sentence of R2 (models, advisor counts) is not carried over; the prompt says model identity is UNKNOWN.
4. Limitation (i): "NEVER run in a real session ... 53 tests" becomes "repaired code NOT run ... 55 tests". Limitation (iv): the in-tree tsc gate now passes (it was NOT_RUN in R2); the auditor is told the engine-laid tsconfig.json is not part of the commit. Added (xi) auditor has no tools; (xii) markdownlint NOT_RUN.
5. Added Q12 and Q13 verbatim as given in the packet; "through Q11" in the output contract became "through Q13". Q1-Q11 are unchanged.
6. Added the labelled sections DELTA_SINCE_PRIOR_AUDIT and PRIOR_FINDINGS_AS_CLAIMS before the DIFF section, each framed as data and untrusted.
7. INTENT text is unchanged from the template; the status-segment wording in it (advisor N/B) predates the repair and the auditor is expected to compare it with the code (this is part of Q12 and Q13).
8. Not included in the prompt: the R2 verdict, the adjudication column, any file outside the seven content paths other than the claims and the gate summary. The string PASS_WITH_RISKS appears once, as an allowed value of the output-contract enum. One repo-relative-looking home reference, `~/.claude`, appears inside the diff itself (README text under audit), not added by this build.

## Sizes and hashes
See SHA256SUMS_INPUTS.txt. AUDIT_PROMPT.txt is within the 160,000 byte limit (size recorded by the return report).

## Pattern scan (AKIA, private key header, xox, ghp_, sk-, and the password/secret/api key/bearer assignment pattern)
Counts per file, all six patterns in that order: FROZEN_CUMULATIVE.diff 0,0,0,0,0,0; FROZEN_DELTA_SINCE_R2_AUDIT.diff 0,0,0,0,0,0; AUDIT_PROMPT.txt 0,0,0,0,0,0; PRIOR_FINDINGS_AS_CLAIMS.md 0,0,0,0,0,0; GATES_PRE_AUDIT.txt 0,0,0,0,0,0. This notes file and SHA256SUMS_INPUTS.txt were scanned after writing: 0 hits each (recorded in the return report).

## Not done
No auditor was run, nothing was sent anywhere, nothing was committed. Hook-related and environment values were not copied into any file.

## Coordinator corrections after the W01 return (2026-10-30, before anything was sent)

W01 returned AUDIT_PROMPT.txt with sha256 `ffaa094e8ff139c9cac87301860940ec56c40c7657fd1e92054a63724933a001` (134,727 bytes). The coordinator re-read the non-diff part and found stale or inaccurate claim text, all in the header sections; no hard rule, question wording other than Q6, output contract, embedded diff or delta was changed. Deviation 7 above (INTENT unchanged from the template) is SUPERSEDED by correction 1.

1. INTENT status bullet and Q6: the template described the pre-repair status (`advisor N/B ⚠` as a session total over a child budget). Both now describe the repaired grammar: `advisor N/B ⚠` against `sessionAdvisorBudget` and a separate `child M/B ⚠` segment for the busiest child against `childAdvisorBudget`.
2. IMPLEMENTER CLAIMS, validation bullet: "pre-commit over the proof-only range" was inaccurate (the range b0b802617..4fcdc9761 contains the repair commit); now stated as such.
3. IMPLEMENTER CLAIMS, API bullet: the installed CLI is now 2.1.314 (it was 2.1.309 at the earlier audit); the mod also loaded live on 2.1.312 and 2.1.314.
4. Limitation (i): the repaired code is not run live, but the pre-repair code (content head 93969e7a3) WAS loaded by the operator in real interactive sessions on 2026-10-30 (status line, over-budget advisor toast, `/route-ledger` table, background Agent joins, an `advisor_call` receipt attributed to the right agent, 36 schema-valid receipt rows across three sessions, one headless). Stated as implementer-side observation, not evidence in the message.
5. Limitation (iii): coexistence with the operator's own `statusLine` command was seen live on the pre-repair code; coexistence with another PLUGIN (dopemux-pulse) stays unverified.
6. N1 claim line (here and in PRIOR_FINDINGS_AS_CLAIMS.md): repair status now says OPEN for the repaired code and cites limitation (i).
7. PRIOR_FINDINGS_AS_CLAIMS.md was re-extracted from the corrected prompt so the two agree byte for byte.

Post-correction: AUDIT_PROMPT.txt is 135,918 bytes (limit 160,000). The embedded DELTA and DIFF sections were re-compared with FROZEN_DELTA_SINCE_R2_AUDIT.diff and FROZEN_CUMULATIVE.diff after the edits: identical. SHA256SUMS_INPUTS.txt was regenerated by the coordinator after the corrections.
