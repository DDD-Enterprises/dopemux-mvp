---
id: repo-cli-system-recovery-tranche-2026-05-02
title: Repo CLI/System Recovery Tranche
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-02'
prelude: Recovery report for TP-DMX-REPOHYG-007.
last_review: '2026-05-03'
next_review: '2026-08-01'
---
# Repo CLI/System Recovery Tranche

## Scope

TP-DMX-REPOHYG-007 recovers the first CLI/system item from the TP006
decision-ready queue. The recovery source is `work/pr-554-fix`; `work/pr-554`
is comparator-only.

This packet does not delete worktrees, branches, remote refs, or stashes. It
does not recover cockpit, dependency, RTE, or stash work.

## Authority

- Current execution base: `origin/main`
- Execution branch: `codex/recover-cli-system-20260502-work-pr-554-fix`
- Recovery source branch: `work/pr-554-fix`
- Comparator branch: `work/pr-554`
- Nearest merged PR evidence: PR #554, "fix(cli): harden dopemux audit surfaces"
- TP006 class: `topic-pr-ready-review`

At execution start, `git cherry -v origin/main work/pr-554-fix` showed
`98da7f5525c6dd55028fe1cbe42d68bbe6660be1` as patch-equivalent to current
`origin/main`. The patch-unique recovery commit was
`595b8e8783863754e9487e00257b57d3af217639`.

## Recovered Behavior

- MCP commands now build subprocess argv lists instead of shell command strings
  for service-scoped operations and validate requested services against
  `compose.yml` or the default MCP service set.
- CLI command failures that previously logged errors without non-zero Click
  failure now raise `click.ClickException` for code repair, code analysis,
  code-agent status, and routed MCP/status operations.
- Routing mode updates now parse and re-emit YAML deterministically while
  preserving unrelated config fields and failing closed on invalid YAML.
- Native hook registration now refuses invalid settings JSON, validates the
  shape it mutates, quotes the hook script path, writes atomically, and keeps a
  backup when replacing an existing settings file.
- Placeholder profile lifecycle commands now delegate to concrete profile
  command callbacks where present.
- Decision command registration no longer masks a self-import failure that
  implied missing decision subcommands existed.
- `dopemux-pr-merge` strategy report paths are redacted to repo-relative or
  basename strings before surfacing in operator reports.

## Excluded Work

`reports/implementation-notes.md` was intentionally excluded from the tracked
recovery. It is a generic local implementation note from the old branch, not a
current operator-facing report required for this PR.

`work/pr-554` contains unrelated cockpit/design and dependency-history commits
outside this packet. Those remain governed by the TP006 queue and later
subsystem packets.

## Validation Expectations

Required validation for this recovery:

- JSON validation for the TP007 packet and proof.
- `git range-diff origin/main...work/pr-554 origin/main...work/pr-554-fix`
- `git diff --check`
- Focused CLI tests through the locked test environment:
  `uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py`
- `uv run --frozen --extra test dopemux --help`
- `uv run --frozen --extra test dopemux-pr-merge self-check`
- `uv run --frozen --extra dev pre-commit run --files` on the packet allowlist.

Command outcomes are recorded in
`proof/repo-cli-system-recovery-tranche-2026-05-02.proof.json`.
