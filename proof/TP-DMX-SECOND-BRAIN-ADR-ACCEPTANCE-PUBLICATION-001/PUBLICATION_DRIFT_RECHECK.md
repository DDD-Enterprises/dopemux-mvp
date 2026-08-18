# Publication-time drift guard — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001 (S4)

## Scope

Standing MA-08 full-diff drift check, discovery base to current execution-time
`origin/main`, plus a targeted overlap check between the acceptance branch's own
changed-file set and the current-main delta.

```
DISCOVERY_BASE        = 72af781e42e0702d9047946e0f5a250e7dff0fa5
PRIOR_MA08_MAIN_SHA    = 75b4cfc581786a53445e412bfc8e25a6e0fdb978
EXECUTION_REMOTE_MAIN  = 57b239e76b8fbb0016ba497bc4a34ec0abee51bb
ISSUE_BASELINE_REMOTE_MAIN = 57b239e76b8fbb0016ba497bc4a34ec0abee51bb   (matches; main did not advance since packet issue)
```

## Composition, not re-derivation

The span `DISCOVERY_BASE..PRIOR_MA08_MAIN_SHA` was already adjudicated fresh in
`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/02_MA08_DRIFT_RECHECK.md`
(part of the audited acceptance-persistence branch, PASS 0/0 at `0defe1cab4`):

```
segment A (72af781e..33d6c353):  MATERIAL_DRIFT_CONTAINED   (recorded, not dissolved into headline)
segment B (33d6c353..cfa4927a):  NO_NEW_MATERIAL_DRIFT
segment C (cfa4927a..75b4cfc5):  NO_NEW_MATERIAL_DRIFT
                                  MA-08 RESULT: NO_NEW_MATERIAL_DRIFT
```

This publication packet adjudicates only the new segment fresh, then composes:

```
segment D (75b4cfc5..57b239e7):  <adjudicated below>
```

Re-running segments A-C would re-diff main's entire history against a stale head for
no new information — `PRIOR_MA08_MAIN_SHA` is confirmed unchanged (see below), so
segments A-C stand on their own controlling, already-audited verdict.

## Verified: merge-base identity

```bash
$ git merge-base tp/DMX-SB-ADR-ACCEPTANCE-002 origin/main
75b4cfc581786a53445e412bfc8e25a6e0fdb978
```

The acceptance branch's merge-base with current `origin/main` is byte-identical to
`PRIOR_MA08_MAIN_SHA`. Segments A-C's controlling verdict is therefore still exactly
the drift history between the acceptance branch and current main, up to that point —
nothing new was inserted into main "underneath" it.

## Segment D: `75b4cfc581`..`57b239e76b`

```bash
$ git diff --name-only 75b4cfc581786a53445e412bfc8e25a6e0fdb978 57b239e76b8fbb0016ba497bc4a34ec0abee51bb
proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/AGY_AUDIT_RAW.json
proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/AUDITOR_REPORT.md
proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/AUDIT_PROMPT.md
proof/pr_merge/embedded-audit/pr-1235/PROOF.json
proof/pr_merge/embedded-audit/pr-1235/PROOF.json.sig
proof/pr_merge/embedded-audit/pr-1235/SIGNING_DISCLOSURE.md
```

6 files, all under `proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/**` and
`proof/pr_merge/embedded-audit/pr-1235/**` — proof/audit records for an unrelated
CI-trust merge-gate incident revert (PR #1235). None of these paths are under:

```
docs/03-reference/architecture/second-brain/**
docs/90-adr/**
schemas/second_brain/**
task-packets/*SECOND-BRAIN*
proof/*SECOND-BRAIN*
AGENTS.md
ADR indexes / architecture indexes
authority manifests / ledgers
privacy / identity / project-boundary governance
```

Segment D classification: **`NO_NEW_MATERIAL_DRIFT`** — zero paths in any watched
class, zero authority/privacy/contract semantic touched.

## Same-path overlap check (acceptance branch vs. current-main delta)

```bash
$ git diff --name-only 75b4cfc581786a53445e412bfc8e25a6e0fdb978 tp/DMX-SB-ADR-ACCEPTANCE-002 | sort > acceptance_branch_files.txt   # 58 files
$ git diff --name-only 75b4cfc581786a53445e412bfc8e25a6e0fdb978 57b239e76b8fbb0016ba497bc4a34ec0abee51bb | sort > main_delta_files.txt   # 6 files
$ comm -12 acceptance_branch_files.txt main_delta_files.txt
(empty)
```

Zero same-path overlap. No textual OR semantic collision is possible for a merge of
current `origin/main` into the acceptance branch.

## Composed verdict

```
segment A:  MATERIAL_DRIFT_CONTAINED   (already audited, recorded — not blocking)
segment B:  NO_NEW_MATERIAL_DRIFT
segment C:  NO_NEW_MATERIAL_DRIFT
segment D:  NO_NEW_MATERIAL_DRIFT      (this recheck)

FULL SPAN (72af781e42..57b239e76b): NO_NEW_MATERIAL_DRIFT
```

```
PUBLICATION_DRIFT_VERDICT = NO_NEW_MATERIAL_DRIFT
BLOCKED_NEW_MATERIAL_DRIFT:                    NOT TRIGGERED
BLOCKED_PUBLICATION_DRIFT:                     NOT TRIGGERED
```

Proceeds to S5 (safe update-by-merge).
