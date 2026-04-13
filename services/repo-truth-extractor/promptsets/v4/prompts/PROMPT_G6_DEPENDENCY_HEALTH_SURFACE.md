# PROMPT_G6

## Goal
Produce `G6` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Extract dependency health governance surfaces: declared dependency manifests, lockfiles, pinning posture, alternate dependency sources, and directly evidenced drift risks that affect reproducibility or operator safety.

## Inputs
- Source scope (scan these roots first):
  - `pyproject.toml`
  - `requirements*.txt`
  - `uv.lock`
  - `poetry.lock`
  - `package.json`
  - `services/**/pyproject.toml`
  - `services/**/requirements*.txt`
  - `.github/workflows/**`
- Upstream normalized artifacts available to this step:
  - `GOV_INVENTORY.json`
  - `GOV_PARTITIONS.json`
  - `GOV_CI_GATES.json`
  - `GOV_HYGIENE_POLICIES.json`
  - `GOV_POLICIES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DEPENDENCY_HEALTH_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"DEPENDENCY_HEALTH_SURFACE@v1","items":[...]}`
- Output contracts:
  - `DEPENDENCY_HEALTH_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G6`
    - `id_rule`: `DEPENDENCY_HEALTH_SURFACE:<stable-hash(path|package_name|issue_type)>`
    - `required_item_fields`: `id, issue_type, package_name, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `issue_type` enum:
  - `unpinned_dependency`
  - `alternate_source`
  - `lockfile_missing`
  - `manifest_duplication`
  - `version_constraint_risk`

## Extraction Procedure
1. Load governance inventory, partitions, and policy artifacts; use dependency manifests and CI files as the primary scan surface.
2. Scan `pyproject.toml`, `requirements*.txt`, and service-local manifests for dependency declarations and version constraints.
3. Scan for lockfiles such as `uv.lock`, `poetry.lock`, or equivalent and record missing lockfile situations only when the manifest is clearly active in the repo.
4. Identify unpinned or weakly pinned dependencies, direct VCS or path sources, duplicated declarations across manifests, and CI workflows that install from undeclared manifests.
5. Build deterministic IDs from `(path|package_name|issue_type)` and attach exact evidence proving the manifest line and, when relevant, the missing or alternate lockfile context.
6. Normalize items by stable sort keys, deduplicate by ID, and emit exactly `DEPENDENCY_HEALTH_SURFACE.json`.

## Evidence Rules
- Every item must include exact manifest or workflow excerpts.
- Every evidence object must include exact `path`, `line_range`, and `excerpt` keys.
- Missing lockfiles require evidence from the active manifest path plus the repo-level absence signal in the note or item context.
- Use repo-relative paths and tight line ranges.
- If package ownership is ambiguous across multiple manifests, include all relevant evidence rather than guessing the canonical owner.

## Determinism Rules
- Do not emit transient resolver output, install timestamps, or host-specific paths.
- Sort items by `(path, line_start, id)`.
- Use enum values exactly as declared for `issue_type`.
- Merge duplicates only when package name, path, and issue type resolve to the same ID.

## Anti-Fabrication Rules
- Do not mark a dependency unpinned when the manifest syntax for that ecosystem is not actually permissive in context.
- Do not infer active usage from historical or commented manifests.
- Do not claim a lockfile is missing if the repo clearly uses another pinned mechanism that covers the same manifest.
- Do not collapse separate manifests into a single record without evidence of shared ownership.

## Failure Modes
- If multiple package managers are present, emit one item per directly evidenced risk instead of inventing a unified package strategy.
- If a manifest is generated, keep the generated file as evidence and note the generation path only when visible in the repo.
- If version constraints are templated through includes or tooling, record only the resolved local file content that is actually present.
- If CI installs from a script wrapper, include the wrapper evidence and keep the dependency-health conclusion conservative.
