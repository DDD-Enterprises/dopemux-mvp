---
id: RELEASE_NOTES_v0.1.0
title: Release Notes V0.1.0
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-04-13'
next_review: '2026-06-15'
prelude: Release Notes V0.1.0 (explanation) for dopemux documentation and developer
  workflows.
---
# Release Notes - v0.1.0

## Unreleased (post-v0.1.0)
- Phase S prompt rendering now supports SP template variables in the v5 runner.
- S_INT and FL_INT prompt files standardized on the `PROMPT_` filename prefix.
- Promptset audit CLI supports `--population` for Phase S, S_INT, FL_INT, prescan, and all.

## Status: VALIDATED
This release represents the first baseline of the PR Merge Specialist, validated across 5 development tranches.

### Validated Capabilities
- **Deterministic Intake**: Reliable extraction of intent from heterogeneous feedback surfaces.
- **Policy Enforcement**: Automated PR body/checklist truthfulness based on evidence.
- **Guarded Resolution**: Threads are resolved only when code or verification evidence exists.
- **Multi-Agent Alignment**: Verified instruction packs for all major LLM agents.

### Known Caveats & Limitations
- **Operational Depth**: Queue admission, retries, and CI rerun logic are structurally validated but have limited live exercise depth.
- **Cost Reporting**: Financial and usage data are currently reported as **Proxies** (1.0 units per rerun).
- **Conflict Handling**: `HIGH_RISK` conflicts are correctly identified but currently require human resolution.

### Artifacts
Evidence for this release is anchored in the `MASTER_PROOF_BUNDLE.json`.
