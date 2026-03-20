---
id: PATH_SIGNAL_RULES
title: Path Signal Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Path Signal Rules (explanation) for dopemux documentation and developer workflows.
---
# Path Signal Rules

## Signals for Docs
- `api/`
- `public/`
- `client/`
- `server/`
- `examples/`
- `tutorials/`

## Signals for Changelog
- `CHANGELOG.md`
- `newsfragments/`
- `changelog.d/`

## Signals for Migrations
- `migrations/`
- `schema.sql`
- `alembic/`
- `flyway/`

## Signals for Linked Context
- Any file matching `ADR-*.md`
- Changes in `docs/adr/`
- Presence of issue patterns like `#123` or `PROJ-123` in commit messages or changed files (future enhancement).
