---
id: DOCS_AND_CHANGELOG_POLICY
title: Docs And Changelog Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Docs And Changelog Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Docs and Changelog Policy

## Documentation Obligation
Documentation is required when a PR introduces changes to the public surface area of the codebase.
- **Trigger**: Changes in `api/`, `public/`, `client/`, or `server/` directories.
- **Trigger**: Change profile is `PUBLIC_SURFACE_CHANGE`.
- **Satisfaction**: Presence of changes in `docs/` or `.md` files (excluding `CHANGELOG.md`).

## Changelog Obligation
A changelog entry is required for any non-trivial change in repositories that maintain a `CHANGELOG.md` file.
- **Trigger**: `CHANGELOG.md` exists in the repo root.
- **Exception**: Changes profiled as `SMALL_CODE_CHANGE`, `REFACTOR`, `DOCS_ONLY`, or `TEST_ONLY` may skip changelog updates.
- **Satisfaction**: `CHANGELOG.md` is included in the PR changeset.

## Release Fragments
For repositories using fragment-based changelogs (e.g., `newsfragments/` or `changelog.d/`), the obligation is marked as `UNKNOWN_REQUIRES_REVIEW` to prompt manual verification.
