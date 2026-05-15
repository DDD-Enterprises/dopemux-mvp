# RTE-PKT-08 Test Report

## PASS

```bash
python -m py_compile services/repo-truth-extractor/lib/batch_clients.py services/repo-truth-extractor/lib/batch_retriever.py services/repo-truth-extractor/run_extraction_v5.py
```

Exit code: `0`.

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_rte_pkt_08_batch_static_proof.py
```

Exit code: `0`. Result: `7 passed`.

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k 'batch and static'
```

Exit code: `0`. Result: `7 passed`.

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_batch_clients_integration.py services/repo-truth-extractor/tests/test_batch_retriever.py services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py
```

Exit code: `0`. Result: `28 passed`.

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_provider_payload_redaction.py
```

Exit code: `0`. Result: `10 passed`.

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_rte_pkt_08_batch_static_proof.py services/repo-truth-extractor/tests/test_batch_clients_integration.py services/repo-truth-extractor/tests/test_batch_retriever.py services/repo-truth-extractor/tests/test_run_extraction_v5_batch_response_format.py services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py
```

Exit code: `0`. Result: `45 passed`.

```bash
python -m json.tool out/rte-pkt-08-xai-batch-static/RTE-PKT-08_MANIFEST.json >/dev/null
```

Exit code: `0`.

```bash
git diff --check
```

Exit code: `0`.

```bash
changed=$(git ls-files --modified --others --exclude-standard); if command -v pre-commit >/dev/null 2>&1; then pre-commit run --files $changed; else echo 'pre-commit NOT_FOUND'; exit 127; fi
```

Exit code: `0`. Hooks either passed or skipped according to their configured file filters.

## Warnings

Pytest emitted an existing warning: `Unknown config option: asyncio_mode`.

## NOT_RUN

No live extraction, provider call, batch submit, batch poll, batch retrieve, batch cancel, or remote provider file retrieval was run.
