---
id: DETERMINISTIC_GATE_RULES
title: Deterministic Gate Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Deterministic Gate Rules for pr-prep-specialist layered validation.
---
# Deterministic Gate Rules

The PR Prep Specialist relies on deterministic local gates before considering consensus or human escalation. These gates represent hard verifiable truths about the local repository state.

## Gate Categories
1. **WORKTREE_CLEANLINESS**: The worktree must not contain uncommitted changes that overlap with the branch or introduce ambiguity.
2. **PRECOMMIT**: The repository's configured `pre-commit` hooks must pass.
3. **LINT / TYPECHECK / TARGETED_TESTS**: If configured locally, these checks must pass.
4. **TEMPLATE_SUFFICIENCY**: The drafted PR body must meet structural requirements.
5. **DOCS_PRESENCE**: If docs are required, they must exist.
6. **CHANGELOG_PRESENCE**: If a changelog is required, it must exist.
7. **MIGRATION_NOTE_PRESENCE**: If migrations are present, notes must exist.
8. **LINKED_CONTEXT_SUFFICIENCY**: Required context (issues/ADRs) must be present.

## Gate Statuses
- **PASS**: The check ran and passed.
- **FAIL**: The check ran and failed.
- **PARTIAL**: Some part of the check ran, or evidence is mixed.
- **NOT_RUN**: The check did not run (due to config or earlier blocking states).

## Blocker Guidance
A single `FAIL` in WORKTREE_CLEANLINESS, PRECOMMIT, TEMPLATE_SUFFICIENCY, DOCS_PRESENCE, CHANGELOG_PRESENCE, or MIGRATION_NOTE_PRESENCE forces a blocking decision (`BLOCKED_*`), preventing PR creation unless policy explicitly allows a draft-only fallback.
