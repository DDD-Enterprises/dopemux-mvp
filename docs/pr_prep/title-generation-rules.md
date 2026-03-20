---
id: TITLE_GENERATION_RULES
title: Title Generation Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Title Generation Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Title Generation Rules

## Primary Rule
The PR title must be concise, descriptive, and accurately reflect the dominant change in the branch. It must not be a vague copy of the last commit message if that message is poor.

## Structure
`[Type/Scope]: Short description`

## Determination Logic
1. **Type**: Derived from the change profile (e.g., `DOCS_ONLY` -> `docs:`, `SMALL_CODE_CHANGE` -> `feat:` or `fix:` depending on branch name convention).
2. **Scope**: Extracted from the branch name or the most heavily modified directory.
3. **Description**: A human-readable summary of the primary change.

## Alternate Titles
Generate up to three alternate titles that highlight different aspects of the changeset (e.g., if a PR is mostly refactoring but includes a bug fix, provide an alternate title highlighting the fix).
