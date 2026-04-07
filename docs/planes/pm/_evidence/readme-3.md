---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# PM Plane Evidence Bundles

This folder stores raw, verbatim evidence captured during PM Plane phases.

## Naming convention
- Bundle name: PM-INV-00, PM-INV-01, PM-FRIC-01, etc.
- Outputs live under:
- docs/planes/pm/_evidence/<BUNDLE>.outputs/
- Command ledgers may live beside the bundle:
- docs/planes/pm/_evidence/<BUNDLE>.commands.txt
- Current authority bundle:
- docs/planes/pm/_evidence/PM-AUTH-01.outputs/
- docs/planes/pm/_evidence/PM-AUTH-01.commands.txt
- Runtime-truth summaries may also live in service-specific folders such as:
- docs/planes/pm/_evidence/task-orchestrator-runtime-truth/
- docs/planes/pm/_evidence/leantime-runtime-truth/
- docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/

## Rules
- Store verbatim command outputs only.
- Do not summarize inside outputs.
- If output is large, split into numbered files:
- 01_baseline.txt
- 02_search.txt
- 03_task_orchestrator_models.txt
- etc.

## What counts as evidence
- file excerpts with line ranges (preferred)
- command output with exact command shown
- explicit absence: 0 hits + command
- runtime-truth summary docs that cite verbatim outputs from a sibling `.outputs/` bundle

## Quarantine
quarantine/** is excluded by default to prevent stale session artifacts from polluting evidence.
Include it only when explicitly investigating provenance drift.
