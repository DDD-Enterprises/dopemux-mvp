---
id: DOC_TRUST_MAP
title: Docs Trust Map
type: reference
owner: '@hu3mann'
author: codex
date: '2026-04-30'
last_review: '2026-04-30'
next_review: '2026-07-29'
prelude: Runtime-backed documentation trust map for dopemux documentation and developer workflows.
---
# DOC_TRUST_MAP

## Scope

This map classifies documentation reliability for the current checkout. It is an audit artifact, not runtime authority.

Authority order used:

1. Runtime code, config, and tests.
2. `config/runtime_authority_manifest.json` plus `scripts/verify_runtime_authority.py` static output.
3. Tracked truth references under `docs/03-reference/truth/`.
4. Derived plane and system references under `docs/03-reference/`.
5. Generated, archived, uploaded, or historical docs.

Generated docs remain advisory unless a runtime or tracked truth source independently supports the same claim.

## Classifications

| Trust | Meaning | Allowed usage |
| --- | --- | --- |
| HIGH | Matches inspected runtime/config/test surfaces or tracked truth docs and preserves known drift. | Use as navigation or secondary authority after checking the runtime path it cites. |
| MEDIUM | Useful current synthesis, but derived or partly dependent on advisory docs. | Use for orientation; verify contract-sensitive claims in runtime code/config/tests. |
| LOW | Potentially useful background, design, examples, plans, or legacy guidance with incomplete runtime backing. | Do not use for current behavior without independent runtime proof. |
| DO NOT TRUST | Known stale, duplicate, overbroad, generated, archived, or conflict-prone for authority decisions. | Do not use as authority. Use only as historical input or drift evidence. |

## Primary Doc Family Map

| Doc family | Classification | Source path(s) | Runtime-backed reason | Recommended usage |
| --- | --- | --- | --- | --- |
| Runtime authority manifest and verifier | HIGH | `config/runtime_authority_manifest.json`; `scripts/verify_runtime_authority.py` | Static verifier ran successfully with `python3` and reported zero errors plus six expected warnings for known conflicts. | Use as the highest doc-adjacent authority pointer set for runtime service claims. |
| Tracked truth references | HIGH | `docs/03-reference/truth/truth-systems.md`; `docs/03-reference/truth/truth-canonicals.md`; `docs/03-reference/truth/truth-gaps.md`; `docs/03-reference/truth/truth-interfaces.md`; `docs/03-reference/truth/truth-data-events.md`; `docs/03-reference/truth/truth-scope.md` | These files separate observed facts, inference, and `UNKNOWN`, and they cite runtime/code/config paths. | Use as the primary documentation truth layer, with runtime verification for changed code. |
| Runtime-derived system boundaries | HIGH | `docs/03-reference/systems/system-boundaries.md`; `docs/assembled/chatgpt_project_top40_upload_files/04_system-boundaries.md` | Preserves split PM authority, bridge non-authority, memory transport drift, and `UNKNOWN` canonicality. | Use for boundary checks; do not treat it as stronger than the code paths it cites. |
| PM plane references | HIGH | `docs/03-reference/planes/pm/pm-plane.md`; `docs/assembled/chatgpt_project_top40_upload_files/12_PM_PLANE.md`; `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py` | PM authority is explicitly split across Leantime metadata, task-orchestrator workflow, ConPort progress/decisions, and dope-memory receipts. | Use for PM routing and non-authority guidance after confirming the current adapter defaults. |
| Current system reference docs generated from repo truth | MEDIUM | `docs/assembled/chatgpt_project_top40_upload_files/15_SYSTEM_TaskOrchestrator.md`; `docs/assembled/chatgpt_project_top40_upload_files/16_SYSTEM_ConPort.md`; system docs under `docs/03-reference/systems/` | Useful because they cite runtime paths, but they are synthesized and can drift from the verifier or code. ConPort and task-orchestrator surfaces are explicitly `CONFLICTING`. | Use for orientation, then inspect cited service files before changing behavior or contracts. |
| Governance docs predating runtime audit | MEDIUM | `docs/03-reference/governance/authority-map.md`; `docs/03-reference/governance/conflict-ledger.md`; `docs/03-reference/governance/rules-2.md` | Broadly aligned with code-over-docs policy, but older conflict entries remain generic and less precise than the runtime verifier. | Use for general governance posture, not as the active drift ledger. |
| Contract and proof documentation | MEDIUM | `docs/03-reference/governance/proof-bundle-schema.md`; `docs/03-reference/governance/proof-contract.md`; `docs/03-reference/governance/handoff-contract.md`; `docs/02-how-to/integrations/dopetask/adapter-schema.md` | Contract docs can be useful, but this audit did not revalidate each schema against its writer/reader implementation. | Use only after checking the canonical writer and tests for the specific contract. |
| Generated assembled upload/navigation docs | LOW | `docs/assembled/*`; `docs/assembled/chatgpt_project_top40_upload_files/*` | `32_CHATGPT_PROJECT_UPLOAD_SET.md` states generated files are navigation/meta context and not source authority. Some top-level promoted files are currently untracked in this worktree. | Use as upload/navigation indexes only. Do not treat as runtime truth. |
| MCP customization upload bundle | LOW | `docs/03-reference/mcp-customization/*` | Contains duplicated constraints, upload manifests, and project customization material. This audit did not validate it against current runtime code. | Use as historical/customization context only unless a claim is verified elsewhere. |
| Top-level promoted or user-provided packet docs in this dirty worktree | LOW | `RULES.md`; `PROJECT.md`; `ARCHITECTURE.md`; `SYSTEM_*.md`; `TRUTH_*.md`; `PAL_*.md`; `dopetask-cannonical-spec.json` | `git status` shows many of these as untracked. `32_CHATGPT_PROJECT_UPLOAD_SET.md` describes several as promoted or user-provided for an upload pass. | Do not use as stronger authority than tracked truth docs or runtime code until committed and reconciled. |
| Instructions, PAL, task packet, and agent guidance | LOW | `docs/03-reference/instructions/*`; `docs/03-reference/task-packets/*`; `config/instructions/agents.instructions.md`; `task-packets/*` | These control operator behavior and packet flow, but they do not establish service runtime truth. Agent authority is `UNKNOWN`. | Use for workflow constraints only. Verify service claims in code/config/tests. |
| Design system and cockpit UI package docs | LOW | `docs/03-reference/Dopemux Cockpit TUI Design System/*`; `clean-53-file-design-pack/*`; `out/*CLAUDE-DESIGN*` | These are product/design artifacts. Existing uncommitted changes in this family are unrelated to runtime authority. | Use for UI design guidance only, not service or PM authority. |
| How-to, tutorial, best-practice, feature, and release docs | LOW | `docs/02-how-to/*`; `docs/03-reference/features/*`; `docs/03-reference/best-practices/*`; `docs/03-reference/releases/*` | Helpful operator material, but not audited against runtime in this packet. | Treat as advisory until checked against current code/config/tests. |
| Historical archives, upload bundles, and copied repo-truth packs | DO NOT TRUST | `docs/archive/*`; `dopemux_uploaded_files_bundle*`; `repo-truth-pack/*`; `reports/*repo-truth-pack/*`; `out/*` | These may preserve old audit outputs or duplicated files. They can conflict with the current verifier and runtime state. | Use only as evidence of past claims or drift, never as current authority. |
| Bridge-as-authority claims | DO NOT TRUST | Any doc claiming `dopecon-bridge` is canonical PM/task/workflow/decision/progress authority; source conflict checked against `services/dopecon-bridge/dopecon_bridge/routes.py` | Active bridge route module says the bridge is adapter/proxy only and must not act as canonical task, workflow, decision, or progress authority. | Replace with bridge-as-adapter language and cite canonical backend writers. |
| Single unified PM authority claims | DO NOT TRUST | Any doc claiming one PM system owns all PM truth; checked against `src/dopemux/pm/writes.py` and `src/dopemux/pm/reads.py` | Runtime PM reads/writes are split by concern. Unified authority is not proven. | Replace with per-slice authority mapping and mark unresolved writer/read paths as `UNKNOWN`. |

## Required Handling Rules

- Docs with runtime conflicts must not be classified HIGH.
- A generated doc can carry a HIGH-supported claim only when it points to runtime or tracked truth evidence; the generated doc itself remains advisory.
- `UNKNOWN` must remain `UNKNOWN` until a canonical writer, reader, or runtime path is inspected.
- `CONFLICTING` runtime pointers must be preserved as drift, not normalized by prose.
- `DO NOT TRUST` means do not rely on the source for authority decisions; it does not require deleting the source.

## Audit Inputs

- Static verifier: `python3 scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static`
- Runtime/config sources sampled: `compose.yml`, `services/registry.yaml`, `services/task-orchestrator/Dockerfile`, `services/task-orchestrator/app/main.py`, `services/task-orchestrator/task_orchestrator/app.py`, `services/dope-memory/mcp_stdio_adapter.py`, `services/dopecon-bridge/dopecon_bridge/routes.py`, `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py`, `src/dopemux/pm/adapters/orchestrator.py`, `src/dopemux/pm/adapters/conport.py`
- Truth docs sampled: all tracked files under `docs/03-reference/truth/`
- Derived docs sampled: `docs/03-reference/systems/system-boundaries.md`, `docs/03-reference/planes/pm/pm-plane.md`, and packet-named Top 40 files under `docs/assembled/chatgpt_project_top40_upload_files/`
