# RTE-PKT-15 Remaining Risks

| Risk | Classification | Why it remains |
| --- | --- | --- |
| Comparison-lane `.FAILED.txt` direct writer | `UNKNOWN / FOLLOW-UP` | `services/repo-truth-extractor/llm_runtime.py` is outside the packet allowlist and still writes `failure_reason` directly. |
| Legacy v3 failed sidecar fixtures | `ACCEPTED_RESIDUAL` | Fixtures are evidence surfaces, not current v5 writer paths. They were not modified and their contents were not quoted. |
| Packet-00 named proof files absent | `UNKNOWN` | The current branch does not contain `out/rte-pkt-00-source-closure/`; operator grounding supplied the packet-00 failed-sidecar risk context. |
| Existing local branch name collision | `PROCESS_DRIFT` | The requested branch already existed with broad unrelated drift. This run used a clean branch and preserved the old branch untouched. |
| Broad test-tree grep positives | `EXPECTED_POSITIVES` | The broad packet grep reports deliberate sanitizer patterns, synthetic test literals, and legacy fixture paths. Proof records only path/count evidence, not matched contents. |
