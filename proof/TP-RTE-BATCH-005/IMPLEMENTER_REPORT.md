# TP-RTE-BATCH-005 Implementer Report

## 1. Change summary

Repaired the OpenAI-compatible batch client path so provider result JSONL rows are parsed into `BatchResult` objects before discard-rate enforcement. The same parser is inherited by `XAIBatchClient`.

Strict batch request intent now fails closed unless the request carries an actual `json_schema` response format. When a strict request includes that schema payload, the generated batch JSONL wire body serializes `response_format.type == "json_schema"` instead of silently staying on `json_object`.

## 2. Authority used

- `AGENTS.md`
- `PROJECT.md`
- `docs/research/mcp-customization/dopemux-constraints/RULES.md`
- `docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_GAPS.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_INTERFACES.md`
- `task-packets/INDEX.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `services/repo-truth-extractor/lib/batch_clients.py`
- `services/repo-truth-extractor/lib/structured_output_contracts.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- Existing batch and strict tests under `services/repo-truth-extractor/tests/`

## 3. Files created

- `services/repo-truth-extractor/tests/test_batch_clients_integration.py`
- `task-packets/generated/TP-RTE-BATCH-005.json`
- `proof/TP-RTE-BATCH-005/PROOF.json`
- `proof/TP-RTE-BATCH-005/IMPLEMENTER_REPORT.md`

## 4. Files modified

- `services/repo-truth-extractor/lib/batch_clients.py`
- `task-packets/INDEX.md`

## 5. Behavior changes

- Added optional `BatchRequest.response_format` for callers that already have a structured-output contract payload.
- Added strict request validation in `OpenAIBatchClient.submit`: strict metadata requires `response_format.type == "json_schema"` and a schema object, otherwise submission fails before upload.
- Preserved non-strict `force_json_output` behavior as `response_format: {"type": "json_object"}`.
- Moved OpenAI-compatible result extraction back into the successful JSONL parse path.
- Kept discard/corruption threshold enforcement after all lines are parsed and evaluated.
- Counted malformed and non-object JSON lines as discarded rows.

## 6. Tests added/modified

Added `services/repo-truth-extractor/tests/test_batch_clients_integration.py` with offline fake-client coverage for:

- valid OpenAI-compatible batch result parsing
- under-threshold corrupt lines preserving valid parsed results
- over-threshold corrupt lines raising the existing BatchCorruptionError-style RuntimeError
- strict request body serialization with `json_schema`
- strict request fail-closed behavior without a schema
- non-strict `json_object` compatibility
- xAI inherited OpenAI-compatible result parsing

## 7. Validation commands and exit codes

- `python -m json.tool task-packets/generated/TP-RTE-BATCH-005.json` -> 0
- `python -m json.tool proof/TP-RTE-BATCH-005/PROOF.json` -> 0
- Task packet Draft7 schema validation -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_batch_clients_integration.py` -> 1 before fix; reproduced 5 expected blocker failures
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_batch_clients_integration.py` -> 0 after fix; 7 passed
- `python -m compileall -q services/repo-truth-extractor src/dopemux` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k "batch or strict"` -> 0; 44 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py` -> 0; 43 passed
- `rg -n "strict.*pass" services/repo-truth-extractor/lib/batch_clients.py` -> 1 expected no-match
- Scope grep for promptsets/model/routing/walker/prescan/cockpit/TUI/dependency/docs-sweep files -> 1 expected no-match
- `git diff --check` -> 0
- `pre-commit run --files services/repo-truth-extractor/lib/batch_clients.py services/repo-truth-extractor/tests/test_batch_clients_integration.py task-packets/INDEX.md task-packets/generated/TP-RTE-BATCH-005.json proof/TP-RTE-BATCH-005/PROOF.json proof/TP-RTE-BATCH-005/IMPLEMENTER_REPORT.md` -> 0

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

## 9. Commit readiness

Manual codereview of the scoped diff passed. Pre-commit passed for changed allowlist files.

## 10. Residual risks and UNKNOWNs

- Strict passthrough attestation risk is narrowed, not fully closed. This TP fixes batch client wire-payload honesty but does not rewrite `STRICT_PASSTHROUGH_ATTESTATIONS` generation.
- Existing v5 runtime avoids batching strict contract steps, so this TP verifies strict batch handling at the batch client boundary rather than through a live runner path.
- Proof files live under ignored `proof/` and must be staged with `git add -f`.
