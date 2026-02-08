---
id: PROFILE_USER_GUIDE
title: Profile User Guide
type: tutorial
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: End-to-end tutorial for creating, applying, auto-detecting, and tuning Dopemux profiles using current CLI behavior.
---
# Profile User Guide

## 1. Launch With a Profile

Start Dopemux with an explicit profile:

```bash
dopemux start --profile developer
```

Preview startup behavior without launching:

```bash
dopemux start --profile developer --dry-run
```

## 2. Discover and Inspect Profiles

List profiles:

```bash
dopemux profile list
```

Show profile details:

```bash
dopemux profile show developer
```

Show current active profile marker:

```bash
dopemux profile current
```

If no marker exists, `profile current` attempts to detect the active profile from `~/.claude/settings.json`.

## 3. Apply and Switch Profiles

Apply profile marker only:

```bash
dopemux profile apply developer --no-apply-config
```

Apply profile and update Claude config (default):

```bash
dopemux profile apply developer
```

Full switch flow with context save/restore and restart:

```bash
dopemux switch developer --restart-claude --save-session --restore-context
```

Useful switch flags:

1. `--no-save-session`: skip pre-switch context save.
2. `--no-restore-context`: skip post-switch context restore.
3. `--target-seconds <n>`: warn if total switch duration exceeds target.

## 4. Auto-Detection and Suggestions

Enable auto-detection suggestions:

```bash
dopemux profile auto-enable
```

Tune defaults:

```bash
dopemux profile auto-enable --check-interval 300 --threshold 0.85
```

Check status:

```bash
dopemux profile auto-status
```

Disable:

```bash
dopemux profile auto-disable
```

Suggestion prompt options are `y`, `N` (default), and `never`.

## 5. Create and Maintain Profiles

Generate a profile from git usage patterns:

```bash
dopemux profile init
```

Analyze patterns without writing a profile:

```bash
dopemux profile analyze-usage --days 90 --max-commits 500
```

Create a profile with the interactive manager command:

```bash
dopemux profile create my-custom --interactive
```

Copy, edit, and archive:

```bash
dopemux profile copy developer developer-quiet
dopemux profile edit developer-quiet
dopemux profile delete developer-quiet
```

## 6. Read Analytics and Recommendations

View profile usage analytics:

```bash
dopemux profile stats --days 30
```

`profile stats` includes:

1. Switch volume and accuracy.
2. Average switch duration and MCP density.
3. Time-of-day heatmap.
4. Generated optimization recommendations.

Recommendations are archived in ConPort category `profile_optimization_recommendations`.
