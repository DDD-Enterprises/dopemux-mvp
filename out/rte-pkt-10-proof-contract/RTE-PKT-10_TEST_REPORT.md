# RTE-PKT-10 Test Report

Generated: 2026-05-15T16:13:41Z

## PASS

| Command | Exit | Result | Notes |
| --- | ---: | --- | --- |
| `pytest services/repo-truth-extractor/tests/test_proof_contract.py -q` | 0 | PASS | 9 passed; existing PytestConfigWarning for unknown `asyncio_mode`. |
| `python -m py_compile services/repo-truth-extractor/lib/proof_contract.py` | 0 | PASS | No syntax errors. |
| `pytest services/repo-truth-extractor/tests -k 'proof_contract or artifact_authority' -q` | 0 | PASS | 9 passed; existing PytestConfigWarning for unknown `asyncio_mode`. |
| `pytest services/repo-truth-extractor/tests -k 'proof and contract' -q` | 0 | PASS | 9 passed; existing PytestConfigWarning for unknown `asyncio_mode`. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/proof_contract.py` | 0 | PASS | No syntax errors in the v5 runner or helper. |
| `python -m json.tool out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json` | 0 | PASS | Manifest parses as JSON. |
| `git diff --check` | 0 | PASS | No whitespace errors. |
| `git status --short --branch` | 0 | PASS | Dirty state before staging was limited to helper, tests, and packet proof outputs. |
| `pre-commit run --files <changed RTE-PKT-10 files>` | 0 | PASS | Configured hooks passed or skipped for the changed file set. |

## NOT_RUN

| Command / validation | Reason |
| --- | --- |
| Live extraction | Out of scope and forbidden by packet. |
| Provider calls to xAI, OpenAI, OpenRouter, Gemini, Anthropic, or other providers | Out of scope and forbidden by packet. |
| Batch submit, poll, retrieve, or cancel | Out of scope and forbidden by packet. |
| Full RTE suite | Narrow packet changed only helper/tests/proof outputs; broader suite not required by packet and not run. |

## Safety Result

All executed tests used local fixtures or in-memory dictionaries. No provider credentials were required.
