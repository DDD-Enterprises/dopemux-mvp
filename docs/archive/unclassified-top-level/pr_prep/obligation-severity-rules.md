---
id: OBLIGATION_SEVERITY_RULES
title: Obligation Severity Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Obligation Severity Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Obligation Severity Rules

## Docs Severity
- **HIGH**: Missing docs when `api/` or `public/` directories are touched.
- **MEDIUM**: Missing docs for broad changes in internal logic.
- **LOW**: Docs present or change is profiled as a small fix.

## Changelog Severity
- **MEDIUM**: Missing changelog update when `CHANGELOG.md` exists and change is not trivial.
- **INFO**: Changelog updated or repo has no `CHANGELOG.md`.

## Migration Severity
- **CRITICAL**: Missing migration notes when files in `migrations/` or `schema.sql` are detected.
- **LOW**: Migration notes present.

## Linked Context Severity
- **MEDIUM**: High adjacent-work ambiguity (>40) without any external links provided in the changeset (e.g., within comments or related docs).
