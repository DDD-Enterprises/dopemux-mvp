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
| PAL MCP clink configs | Static read of repo-local `docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients/*-audit.json` | `claude-audit` or `gemini-audit` exposes only `default` and `codereviewer`, both mapped to `default_codereviewer.txt`, with no mutation flags in effective args. | Do not call PAL MCP; reject default, Copilot, unknown, or mutation-capable configs. |

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

PAL MCP clink route preflight is also advisory route evidence. It does not produce an audit verdict and does not replace the required host-side audit capture. `PAL_CLINK_AUDIT_OUTPUT.json` must be produced by the operator or host runner and normalized into `AUDITOR_REPORT.md`.
