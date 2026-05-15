# RTE-PKT-15 Remaining Unknowns

## UNKNOWN: comparison-lane failed text sidecar

`services/repo-truth-extractor/llm_runtime.py:1342` writes comparison-lane `.FAILED.txt` content directly from `failure_reason`.

This file is outside the packet allowlist, so it was not patched. If comparison-lane failed sidecars are in the live proof-storage boundary, a follow-up packet should either add `llm_runtime.py` to scope or prove comparison-lane failure text cannot contain provider/source/error secret-shaped content.

## UNKNOWN: legacy v3 failed sidecar fixtures

Legacy v3 fixture sidecars were not modified. This packet focused on RTE v5 runtime failed sidecar safety. Existing fixture contents were not quoted in proof.

## NOT PRESENT: provider payload redaction regression file

The packet named `services/repo-truth-extractor/tests/test_provider_payload_redaction.py` as a conditional regression command. That file was not present in this checkout.

## Drift: broader prelive hardening validation

The broader command `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py -q` failed one provider escalation assertion unrelated to changed sidecar-redaction lines.

Closeout comparison against `/Users/hue/.codex/worktrees/rte-pkt-15a-clean-base` at `a4214ca5bf431e1b59791661e2b664a6cd24c1da` reproduced the same failing test, assertion, and observed `provider_failure` value. Classification: `BASELINE_FAILURE`.
