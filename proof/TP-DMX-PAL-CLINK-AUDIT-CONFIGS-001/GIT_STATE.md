# Git State

## Repo

- Path: `/Users/hue/.codex/worktrees/792d/dopemux-mvp`
- Remote: `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- Branch: `codex/pal-clink-audit-configs-001`
- Base HEAD: `17d3fe3bf31dc7020b25daf27894500b1368d95d`

## Status

Intent-to-add was applied for new files so `git diff --stat` and `git diff --name-only` include the full proof/config/test/task packet scope.

`proof/*` is ignored by `.gitignore`, so proof artifacts require force-staging for commit. The local PAL `.venv` created for validation is also ignored and is not part of the commit.
