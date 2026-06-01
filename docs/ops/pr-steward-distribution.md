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
