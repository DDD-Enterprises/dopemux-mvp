---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# UPGRADES (Legacy Docs Only)

`UPGRADES/` is now a legacy documentation namespace.

## Policy

- Do not add executable code, scripts, or runtime assets under `UPGRADES/`.
- Keep historical markdown reports and runbooks as archival evidence.
- New active extraction implementation lives under `services/repo-truth-extractor/`.

## Canonical Active Paths

- Service root: `services/repo-truth-extractor/`
- CLI group: `dopemux extractor ...`
- Engine selector flag: `--engine-version {v3|v4}`
- Output roots:
  - `extraction/repo-truth-extractor/v3/`
  - `extraction/repo-truth-extractor/v4/`

Historical filenames containing `UPGRADES` are intentionally preserved.
