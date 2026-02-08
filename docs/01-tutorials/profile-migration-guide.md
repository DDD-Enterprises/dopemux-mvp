---
id: PROFILE_MIGRATION_GUIDE
title: Profile Migration Guide
type: tutorial
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: Step-by-step migration guide from legacy/manual MCP setups to Dopemux profile-managed workflows.
---
# Profile Migration Guide

## Goal

Move from ad-hoc MCP selection to repeatable Dopemux profile workflows without breaking current behavior.

## Step 1: Snapshot Current State

Capture your current settings and active profile marker:

```bash
cat ~/.claude/settings.json
cat .dopemux/active_profile 2>/dev/null || true
```

## Step 2: Inspect Available Profiles

```bash
dopemux profile list
dopemux profile show developer
```

If no profile marker exists, confirm what Dopemux detects:

```bash
dopemux profile current
```

## Step 3: Create a Personalized Baseline

Analyze historical work patterns:

```bash
dopemux profile analyze-usage --days 90 --max-commits 500
```

Generate a profile from those patterns:

```bash
dopemux profile init
```

## Step 4: Apply Safely

Apply profile with default safeguards (config update + rollback-safe flow):

```bash
dopemux profile apply developer
```

Switch with full orchestration:

```bash
dopemux switch developer --restart-claude --save-session --restore-context
```

## Step 5: Enable Guided Automation

Enable auto-detection:

```bash
dopemux profile auto-enable
```

Adjust suggestion sensitivity when needed:

```bash
dopemux profile auto-enable --threshold 0.9
```

## Step 6: Verify Stability

Validate profiles:

```bash
dopemux profile validate --all
```

Review usage and optimization signals:

```bash
dopemux profile stats --days 30
```

## Migration Troubleshooting

1. `Profile not found`: run `dopemux profile list` and check profile names.
2. `Apply failed`: rerun with `--no-apply-config` to isolate config mapping issues.
3. `Unexpected suggestions`: raise threshold with `profile auto-enable --threshold`.
4. `Slow switching`: tune options (`--no-restore-context`, no restart) and inspect timing output.
