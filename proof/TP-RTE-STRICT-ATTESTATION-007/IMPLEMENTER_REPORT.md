# TP-RTE-STRICT-ATTESTATION-007 Implementer Report

## 1. Change summary

- Added strict passthrough runtime evidence summaries from BatchRequest, constructed request, and fake wire JSONL payload rows.
- Updated `STRICT_PASSTHROUGH_ATTESTATIONS` generation to V2 with explicit `VERIFIED`, `UNVERIFIED`, `FAILED`, `UNKNOWN`, and `NOT_APPLICABLE` truth states.
- Removed the unsafe synthesized OpenRouter strict passthrough bypass for explicit and benchmark selected routes outside primary contract proof.
- Addressed post-PR review feedback by classifying `selected: false` strict-route misses as `FAILED` before any `NOT_APPLICABLE` fallback, including rows with no `strict_required` field and empty attempts.
- Applied targeted INDEX hygiene for TP-RTE-BATCH-005, TP-RTE-BATCH-E2E-006, and this packet.

## 2. Authority used

- User-provided TP-RTE-STRICT-ATTESTATION-007 implementation prompt
- `AGENTS.md`
- `PROJECT.md`
- `docs/research/mcp-customization/dopemux-constraints/RULES.md`
- `docs/research/mcp-customization/dopemux-constraints/PROJECT.md`
- `docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md`
- `task-packets/INDEX.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/lib/batch_clients.py`
- `services/repo-truth-extractor/lib/structured_output_contracts.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py`
- `services/repo-truth-extractor/tests/test_batch_clients_integration.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`

## 3. Files created

- `services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py`
- `task-packets/generated/TP-RTE-STRICT-ATTESTATION-007.json`
- `proof/TP-RTE-STRICT-ATTESTATION-007/PROOF.json`
- `proof/TP-RTE-STRICT-ATTESTATION-007/IMPLEMENTER_REPORT.md`

## 4. Files modified

- `services/repo-truth-extractor/run_extraction_v5.py`
- `task-packets/INDEX.md`

## 5. Behavior changes

- `strict_passthrough_verified` in the attestation artifact is now true only when observed runtime/wire/construction evidence proves `response_format.type == "json_schema"`, `json_schema` exists, `json_schema.strict is true`, and a schema hash exists.
- Static route claims are retained as `route_strict_passthrough_claim` and `route_strict_capable_claim` rather than promoted to verification.
- Missing selected strict routes are reported as `FAILED` with `no_selected_strict_route`, not `NOT_APPLICABLE`, even if the attestation row has no attempts.
- Explicit/benchmark OpenRouter selected route synthesis now uses primary contract proof when present; otherwise strict capability fails closed.
- Gemini strict routes remain failed/excluded, not verified.

## 6. Tests added/modified

- Added `services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py`, including post-review coverage for selected:false strict-route misses with no attempts.

## 7. Validation commands and exit codes

- `python -m json.tool task-packets/generated/TP-RTE-STRICT-ATTESTATION-007.json` -> 0
- `python -m json.tool proof/TP-RTE-STRICT-ATTESTATION-007/PROOF.json` -> 0
- `python -c "import json, pathlib; from jsonschema import Draft7Validator; schema=json.loads(pathlib.Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text()); doc=json.loads(pathlib.Path('task-packets/generated/TP-RTE-STRICT-ATTESTATION-007.json').read_text()); errs=sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: e.path); [print('/'.join(map(str,e.path)) + ': ' + e.message) for e in errs]; raise SystemExit(0 if not errs else 1)"` -> 0
- `python -m compileall -q services/repo-truth-extractor src/dopemux` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py` -> 0, 5 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py` -> 0, 7 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_batch_clients_integration.py` -> 0, 7 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k "batch or strict"` -> 0, 56 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py` -> 0, 43 passed
- `git diff --check` -> 0
- `rg -n "strict_passthrough_verified=True|strict_passthrough_verified = True" services/repo-truth-extractor/run_extraction_v5.py` -> 1, no matches
- `pre-commit run --files services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py task-packets/INDEX.md task-packets/generated/TP-RTE-STRICT-ATTESTATION-007.json proof/TP-RTE-STRICT-ATTESTATION-007/PROOF.json proof/TP-RTE-STRICT-ATTESTATION-007/IMPLEMENTER_REPORT.md` -> 0

## 8. Safety boundary confirmation

- live provider calls: not run
- live extraction runs: not run
- external batch jobs: not submitted
- real provider files: not retrieved
- sync behavior broadening: no broadening; only metadata evidence propagation
- promptsets changed: no
- model routing broad edit: no
- walker/prescan changed: no
- docs sweep: no
- dependency files changed: no

## 9. F3-HIGH-2 classification

CLOSED. Evidence: V2 strict passthrough attestations require observed runtime/wire/construction evidence for VERIFIED, intent-only strict claims are UNVERIFIED, missing selected strict routes are FAILED, synthesized OpenRouter passthrough proof is no longer hardcoded, and focused plus existing strict/batch tests pass.

## 10. Index hygiene summary

- `TP-RTE-BATCH-005` marked `Merged (PR #614)`.
- `TP-RTE-BATCH-E2E-006` marked `Merged (PR #615)`.
- `TP-RTE-STRICT-ATTESTATION-007` added as `Active`.

## 11. Commit readiness

Ready for commit after final JSON parse and git diff review.

## 12. Residual risks and UNKNOWNs

- External provider passthrough was not live-tested because live provider calls and batch submissions are forbidden for this TP.
- F4-CRIT-2 docs canonical naming inversion remains open and out of scope.
