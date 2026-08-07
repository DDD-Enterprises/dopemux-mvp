---
id: ddd-release-gate-app
title: DDD Release Gate GitHub App setup
type: runbook
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-27'
last_review: '2026-07-27'
next_review: '2026-10-25'
prelude: Operator runbook to create and install the ddd-release-gate GitHub App for solo-maintainer security-release approvals.
---

# DDD Release Gate GitHub App setup

## Purpose

Provide an organization-owned automated security-release authority for solo-maintainer repositories. The app posts exact-head PR approvals that PR Steward accepts only when audit, CI, and proof gates are green.

## Permissions (minimal)

| Permission | Access |
|---|---|
| Metadata | read |
| Contents | read |
| Actions | read |
| Checks | read |
| Pull requests | write |

**Do not grant:** secrets, administration, deployments, workflow write, contents write.

## Create the app

1. Organization: `DDD-Enterprises` → Settings → Developer settings → GitHub Apps → New GitHub App.
2. Name: `ddd-release-gate` (bot login will be `ddd-release-gate[bot]`).
3. Homepage: repo docs URL.
4. Webhook: optional; disable if unused.
5. Permissions as table above.
6. Subscribe to events only if needed (`check_suite`, `check_run`, `pull_request` carefully).
7. Where can this app be installed: only on this account.

## Install

1. Install on **only** `DDD-Enterprises/dopemux-mvp` initially.
2. Confirm installation appears under org Installed GitHub Apps.

## Secrets (if using Actions to drive the app)

Store App ID and private key in org/repo secrets, e.g.:

- `DDD_RELEASE_GATE_APP_ID`
- `DDD_RELEASE_GATE_PRIVATE_KEY`

Any workflow that mints tokens and posts reviews must run from **trusted main** (or an external service), never from untrusted PR head code. Prefer `workflow_run` after CI on the PR, with code checkout of `main` for the approval script.

## Config already in repo

`tools/pr_steward/known_reviewers.json` → `trusted_security_release_apps` entry for `ddd-release-gate[bot]`.

## Approval behavior

After independent audit PASS/PASS_WITH_RISKS and required checks green at head `H`, the app submits:

```text
POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
event: APPROVE
commit_id: H
```

PR Steward then re-runs and should clear `SECURITY_RELEASE_APPROVAL_REQUIRED` with `approval_kind=github_app` when gates remain green.

## Workflow: exact-head APPROVE from main

Workflow file: `.github/workflows/ddd-release-gate.yml`

### Secrets required (org or repo)

| Secret | Value |
|---|---|
| `DDD_RELEASE_GATE_APP_ID` | Numeric App ID (e.g. `4420140`) |
| `DDD_RELEASE_GATE_PRIVATE_KEY` | Full PEM private key |

### Run (always from branch `main`)

1. Actions → **ddd-release-gate** → **Run workflow**
2. Branch: **`main`** (required; other branches are rejected)
3. Inputs:
   - `pr_number`: e.g. `1126`
   - `expected_head_sha`: full 40-char SHA (recommended), e.g. `ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3`
   - `require_green_checks`: leave `true` unless debugging
4. Confirm the run posted an APPROVE as `ddd-release-gate[bot]` on that commit.
5. Re-run PR Steward; require READY; then separate operator merge authorization.

### CLI equivalent

```bash
gh workflow run ddd-release-gate.yml \
  --repo DDD-Enterprises/dopemux-mvp \
  --ref main \
  -f pr_number=1126 \
  -f expected_head_sha=ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3 \
  -f require_green_checks=true
```

## Explicit non-authority

The app does **not** authorize deployment, production changes, or auto-merge.
