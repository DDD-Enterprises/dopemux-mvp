# RTE-PKT-01 Diff Summary

Generated: `2026-05-15T02:18:28.825840+00:00`

## Changed Files

- `services/repo-truth-extractor/run_extraction_v5.py`: Add live-capable operation classifier and early parser-level consent refusal before provider/network dispatch; allow batch retrieve to reach its own guarded dispatch without requiring a phase. Scope: `allowed_code_path`.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py`: New local monkeypatch tests for consent classification, refusal before live-capable dispatch, dry-run allowance, and consent-success path without provider calls. Scope: `allowed_test_path`.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py`: Align validator-behavior tests with explicit --execute plus DPMX_LIVE_OK=1 so they test validator behavior rather than consent refusal. Scope: `allowed_test_path`.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py`: Same validator-behavior alignment as the sibling validator test module. Scope: `allowed_test_path`.

## Git Diff Stat At Generation

```text
services/repo-truth-extractor/run_extraction_v5.py | 128 ++++++++++++++++++++-
 .../tests/test_run_extraction_v5_validator.py      |   7 +-
 ...un_extraction_v5_validator_repair_provenance.py |   6 +-
 3 files changed, 135 insertions(+), 6 deletions(-)
```

## Git Name Status At Generation

```text
M	services/repo-truth-extractor/run_extraction_v5.py
M	services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
M	services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py
```

## Git Status At Proof Finalization

```text
## codex/rte-pkt-01-live-gate
 M services/repo-truth-extractor/run_extraction_v5.py
 M services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
 M services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py
?? out/rte-pkt-01-live-gate/
?? services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py
```
