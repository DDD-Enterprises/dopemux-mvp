# Artifact Index

## Core Review Files

| Path | Purpose |
| --- | --- |
| `MANIFEST.json` | Machine-readable review bundle manifest. |
| `SUMMARY.md` | Human supervisor summary. |
| `PROOF.json` | Review-ready copy of packet proof. |
| `AUDITOR_REPORT.md` | Embedded audit attempt report. |
| `VALIDATION_OUTPUT.md` | Validation command summary. |
| `GIT_STATE.md` | Repo, branch, and status evidence. |
| `DIFF_STAT.txt` | Diff size summary. |
| `CHANGED_FILES.txt` | Changed-file inventory. |
| `artifacts/COPILOT_AUDIT_INPUT.md` | Bounded Copilot fallback audit prompt. |
| `artifacts/COPILOT_AUDIT_OUTPUT.md` | Copilot fallback audit output summary. |

## PR Steward Artifacts

| Path | Source | Purpose |
| --- | --- | --- |
| `artifacts/PR_STATE_SNAPSHOT.json` | `/tmp/pr-steward-ready/PR_STATE_SNAPSHOT.json` | Fixture-smoke harvested PR state snapshot. |
| `artifacts/REVIEW_ITEM_LEDGER.json` | `/tmp/pr-steward-ready/REVIEW_ITEM_LEDGER.json` | Fixture-smoke review item classifications. |
| `artifacts/THREAD_DISPOSITIONS.json` | `/tmp/pr-steward-ready/THREAD_DISPOSITIONS.json` | Fixture-smoke review-thread dispositions. |
| `artifacts/CI_TRIAGE.json` | `/tmp/pr-steward-ready/CI_TRIAGE.json` | Fixture-smoke check/CI triage. |
| `artifacts/MERGE_READINESS.json` | `/tmp/pr-steward-ready/MERGE_READINESS.json` | Fixture-smoke readiness verdict. |
| `artifacts/PR_STEWARD_SUMMARY.md` | `/tmp/pr-steward-ready/PR_STEWARD_SUMMARY.md` | Fixture-smoke markdown summary. |

## Exclusions

See `MANIFEST.json` for excluded paths and reasons.
