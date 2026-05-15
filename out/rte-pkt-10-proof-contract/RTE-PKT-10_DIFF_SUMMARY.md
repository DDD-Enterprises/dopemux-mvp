# RTE-PKT-10 Diff Summary

Generated: 2026-05-15T16:13:41Z

## Source Changes

| Path | Scope | Purpose |
| --- | --- | --- |
| `services/repo-truth-extractor/lib/proof_contract.py` | Conditional code path allowed by packet | Adds deterministic proof-contract field mapping, conformance classification, artifact authority classification, exact Pass 1 identity gap assessment, and static/no-provider status derivation. |
| `services/repo-truth-extractor/tests/test_proof_contract.py` | Allowed test path | Adds focused local tests for all requested proof-contract boundary cases. |

## Proof Output Changes

| Path | Scope | Purpose |
| --- | --- | --- |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json` | Allowed output root | Packet manifest with repo identity, authority used, changed files, validation summary, and no-provider boundary. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_PROOF_CONTRACT_GAP_MATRIX.md` | Allowed output root | Field-by-field proof-contract gap matrix. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_ARTIFACT_AUTHORITY_MAP.md` | Allowed output root | Artifact authority classification map. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_CONFORMANCE_EXAMPLES.md` | Allowed output root | Examples for satisfied, partial, missing, unknown, and not-applicable statuses. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_RUN_PROOF_VS_BUNDLE_PROOF.md` | Allowed output root | Operator-facing distinction between run proof and bundle proof. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_TEST_REPORT.md` | Allowed output root | Targeted validation commands and results. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_NO_PROVIDER_CALLS_ATTESTATION.md` | Allowed output root | No-live/no-provider/no-batch attestation. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_DIFF_SUMMARY.md` | Allowed output root | Scope and diff summary. |
| `out/rte-pkt-10-proof-contract/RTE-PKT-10_REMAINING_UNKNOWNS.md` | Allowed output root | Unknowns and residual risks ledger. |

## Explicit Non-Changes

- No prompt files changed.
- No promptset YAML changed.
- No model map or provider route selection changed.
- No provider client behavior changed.
- No batch provider protocol changed.
- No compose/config/deployment files changed.
- No proof writer refactor was performed because the observed writer is `reporting.py`, outside this packet allowlist.
