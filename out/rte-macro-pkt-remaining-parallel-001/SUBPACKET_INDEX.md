# Subpacket Index

## Wave 1 Candidates

| Packet | Objective | Expected write scope | Scope classes | Macro decision |
| --- | --- | --- | --- | --- |
| `RTE-PKT-03-PRESCAN-STALE` | Validate imported prescan against current repo/source identity before steering execution. | `services/repo-truth-extractor/lib/intelligence_router.py`; `services/repo-truth-extractor/lib/prescan/engine.py`; `services/repo-truth-extractor/run_extraction_v5.py`; tests; `out/rte-pkt-03-prescan-stale/` | runtime, test, proof | executable, serialized outside 1A |
| `RTE-PKT-05-PROVENANCE-FIELDS` | Mark repaired and sidefilled values at field level. | `services/repo-truth-extractor/run_extraction_v5.py`; provenance helper; normalize/merge tests; `out/rte-pkt-05-provenance-fields/` | runtime, test, proof | executable, serialized outside 1A |
| `RTE-PKT-07-XAI-METADATA` | Capture returned/effective model, refusal, incomplete state, finish reason, and response IDs where available. | `services/repo-truth-extractor/llm_runtime.py`; `services/repo-truth-extractor/run_extraction_v5.py`; response-summary tests; `out/rte-pkt-07-xai-metadata/` | runtime, test, proof | executable, serialized outside 1A |
| `RTE-PKT-08-XAI-BATCH-STATIC` | Close static batch proof gaps and mark xAI batch as live-unvalidated. | batch clients/retriever; `services/repo-truth-extractor/run_extraction_v5.py`; batch parser fixtures; `out/rte-pkt-08-xai-batch-static/` | runtime, test, proof | executable in Subwave 1A |
| `RTE-PKT-10-PROOF-CONTRACT` | Distinguish run proof from full proof-bundle compliance. | proof contract helper/mapping; proof conformance tests; `out/rte-pkt-10-proof-contract/` | runtime, test, proof | executable in Subwave 1A |
| `RTE-PKT-15B-COMPARISON-SIDECAR` | Optional remediation of comparison-lane `.FAILED.txt` writer. | `services/repo-truth-extractor/llm_runtime.py`; comparison failed-sidecar tests; `out/rte-pkt-15b-comparison-sidecar/` | runtime, test, proof | blocked until explicitly enabled |

## Dependent Packets

| Packet | Depends on | Expected write scope | Scope classes | Macro decision |
| --- | --- | --- | --- | --- |
| `RTE-PKT-04-PRESCAN-INFLUENCE` | `RTE-PKT-03` | `intelligence_router.py`; `run_extraction_v5.py`; influence tests; proof | runtime, test, proof | wait |
| `RTE-PKT-06-TRUTH-LABELS` | `RTE-PKT-05` | `run_extraction_v5.py`; provenance helper; truth label helper; tests; proof | runtime, test, proof | wait |
| `RTE-PKT-13-ROUTE-FINGERPRINT` | `RTE-PKT-07` | `run_extraction_v5.py`; `llm_runtime.py`; route fingerprint tests; proof | runtime, test, proof | wait |
| `RTE-PKT-12-OPENROUTER-XAI` | `RTE-PKT-07`, `RTE-PKT-13` | `llm_runtime.py`; `run_extraction_v5.py`; route metadata helpers; structured output labels if explicitly scoped; tests; proof | runtime, test, proof, contract-sensitive | wait |
| `RTE-PKT-09-LIVE-VALIDATION-PLAN` | `RTE-PKT-01`, `RTE-PKT-02`, `RTE-PKT-07`, `RTE-PKT-08` | plan/proof only | proof | plan-only |
| `RTE-PKT-11-RISK-DASHBOARD` | `RTE-PKT-01/02/03/04/05/06/07/08/10/12/13/15` | `run_extraction_v5.py`; proof contract helper; risk dashboard helper; tests; proof | runtime, test, proof | wait |
| `RTE-PKT-14-PRICING-VISIBILITY` | `RTE-PKT-11` | pricing/spend helpers; `llm_runtime.py`; `run_extraction_v5.py`; pricing tests; proof | runtime, test, proof | wait |
| `RTE-PKT-16-CLI-LEGACY-UX` | `RTE-PKT-11` | likely CLI/docs/tests, exact packet source not found locally | unknown, docs, test | plan-only until source resolved |

## Blocked Or Not Executed

No subpacket was executed in this macro.

`RTE-PKT-15B-COMPARISON-SIDECAR` is blocked until explicit operator enablement.

`RTE-PKT-16-CLI-LEGACY-UX` is plan-only until exact source and write scope are resolved.
