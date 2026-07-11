# Independent Audit Prompt

You are the independent embedded auditor for `TP-DMX-MERGE-INTEGRITY-0001`.

Audit exact content commit:

```text
b71e13a9b8691217dc6b35d148ccc122bc7d0f06
```

Repository:

```text
/Users/hue/code/dopemux-merge-integrity-0001
```

Read these artifacts:

- `docs/03-reference/merge-integrity/merge-integrity-investigation.md`
- `docs/90-adr/adr-dmx-merge-integrity-agent-patch-admission.md`
- `docs/03-reference/merge-integrity/merge-integrity-architecture.md`
- `docs/03-reference/merge-integrity/implementation-series-plan.md`
- `proof/TP-DMX-MERGE-INTEGRITY-0001/EVIDENCE_LEDGER.md`
- `proof/TP-DMX-MERGE-INTEGRITY-0001/INCIDENT_MATRIX.json`
- `proof/TP-DMX-MERGE-INTEGRITY-0001/GITHUB_CONTROLS_SNAPSHOT.json`

Challenge whether the design:

1. Would have blocked PRs #932 and #1025.
2. Handles the unresolved/CONFLICTING evidence for PR #720 honestly.
3. Allows legitimate mass deletion only through explicit intent and extra gates.
4. Can process PR #1038 without trusting its title or source branch.
5. Avoids authority leakage from PR text, labels, branches, GitHub UI, generated proof, or worktree hygiene.
6. Avoids race conditions around head SHA, tree SHA, diff hash, checks, review threads, labels, and base branch changes.
7. Avoids self-reference and stale-proof problems.
8. Handles GitHub pagination and patch-size limits.
9. Avoids GitHub event-loop and required-check deadlocks.
10. Avoids solo-operator review deadlocks by requiring explicit supervisor override semantics.
11. Avoids unbounded destructive permissions.
12. Keeps PR Steward read-only.
13. Requires Candidate Sanitizer to apply a bounded patch to current `main`.
14. Keeps heuristics as secondary risk signals, not authorization.

Return exactly one verdict:

```text
PASS
PASS_WITH_RISKS
FAIL
NEEDS_SUPERVISOR
```

Then provide concise findings, required fixes if any, accepted risks, and residual uncertainty. Do not edit files.
