---
id: mac-system-data-scrubber-safety-model
title: Mac System Data Scrubber Safety Model
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-08-01'
prelude: Safety and truthfulness model for macOS system-data cleanup.
---
# Mac System Data Scrubber Safety Model

## Risk Classes

- `safe_clear`: rebuildable or temporary data that may be deleted with low risk.
- `rebuildable_cache`: cache data that can be regenerated, with rebuild cost.
- `tool_mediated`: cleanup must be routed through a domain tool.
- `review_first`: likely user-important or release evidence; no broad deletion.
- `blocked`: dangerous, protected, or unsupported.

## Mutation Rules

`clean` defaults to dry-run. Real mutation requires:

```bash
dopemux system-data clean --execute --yes
```

Dry-run emits in-memory execution records only; it does not create manifest
files or touch the filesystem.

External tools provide evidence. Dopemux performs mutation so manifests and
proof remain deterministic.

## Reclaim Truthfulness

Same-volume quarantine does not free disk capacity. It may improve rollback
comfort, but expected reclaim is reported as zero unless data is deleted or
moved to another filesystem.

## Blocked Classes

Dopemux does not mutate:

- protected system paths
- Apple databases
- raw Docker VM/container backing files
- SIP/TCC-protected assets
- Messages attachments in broad mode

## Tool-Mediated Cleanup

Docker cleanup uses Docker CLI prune flows when Docker is reachable.
Simulator cleanup uses `xcrun simctl delete unavailable`.
Homebrew/package caches are treated as rebuildable and explicit.
