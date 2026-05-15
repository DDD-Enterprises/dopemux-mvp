# RTE-PKT-10 Artifact Authority Map

Generated: 2026-05-15T16:13:41Z

## Authority Rule

Runtime source authority outranks generated proof evidence. Generated artifacts may support review, but they do not become source truth without explicit runtime/schema evidence.

## Classification Map

| Artifact family | Observed paths | Classification | Authority role | Review risk |
| --- | --- | --- | --- | --- |
| RTE primary runtime | `services/repo-truth-extractor/run_extraction_v5.py` | `runtime_authority` | Runtime behavior authority for v5 orchestration entrypoint. | Must be inspected before changing proof semantics. |
| RTE proof writer implementation | `services/repo-truth-extractor/reporting.py` through `rte_reports.py` seam | `runtime_authority` | Canonical writer for `PROOF_PACK.json`, `RUN_MANIFEST.json`, certification, rollups, dashboard, and failure index. | Outside this packet allowlist, so it was not modified. |
| RTE run manifests and certification files | `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/*/RUN_MANIFEST.json`, `CERTIFICATION_RESULT.json` | `runtime_generated_evidence` | Runtime-generated evidence about prior runs. | Useful witness evidence; not proof-bundle complete by default. |
| `PROOF_PACK.json` writer shape | `reporting.py::update_proof_pack` and `write_blocked_promptset_proof_pack` | `runtime_generated_evidence` | Run evidence surface with run ID, git SHA, runner hash, argv, cwd, phase counts, and linked artifacts. | Not full proof-contract bundle unless governance fields are present. |
| Packet proof outputs | `out/rte-pkt-01-*` through `out/rte-pkt-06-*`, `out/rte-pkt-15-*` where present | `proof_governance_artifact` | Packet closeout evidence and review context. | Does not outrank runtime source or prove live provider behavior unless live evidence is present. |
| RTE TP proof files | `proof/TP-RTE-*.json` where present | `proof_governance_artifact` | Historical implementation proof and safety boundary evidence. | Often lacks canonical bundle fields such as `bundle_id` and `chain_of_custody`. |
| Audit-pack material | `out/rte-55pro-audit-pack/*`, `audit_inputs/*` | `generated_audit_context` | Review input and synthesis context. | Must remain below runtime code/config/tests in authority order. |
| External advisory reports | External DR/advisory files, when present | `external_advisory_context` | Advisory context only. | Cannot establish repo truth without local evidence. |
| Test fixtures and samples | `services/repo-truth-extractor/tests/fixtures/*`, sample proof payloads | `sample_artifact_uncertain_lineage` | Local test/sample evidence. | Cannot prove exact Pass 1 identity without exact hashes and run IDs. |
| Missing packet roots | `out/rte-pkt-07-xai-metadata`, `out/rte-pkt-08-xai-batch-static`, `out/rte-pkt-09-live-validation-plan` | `unknown` in this worktree | Not locally available in this checkout. | Must not be inferred from packet text alone. |

## Ordering Used By Helper

| Classification | Rank |
| --- | ---: |
| `runtime_authority` | 100 |
| `proof_governance_artifact` | 60 |
| `runtime_generated_evidence` | 50 |
| `generated_audit_context` | 40 |
| `external_advisory_context` | 30 |
| `sample_artifact_uncertain_lineage` | 20 |
| `unknown` | 0 |

The rank is deliberately conservative: runtime source remains higher than all generated evidence, while packet proof evidence remains higher than audit context but still below source authority.
