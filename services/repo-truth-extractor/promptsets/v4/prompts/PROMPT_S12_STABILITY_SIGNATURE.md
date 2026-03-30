# PROMPT_S12

## Goal
Produce `S12` stability-signature output for phase `S` with deterministic structure, explicit evidence anchors, and fail-closed behavior suitable for regression tracking.
This step does not perform broad repository discovery. It computes a reproducible signature from supplied canonical phase artifacts and emits only the declared JSON artifact.

## Inputs
- Required upstream synthesis artifacts:
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`
  - `S2_DECISION_DOSSIER.md`
  - `S3_ARCH_PROOF_HOOKS.md`
  - `S4_TWO_PLANE_ARCHITECTURE.md`
  - `S5_TASK_ORCHESTRATOR.md`
  - `S6_LEANTIME_SYNTHESIS.md`
  - `S7_OVERSEER_AGENT_FLOW_DESIGN.md`
  - `S8_ARCHITECTURE_DIAGRAMS.md`
  - `S9_DEPENDENCY_GRAPH_SUMMARY.md`
  - `S10_API_SURFACE_REFERENCE.md`
  - `S11_DOCUMENTATION_GENERATION.md`
- Optional supporting artifacts:
  - `PROOF_PACK.md`
  - `FREEZE_README.md`
  - `CONFLICT_LEDGER.md`
  - `RISK_REGISTER_TOP20.md`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Operate only on supplied artifacts and canonicalized content. Do not scan the repository directly.

## Outputs
- `S12_STABILITY_SIGNATURE.json`

## Schema
- Output contract:
  - `S12_STABILITY_SIGNATURE.json`
    - `kind`: `json_item_list`
    - `canonical_writer_step_id`: `S12`
    - `merge_strategy`: `itemlist_by_id`
    - `required_registry_fields`: `id, path, line_range`
- Emit exactly one item in `items`:
```json
{
  "schema": "S12_STABILITY_SIGNATURE@v1",
  "items": [
    {
      "id": "S12_STABILITY_SIGNATURE:root",
      "path": "phase:S",
      "line_range": [1, 1],
      "status": "OK",
      "normalization": {
        "sorted_keys": true,
        "stable_lists": true,
        "notes": "Normalization rules applied to canonical synthesis inputs."
      },
      "hashes": [
        {
          "section": "root",
          "hash_alg": "sha256",
          "hash": "<hex>"
        }
      ],
      "counts": [
        {
          "name": "artifacts",
          "count": 0
        }
      ],
      "evidence": [
        {
          "path": "services/repo-truth-extractor/promptsets/v4/promptset.yaml",
          "line_range": [1080, 1085],
          "excerpt": "step_id: S12"
        }
      ]
    }
  ]
}
```
- If normalization cannot be applied safely, emit the same structure with `status: "FAIL_CLOSED"` and an evidence-backed explanation in `normalization.notes`.

## Extraction Procedure
1. Load the required upstream synthesis artifacts and derive the canonical input set for the signature.
2. Normalize the canonical input deterministically:
   - sort object keys lexicographically
   - preserve list order unless stable IDs exist; when they do, sort by stable ID
   - normalize whitespace consistently before hashing
3. Compute section hashes and aggregate counts from the normalized canonical input set.
4. Emit exactly one JSON artifact with the declared schema and evidence anchors for the source set used.
5. If any required input is missing or normalization rules cannot be applied safely, emit `FAIL_CLOSED` instead of guessing.
6. Legacy Context is intent guidance only and is never evidence.

## Evidence Rules
- Every load-bearing field must be supported by at least one evidence object with:
  - `path`
  - `line_range`
  - `excerpt`
- Evidence must point to supplied upstream artifacts or promptset/registry metadata used to define the canonical input set.
- Do not cite synthetic or inferred sources.
- If an input artifact is missing, cite the promptset/registry evidence for the expected artifact and mark the output `FAIL_CLOSED`.

## Determinism Rules
- Do not include `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Hash algorithm is always `sha256`.
- Sort object keys lexicographically before hashing.
- Reorder lists only when a stable sort key exists; otherwise preserve canonical upstream order.
- Output byte content must be reproducible for the same canonical inputs and configuration.

## Anti-Fabrication Rules
- Do not invent hashes, counts, or normalization decisions.
- Do not claim an input artifact was included if it was not present in the supplied set.
- Do not infer missing canonical content from filenames or neighboring steps.
- If required inputs are incomplete, emit `FAIL_CLOSED` with explicit evidence-backed gaps.

## Failure Modes
- Missing required synthesis artifact: emit `FAIL_CLOSED` with evidence of the missing expected input.
- Unstable list ordering with no stable key: preserve canonical order and record the rule in `normalization.notes`.
- Non-JSON canonical source ambiguity: hash the normalized canonical text representation and cite the exact source artifact.
- Conflicting canonical inputs: keep `FAIL_CLOSED` and document the contradiction with evidence.
