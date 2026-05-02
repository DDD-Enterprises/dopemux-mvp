---
id: mac-system-data-scrubber-operator-guide
title: Mac System Data Scrubber Operator Guide
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-08-01'
prelude: Operator guide for safe macOS system-data cleanup.
---
# Mac System Data Scrubber Operator Guide

## Setup

Install the required toolchain:

```bash
brew install dust duf btop procs gdu dua-cli ncdu
```

Then run:

```bash
dopemux system-data doctor
```

If any tool is missing, the command fails and repeats the install command. No
automatic installation is performed.

## Normal Flow

```bash
dopemux system-data scan
dopemux system-data report --json
dopemux system-data plan
dopemux system-data clean --dry-run
```

Dry-run prints execution records without writing manifests or touching the
target filesystem.

Only execute after inspecting the plan:

```bash
dopemux system-data clean --execute --yes --target clear-safe-path
```

## Interactive Flow

```bash
dopemux system-data tui
```

Use the TUI to inspect findings, plan groups, process preconditions, and the
live `btop` monitor. Execution remains explicit and dry-run-first.

## Critical Disk Flow

When disk pressure is critical, same-volume quarantine is shown as zero reclaim.
Dopemux may prefer delete-in-place for safe-clear classes, but review-first and
blocked classes remain protected.

## Messages Scenario

Large `~/Library/Containers/com.apple.MobileSMS/Data/tmp` is safe-clear when
Messages is closed. `~/Library/Messages/Attachments` is review-first and is not
broad-deleted.

## Docker Scenario

Docker cleanup is tool-mediated. If Docker is reachable, Dopemux plans Docker
CLI prune flows. Raw Docker Desktop VM deletion is blocked by default.

## Restore

List manifests:

```bash
dopemux system-data restore --list
```

V1 records restore evidence and blocks non-reviewed automatic restore.
