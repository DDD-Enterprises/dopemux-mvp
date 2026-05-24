# Source Resolution Report

Packet: TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP
Created at UTC: 2026-05-20T01:30:11Z

## Selection Method

No general `docs/assembled/chatgpt_project_top40_upload_files/` directory or exact `CHATGPT_PROJECT_UPLOAD_SET.md` source was observed in the current worktree. The selected 40-file upload set was assembled from the authority classes in the packet prompt, preferring live root files when present and tracked `docs/03-reference/` equivalents when root files were absent.

## Resolutions

| Bundle file | Source | Status | Note |
|---|---|---|---|
| 01_RULES.md | docs/03-reference/governance/rules.md | OBSERVED | Root RULES.md absent in current worktree; tracked governance equivalent used. |
| 02_PROJECT.md | PROJECT.md | OBSERVED | Root project file observed. |
| 03_ARCHITECTURE.md | ARCHITECTURE.md | OBSERVED | Root architecture file observed. |
| 04_SYSTEM_BOUNDARIES.md | docs/03-reference/systems/system-boundaries.md | OBSERVED | Root SYSTEM_BOUNDARIES.md absent; tracked systems equivalent used. |
| 05_PM_PLANE.md | PM_PLANE.md | OBSERVED | Root PM plane file observed. |
| 06_SERVICE_CATALOG.md | SERVICE_CATALOG.md | OBSERVED | Root service catalog observed. |
| 07_TRUTH_SCOPE.md | docs/03-reference/truth/truth-scope.md | OBSERVED | Tracked truth equivalent used. |
| 08_TRUTH_SYSTEMS.md | docs/03-reference/truth/truth-systems.md | OBSERVED | Tracked truth equivalent used. |
| 09_TRUTH_INTERFACES.md | docs/03-reference/truth/truth-interfaces.md | OBSERVED | Tracked truth equivalent used. |
| 10_TRUTH_DATA_EVENTS.md | docs/03-reference/truth/truth-data-events.md | OBSERVED | Tracked truth equivalent used. |
| 11_TRUTH_CANONICALS.md | docs/03-reference/truth/truth-canonicals.md | OBSERVED | Tracked truth equivalent used. |
| 12_TRUTH_GAPS.md | docs/03-reference/truth/truth-gaps.md | OBSERVED | Tracked truth equivalent used. |
| 13_SYSTEM_DOPEMUX.md | docs/03-reference/systems/dopemux/system-dopemux.md | OBSERVED | Tracked system doc used. |
| 14_SYSTEM_DOPETASK.md | docs/03-reference/systems/dopetask/system-dopetask.md | OBSERVED | Tracked system doc used. |
| 15_SYSTEM_TASKORCHESTRATOR.md | docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md | OBSERVED | Tracked system doc used. |
| 16_SYSTEM_CONPORT.md | docs/03-reference/systems/conport/system-conport.md | OBSERVED | Tracked system doc used. |
| 17_SYSTEM_DOPEMEMORY.md | docs/03-reference/systems/dope-memory/system-dopememory.md | OBSERVED | Tracked system doc used. |
| 18_SYSTEM_DOPECONTEXT.md | docs/03-reference/systems/dope-context/system-dopecontext.md | OBSERVED | Tracked system doc used. |
| 19_SYSTEM_DOPECONBRIDGE.md | docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md | OBSERVED | Tracked system doc used. |
| 20_SYSTEM_ADHDENGINE.md | docs/03-reference/systems/adhd-engine/system-adhdengine.md | OBSERVED | Tracked system doc used. |
| 21_SYSTEM_REPOTRUTHEXTRACTOR.md | docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md | OBSERVED | Tracked system doc used. |
| 22_AGENTS.md | AGENTS.md | OBSERVED | Live durable Codex/agent repo guidance observed. |
| 23_PAL_EXECUTION_RULES.md | docs/03-reference/execution/pal-execution-rules.md | OBSERVED | Root PAL_EXECUTION_RULES.md absent; tracked execution equivalent used. |
| 24_PAL_CHAINING_DOCTRINE.md | docs/03-reference/execution/pal-chaining-doctrine.md | OBSERVED | Root PAL_CHAINING_DOCTRINE.md absent; tracked execution equivalent used. |
| 25_DOPETASK_CANONICAL_SPEC.json | docs/03-reference/spec/dopetask/dopetask-canonical-spec.json | OBSERVED | Live canonical dopetask schema path observed. |
| 26_PROOF_CONTRACT.md | docs/03-reference/governance/proof-contract.md | OBSERVED | Tracked proof contract observed. |
| 27_PROOF_BUNDLE_SCHEMA.md | docs/03-reference/governance/proof-bundle-schema.md | OBSERVED | Tracked proof bundle schema observed. |
| 28_HANDOFF_CONTRACT.md | docs/03-reference/governance/handoff-contract.md | OBSERVED | Tracked handoff contract observed. |
| 29_ADAPTER_CONTRACT.md | docs/integrations/dopetask/adapter-contract.md | OBSERVED | Tracked dopetask adapter contract observed. |
| 30_ADAPTER_SCHEMA.md | docs/integrations/dopetask/adapter-schema.md | OBSERVED | Tracked dopetask adapter schema observed. |
| 31_TASK_PACKET_TEMPLATE.md | task-packets/TEMPLATE_TASK_PACKET.md | OBSERVED | No root PAL_PACKET_TEMPLATE.md observed; task packet template used. |
| 32_AUTHORITY_MAP.md | docs/03-reference/governance/authority-map.md | OBSERVED | Closest observed SOURCE_AUTHORITY_MAP equivalent. |
| 33_DOC_TRUST_MAP.md | docs/03-reference/governance/doc-trust-map.md | OBSERVED | Observed doc authority/trust map. |
| 34_DOCUMENTATION_SOURCE_MAP.md | docs/03-reference/governance/dopemux-documentation-source-map.md | OBSERVED | Observed documentation source map. |
| 35_RUNTIME_AUTHORITY_VERIFICATION.md | docs/03-reference/governance/runtime-authority-verification.md | OBSERVED | Observed runtime authority verification guide. |
| 36_CODEX_AUTHORITY_REFRESH.md | docs/03-reference/governance/codex-authority-refresh.md | OBSERVED | Observed current Codex authority refresh artifact. |
| 37_CODEX_PROMPT_PACK.md | docs/03-reference/governance/codex-prompt-pack.md | OBSERVED | Observed current Codex prompt pack. |
| 38_CODEX_REFRESH_GAP_REGISTER.md | docs/03-reference/governance/codex-refresh-gap-register.md | OBSERVED | Observed Codex refresh gap register. |
| 39_AGENT_WORKFLOW.md | docs/03-reference/governance/agent-workflow.md | OBSERVED | Observed agent workflow governance reference. |
| 40_GOVERNANCE_MODEL.md | docs/03-reference/governance/governance-model.md | OBSERVED | Observed governance model reference. |

## Missing Exact-Name Sources

- Root `RULES.md`: MISSING; used `docs/03-reference/governance/rules.md`.
- Root `SYSTEM_BOUNDARIES.md`: MISSING; used `docs/03-reference/systems/system-boundaries.md`.
- Root `TRUTH_*.md`: MISSING; used tracked `docs/03-reference/truth/*` equivalents.
- Root `SYSTEM_*.md`: MISSING; used tracked `docs/03-reference/systems/*/system-*.md` equivalents.
- Root `PAL_EXECUTION_RULES.md` and `PAL_CHAINING_DOCTRINE.md`: MISSING; used tracked execution equivalents.
- Root `PAL_PACKET_TEMPLATE.md`: MISSING; used `task-packets/TEMPLATE_TASK_PACKET.md`.
- General repo-map/current recon download: MISSING; see `REPO_MAP_CURRENT_RECON.md`.
