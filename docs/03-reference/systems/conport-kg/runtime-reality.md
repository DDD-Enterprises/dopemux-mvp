---
id: conport-kg-runtime-reality
title: ConPort KG Runtime Reality
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Evidence-backed runtime status for conport-kg, including the absence of repo-proven active source and deployment surfaces.
---
# ConPort KG Runtime Reality

## Result

`conport-kg` is not repo-proven runtime-real in the current workspace.

## Evidence

- `services/conport_kg/` contains pycache residue, not active source files or a runnable entrypoint
- `docker/conport-kg/` contains documentation and example environment configuration, but no current repo-proven deployment artifact
- no active compose wiring or registry entry establishes a live `conport-kg` runtime

## Callable surface status

Repo-proven callable surfaces: `0`

Any endpoint claims in READMEs or historical extraction artifacts are treated as non-authoritative until a live runtime is proven.

## Runtime posture for current architecture

Selected posture:

- `quarantined_not_runtime_real`
