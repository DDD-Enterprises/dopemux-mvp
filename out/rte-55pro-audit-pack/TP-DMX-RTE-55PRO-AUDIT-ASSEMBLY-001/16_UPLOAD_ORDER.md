# Upload Order

OBSERVED: no `docs/assembled/chatgpt_project_top40_upload_files/` directory was present in this worktree. The prior 5.4 audit report has a bounded recommended upload set, so this order starts from that logic and updates it with current RTE source/proof surfaces and this packet.

## 1. Base Authority Sources

1. `AGENTS.md`
2. `PROJECT.md`
3. `ARCHITECTURE.md`
4. `docs/03-reference/systems/system-boundaries.md`
5. `PM_PLANE.md`
6. `SERVICE_CATALOG.md`
7. `docs/03-reference/truth/truth-scope.md`
8. `docs/03-reference/truth/truth-systems.md`
9. `docs/03-reference/truth/truth-interfaces.md`
10. `docs/03-reference/truth/truth-data-events.md`
11. `docs/03-reference/truth/truth-canonicals.md`
12. `docs/03-reference/truth/truth-gaps.md`
13. `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
14. `docs/03-reference/governance/proof-contract.md`
15. `docs/03-reference/governance/proof-bundle-schema.md`

## 2. RTE Runtime And CLI Sources

16. `services/repo-truth-extractor/run_extraction_v5.py`
17. `services/repo-truth-extractor/rte_config.py`
18. `services/repo-truth-extractor/llm_runtime.py`
19. `services/repo-truth-extractor/lib/structured_output_contracts.py`
20. `services/repo-truth-extractor/run_extraction_v4.py`
21. `services/repo-truth-extractor/run_extraction_v3.py`
22. `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
23. `services/repo-truth-extractor/extraction_hygiene.py`
24. `src/dopemux/cli.py`
25. `src/dopemux/commands/extractor_commands.py`

## 3. RTE Prompt, Prescan, Batch, And Test Sources

26. `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
27. `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
28. `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
29. `services/repo-truth-extractor/promptsets/v4/prompt_artifact_coverage_map.json`
30. `services/repo-truth-extractor/prompts/phase_s/registry.json`
31. `services/repo-truth-extractor/prompts/prescan/registry.json`
32. `services/repo-truth-extractor/lib/prescan/engine.py`
33. `services/repo-truth-extractor/lib/prescan/corpus_walker.py`
34. `services/repo-truth-extractor/lib/prescan/provider_catalog.py`
35. `services/repo-truth-extractor/lib/batch_clients.py`
36. `services/repo-truth-extractor/lib/batch_retriever.py`
37. Focused tests from `services/repo-truth-extractor/tests/` for operator safety, v3 consent, prescan corpus/walker, batch response format, strict passthrough attestations, promptset truth/lint, and pre-live gate v25.

## 4. Prior Audit And Remediation Proof

38. `task-packets/TP-DMX-RTEAUDIT-110.json`
39. `proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json`
40. `docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md`
41. `task-packets/TP-DMX-RTEAUDIT-001.json`
42. `proof/rte-prelive-audit-pack-2026-04-23.proof.json`
43. `proof/TP-RTE-V3-CONSENT-004/PROOF.json`
44. `proof/TP-RTE-WALKER-006/PROOF.json`
45. `proof/TP-RTE-BATCH-005/PROOF.json`
46. `proof/TP-RTE-BATCH-E2E-006/PROOF.json`
47. `proof/TP-RTE-STRICT-ATTESTATION-007/PROOF.json`
48. `proof/TP-RTE-DOCS-CANON-008/PROOF.json`

## 5. Generated Audit-Pack Files

49. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/00_README.md`
50. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/01_BASELINE_STATE.md`
51. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md`
52. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md`
53. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/04_RTE_RUNTIME_POINTERS.md`
54. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md`
55. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/06_MODEL_ROUTING_AND_ESCALATION_INVENTORY.md`
56. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/07_ARTIFACT_PROOF_INVENTORY.md`
57. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/09_UX_OPERATOR_JOURNEY_CURRENT.md`
58. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/10_KNOWN_DRIFT_AND_UNKNOWNS.md`
59. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/12_GPT55_PROJECT_INSTRUCTIONS.md`
60. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/13_GPT55_PASS1_BROAD_AUDIT_PROMPT.md`
61. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/14_GPT55_SPECIALIST_PASS_PROMPTS.md`
62. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/17_SOURCE_EXCERPT_INDEX.md`
63. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/18_CHATGPT_PROJECT_PRIMING_PROMPT.md`

## 6. Advisory Deep Research Briefs

64. `out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/11_DEEP_RESEARCH_QUESTIONS.md`

## Excluded Or Unsafe For First Upload

- `.env*`, credentials, private keys, tokens, and local machine secrets.
- Full historical run trees, raw provider outputs, and large logs unless explicitly needed for a focused addendum.
- Full v3 prompt archives unless the audit reaches legacy-v3-specific findings.
- Generated extraction outputs outside this packet unless source authority and privacy are confirmed.
