---
id: SKILL_MODEL
title: Skill Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Skill Model (explanation) for dopemux documentation and developer workflows.
---
# PR Prep Specialist: Skill Model

## Mission
Take a branch and turn it into a truthful, complete, reviewer-usable PR package, then hand it off to `pr-merge-specialist`.

## Core Philosophy
- **No Lies**: Every claim in the PR body or checklist must be backed by verifiable local evidence.
- **No Silent Magic**: Never automatically import stashes or sibling branches without explicit user confirmation.
- **Deterministic First**: Use shell tools and static analysis before invoking high-cost consensus or LLM arbitration.
- **Layered Validation**: Run local gates (lint, typecheck, tests) as a hard prerequisite for "Ready" status.

## Lifecycle
1. **Intake**: Detect branch identity, base branch, and worktree cleanliness.
2. **Audit**: Detect adjacent local work (stashes, sibling branches) that might be missing.
3. **Obligations**: Determine if docs, changelog, or migration notes are required by the changeset.
4. **Drafting**: Generate a complete PR body using a canonical template and identified evidence.
5. **Validation**: Run a layered gate (Deterministic -> Consensus) to confirm PR readiness.
6. **Handoff**: Create the PR/package and pass a machine-readable bundle to `pr-merge-specialist`.

## Risk Classification
- **LOW**: Docs-only, test-only, or small isolated code changes.
- **MEDIUM**: Refactors, mixed changesets, or minor config updates.
- **HIGH**: Migrations, schema changes, public API changes, or infrastructure modifications.

## Postures
- **NORMAL**: Proceed with automated preparation.
- **CAUTION**: Warn user about mixed signals or dirty worktree.
- **BLOCK**: Stop preparation due to malformed state or critical missing evidence.
- **ESCALATE**: Flag for high-risk manual review or merge-specialist arbitration.
