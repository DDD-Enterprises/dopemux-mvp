# TP-RTE-BATCH-E2E-006 Implementer Report

## 1. Change summary

Wired v5 strict batch request construction to build and attach the existing structured-output `json_schema` response format before batch upload/submission. Strict batch construction now fails closed when no valid schema can be resolved or when a strict request would downgrade to `json_object`.

## 2. Authority used

- User-provided TP-RTE-BATCH-E2E-006 implementation prompt
- `AGENTS.md`
- `PROJECT.md`
- `docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md`
- `task-packets/INDEX.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `proof/TP-RTE-BATCH-005/PROOF.json`
- `proof/TP-RTE-BATCH-005/IMPLEMENTER_REPORT.md`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/lib/batch_clients.py`
- `services/repo-truth-extractor/lib/structured_output_contracts.py`
- `services/repo-truth-extractor/lib/phase_contract_map.py`
- Existing strict/batch tests under `services/repo-truth-extractor/tests/`

## 3. Files created

- `services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py`
- `task-packets/generated/TP-RTE-BATCH-E2E-006.json`
- `proof/TP-RTE-BATCH-E2E-006/PROOF.json`
- `proof/TP-RTE-BATCH-E2E-006/IMPLEMENTER_REPORT.md`

## 4. Files modified

- `services/repo-truth-extractor/run_extraction_v5.py`
- `task-packets/INDEX.md`

## 5. Behavior changes

- Added `build_v5_batch_request(...)` in `run_extraction_v5.py` as the v5 batch request construction seam used by the real batch branch.
- Added `_resolve_batch_route_override(...)` so strict 2-tuple route ladders are widened to 3-tuples when a `batch_provider` override selects one.
- Removed the `not strict_contract_required` exclusion from the v5 batch path.
- Strict batch construction uses `route_entries_for_stage(...)` and `build_provider_step_contract_output(...)` to populate `BatchRequest.response_format`.
- Strict batch construction requires `response_format.type == "json_schema"`, a schema object, `json_schema.strict == true`, and non-empty artifact schema metadata.
- Strict batch request metadata sets `strict=true`, preserving the TP-RTE-BATCH-005 batch-client fail-closed boundary.
- Non-strict OpenAI-compatible batch behavior remains unchanged: no `response_format` is emitted when `force_json_output` is false.

## 6. Tests added/modified

Added `services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py` with offline coverage for:

- strict v5 batch request construction populating `BatchRequest.response_format`
- fake OpenAI-compatible upload JSONL containing `response_format.type == "json_schema"`
- strict missing schema failing before fake upload/submission
- strict `json_object` downgrade rejection
- strict 2-tuple ladder provider override widening via `PROVIDER_API_KEY_ENV`
- non-strict OpenAI-compatible behavior preserving omitted `response_format`

## 7. Validation commands and exit codes

- `python -m json.tool task-packets/generated/TP-RTE-BATCH-E2E-006.json` -> 0
- `python -m json.tool proof/TP-RTE-BATCH-E2E-006/PROOF.json` -> 0
- Task packet Draft7 schema validation -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py` -> 1 during intermediate guard correction
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py` -> 0; 5 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_batch_clients_integration.py` -> 0; 7 passed
- `python -m compileall -q services/repo-truth-extractor src/dopemux` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k "batch or strict"` -> 0; 49 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py` -> 0; 43 passed
- Forbidden-scope diff grep -> 1 expected no-match
- Strict batch exclusion/downgrade grep -> 1 expected no-match
- Attestation writer diff grep -> 1 expected no-match
- `git diff --check` -> 0
- `pre-commit run --files services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py task-packets/INDEX.md task-packets/generated/TP-RTE-BATCH-E2E-006.json proof/TP-RTE-BATCH-E2E-006/PROOF.json proof/TP-RTE-BATCH-E2E-006/IMPLEMENTER_REPORT.md` -> 0

## 8. Safety boundary confirmation

- No provider calls were run.
- No live extraction was run.
- No external batch jobs were submitted.
- No real provider files were retrieved.
- No sync extraction path was changed.
- No promptsets were touched.
- No model routing files were touched.
- No walker/prescan files were touched.
- No docs sweep was included.
- No dependency files were changed.
- No attestation writer rewrite was performed.

## 9. Commit readiness

Manual diff review passed. Pre-commit passed for changed allowlist files. Proof files are under ignored `proof/` and must be staged with `git add -f`.

## 10. Residual risks and UNKNOWNs

- `STRICT_PASSTHROUGH_ATTESTATIONS` writer remains out of scope for TP-RTE-STRICT-ATTESTATION-007.
- F3-HIGH-2 is `NARROWED_FURTHER`, not closed, because attestation generation is not proven to derive from actual wire/runtime payload.
- No live provider batch job was submitted; validation uses fake OpenAI-compatible transport only.
- `GeminiBatchClient` still does not serialize `response_format` directly. Current strict route logic excludes Gemini strict routes, and this TP verified the OpenAI-compatible wire path.
- `task-packets/INDEX.md` still lists TP-RTE-BATCH-005 as Active despite PR #614 being present on main; this TP only added the new active packet row.
