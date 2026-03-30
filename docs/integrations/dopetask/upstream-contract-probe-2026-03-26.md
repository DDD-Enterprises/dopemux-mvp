---
id: UPSTREAM_CONTRACT_PROBE_2026-03-26
title: Upstream Contract Probe 2026 03 26
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
prelude: Upstream Contract Probe 2026 03 26 (explanation) for dopemux documentation
  and developer workflows.
---
# Upstream Contract Probe - dopetask 0.5.x
**Date**: 2026-03-26
**Branch**: `tp-dser-001-dopetask-probe`

## Summary of Probes
Probed `dopetask` versions 0.5.1, 0.5.0, and 0.2.0 in isolated virtual environments.

### 1. version-0.5.1.txt
- **Status**: Stable.
- **Key Features**: Introduces `tp series` with `exec`, `status`, and `finalize`.
- **Finding**: CLI expects to be on `main` branch for some operations (e.g. `doctor`).

### 2. version-0.5.0.txt
- **Status**: Major release.
- **Key Features**: Introduced `series` command and `dopetask.yaml` support.
- **Finding**: Foundational series support.

### 3. version-0.2.0.txt
- **Status**: Legacy.
- **Key Features**: Current pinned version. No `series` command group found.

## CLI Surface Findings (0.5.1)
- `dopetask tp series exec TP_FILE`: Executes a JSON Task Packet in a DAG-aware workflow.
- `dopetask tp series status SERIES_ID`: Authoritative series state reporter.
- `dopetask tp series finalize SERIES_ID`: Finalizes a series into a PR.

## Artifact Surface
- `.dopetask/project.json` is the root anchor.
- `SERIES_STATE.json` (expected in draft plan) is consistent with the `status` command output model.
