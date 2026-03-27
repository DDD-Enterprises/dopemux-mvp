# PROMPT_S12

## Goal
Produce `S12` synthesis output for phase `S` with deterministic structure and explicit normalization guarantees.
Generate a regression-tracking stability signature from canonical synthesis artifacts so operators can compare runs without leaking secrets or unstable metadata.

## Inputs
- Required upstream artifacts:
  - `S0_OPUS_ARCHITECTURE_SYNTHESIS.md`
  - `S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md`
  - `S2_DECISION_DOSSIER.md`
  - `S3_ARCH_PROOF_HOOKS.md`
  - `S4_TRUTH_PACK_INDEX.md`
  - `S5_DECISION_GRAPH.md`
  - `S6_LEANTIME_ANALYSIS.md`
- Optional upstream artifacts:
  - `S7_DEDUPE_SORT.json`
  - `S8_DRIFT_CHECK.json`
  - `S9_PROMOTION_READINESS.json`
  - `S10_API_SURFACE_REFERENCE.md`
  - `S11_DOCUMENTATION_GENERATION.md`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only upstream synthesis artifacts. Do not rescan repository source trees directly.

## Outputs
- `S12_STABILITY_SIGNATURE.json`

## Schema
- Artifact kind: deterministic JSON object for regression tracking.
- Canonical writer: `S12`
- Required output content contracts:
  - `S12_STABILITY_SIGNATURE.json`
    - `status`: `OK` or `FAIL_CLOSED`
    - `normalization`: object with `sorted_keys`, `stable_lists`, and `notes`
    - `hashes`: array of `{section, hash_alg, hash}`
    - `counts`: array of `{name, count}`
    - `inputs`: sorted list of upstream artifact names that contributed to the signature
- Required normalization assumptions:
  - sort object keys lexicographically
  - preserve list order unless stable identifiers allow a deterministic sort
  - use `sha256` for emitted hashes

## Extraction Procedure
1. Load the required upstream synthesis artifacts in fixed order and note which optional artifacts are present.
2. Normalize each input into a canonical text or JSON representation that excludes unstable runtime metadata.
3. Produce section-level hashes for each included artifact and a top-level aggregate signature derived from the normalized content.
4. Count major structures such as included artifacts, hashed sections, and redacted fields, then emit them in deterministic order.
5. If any required artifact is missing or normalization cannot be applied safely, set `status` to `FAIL_CLOSED`, explain the gap in `normalization.notes`, and still emit a deterministic payload.
6. Emit exactly `S12_STABILITY_SIGNATURE.json` and no additional files.

## Evidence Rules
- The output must cite the upstream artifact filenames that contributed to each signature component via the `inputs` list and `section` labels.
- Do not claim a hash or count for an artifact that was not loaded from the declared input set.
- If an optional artifact is absent, omit it from `inputs` and explain the absence in `normalization.notes`.
- When normalization fails for a required artifact, preserve the artifact name and the failure reason in deterministic text.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `inputs` lexicographically.
- Sort `hashes` by `section`.
- Sort `counts` by `name`.
- Use stable placeholder text for missing artifacts and normalization failures so repeated runs with the same gaps produce identical bytes.

## Anti-Fabrication Rules
- Do not invent upstream artifacts, signatures, counts, or normalization success.
- Do not include secrets, tokens, or machine-local paths in emitted hashes or notes.
- Do not claim list stability when the source lacks deterministic identifiers; mark the output `FAIL_CLOSED` instead.
- Do not emit convenience metadata outside the declared schema.

## Failure Modes
- Missing required synthesis artifact: emit `FAIL_CLOSED`, include the missing artifact name in `normalization.notes`, and continue with the remaining declared inputs.
- Unsupported input shape: emit `FAIL_CLOSED`, preserve the artifact name, and omit unverifiable hashes.
- Empty but present input: include the artifact in `inputs`, emit a deterministic empty-content hash, and note the condition.
- Mixed JSON and markdown inputs: normalize each with its appropriate deterministic serializer before hashing.
