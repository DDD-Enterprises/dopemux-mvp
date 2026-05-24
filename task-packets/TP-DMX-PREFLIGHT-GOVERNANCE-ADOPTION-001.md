---
id: TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001
title: Preflight Governance Adoption
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-05-23'
prelude: Task packet for adopting the local preflight hook, CI workflow, ledger,
  and ignored run manifest path as one bounded governance slice.
last_review: '2026-05-23'
next_review: '2026-08-21'
---
# Task Packet: TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001 · Governance · Preflight Adoption

## Objective

Adopt the existing uncommitted preflight bundle as a bounded governance/CI slice, preserving deterministic local checks and CI evidence without mutating unrelated repo state.

## Scope

IN:

* Add `scripts/preflight.sh` as the local/CI preflight runner.
* Add `config/preflight/ledger.json` as the minimal preflight ledger required by the runner.
* Add `.github/workflows/preflight.yml` to run preflight on pull requests and manual dispatch.
* Update `.githooks/pre-commit` to invoke preflight in hook-safe mode.
* Update `.gitignore` to ignore generated `.runs/` manifests.
* Validate the runner syntax, ledger JSON, ignore behavior, smoke path, and diff hygiene.

OUT:

* No changes to runtime services, Docker wiring, provider credentials, MCP servers, or generated research outputs.
* No broad test-suite rewrite.
* No deletion or mutation of the primary checkout dirty state.

## Invariants (Must Remain True)

* Preflight manifests must be generated under `.runs/` and remain ignored.
* Hook execution must not require a clean worktree because hooks run while files are staged.
* CI execution must fail closed on missing ledger, invalid ledger JSON, diff whitespace errors, and smoke-test failures.
* The runner must not print or capture secrets.
* The primary checkout remains untouched except for the user-existing dirty bundle already classified.

If an invariant appears impossible, stop and report.

## Plan (Numbered)

1. Isolate the existing dirty bundle in a dedicated worktree and create this task packet.
1. Inspect the preflight runner, hook, workflow, ledger, and ignore entry.
1. Make only minimal correctness fixes required by validation.
1. Run syntax, ledger, ignore, dry-run/enforce preflight, diff, and pre-commit validations.
1. Commit and push the bounded governance slice, then open a PR if validation passes.

## Files to Touch

* `.githooks/pre-commit`
* `.github/workflows/preflight.yml`
* `.gitignore`
* `config/preflight/ledger.json`
* `scripts/preflight.sh`
* `task-packets/TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001.md`

If additional files are needed, stop and request approval.

## Exact Commands to Run

* `bash -n scripts/preflight.sh`
* `jq -e . config/preflight/ledger.json`
* `git check-ignore -v .runs/example.manifest.json`
* `PREFLIGHT_SKIP_GIT_CLEAN=1 RUN_MODE=dry-run TP_ID=TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001 ./scripts/preflight.sh`
* `PREFLIGHT_SKIP_GIT_CLEAN=1 RUN_MODE=enforce TP_ID=TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001 ./scripts/preflight.sh`
* `git diff --check`
* `pre-commit run --files .githooks/pre-commit .github/workflows/preflight.yml .gitignore config/preflight/ledger.json scripts/preflight.sh task-packets/TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001.md`
* `git status --short`

## Output Capture Rules (Verbatim)

Implementer must return:

* `git diff --stat`
* `git diff`
* Command outputs verbatim
* Exit codes
* Any generated `.runs/` manifest paths
* Any blockers or skipped validations

## Acceptance Criteria

* The preflight runner passes shell syntax validation.
* `config/preflight/ledger.json` is valid JSON.
* `.runs/` is ignored.
* Preflight dry-run and enforce modes pass with `PREFLIGHT_SKIP_GIT_CLEAN=1`.
* Targeted pre-commit checks pass for the touched files.
* Diff scope is limited to the task packet allowlist.

## Rollback Steps

* Delete `.github/workflows/preflight.yml`.
* Delete `config/preflight/ledger.json`.
* Delete `scripts/preflight.sh`.
* Delete `task-packets/TP-DMX-PREFLIGHT-GOVERNANCE-ADOPTION-001.md`.
* Revert `.githooks/pre-commit`.
* Revert `.gitignore`.

## STOP CONDITIONS

Stop immediately if:

* Preflight requires live provider credentials or network/provider validation.
* The smoke path requires broad unrelated source changes.
* Hook execution cannot be made deterministic without expanding scope.
* Secrets appear in generated manifests or command output.

If stopped, return:

* What you attempted
* Evidence collected
* What output is needed next
