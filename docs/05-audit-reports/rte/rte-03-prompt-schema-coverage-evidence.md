---
id: rte-03-prompt-schema-coverage-evidence
title: Rte 03 Prompt Schema Coverage Evidence
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Rte 03 Prompt Schema Coverage Evidence (reference) for dopemux documentation
  and developer workflows.
---
# RTE-03 Prompt and Schema Coverage Evidence

- Worktree/clone: `/tmp/dopemux-rte-03-prompt-schema-coverage`
- Branch: `packet/rte-03-prompt-schema-coverage`
- Base commit: `f74dd1baf`
- Scope:
  - added missing prompt files for `C18`, `C19`, `C20`, `C21`, `G6`, and `G7`
  - registered those steps in `promptset.yaml`, `artifacts.yaml`, and `model_map.yaml`
  - created `services/repo-truth-extractor/promptsets/v4/schemas/`
  - added an initial measurable schema coverage manifest for the six-prompt tranche
- Validation target:
  - promptset lint must pass with the new steps
  - phase C/G/Q prompt truth tests must pass
  - schema directory and manifest must be present and internally consistent
- Residual risk:
  - schema rollout is an initial tranche only and is not yet wired into the runtime
  - `prompt_artifact_coverage_map.json` was not regenerated in this packet because current validation does not treat it as canonical
