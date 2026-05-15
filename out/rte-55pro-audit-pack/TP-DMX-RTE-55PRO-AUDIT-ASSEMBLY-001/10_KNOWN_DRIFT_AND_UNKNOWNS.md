# Known Drift And Unknowns

## Required Drift Items

- OBSERVED v5 vs v4/v3 layering: v5 is canonical; v4 wrapper and v3 legacy/fallback surfaces remain present.
- OBSERVED output-root drift: current v5 constants point to `extraction/repo-truth-extractor/v5`, while historical audit reports reference paths under `services/repo-truth-extractor/extraction/...`.
- OBSERVED legacy dopemux extractor/truth/upgrades drift: `dopemux rte` is canonical, `upgrades` remains an alias, hidden `extractor` remains for support workflows, and older truth/extractor wording appears in historical docs/proofs.
- OBSERVED docs vs runtime mismatch risk: PR #617 closed known docs canonicalization drift, but generated/historical docs remain lower authority than runtime.
- UNKNOWN promptset authority: active prompt truth may span v4 promptsets, generated promptsets, phase registries, prescan Python constants, and v3 archives. Audit actual loaders.
- UNKNOWN provider/model routing behavior: route names and model constants exist, but current provider capabilities require source tracing plus external/current research.
- UNKNOWN proof/schema coverage gaps: proof contract docs exist, but this assembly did not prove every runtime artifact has schema-backed tests.

## Additional Unknowns

- UNKNOWN: no root `RULES.md`, `SYSTEM_BOUNDARIES.md`, top-level `TRUTH_*.md`, `SYSTEM_RepoTruthExtractor.md`, or root PAL files were present. Tracked equivalents were used where available.
- UNKNOWN: no `docs/assembled/chatgpt_project_top40_upload_files/` directory was present in this worktree, despite doc-trust-map mentioning packet-named Top 40 files.
- UNKNOWN: current Opus-specific audit packet/report was not identified beyond Phase S Opus-labeled material and the Gemini PAL audit/proof.
- UNKNOWN: whether PR #603 `fix(rte): make introspection commands readonly` has a proof packet in the expected `proof/TP-RTE-SAFE-INTROSPECTION-001/PROOF.json`; task-packet file exists but matching proof path was not found during this pass.
- UNKNOWN: real provider behavior for strict JSON schema, batch response format, and passthrough fields across OpenAI, Anthropic, Gemini, xAI, and OpenRouter as of audit time.
- UNKNOWN: real end-to-end UX for a long extraction run, status loop, resume/retry, and proof review because live extraction was forbidden.
