---
id: pr-steward-distribution
title: PR Steward Distribution
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Minimal dopemux init scaffold contract for PR Steward distribution.
---
# PR Steward Distribution

`dopemux init` copies PR Steward scaffold files from
`src/dopemux/templates/init/` into a target workspace. The template installer is
recursive and skips existing files, so normal init and `init --force` do not
overwrite local workflow or policy edits.

## Scaffolded Files

- `.github/workflows/pr-steward.yml`
- `.github/workflows/embedded-audit.yml`
- `config/pr_steward/policy.json`
- `config/pr_merge_specialist/policy.yaml`

## Boundaries

- The workflows call the packaged `python -m dopemux.cli pr-steward` command.
- Scaffolded workflows install Dopemux from `DOPEMUX_INSTALL_SPEC` before
  invoking the packaged command, because downstream repositories do not carry
  this source tree on `PYTHONPATH`.
- Review settlement has one implementation in
  `dopemux_pr_steward.review_settlement`. Repository automation reaches it
  through the compatibility script; initialized repositories use packaged
  `pr-steward settlement fetch|compare` commands.
- Template Steward never imports downstream `tools.pr_steward` or
  `scripts.audit` modules directly.
- Template embedded audit reads candidate proof bytes from the validated live
  PR head as Git data. It never checks out or executes candidate code.
- The scaffold does not generate or copy `steward_gate` Python logic.
- The scaffold does not add a setup subcommand, checksum manifest, or reusable
  composite action.
- PR Steward remains check-only; the scaffolded policy records
  `mutates_github: false`.
- Merge specialist governed automerge is off by default.

## Follow-Up

`dopemux pr-steward doctor` is report-only. It validates
`config/pr_steward/policy.json` against
`schemas/pr_steward/config.schema.json`, compares the local policy to the
packaged scaffold policy, and exits blocked on missing config, unknown schema,
invalid config, or scaffold skew. It does not auto-fix, migrate, or write files.

## Hardening Posture

Distribution intentionally keeps runtime authority in the installed package:

- scaffolded workflows call `python -m dopemux.cli pr-steward`
- scaffolded workflows install the package explicitly before that call
- scaffolded policy files are small operator-owned inputs
- `dopemux init` does not overwrite existing workflow or policy files
- doctor reports drift and config problems without mutating the target repo

## Template Finality Contract

Manual template audit dispatch binds repository, PR number, exact live head,
base repository, base SHA, and proof path before reading `PROOF.json`. A valid
run uploads exactly one artifact named
`embedded-audit-pr-<PR>-head-<SHA>-proof`. Template Steward accepts that
artifact only through a completed trusted `workflow_run`, revalidates live
PR/head and canonical proof identity, and evaluates settlement through the
installed package before publishing final readiness.

API spend permission is unrelated to repository mutation authority. These
template workflows invoke no provider and grant no merge authority.

This leaves downstream repositories with an explicit operator step for local
policy drift. That is deliberate for v1; automatic migration or repair would
cross from distribution into mutation authority and requires a later packet.
