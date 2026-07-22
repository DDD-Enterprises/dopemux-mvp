# AUDITOR_REPORT — TP-DMX-GHA-HARDEN-001

## Verdict

`PASS_WITH_RISKS_FOR_DRAFT_REVIEW`

The active root GitHub Actions set was fully inventoried and the evidence-backed defects were repaired on PR #1100. Deterministic workflow lint and live current-head CI passed at workflow-code SHA `e700cc0794ebb0de2e791573d26594882c94eb99` before this proof-only commit.

This is **not** a merge-readiness verdict. Workflow files are a security/release authority surface, the branch was four commits behind `main` at the last comparison, and no independent embedded LLM auditor was available. Keep the PR draft until the proof-only head reruns are current and PR Steward classifies the final state.

## Workflow census

Seventeen pre-existing active root workflows were inspected:

1. `ci-complete.yml`
2. `clobber-guard.yml`
3. `codeql.yml`
4. `containers.yml`
5. `docker-scout.yml`
6. `docs.yml`
7. `embedded-audit.yml`
8. `gemini-dispatch.yml`
9. `gemini-invoke.yml`
10. `gemini-plan-execute.yml`
11. `gemini-review.yml`
12. `gemini-scheduled-triage.yml`
13. `gemini-triage.yml`
14. `preflight.yml`
15. `pr-steward.yml`
16. `repo-identity.yml`
17. `security-review.yml`

A new eighteenth workflow, `workflow-lint.yml`, now validates the complete active set.

## OBSERVED defects repaired

### Docker Scout authentication and DHI behavior

- The workflow attempted Docker Hub login even when credentials were empty, producing `Username and password required`.
- It now detects namespace and credential availability before the matrix starts.
- An unconfigured repository gets a clean, visible advisory skip rather than a false CI failure.
- When DHI authentication is unavailable, Scout now uses the same public-image fallback posture as the container build workflow instead of applying inconsistent PR-versus-main behavior.

### Gemini triage query and mutation bugs

- Scheduled triage combined `no:label` and `label:"status/needs-triage"` in one search, an impossible intersection.
- It now queries both populations separately and deduplicates by issue number.
- Both triage workflows used label replacement semantics. They now add validated labels, preserve unrelated existing labels, and remove only `status/needs-triage` after a valid classification.

### Misleading and duplicate CI summaries

- `ci-complete.yml` checked `$?` immediately after an `echo`, so its code-quality summary could not report the preceding validation result.
- The summary now uses actual job/dependency results and fails closed on required lanes.
- Duplicate Claude and documentation jobs were removed from the giant workflow. Dedicated path-scoped workflows own those advisory surfaces.
- The dedicated Claude summary now distinguishes a missing credential, a trusted-PR skip, successful action completion, and action failure. It no longer claims code is secure merely because the job completed.

### Action and workflow hardening

- CodeQL moved from deprecated v3 to a pinned v4.37.3 commit.
- The Anthropic security-review action is pinned to an inspected commit rather than `@main`.
- Docs, preflight, repo identity, CodeQL, and workflow lint gained explicit least-privilege permissions and concurrency cancellation.
- Docs and CodeQL gained path scoping to avoid expensive irrelevant runs.
- Preflight avoids `apt-get update` when `jq` is already present.
- Dependabot update concurrency was reduced and container updates were ungrouped because image tags are not reliably SemVer.

## Validation evidence

- **Workflow Lint run 29908297532:** `actionlint` completed successfully; checksum verification, installation, and validation steps all passed.
- **CodeQL run 29908297229:** completed successfully for the current workflow-code head.
- **Complete CI run 29908297656:** all required lanes completed successfully before `ci-complete.yml` was simplified. The required gates were code quality, tests, extractor smoke, audit proof validation, routing consistency, extractor full, and auditor router.
- **Security Review run 29908297428:** credential detection and truthful summary passed; the external Claude analysis was explicitly `skipped` because the credential gate did not authorize it.
- **Repo Identity, clobber guard, preflight, and docs:** completed successfully for the workflow-code head.
- **Docker Scout:** credential detection and Docker Hub authentication succeeded in the observed run; DHI fallback executed successfully. The long image matrix was still executing when the final workflow-code commit superseded the run.

## Embedded audit

- `auditor_tool`: `none`
- `auditor_model`: `unknown`
- `auditor_verdict`: `SKIPPED`
- `skip_reason`: External embedded-auditor capacity/credentials were unavailable. Deterministic `actionlint` plus live GitHub Actions were used as implementation validation, but they do not replace independent semantic review of red-lane workflow policy.

## Remaining risks

1. **Branch freshness:** the branch was four commits behind `main` at the last comparison. Rebase or update the branch, rerun current-head checks, and inspect conflicts before merge.
2. **Independent review:** no independent embedded auditor reviewed this red-lane workflow change. PR Steward or an approved independent reviewer must classify the final exact head.
3. **Branch protection:** whether `CI Pipeline Summary`, `Workflow Lint`, CodeQL, or other checks are enforced by branch protection remains `UNKNOWN` from this run.
4. **Third-party action pinning:** several established Google Gemini workflows intentionally remain on `google-github-actions/run-gemini-cli@v0` with repository ratchet exclusions. No immutable compatible SHA was established during this bounded repair, so this remains a separate follow-up rather than a guessed pin.
5. **Docker Scout cost:** the nine-image Scout matrix is expensive and duplicates some build work. A future artifact-reuse design should consume trusted images from the container workflow rather than silently changing scan provenance here.
6. **CodeQL transport:** a future `ECONNRESET` while downloading the official CodeQL bundle remains a transient GitHub transport failure. The supported response is a job rerun, not an invented downloader or swallowed failure.

## Final posture

- Objective: **met for bounded workflow repair and optimization**
- Merge performed: **false**
- PR state: **draft**
- Confidence: **HIGH for repaired defects; not VERIFIED for merge readiness**
