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
