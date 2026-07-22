# AUDITOR_REPORT — TP-DMX-GHA-HARDEN-001

## Verdict

`PASS_WITH_RISKS_FOR_DRAFT_REVIEW`

The active root GitHub Actions set was fully inventoried and the evidence-backed defects were repaired on PR #1100. Deterministic workflow lint and live CI passed at implementation SHA `de8ea3c0272260f1bddb6414d047e5b67ce4a1f7`.

This is **not** a merge-readiness verdict. Workflow files are a security/release authority surface and no independent embedded LLM auditor was available. Keep the PR draft until PR Steward classifies the final proof-only head, review threads, bots, and checks.

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

## Regression caught by the repo's own contract gate

While simplifying `ci-complete.yml`, the canonical DCP step name was shortened to `Run DCP red-lane gate`. The DCP contract manifest treats the exact name `🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)` as a machine-checked interface. Run `29909285292` failed correctly. Commit `de8ea3c` restored the exact name, and run `29909845483` passed the DCP gate and all required Complete CI lanes.

This was not cosmetic pedantry. The failure proved that workflow labels are part of the repository's executable governance contract.

## Validation evidence

Implementation SHA: `de8ea3c0272260f1bddb6414d047e5b67ce4a1f7`

- **Workflow Lint run 29909845766:** checksum verification, actionlint installation, and validation of all workflows succeeded.
- **CodeQL run 29909845991:** JavaScript/TypeScript, Ruby, and Python analyses succeeded.
- **Complete CI run 29909845483:** code quality, unit tests, dope-memory gate, canonical DCP red-lane gate, brand lint, import smoke, audit proof validator, routing consistency, extractor smoke/full, auditor router, and fail-closed CI Pipeline Summary succeeded.
- **Security Review run 29909845507:** credential detection and truthful summary passed; the external Claude analysis was explicitly skipped by the credential/trusted-PR gate.
- **Repo Identity run 29909845976, clobber guard 29909845927, preflight 29909845482, docs 29909845654:** succeeded.
- **Docker Scout run 29909845544:** still executing at proof refresh, but credential detection, Docker Hub authentication, public-base fallback, image builds, and observed CVE scans were functioning.
- **Branch freshness:** branch was merged from current `main` without force-push and was zero commits behind at implementation validation.

## Embedded audit

- `auditor_tool`: `none`
- `auditor_model`: `unknown`
- `auditor_verdict`: `SKIPPED`
- `skip_reason`: External embedded-auditor capacity/credentials were unavailable. Deterministic `actionlint` plus live GitHub Actions were used as implementation validation, but they do not replace independent semantic review of red-lane workflow policy.

## Review-item classifications

- Docker Scout image vulnerabilities: `OUT_OF_SCOPE_FOLLOWUP`. The scanner surfaced existing critical/high findings. Suppressing them would be idiotic; image remediation belongs in separate packets.
- Remaining `google-github-actions/run-gemini-cli@v0` references: `OPTIONAL_DEFERRED`. No compatible immutable SHA was proven, so no guessed pin was introduced.
- Missing independent embedded auditor: `NEEDS_SUPERVISOR`.

## Remaining risks

1. **Independent review:** no independent embedded auditor reviewed this red-lane workflow change. PR Steward or an approved independent reviewer must classify the final exact head.
2. **Branch protection:** whether `CI Pipeline Summary`, `Workflow Lint`, CodeQL, or other checks are enforced by branch protection remains `UNKNOWN` from this run.
3. **Third-party action pinning:** several established Google Gemini workflows intentionally remain on `google-github-actions/run-gemini-cli@v0` with repository ratchet exclusions. No immutable compatible SHA was established during this bounded repair.
4. **Docker Scout cost:** the nine-image Scout matrix is expensive and duplicates some build work. A future artifact-reuse design should consume trusted images from the container workflow rather than silently changing scan provenance here.
5. **Container vulnerabilities:** Scout surfaced existing critical/high image findings, including the LiteLLM image. Those are real follow-ups outside this workflow-only packet.
6. **Proof-only head:** refreshing this report creates a newer PR head. Merge readiness remains blocked until PR Steward confirms checks/proof are current and no unknown review items remain.

## Final posture

- Objective: **met for bounded workflow repair and optimization**
- Merge performed: **false**
- PR state: **draft**
- Confidence: **HIGH for repaired defects; not VERIFIED for merge readiness**
