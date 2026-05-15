# RTE-PKT-08 Implementation Notes

## Scope

Implemented static-only xAI/OpenAI-compatible batch proof hardening. No live provider validation was performed.

## Changed Runtime Surfaces

- `services/repo-truth-extractor/lib/batch_clients.py`
  - Added static markers, terminal status classification, request metadata extraction, output/error JSONL fixture parsers, corrupt-line accounting, and custom_id correlation proof.
  - Sanitized OpenAI-compatible batch result error/meta values before returning `BatchResult` metadata.
- `services/repo-truth-extractor/lib/batch_retriever.py`
  - Preserves output/error file IDs and terminal status class in retrieval metadata.
  - Parses downloaded files only after the existing retrieval path has produced local files; no new retrieval operation was introduced.
- `services/repo-truth-extractor/run_extraction_v5.py`
  - Treats `expired` as terminal for batch watch.
  - Emits `batch_status` and `batch_status_class` into batch-watch metadata.
- `services/repo-truth-extractor/tests/`
  - Added static fixture tests for output rows, error rows, missing rows, partial failures, terminal states, corrupt-line thresholds, request metadata, and no-provider-call safety.

## Validation Summary

- `python -m py_compile` passed for changed runtime modules.
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_rte_pkt_08_batch_static_proof.py` passed: 7 tests.
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k 'batch and static'` passed: 7 tests.
- Targeted batch/retriever/strict/redaction suite passed: 45 tests.

## Remaining Risk

Live xAI/OpenAI-compatible batch submit, poll, retrieve, cancel, output/error JSONL shape, pagination, remote file lifecycle, and retention behavior remain `LIVE_VALIDATION_REQUIRED`.

<workflow-checkpoint phase="implement" status="complete" task="RTE-PKT-08-XAI-BATCH-STATIC" summary="Static batch proof implementation validated on local fixtures" artifact="/Users/hue/.codex/worktrees/d17a/dopemux-mvp/out/rte-pkt-08-xai-batch-static/implementation-notes.md" verification="python -m py_compile; pytest targeted static batch suites" />
