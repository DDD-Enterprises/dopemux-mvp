---
id: mac-system-data-scrubber
title: Mac System Data Scrubber
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-08-01'
prelude: Required-tool macOS system-data diagnosis and cleanup feature.
---
# Mac System Data Scrubber

`dopemux system-data` diagnoses and plans macOS System Data cleanup with a
required external toolchain:

```bash
brew install dust duf btop procs gdu dua-cli ncdu
```

The command family is macOS-only and fails closed when required tools are
missing. The tools provide evidence and visibility; Dopemux owns cleanup
policy, mutation, manifests, restore posture, and proof.

## Commands

- `dopemux system-data doctor`
- `dopemux system-data scan`
- `dopemux system-data report`
- `dopemux system-data plan`
- `dopemux system-data clean`
- `dopemux system-data restore`
- `dopemux system-data tui`

`clean` defaults to dry-run. Dry-run does not create manifests or mutate the
filesystem. Real mutation requires `--execute --yes`.

## Required Tool Roles

- `duf --json`: mounted-volume and free-space snapshot.
- `dust -j`: fast ranked target-tree discovery.
- `gdu`: deep candidate scan, supporting GNU `du` fallback when that is the installed `gdu`.
- `ncdu`: review artifact for broad roots.
- `dua`: developer-cache aggregate evidence.
- `procs --json`: process preconditions.
- `btop`: launchable live monitor from the TUI.

## TUI Screens

The Textual TUI exposes Overview, Findings, Plan, Processes, Monitor, Execute,
and Restore screens. The Processes screen is backed by `procs`; Monitor launches
`btop`; Execute remains dry-run-first and points real mutation back through the
audited CLI executor.

## Safety Model

Safe-clear classes include Messages tmp, Messages previews, CloudKit cache,
Xcode DerivedData, and package-manager caches.

Review-first classes include Messages attachments, Xcode archives, iOS backups,
Downloads, large media, and simulator runtimes.

Tool-mediated classes include Docker prune, Homebrew cleanup, and unavailable
simulator cleanup via `xcrun simctl delete unavailable`.

Blocked classes include protected system paths, Apple databases, raw Docker VM
deletion, SIP/TCC assets, and broad Messages attachment deletion.

## Proof

The bundled proof artifact lives at:

```text
proof/TP-OPS-MAC-SCRUBBER-001/PROOF.json
```

It records tool preflight, implementation notes, validation state, docs, and
acceptance mapping.

## Known Limitations

- V1 does not auto-install Homebrew tools.
- V1 does not mutate protected system paths.
- V1 does not restore quarantined data automatically without review.
- Full Disk Access cannot be proven absolutely from userspace; the tool reports
  confidence and visibility warnings.
