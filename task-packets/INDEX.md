---
id: INDEX
title: Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-03-22'
next_review: '2026-06-20'
prelude: Index (explanation) for dopemux documentation and developer workflows.
---
📑 Dopemux Task Packet Index
Canonical Registry · Execution History · Change Traceability
════════════════════════════════════════════════════════════
🎯 Purpose
This index is the authoritative registry of all Task Packets in Dopemux.
It exists to provide:
Traceability from design → execution
Visibility into active and completed work
A deterministic audit trail of system evolution
If a change cannot be traced to a Task Packet listed here, it is considered out of process.
────────────────────────────────────────────────────────────
🧭 How to Use This Index
Active packets indicate work in progress
Completed packets represent executed and audited changes
Superseded packets are preserved for history but must not be reused
This file should be updated whenever:
A new Task Packet is created
A packet changes status
A packet is superseded by another packet
────────────────────────────────────────────────────────────
🟡 Active Task Packets

| Packet ID | Subsystem | Title | Status | Related ADR |
| --- | --- | --- | --- | --- |
| TP-DMX-REPOSITORY-MERGE-PLANNER-DESIGN-001 | Control Tower / Planner | Design read-only interactive repository merge planner | Active (design only) | docs/91-rfc/repository-merge-planner.md |
| TP-DMX-PCP-PLANNER-FOUNDATION-001 | Control Tower / Planner | Fixture-backed deterministic PCP planner foundation | Draft / blocked on design acceptance | TP-DMX-REPOSITORY-MERGE-PLANNER-DESIGN-001 |
| TP-DMX-PCP-ADOPS-EXTENSION-002 | Control Tower / Planner | Read-only AdOps PROJECT extension | Draft / blocked on foundation | TP-DMX-PCP-PLANNER-FOUNDATION-001 |
| TP-DMX-PCP-DNH-RDCP-BRIDGE-003 | Control Tower / Planner | Read-only dNh RDCP extension bridge | Draft / blocked on foundation | TP-DMX-PCP-PLANNER-FOUNDATION-001 |
| TP-DMX-PCP-GITHUB-REFRESH-004 | Control Tower / Planner | Allowlisted GitHub GET/HEAD evidence refresh | Draft / blocked on AdOps+dNh adapters | TP-DMX-PCP-ADOPS-EXTENSION-002, TP-DMX-PCP-DNH-RDCP-BRIDGE-003 |
| TP-DMX-PCP-CONVERSATION-DECISIONS-005 | Control Tower / Planner | Approved decision-capsule intake and reconciliation | Draft / blocked on live refresh | TP-DMX-PCP-GITHUB-REFRESH-004 |
| DMX-MCPINT-HRD-REPORT-001 | MCP Fleet (P7/HRD) | Consolidated fleet reconciliation report 2026-07-18 (P7 anchor) | Active | claudedocs/mcp-fleet-reconciliation-2026-07-18.md |
| DMX-MCPINT-HRD-CONSENSUS-VEC-002 | MCP Fleet (P7/HRD) | G6 ConPort vector-search boundary via PAL consensus | Ready | adr-mcpint-006 (to be authored) |
| DMX-MCPINT-HRD-CONSENSUS-CPLX-003 | MCP Fleet (P7/HRD) | G7 complexity federation — ratify/challenge G5 via PAL consensus | Ready | adr-mcpint-001 (G5) |
| DMX-MCPINT-HRD-CONSENSUS-PMSYNC-004 | MCP Fleet (P7/HRD) | G8 Leantime/PM write-sync boundary via PAL consensus | Ready | ADR to be authored |
| DMX-MCPINT-HRD-CONPORTWRAP-005 | MCP Fleet (P7/HRD) | Retire conport shadow-twin wrapper; stub phantom serena wrapper | Ready | Gate G-02a |
| DMX-MCPINT-HRD-SERENAWRAP-006 | MCP Fleet (P7/HRD) | Repoint serena wrapper at deployed in-repo engine | Blocked on DOPECODE-001 | Gate G-02b |
| DMX-MCPINT-HRD-DESKCMD-007 | MCP Fleet (P7/HRD) | desktop-commander host-run singleton; retire Linux container | Ready | catalog follow_on_decision |
| DMX-MCPINT-HRD-EVHYG-008 | MCP Fleet (P7/HRD) | Chronicle ingress event_id dedup + PII redaction | Blocked on EVENTS-006 | adr-mcpint-004 (G2) |
| DMX-MCPINT-HRD-IDENTITY-009 | MCP Fleet (P7/HRD) | Per-request instance identity + instances registry | Ready | CHATGPT_TARGET_RESOLUTION_CONTRACT |
| DMX-MCPINT-HRD-DCTXIDX-010 | MCP Fleet (P7/HRD) | Enable dope-context decision auto-indexing | Blocked on G6 | adr-mcpint-006 |
| DMX-MCPINT-HRD-TOKTRUNC-011 | MCP Fleet (P7/HRD) | Fleet token-truncation standard (9K budget + boundary guard) | Ready | N/A |
| DMX-MCPINT-HRD-LOOPBACK-012 | MCP Fleet (P7/HRD) | Loopback-only binds fleet-wide | Ready | N/A |
| DMX-MCPINT-HRD-KGREAD-013 | MCP Fleet (P7/HRD) | Read-only KG graph traversal tools in conport | Blocked on G6 | adr-mcpint-006 |
| DMX-MCPINT-HRD-FACADEDCTX-014 | MCP Fleet (P7/HRD) | Facade dope-context JSON-RPC bridge + catalog registration | Blocked on FACADE-001 | TOOL_CONTRACT.md |
| DMX-MCPINT-HRD-RENAME-015 | MCP Fleet (P7/HRD) | Rename python task-orchestrator → workflow-api | Ready | N/A |
| DMX-MCPINT-HRD-ADHDSURF-016 | MCP Fleet (P7/HRD) | PM surface for context_preserver + overwhelm snapshot | Blocked on RENAME-015 + G8 | G8 ADR |
| DMX-MCPINT-HRD-ADHDROUTE-017 | MCP Fleet (P7/HRD) | Energy-aware routing + event-bus workflow triggers | Blocked on RENAME-015 + EVENTS-006 | adr-mcpint-004 (G2) |
| DMX-MCPINT-HRD-LANE-018 | MCP Fleet (P7/HRD) | Wire decide_lane() into packet pipeline | Ready | model-routing-domain.md |
| TP-DMX-UR-ARTIFACT-INTAKE-001 | Universal Router | Import accepted architecture and audit evidence | Ready | UR-ARCH-001 |
| UR-TP-001 | Universal Router | Strict Universal Router contracts and typed governance refs | Ready after dependency | UR-ARCH-001 |
| TP-SIA-EXEC-0001 | Workflow Plane | Packet Execution Domain Models + Lease Store | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0002 | Workflow Plane | Packet Manifest V2 + Sidecar Contract | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0003 | Workflow Plane | Explicit Routing Slots + Cost Policy | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0004 | Workflow Plane | Supervisor Service + Canonical Commit Flow | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0005 | Workflow Plane | Implementer Runner Adapter Contract | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0006 | Workflow Plane | Auditor Runner + Proof Bundle Manifest | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0007 | Workflow Plane | Manual Handoff + Operator Resume Semantics | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0008 | Workflow Plane | Replay Repro Suite + Projection Hardening | Ready | SIA Packet Execution ADR |
| TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001 | Governance / CI | Local Proof Schema Validation Before Push | Active | N/A |
| TP-DMX-EMBEDDED-AUDIT-VALIDATOR-SCOPE-PARITY-001 | Governance / CI | Bring proof/pr_merge embedded-audit proofs into deterministic validation scope (sweep + pre-commit) | Active | Discovered via PR #1165 |
| TP-DMX-PALETTE-FOCUS-1180-001 | UI Dashboard | Preserve TaskSequencer keyboard focus across task transitions | Active | Discovered via PR #1180 |
| TP-DMX-AIG-001 | Adaptive Ingress Plane | Service Census + Ingress Map + First Safe Slice | Ready | ADR — Adopt a Dopemux Adaptive Ingress Plane with Local Runtime Shims |
| TP-DMX-REPOHYG-001 | Repo Hygiene | Branch and worktree audit with deterministic cleanup plan | Ready | N/A |
| TP-DMX-REPOHYG-002 | Repo Hygiene | Execute phase2 safe archive cleanup | Ready | N/A |
| TP-DMX-REPOHYG-003 | Repo Hygiene | Resolve blocked and ambiguous cleanup survivors | Ready | N/A |
| TP-DMX-REPOHYG-004 | Repo Hygiene | Lost-work audit, stash preservation, and conservative cleanup | Ready | N/A |
| TP-DMX-REPOHYG-005 | Repo Hygiene | Remaining work disposition audit and cleanup-safe local pruning | Ready | N/A |
| TP-DMX-REPOHYG-006 | Repo Hygiene | Deep remaining work audit and recovery queue classification | Ready | N/A |
| TP-DMX-REPOHYG-007 | Repo Hygiene | Recover CLI/system audit hardening tranche from PR #554 | Ready | N/A |
| TP-DMX-REPOHYG-008 | Repo Hygiene | Remove Genetic Agent and Taskmaster active surfaces | Ready | N/A |
| TP-DMX-RTEAUDIT-001 | Repo Truth Extractor | Assemble pre-live audit pack for GPT-5.4 Pro | Ready | N/A |
| TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001 | Repo Truth Extractor | Assemble GPT-5.5 Pro multi-pass audit pack | Active | N/A |
| TP-DMX-RTEOPUS-AUDIT-DOCS-001 | Repo Truth Extractor | Add recovered Opus UI/UX Claude design audit bundle to docs/audit | Active | N/A |
| TP-DMX-RTEINT-001 | Repo Truth Extractor | Integrate current RTE branch deltas into staging audit branch | Ready | N/A |
| TP-DMX-RTECANON-001 | Repo Truth Extractor | Establish `dopemux rte` as the canonical operator entrypoint | Ready | N/A |
| TP-RTE-V3-CONSENT-004 | Repo Truth Extractor | Gate legacy v3 execution and fail closed on unknown pipeline versions | Active | N/A |
| TP-RTE-WALKER-006 | Repo Truth Extractor | Exclude generated artifacts and secret-bearing files from prescan walker input | Active | N/A |
| TP-RTE-GOLIVE-REMEDIATION-001 | Repo Truth Extractor | Harden go-live preflight truth-split, SP registry contract, and cost-cap gates | Active | N/A |
| TP-RTE-GOLIVE-REMEDIATION-002 | Repo Truth Extractor | Contain pre-live validator execution and require parsed GO verdicts | Active | N/A |
| TP-RTE-BATCH-005 | Repo Truth Extractor | Repair batch result extraction and strict batch request payload handling | Merged (PR #614) | N/A |
| TP-RTE-BATCH-E2E-006 | Repo Truth Extractor | Wire strict batch response_format through v5 request construction | Merged (PR #615) | N/A |
| TP-RTE-STRICT-ATTESTATION-007 | Repo Truth Extractor | Ground strict passthrough attestations in runtime evidence | Merged (PR #616) | N/A |
| TP-RTE-DOCS-CANON-008 | Repo Truth Extractor | Canonicalize RTE operator docs around `dopemux rte` | Active | N/A |
| TP-RTE-FINAL-AUDIT-GROK-NONE-REASONING-006 | Repo Truth Extractor | Preserve xAI Grok 4.3 reasoning_effort=none | Merged (PR #705) | proof/repo-truth-extractor/audit-2026-05-22/TP-RTE-FINAL-AUDIT-GROK-NONE-REASONING-006_PROOF.json |
| TP-RTE-COSTPROFILE-E3-CONTRACTS-001 | Repo Truth Extractor | Extend structured_output_contracts.py: service_tier passthrough, prompt_caching_directives helper, anthropic_tool_use schema variant | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-E4-FINISH-001 | Repo Truth Extractor | Finish llm_runtime wiring: meta-dict exposure of service_tier / cached_tokens; cell alias resolution at call_llm entry | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-E7-LADDERS-FAILOVER-001 | Repo Truth Extractor | Rewrite 11 hardcoded ladder constants to cell-aliased lookups; add per-request failover + --disable-provider kill-switch | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-E8-YAML-V3-001 | Repo Truth Extractor | Restructure model_map.yaml to v3 (lane_defaults + tag_definitions + impact_class + 6 per-step overrides) + migration script | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-E9-TESTS-001 | Repo Truth Extractor | Integration coverage for cost-profile end-to-end flow across all 4 profiles + Anthropic cache + batch discount | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-F-VERIFY-001 | Repo Truth Extractor | Series-final verification gate: full test run + promptset v3 audit + bounded-lane dry-run + pal/codereview + pal/precommit | NOT_VERIFIED_ACCEPTED_AS_EVIDENCE | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-F-VERIFY-TOPOLOGY-REPAIR-001 | Repo Truth Extractor | Rehome F-VERIFY-001 proof/ledger evidence from polluted PR #698 onto a main-targeted replacement PR | Active | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001 | Repo Truth Extractor | Repair CostProfile F full-suite failures accepted as evidence by F-VERIFY-001 | Merged (PR #709) | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-F-VERIFY-002 | Repo Truth Extractor | Series-gate verification after F-FULLSUITE-REPAIR (#709) and INDEX correction (#710): full RTE suite + bounded print-config + OpenRouter route-readiness + CLI import probes | Merged (PR #712) | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-OUTPUT-VALIDATORS-001 | Repo Truth Extractor | Post-step output validators (control_plane_truth_check + security_claim_verification) for structural / security_sensitive impact_class | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-RTE-COSTPROFILE-XAI-BATCH-VERIFY-001 | Repo Truth Extractor | Live probe to determine xAI /v1/batches support; updates spend_ledger + batch_clients + cost profile based on verdict | Ready | docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md |
| TP-DMX-AGENTS-CODEX-ENDTOEND-0001 | Agent Guidance | Make Codex execute TP lifecycle end-to-end by default | Ready | N/A |
| TP-DMX-ORCH-DOCS-003 | Task Orchestrator | Document read-only/operator-status integration authority boundaries | Active | N/A |
| TP-DMX-COMPOSE-RESTORE-001 | Infra | Restore canonical Docker Compose authority | Ready | N/A |
| TP-CI-FULL-TEST-SUITE-001 | CI | Gate full RTE and auditor-router test suites | Active | N/A |
| TP-UI-DASHBOARD-BUILD-001 | UI Dashboard | Restore ui-dashboard npm install and build | Active | N/A |
| TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS | Infra | Gate core MCP compose dependencies on healthchecked services | Active | N/A |
| TP-BETA-MCP-03-ADHD-REDIS-ISOLATION | ADHD Engine | Isolate ADHD Engine Redis keys by instance | Active | N/A |
| TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001 | Infra / MCP | Restore GPT Researcher MCP container entrypoint and update package pin | Active | N/A |
| TP-DMX-MCP-FLEET-ROADMAP-001-CATALOG-CONTRACT | MCP Fleet | Canonical catalog contract and static drift gates | Active | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-002-GENERATED-OUTPUTS | MCP Fleet | Generated MCP config outputs from canonical catalog | Ready | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-003-MCP-ENSURE | MCP Fleet | Add `dopemux mcp ensure --fast/--full` remediation layer | Ready | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-004-MEMORY-SPINE | MCP Fleet / Memory | Capture promotable source events for chronicle spine | Ready | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-005-SERVER-PERSONALITIES | MCP Fleet | Converge server personalities after catalog gates | Ready | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-006-DCP-ACTIVATION | DCP / MCP | Activate read-only DCP facade follow-ons | Ready | PR #993 audit input |
| TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE | MCP Fleet | Quarantine dead MCP surfaces after reverse dependency proof | Ready | PR #993 audit input |
| TP-SEC-COMPOSE-LITELLM-LOCALHOST-001 | Security | Externalize LiteLLM healthcheck key and localize compose service ports | Active | N/A |
| TP-SEC-WEAK-DEFAULT-SECRETS-001 | Security | Reject weak default secrets in env template and installer | Active | N/A |
| TP-DMX-ADHD-SIGNAL-E2E-WIRING-001 | ADHD Engine / Dashboard | Prove synthetic ADHD state updates reach the dashboard UI band | Active | N/A |
| TP-DMX-ADHD-SECRET-DEFAULTS-001 | ADHD Engine / Security | Remove remaining ADHD/WMA weak default secrets and fail closed outside dev/test/local | Active | N/A |
| TP-DMX-ADHD-PRIVACY-PAYLOADS-001 | ADHD Engine / Activity Capture | Enforce content-free ADHD activity payloads | Active | N/A |
| TP-DOCS-FIRST-TOUCH-PRODUCT-NAME-001 | Docs | Refresh active Start Here onboarding and product naming | Active | N/A |
| TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001 | Auditor Fleet / Governance | Deterministic evidence intake for auditor fleet campaign DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13 | Active | N/A |
| DMX-COCKPIT-STATIC-002 | UI Cockpit | Expose deterministic static cockpit renderer through guarded CLI wrapper | Merged (PR #528) | N/A |
| TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001 | UI Cockpit | Audit and prepare Cockpit PR stack 568-571 plus PR 573 evidence for safe consolidation | Active | N/A |
| TP-DMX-COCKPIT-COMMAND-PALETTE-001 | UI Cockpit | Reconcile Command Palette broker primitive onto current main | Active | N/A |
| TP-DMX-COCKPIT-RUNTIME-RENDER-001 | UI Cockpit | Wire runtime renderer primitives to accepted Cockpit IA package contract | Active | N/A |
| TP-DMX-COCKPIT-SAFE-ACTIONS-001 | UI Cockpit | Materialize Safe Action Gate primitive contract packet metadata | Active | N/A |
| TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 | UI Cockpit | Wire Settings/Admin/Runtime primitive surface to runtime renderer | Active | N/A |
| TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 | UI Cockpit | Wire Unknown / Drift Queue primitive surface to runtime renderer | Active | N/A |
| TP-DMX-COCKPIT-INVENTORY-REGEN-001 | UI Cockpit | Regenerate current-head Cockpit command/surface inventory artifacts | Active | N/A |
| TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001 | UI Cockpit | Repair Cockpit runtime contract-fidelity gaps | Active | N/A |
| TP-DMX-COCKPIT-DESIGN-PICKUP-001 | UI Cockpit | Create current-state Cockpit design pickup brief after pack-to-main consolidation | Active | N/A |
| TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001 | UI Cockpit | Implement Direction B Electric Refresh five-mode runtime continuation | Active | N/A |
| TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001 | UI Cockpit | Compare merged Cockpit runtime renders against uploaded PNG references without design fixes | Active | N/A |
| TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001 | UI Cockpit | Generate repeatable Cockpit Textual screenshots for current five-mode runtime proof | Active | N/A |
| TP-DMX-MOBILE-TUI-SPEC-001 | UI Cockpit | Install mobile-first tmux Cockpit UX specification without runtime changes | Active | N/A |
| PACKET_031 | Memory | Dual Capture Adapters, Single Ledger | Executing | ADR-213 |
| PACKET_032 | Memory | Chronicle Promotion Guards | Pending Audit | ADR-214 |
| DMX-COCKPIT-PMIMPL-PACK-001 | Cockpit / PM Plane | PM/Implementer cockpit processing pack | Ready | N/A |
| TP-DMX-COCKPIT-MAIN-STATE-RECON-001 | UI Cockpit | Reconcile origin/main and open PR cockpit state vs the pack remediation stack | Executed | N/A |
| TP-DMX-COCKPIT-MERGE-EXECUTE-001 | UI Cockpit | Define Ledger-gated Cockpit pack merge execution procedure without authorizing runtime mutation | Blocked Preflight | N/A |
| TP-DMX-DEPENDABOT-UV-RESOLVER-001 | Dependencies / CI | Repair Dependabot uv security update resolver metadata | Active | N/A |
| TP-BETA-INSTALL-02-CLAUDE-REVIEW-001 | Installer | Apply Claude review cleanup to BETA-INSTALL-02 network repair | Active | N/A |
| TP-BETA-INSTALL-01-MCP-01-REVIEW-001 | MCP Config | Repair PR #737 review blockers for portable Task Orchestrator launch | Active | N/A |
| TP-BETA-CLI-01-DECISIONS-REVIEW-001 | CLI Decisions | Repair PR #740 review blockers for decisions CLI subcommands | Active | N/A |
| TP-DMX-ADHD-INTERACTIVE-PROMPTS-001 | ADHD UX | Wire interactive prompts into launch and profile flows | Active | N/A |
| TP-DMX-ORCH-AUDIT-FIX-001 | Task Orchestrator | Close DMX-ORCH integration audit gaps | Active | N/A |
| DMX-DCP-MODEL-ROUTING-MVP-0006 | DCP / Model Routing | Classifier provenance hardening for trust-lowering signals | Active | N/A |
| DMX-DCP-MODEL-ROUTING-MVP-0007 | DCP / Model Routing | Trusted input-provenance contract for execution eligibility | Active | N/A |
| TP-DMX-DCP-FULL-SYSTEM-P0-AUTHORITY-CONTRACT-FREEZE-001 | DCP / Full System | Freeze DCP full-system authority and contracts | Active | docs/90-adr/adr-dcp-full-system-v1-authority-and-contract-freeze.md |
| TP-DMX-DCP-P0-PR1283-REPAIR-001 | DCP / Full System | Repair PR #1283 P0 contract review findings in place | Active | TP-DMX-DCP-FULL-SYSTEM-P0-AUTHORITY-CONTRACT-FREEZE-001 |
| TP-DMX-DCP-P0-PR1283-REPAIR-002 | DCP / Full System | Repair PR #1283 P0 cross-object authority validation in place | Active | TP-DMX-DCP-P0-PR1283-REPAIR-001 |
| TP-DMX-DCP-P0-PR1283-CROSS-AUTHORITY-CLOSURE-001 | DCP / Full System | Close PR #1283 cross-authority contract relationships | Active | TP-DMX-DCP-P0-PR1283-REPAIR-002 |
| TP-DCP-MCP-RO-0002 | DCP / MCP | Architecture Doc And Multi Project Contract | Active | N/A |
| TP-DCP-MCP-RO-0003 | DCP / MCP | Inspect Dopemux Init Registry Contract | Active | N/A |
| TP-DCP-MCP-RO-0004 | DCP / MCP | Facade Scaffold Registry Resolver Repo Proof Tools | Active | N/A |
| TP-DCP-MCP-RO-0005 | DCP / MCP | ConPort And Dope Memory Read Adapters | Active | N/A |
| TP-DCP-MCP-RO-0006 | DCP / MCP | Dope Context And Task Orchestrator Read Adapters | Active | N/A |
| TP-DCP-MCP-RO-0007 | DCP / MCP | Secure MCP Tunnel Integration Docs And Manual Validation | Active | N/A |
| TP-DCP-MCP-RO-0008 | DCP / MCP | Hardening Cross Project Isolation And PR Readiness | Active | N/A |
| TP-DCP-MCP-RO-0012 | DCP / MCP | Public Facade Target Contract Migration | Active | TP-DCP-MCP-RO-0011-REMEDIATION-01 |
| TP-DCP-MCP-RO-0013 | DCP / MCP | Connector Policy Schema And Auth Context | Active | TP-DCP-MCP-RO-0012 |
| TP-DCP-MCP-RO-0014 | DCP / MCP | Loopback Streamable HTTP Ingress | Active | TP-DCP-MCP-RO-0013 |
| TP-DCP-MCP-RO-0015 | DCP / MCP | Ownership Verification And Release-One Adapters | Active | TP-DCP-MCP-RO-0014 |
| TP-DCP-MCP-RO-0016 | DCP / MCP | Multi-Provider Setup And Rollback Docs | Active | TP-DCP-MCP-RO-0015 |
| TP-DCP-MCP-RO-0017 | DCP / MCP | Acceptance Matrix And Fail-Closed Harness | Active | TP-DCP-MCP-RO-0016 |
| TP-DCP-MCP-RO-0018 | DCP / MCP | Exact-Head Proof Readiness Evaluator | Active | TP-DCP-MCP-RO-0017 |
| TP-DCP-MCP-RO-0017-VENDOR | DCP / MCP | Vendor-Live Preflight And Two-Target Isolation | Active | TP-DCP-MCP-RO-0017 |
| DMX-DCP-PROMPT5-EXTRACT-RECON-001 | DCP / Prompt 5 | Extract Prompt 5 chat-history docs and reconcile PR/Task Orchestrator runway state | Active | N/A |

────────────────────────────────────────────────────────────
🟢 Completed Task Packets

| Packet ID | Subsystem | Title | Completion Date | Outcome |
| --- | --- | --- | --- | --- |
| TP-DMX-RTEAUDIT-110 | Repo Truth Extractor | Gemini deep PAL audit across UX, prompts, routing, and operator readiness | 2026-04-23 | Accepted (Conditional Go) |
| TP-PM-ARCH-04A | PM Plane | Canonical PMTask Model + Store (Unit-only) | 2026-03-22 | Accepted |
| TP- PM-ARCH-04B | PM Plane | Canonical pm.* Events + Adapters | 2026-03-22 | Accepted |
| PACKET_024 | Infra | MCP Health Surface Hardening | 2026-01-26 | Accepted |
| PACKET_021 | Memory | Deterministic Chronicle Schema | 2026-01-18 | Accepted |
| TP-DMX-AI-ROUTING-001 | Governance / AI Routing | Stage-based dev-workflow AI model routing policy, reference, how-to, and Copilot agent stage tagging | 2026-06-06 | Accepted (PR #837, commit b987da994) |
| TP-DMX-AI-ROUTING-002 | Governance / AI Routing | Proof bundle schema and proof contract cross-references to the stage routing policy | 2026-06-06 | Accepted (PR #837, commit b987da994) |

────────────────────────────────────────────────────────────
⚪ Superseded Task Packets

| Packet ID | Superseded By | Reason |
| --- | --- | --- |
| PACKET_017 | PACKET_021 | Incomplete determinism guarantees |

────────────────────────────────────────────────────────────
🧠 Index Maintenance Rules
Never delete historical packets
Never reuse packet IDs
Status changes must be explicit
Completed packets require an audit outcome
Superseded packets must reference the replacing packet
────────────────────────────────────────────────────────────
Final Rule
If it’s not indexed here, it didn’t happen.

────────────────────────────────────────────────────────────

## 🟡 Active Task Packets — DMX-BACKLOG-2026-07-07 (52)

Backlog conversion of Memory Context Fabric + MCP fleet audit + forgotten-features + runtime-bug findings (PRs #1011/#1002/#1009). Decisions: `claudedocs/backlog/decisions-ledger.md`. Traceability: `claudedocs/backlog/README.md`. Load-plan: `claudedocs/backlog/loadplan.json`. All schema-valid; authored, not executed.

| Packet ID | Series | Disp | Status | Depends On |
| --- | --- | --- | --- | --- |
| DMX-MCF-002-transcript-ingest | DMX-MCF | BUILD | Ready | — |
| DMX-MCF-003-decision-candidate | DMX-MCF | BUILD | Ready | DMX-MCF-002-transcript-ingest |
| DMX-MCF-004-sessionstart-recap | DMX-MCF | BUILD | Ready | DMX-MCF-003-decision-candidate |
| DMX-MCF-005-semantic-projection-spec | DMX-MCF | SPEC | Ready | DMX-MCF-004-sessionstart-recap, DMX-ADR-001-semantic-memory-home |
| DMX-MCF-006-conport-graph-spike-spec | DMX-MCF | SPEC | Ready | DMX-ADR-005-conport-graph-exposure |
| DMX-MCF-007-fabric-orchestrator-spec | DMX-MCF | SPEC | Ready | DMX-MCF-002-transcript-ingest, DMX-MCF-003-decision-candidate, DMX-MCF-004-sessionstart-recap |
| DMX-MCF-008-summarizer-spec | DMX-MCF | SPEC | Ready | DMX-MCF-003-decision-candidate, DMX-MCF-007-fabric-orchestrator-spec |
| DMX-MCF-009-proactive-injection-spec | DMX-MCF | SPEC | Ready | DMX-MCF-007-fabric-orchestrator-spec |
| DMX-FLEET-P0-001-real-healthchecks | DMX-FLEET-P0 | BUILD | Ready | — |
| DMX-FLEET-P0-002-ensure-pal-managed | DMX-FLEET-P0 | BUILD | Ready | — |
| DMX-FLEET-P0-003-conport-schema-verify-failclosed | DMX-FLEET-P0 | WIRE | Ready | — |
| DMX-FLEET-P0-004-registry-dedup | DMX-FLEET-P0 | DELETE | Ready | — |
| DMX-FLEET-P0-005-wrapper-path-fixes | DMX-FLEET-P0 | BUILD | Ready | — |
| DMX-FLEET-P0-006-quarantine-killlist | DMX-FLEET-P0 | BUILD | Ready | — |
| DMX-FLEET-P0-007-desktop-commander-upstream | DMX-FLEET-P0 | REBUILD | Ready | — |
| DMX-FLEET-P1-001-unified-catalog-spec | DMX-FLEET-P1 | SPEC | Ready | DMX-FLEET-P0-004-registry-dedup |
| DMX-FLEET-P1-002-codegen-pipeline-spec | DMX-FLEET-P1 | SPEC | Ready | DMX-FLEET-P1-001-unified-catalog-spec |
| DMX-FLEET-P1-003-mcp-ensure-command | DMX-FLEET-P1 | SPEC | Ready | DMX-FLEET-P1-001-unified-catalog-spec, DMX-FLEET-P0-002-ensure-pal-managed |
| DMX-FLEET-P1-004-ci-drift-gates | DMX-FLEET-P1 | BUILD | Ready | DMX-FLEET-P1-002-codegen-pipeline-spec |
| DMX-FLEET-P1-005-orchestrator-autostart | DMX-FLEET-P1 | SPEC | Ready | — |
| DMX-FLEET-P1-006-exa-retire-cleanup | DMX-FLEET-P1 | RETIRE | Ready | — |
| DMX-FLEET-P1-007-token-truncation-utility-spec | DMX-FLEET-P1 | SPEC | Ready | — |
| DMX-FLEET-P2-001-event-source-wiring | DMX-FLEET-P2 | WIRE | Ready | — |
| DMX-FLEET-P2-002-heartbeat-ratelimit | DMX-FLEET-P2 | BUILD | Ready | — |
| DMX-FLEET-P2-003-instance-identity-propagation | DMX-FLEET-P2 | SPEC | Ready | — |
| DMX-FLEET-P2-004-skill-mirror-receipts | DMX-FLEET-P2 | BUILD | Ready | — |
| DMX-FLEET-P2-005-dopecontext-indexing-enable | DMX-FLEET-P2 | BUILD | Ready | DMX-FLEET-P2-001-event-source-wiring |
| DMX-FLEET-P3-001-conport-jsonrpc-parity | DMX-FLEET-P3 | SPEC | Ready | — |
| DMX-FLEET-P3-002-serena-promotion | DMX-FLEET-P3 | WIRE | Ready | DMX-ADR-002-serena-promotion |
| DMX-FLEET-P3-003-complexity-unify-spec | DMX-FLEET-P3 | SPEC | Ready | DMX-ADR-004-complexity-scorer |
| DMX-FLEET-P3-004-qdrant-gc | DMX-FLEET-P3 | DELETE | Ready | — |
| DMX-FLEET-P3-005-voyage-cost-guard | DMX-FLEET-P3 | WIRE | Ready | — |
| DMX-FLEET-P3-006-loopback-binds | DMX-FLEET-P3 | BUILD | Ready | — |
| DMX-FLEET-P4-001-facade-g1-contract-test | DMX-FLEET-P4 | WIRE | Ready | — |
| DMX-FLEET-P4-002-dopecontext-bridge-spec | DMX-FLEET-P4 | SPEC | Ready | — |
| DMX-FLEET-P4-003-lane-engine-wire | DMX-FLEET-P4 | WIRE | Ready | DMX-ADR-003-lane-engine-dispatch |
| DMX-FLEET-P4-004-inventory-freshness-gate | DMX-FLEET-P4 | WIRE | Ready | DMX-FLEET-P4-001-facade-g1-contract-test |
| DMX-FLEET-P4-005-facade-catalog-register | DMX-FLEET-P4 | WIRE | Ready | DMX-FLEET-P1-001-unified-catalog-spec |
| DMX-FLEET-P5-001-e2e-acceptance | DMX-FLEET-P5 | SPEC | Ready | DMX-FLEET-P1-003-mcp-ensure-command, DMX-FLEET-P2-005-dopecontext-indexing-enable |
| DMX-FLEET-P5-002-docs-reconciliation | DMX-FLEET-P5 | WIRE | Ready | — |
| DMX-FLEET-P5-003-proof-discipline | DMX-FLEET-P5 | BUILD | Ready | — |
| DMX-ADHD-WIRE-001-predictive-risk-hook | DMX-ADHD-WIRE | WIRE | Ready | — |
| DMX-ADHD-WIRE-002-context-preservation-display | DMX-ADHD-WIRE | WIRE | Ready | — |
| DMX-ADHD-WIRE-003-overwhelm-snapshot | DMX-ADHD-WIRE | WIRE | Ready | — |
| DMX-ADHD-WIRE-004-relationship-vocab-widening | DMX-ADHD-WIRE | WIRE | Ready | DMX-FLEET-P3-001-conport-jsonrpc-parity |
| DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec | DMX-ADHD-WIRE | SPEC | Ready | DMX-FLEET-P3-002-serena-promotion |
| DMX-ADHD-WIRE-006-fatigue-contextswitch-resurrect-spec | DMX-ADHD-WIRE | SPEC | Ready | DMX-FLEET-P3-002-serena-promotion, DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec |
| DMX-ADR-001-semantic-memory-home | DMX-ADR | ADR | Ready | — |
| DMX-ADR-002-serena-promotion | DMX-ADR | ADR | Ready | — |
| DMX-ADR-003-lane-engine-dispatch | DMX-ADR | ADR | Ready | — |
| DMX-ADR-004-complexity-scorer | DMX-ADR | ADR | Ready | — |
| DMX-ADR-005-conport-graph-exposure | DMX-ADR | ADR | Ready | — |
