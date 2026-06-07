---
id: pr-steward-and-readiness
title: Pr Steward And Readiness
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Pr Steward And Readiness (reference) for dopemux documentation and developer
  workflows.
---
# PR Steward & Merge Readiness

**PR Steward is advisory only. It is NOT merge authority.**

Merge decisions require GPT-5.5 Pro Supervisor judgement and, while `DCP-RED-MERGE-SEAM-0001` is active, explicit operator authorization. PR Steward produces a structured readiness artifact — it does not merge, approve, or authorize anything.

---

## What It Harvests

PR Steward reads and aggregates the following signals before emitting a readiness verdict:

- **CI check results** — required gates (must all pass) and advisory gates (may be flagged without blocking)
- **AI review comments** — embedded-audit, security-review, gemini-review; presence and pass/fail status
- **Human reviewer sign-offs** — recognized human approvals from the PR's review thread
- **Proof bundle freshness** — `PROOF.json` `head_sha` compared against current target branch tip
- **Obligation ledger status** — any OPEN obligations whose scope overlaps this PR's diff
- **Scope escape detection** — whether the diff touches files outside the capsule's declared `allowed_files`
- **Auditor status** — whether PAL clink completed (`PASS` / `PASS_WITH_RISKS`), is pending (`NEEDS_SUPERVISOR`), or was skipped/failed (`SKIPPED` / `FAILED`)

---

## Readiness Blocking Conditions

PR Steward **must NOT** emit `MERGE_READINESS: READY` if ANY of the following conditions are true:

| Condition | Detail |
|---|---|
| Proof is stale | `head_sha` in `PROOF.json` does not match current target branch tip |
| Open obligations present | Any obligation in the obligation ledger is `OPEN` and in scope of this PR |
| Unknown reviewers or bots approved | No recognized human or known-good AI reviewer has approved; unknown bot approvals do not count |
| Required CI gate failed | Any gate marked `required` in the repo's branch protection has a non-passing status |
| Scope escape detected | Diff includes edits to files outside the capsule's `allowed_files` declaration |
| Auditor status is `SKIPPED` or `FAILED` | PAL clink did not complete successfully; `NEEDS_SUPERVISOR` is permitted but must be flagged |
| Supervisory sign-off absent | No GPT-5.5 Pro Supervisor or human operator has signed off on the proof bundle |

If any blocking condition is present, PR Steward emits:

```
MERGE_READINESS: BLOCKED
blocking_conditions:
  - <condition-id>: <detail>
```

If no blocking conditions are present and all required signals are green:

```
MERGE_READINESS: READY (advisory)
```

The `(advisory)` qualifier is always present. `READY` is a recommendation, not an authorization.

---

## Not Merge Authority

PR Steward emits two artifacts:

```
PR_STEWARD_SUMMARY.md    # human-readable readiness report
MERGE_READINESS          # structured verdict field (READY | BLOCKED | PENDING)
```

These artifacts are inputs to the supervisor's merge decision. The supervisor (GPT-5.5 Pro or human operator) reads the summary, reviews the proof bundle, and makes the final call.

While `DCP-RED-MERGE-SEAM-0001` is active:

- `queue_drain.py execute=True` is **hard-blocked** regardless of readiness verdict
- `scripts/batch_resolve_and_merge.py` is **hard-blocked** regardless of readiness verdict
- All merges require explicit operator authorization per `red-lines-and-stop-conditions.md`

PR Steward does not invoke, trigger, or queue any merge operation. It reads. It reports. It stops there.
