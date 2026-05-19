# Write Scope Collision Matrix

## Scope Classification

| Packet | runtime | test | proof | docs | config | forbidden | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `RTE-PKT-03` | `intelligence_router.py`, `lib/prescan/engine.py`, `run_extraction_v5.py` | stale prescan/import tests | `out/rte-pkt-03-prescan-stale/` | none expected | none expected | prompt edits, live Grok, provider calls | none |
| `RTE-PKT-05` | `run_extraction_v5.py`, provenance/merge helper path | provenance/repair/sidefill tests | `out/rte-pkt-05-provenance-fields/` | none expected | none expected | prompt/model-route redesign, broad schema rewrite, provider validation | exact normalize/merge helper path must be reverified |
| `RTE-PKT-07` | `llm_runtime.py`, `run_extraction_v5.py` or response summarizer | xAI/OpenRouter/OpenAI-like fixtures | `out/rte-pkt-07-xai-metadata/` | none expected | none expected | live calls, route changes, pricing changes | none |
| `RTE-PKT-08` | batch clients/retriever, `run_extraction_v5.py` | JSONL/missing-row fixtures | `out/rte-pkt-08-xai-batch-static/` | none expected | none expected | batch submit/poll/retrieve/cancel | none |
| `RTE-PKT-10` | proof contract helper/mapping | proof field/conformance tests | `out/rte-pkt-10-proof-contract/` | none expected | none expected | broad proof system refactor, source truth changes | exact proof writer mapping path must be reverified |
| `RTE-PKT-15B` | `llm_runtime.py` | comparison failed-sidecar tests | `out/rte-pkt-15b-comparison-sidecar/` | none expected | none expected | comparison semantics, provider calls, retry/repair changes | operator enablement missing |
| `RTE-PKT-04` | `intelligence_router.py`, `run_extraction_v5.py` | prescan influence tests | `out/rte-pkt-04-prescan-influence/` | none expected | none expected | live/provider work | none |
| `RTE-PKT-06` | `run_extraction_v5.py`, provenance helper, truth label helper | truth-label preservation tests | `out/rte-pkt-06-truth-labels/` | none expected | none expected | semantic normalization of `UNKNOWN`/`CONFLICTING` | none |
| `RTE-PKT-13` | `run_extraction_v5.py`, `llm_runtime.py` | route fingerprint tests | `out/rte-pkt-13-route-fingerprint/` | none expected | none expected | route changes, provider calls | none |
| `RTE-PKT-12` | `llm_runtime.py`, `run_extraction_v5.py`, route metadata helpers, structured-output labels if explicitly scoped | OpenRouter/direct xAI tests | `out/rte-pkt-12-openrouter-xai/` | none expected | none expected | route selection changes, pricing changes, provider calls | exact structured-output scope must be confirmed in subpacket |
| `RTE-PKT-09` | none | none | `out/rte-pkt-09-live-validation-plan/` | plan docs only | none expected | actual provider calls, live extraction, batch submission | none |
| `RTE-PKT-11` | `run_extraction_v5.py`, proof contract helper, risk dashboard helper | dashboard/status tests | `out/rte-pkt-11-risk-dashboard/` | none expected | none expected | turning static proof into live proof | none |
| `RTE-PKT-14` | pricing/spend helpers, `llm_runtime.py`, `run_extraction_v5.py` | estimate-vs-billing tests | `out/rte-pkt-14-pricing-visibility/` | none expected | none expected | live billing claims, provider calls | none |
| `RTE-PKT-16` | unresolved, likely `src/dopemux/cli.py` | CLI snapshot tests | `out/rte-pkt-16-cli-legacy-ux/` | possible docs | none expected | stale command claims | exact source packet not found locally |

## Wave 1 Pair Matrix

| Pair | Classification | Evidence |
| --- | --- | --- |
| `03` x `05` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `03` x `07` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `03` x `08` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `03` x `10` | `PARALLEL_SAFE` | no expected shared runtime file |
| `03` x `15B` | `PARALLEL_SAFE_IF_ENABLED` | no expected shared file; 15B not enabled |
| `05` x `07` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `05` x `08` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `05` x `10` | `PARALLEL_SAFE` | no expected shared runtime file |
| `05` x `15B` | `PARALLEL_SAFE_IF_ENABLED` | no expected shared file; 15B not enabled |
| `07` x `08` | `SERIAL_REQUIRED` | both likely touch `run_extraction_v5.py` |
| `07` x `10` | `PARALLEL_SAFE` | no expected shared runtime file |
| `07` x `15B` | `SERIAL_REQUIRED_IF_ENABLED` | both touch `llm_runtime.py` |
| `08` x `10` | `PARALLEL_SAFE` | no expected shared runtime file |
| `08` x `15B` | `PARALLEL_SAFE_IF_ENABLED` | no expected shared file; 15B not enabled |
| `10` x `15B` | `PARALLEL_SAFE_IF_ENABLED` | no expected shared file; 15B not enabled |

## Dependent Pair Classifications

| Pair or group | Classification | Evidence |
| --- | --- | --- |
| `03` before `04` | `SERIAL_REQUIRED` | direct dependency and shared `intelligence_router.py` / `run_extraction_v5.py` |
| `05` before `06` | `SERIAL_REQUIRED` | direct dependency and shared provenance/runtime surfaces |
| `07` before `13` | `SERIAL_REQUIRED` | direct dependency and shared `llm_runtime.py` / `run_extraction_v5.py` |
| `13` before `12` | `SERIAL_REQUIRED` | direct dependency and shared route metadata/runtime surfaces |
| `07` before `12` | `SERIAL_REQUIRED` | direct dependency and shared `llm_runtime.py` / `run_extraction_v5.py` |
| `07` and `08` before `09` | `PLAN_ONLY_UNTIL_DEPENDENCIES_ACCEPTED` | `09` is plan-only, but depends on both static metadata packets |
| `01/02/03/04/05/06/07/08/10/12/13/15` before `11` | `SERIAL_REQUIRED` | dashboard is aggregation after accepted dependency proofs |
| `11` before `14` | `SERIAL_REQUIRED` | direct dependency and likely shared runtime/status surfaces |
| `11` before `16` | `PLAN_ONLY_UNTIL_SOURCE_RESOLVED` | `16` exact source packet/write scope not found locally |

## Full-Matrix Rule

For pairs not listed above:

- `PARALLEL_SAFE` only if neither packet has a direct dependency and neither packet shares `run_extraction_v5.py`, `llm_runtime.py`, or another exact runtime/test helper path.
- `PLAN_ONLY_UNTIL_SOURCE_RESOLVED` for every `RTE-PKT-16` pair until its exact source packet and write scope are found.
- `BLOCKED` for every `RTE-PKT-15B` execution pair until the operator explicitly enables that optional micro-packet.

## Result

Initial parallel execution is limited to:

```text
RTE-PKT-08-XAI-BATCH-STATIC
RTE-PKT-10-PROOF-CONTRACT
```

All other Wave 1 candidates are serialized because of `run_extraction_v5.py` and/or `llm_runtime.py` collisions.
