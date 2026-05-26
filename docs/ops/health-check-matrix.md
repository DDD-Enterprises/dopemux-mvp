---
id: ops-health-check-matrix
title: DevOps AutoPR Health Check Matrix
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Required preflight and health checks for optimized development workflow packets.
---
# DevOps AutoPR Health Check Matrix

## Required Preflight

| Check | Command | Pass Condition | Failure Handling |
| --- | --- | --- | --- |
| Workspace path | `pwd` | Expected repo worktree path. | Stop if repo identity is unclear. |
| Remote identity | `git remote -v` | Remote resolves to `DDD-Enterprises/dopemux-mvp`. | Stop if mismatch. |
| Branch identity | `git branch --show-current` | Non-empty scoped branch. | Create or switch to a scoped branch before editing; stop if unsafe. |
| Worktree cleanliness | `git status --short` | Empty or understood unrelated user changes. | Preserve unrelated dirty state. |
| Repo marker | `test -f .dopetaskroot` | Exit 0. | Stop if absent. |
| Task-packet schema | `test -f docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | Exit 0. | Stop or manually validate if absent. |
| GitHub CLI | `gh --version` and `gh auth status` | Installed and authenticated for PR actions. | PR Steward returns not ready if unauthenticated. |
| Auditor CLIs | `agy --help`, `claude --help`, `gemini --help` | Invocation flags proven before use. | Do not guess flags; record skipped or fallback route. |

## PR Steward Health Inputs

PR Steward v1 must harvest, without mutation:

- PR number, URL, base branch, head branch, and head SHA
- changed files
- commits
- submitted reviews
- review comments
- review threads
- issue comments
- status checks and CI conclusions
- proof freshness and embedded-audit status

Any missing or unauthenticated harvest result is a blocking readiness failure.

The PR Steward workflow is advisory in v1. Pending checks can make the emitted readiness `NOT_READY`, but the workflow job records the result in uploaded artifacts and the job summary without becoming a required branch-protection gate.
