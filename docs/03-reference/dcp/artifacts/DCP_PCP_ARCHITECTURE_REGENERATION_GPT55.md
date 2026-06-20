---
id: DCP_PCP_ARCHITECTURE_REGENERATION_GPT55
title: Dcp Pcp Architecture Regeneration Gpt55
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: Dcp Pcp Architecture Regeneration Gpt55 (reference) for dopemux documentation
  and developer workflows.
---
# Full PCP/DCP Architecture Regeneration — Decision Artifact (GPT-5.5 Pro, 2026-06-19)

> [!NOTE]
> **Provenance**: `EXTERNAL_PROPOSED`
> **Status**: Audited design input (not runtime authority)
> **Source**: `audit_inputs/PCP-DCP-RECONCILIATION.md`
> **Audited-by**: `DCP_PCP_OPUS_AUDIT_OF_REGENERATION.md`
> **Audit verdict**: `ACCEPT_WITH_CORRECTIONS` (apply the audit's §6 corrections before writing the AIR)
>
> This file is the verbatim GPT-5.5 Pro PCP/DCP architecture regeneration result, preserved
> durably as a design-input artifact. It is not runtime truth. Where it conflicts with runtime
> code, config, tests, or the repo authority docs, runtime wins (AGENTS.md §2). The companion
> Opus audit records confirmed claims, required corrections, and build-order reordering.

According to a document from June 19, 2026, the strongest reconciliation is: **PCP Core is the parent, DCP is a Dopemux extension, dNh is a project extension, and PR #925 is salvageable but not merge-ready.** 

# Full PCP/DCP Architecture Regeneration and Build Plan

## 1. Executive Decision

```text
ARCHITECTURE_VERDICT: PCP_PARENT_MODEL_ACCEPTED_WITH_CORRECTIONS
CURRENT_PR925_VERDICT: KEEP_DRAFT_PENDING_CORE_REPAIR
NEXT_BUILD_ACTION: PR925_FRAMING_PROOF_REPAIR
```

**OBSERVED_BY_ADJUDICATION:** PCP Core is the reusable parent substrate; DCP is not the parent; dNh is not the template; both are extensions. 
**OBSERVED_BY_FILE:** The repo authority model is split across `dopemux`, `dopetask`, task-orchestrator, Leantime, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, and Repo-Truth-Extractor, so a monolithic DCP parent model is wrong. 
**OBSERVED_BY_ADJUDICATION:** PR #925 still leaks Dopetask and Task Orchestrator concepts into generic PCP artifacts, and the extension contract plus generic authority-map schema are missing. 
**OBSERVED_BY_PROOF:** PR #925 currently validates fixture shape and dry-run contracts only; generic runtime exporter behavior remains unproven. 
**CLAIMED_ONLY:** The newly supplied Pro 5.5 adjudication is useful as input, especially on verdict-label repair and proof freshness, but its proposed order putting the generic exporter before the extension contract is not accepted.
**INFERRED:** Building the exporter before the extension boundary risks baking the current Dopemux-shaped core into runtime code.
**PROPOSED:** Do PR #925 framing/proof repair first because it is the narrowest safe cleanup, then define the extension contract and de-Dopemux the core before any generic exporter.
**BLOCKED:** No live writes, no FastAPI bridge, no Task Orchestrator write, no dNh runtime mutation, and no `dopetask` execution belong in the next move.
**READY:** The target architecture model is ready for build sequencing.
**NEEDS_SUPERVISOR:** PR #925 is not ready to merge.

---

## 2. Evidence Ledger

| Evidence                             |                     Status | What it proves                                                                                             | What it does not prove                  | Caveat                                                                |
| ------------------------------------ | -------------------------: | ---------------------------------------------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------- |
| Opus adjudication                    |   OBSERVED_BY_ADJUDICATION | PCP parent model accepted with corrections; #925 is Dopemux-shaped in required fields                      | Runtime exporter correctness            | Strongest on boundary repair                                          |
| Pro adjudication                     |   OBSERVED_BY_ADJUDICATION | Target model accepted; PR #925 needs label/proof repair                                                    | Safe build order by itself              | New pasted Pro input is CLAIMED_ONLY until independently validated    |
| Synthesized adjudication             |   OBSERVED_BY_ADJUDICATION | Stricter reading wins; PCP parent, DCP/dNh extensions                                                      | Merge readiness                         | It is a synthesis, not runtime                                        |
| Grok Build input pack                |           OBSERVED_BY_FILE | Contains PR #925, PR #931, DCP, dNh, repo authority, proof inputs                                          | Live current GitHub after pack creation | Fresh as June 19, 2026 bundle                                         |
| PR #925 metadata                     |           OBSERVED_BY_FILE | Open draft fixture-only architecture PR in bundle                                                          | Current remote status after bundle      | Treat as stale if PR moved                                            |
| PR #925 diff                         |           OBSERVED_BY_DIFF | Adds schemas, fixtures, proof/report docs, dry-run artifacts                                               | Runtime implementation                  | No exporter/runtime package                                           |
| PR #925 checks                       |             OBSERVED_BY_CI | Syntax/schema checks ran in captured evidence                                                              | Semantic architecture proof             | Green CI is not semantic proof                                        |
| PR #925 review threads               |         OBSERVED_BY_GITHUB | Review state exists and must be classified                                                                 | Merge safety                            | Unknown/unclassified blocks READY                                     |
| `PROOF.json`                         |          OBSERVED_BY_PROOF | Captures fixture validation and proof posture                                                              | Runtime behavior                        | Proof freshness is disputed/stale                                     |
| `AUDITOR_REPORT.md`                  |          OBSERVED_BY_PROOF | `NEEDS_SUPERVISOR`; flags finality/audit-independence issues                                               | Acceptance                              | Auditor is not merge authority                                        |
| `ARCHITECTURE_VALIDATION_REPORT.md`  |          OBSERVED_BY_PROOF | Contract-shape validation posture                                                                          | Generic runtime operation               | Overstrong if called “confirmed”                                      |
| `E2E_DRY_RUN_RESULT.json`            |          OBSERVED_BY_PROOF | Dry-run chain exists; no live writes claimed                                                               | Executed classifier/exporter behavior   | Negative cases are asserted                                           |
| PCP schemas                          |           OBSERVED_BY_DIFF | Core-ish schema set exists                                                                                 | Clean core boundary                     | Contains Dopetask/TO leaks                                            |
| DCP schemas                          |           OBSERVED_BY_FILE | Rich Dopemux/DCP routing/lane schema family exists                                                         | PCP parenthood                          | Extension material must be mapped down                                |
| OpenClaw routing contracts / PR #931 |           OBSERVED_BY_FILE | Contracts-only routing policy exists; PR #931 bundle says no production routing and no benchmark execution | Runtime routing readiness               | PR #931 state in local bundle was closed; not treated as live current |
| dNh fixtures                         |           OBSERVED_BY_FILE | dNh can be modeled as fixture/adapter target                                                               | Live dNh adapter/exporter               | Runtime mutation is unproven                                          |
| Dopemux fixture                      |           OBSERVED_BY_FILE | Dopemux extension profile direction exists                                                                 | Generic PCP                             | It is the project extension, not core                                 |
| Minimal fixture                      |           OBSERVED_BY_FILE | Shape for a generic repo was attempted                                                                     | True genericity                         | Still contains Dopetask/Task Orchestrator flags                       |
| Repo authority docs                  |           OBSERVED_BY_FILE | Split authority and non-responsibility boundaries                                                          | Target PCP implementation               | Docs may lag runtime, but align with truth order                      |
| DCP runtime code if attached         | PARTIAL / OBSERVED_BY_FILE | DCP classifier/lane/red-lane material exists in bundle                                                     | PCP runtime                             | Treat as Dopemux extension material unless generalized                |

---

## 3. True Target Architecture

```text
PCP Core
  generic repo discovery
  generic project identity
  generic project profile
  generic authority map
  generic evidence export
  generic red-lane policy and engine
  generic proof/status pointers
  generic validation and dry-run harness
  generic negative-case runner
  generic extension contract
  generic exporter
  baseline no-extension operation

Extensions
  Dopemux / DCP extension
    dopemux CLI/startup/routing profile
    Dopetask execution mapping
    Task Orchestrator projection mapping
    Leantime metadata mapping
    ConPort structured context mapping
    dope-memory chronicle mapping
    dope-context retrieval mapping
    dopecon-bridge adapter mapping
    ADHD Engine operator-support mapping
    Repo Truth Extractor artifact mapping
    PR Steward readiness mapping
    OpenClaw / OpenRouter / model-routing contracts

  dNh CRM extension
    dNh project profile
    dNh authority docs
    CRM runtime map
    Telegram map
    calendar map
    identity/policy/event-store/runtime DB map
    dNh proof roots
    dNh red lanes
    artifact-only exporter constraints

  Other project extensions
    project profile values
    project authority map
    project red lanes
    project proof/status paths
    project adapters

Planes
  project runtime boundary
  execution plane
  audit plane
  proof plane
  workflow/projection plane
  live-write gates
```

**PCP Core** is the reusable control substrate for any Git repo. It must operate with `.git` discovery, conservative defaults, generic evidence export, fail-closed UNKNOWNs, and no dependency on Dopemux/dNh-specific systems.

**Extensions** enrich PCP with project-specific systems. They do not replace PCP Core rules, promote themselves to authority, or weaken proof/audit gates.

**Project runtime boundary** marks the line where PCP observes and exports evidence but does not mutate runtime state without a later live-write gate.

**Execution plane** handles runner mapping and proof requirements. In PCP Core this is generic; in DCP it maps to Dopetask/Codex/Claude/Gemini/AGY/OpenClaw only through extension contracts.

**Audit plane** requires independence. Creator cannot be sole auditor, and release/security work requires independent audit or explicit human approval. 

**Proof plane** binds evidence to repo, branch, head SHA, commands, exits, diffs, and artifacts. READY cannot derive from stale proof. 

**Workflow/projection plane** exposes status/views. It must not become authority for proof, merge, PM truth, or runtime writes.

**Live-write gates** come last. No live write until canonical writer, allowlist, rollback, human signoff, independent audit, dry-run proof, and post-write verification are all proven.

---

## 4. PCP Core Contract

| Capability                         | Core responsibility                                                      | Required schema/artifact                                |          Current status | Missing work                                       |
| ---------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------- | ----------------------: | -------------------------------------------------- |
| Generic repo discovery             | Discover repo root, branch/ref, dirty state, file inventory, source docs | `repo_discovery.schema.json` or exporter output section |       MISSING / PARTIAL | Implement `.git`-first discovery                   |
| Generic project identity           | Stable project ID/name/kind without Dopemux assumptions                  | `project_identity` inside `project_profile`             |                 PARTIAL | Remove task-packet assumptions as required core    |
| Generic project profile            | Describe repo and optional control-plane surfaces                        | `project_profile.schema.json`                           |                 PARTIAL | Split core required fields from extension fields   |
| Generic authority map              | Model canonical owners by domain/action                                  | `authority_map.schema.json`                             |                 MISSING | Build first-class generic schema                   |
| Generic evidence export            | Export observed repo/profile/proof/red-lane facts                        | `project_evidence_export.schema.json`                   |   PARTIAL / CONFLICTING | Remove Dopetask/Task Orchestrator fields from core |
| Generic red-lane policy/engine     | Evaluate generic risk lanes and fail closed                              | `project_red_lanes.schema.json`, runner                 |                 PARTIAL | Actual evaluator, not asserted fixture result      |
| Generic proof/status pointer       | Point to proof with freshness/status/audit states                        | `proof_pointer.schema.json`                             |                 PARTIAL | Bind to head SHA and proof family                  |
| Generic validation/dry-run harness | Validate schemas and computed outputs                                    | validation reports + tests                              |                 PARTIAL | Replace asserted negatives with executed traps     |
| Generic extension contract         | Load extension manifest and extension-owned fields safely                | `extension_manifest.schema.json`, registry              |                 MISSING | Keystone packet                                    |
| Generic negative-case runner       | Execute fail-closed traps                                                | `negative_case_result.schema.json`                      | MISSING / ASSERTED_ONLY | Computed failure index                             |
| Generic exporter                   | Run on arbitrary Git repo with no extension                              | exporter command + output artifacts                     |                 MISSING | Must wait until boundary repair                    |
| Baseline no-extension operation    | Generate minimal profile/evidence/proof pointers                         | generic fixture + runtime proof                         |                 UNKNOWN | Plain Git repo acceptance test                     |

---

## 5. PCP Extension Contract

**PROPOSED:** The missing contract is the architecture hinge. Without it, “PCP + extension” is prose in a lab coat.

Required elements:

```yaml
extension_manifest:
  schema_version: pcp.extension_manifest.v0
  extension_id: string
  extension_name: string
  extension_kind: [DOPMUX_DCP, DNH_CRM, PROJECT, UNKNOWN]
  compatible_pcp_core_versions: [string]
  extension_identity:
    project_id_patterns: []
    repo_markers: []
    optional_discovery_hints: []
  capabilities:
    authority_map_contributions: []
    red_lane_contributions: []
    evidence_export_sections: []
    proof_status_mappings: []
    runtime_mappings: []
    adapter_mappings: []
    exporter_modes: []
  schemas:
    owned_schema_ids: []
    core_schema_extensions: []
    forbidden_core_overrides: []
  evidence_paths:
    authority_docs: []
    proof_roots: []
    status_roots: []
    fixture_roots: []
  adapters:
    read_adapters: []
    projection_adapters: []
    write_adapters: []
  invariants:
    cannot_override_core_fail_closed: true
    cannot_weaken_proof_gates: true
    cannot_weaken_audit_gates: true
    cannot_promote_adapter_to_authority: true
    cannot_require_extension_for_baseline_core: true
```

| Contract rule                         | Required behavior                                                            |
| ------------------------------------- | ---------------------------------------------------------------------------- |
| Extension manifest                    | Declares identity, capabilities, schema ownership, evidence paths            |
| Extension identity                    | Names project/repo/domain without changing PCP Core identity                 |
| Extension capabilities                | Additive only                                                                |
| Extension-owned schemas               | Namespaced under extension, not `schemas/project_control_plane/`             |
| Extension-owned red lanes             | Contribute to core engine; cannot bypass it                                  |
| Extension-owned evidence paths        | Add paths; cannot make baseline PCP require them                             |
| Extension-owned adapters              | Read/projection/write adapters must declare authority owner                  |
| Extension-owned proof/status mappings | Map project proof roots to generic proof pointers                            |
| Extension-owned runtime mappings      | Runtime-facing only after proof gates                                        |
| Non-overrides                         | Cannot weaken fail-closed UNKNOWNs or proof/audit gates                      |
| No self-promotion                     | Extension cannot declare itself canonical authority without runtime evidence |
| Baseline independence                 | PCP Core must run without Dopemux, dNh, or any named extension               |

---

## 6. DCP / Dopemux Extension

| Element                                | Extension role                                                     | Must not own                                      | Proof required                                             |      Runtime readiness |
| -------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------- | ---------------------------------------------------------- | ---------------------: |
| Dopemux CLI/startup/routing facts      | Provide Dopemux project profile and startup/control-plane evidence | PCP Core, PM truth, memory truth, retrieval truth | Runtime pointers, config, command surfaces                 |                PARTIAL |
| DCP routing classifier                 | Dopemux extension classifier/lane integration                      | PCP generic contract                              | Classifier inputs/outputs, fail-closed tests               |                PARTIAL |
| DCP lane engine                        | Dopemux-specific lane assignment                                   | Merge authority, live writes                      | Lane decisions, stop reasons, proof plan                   |     PARTIAL / PROPOSED |
| DCP proof pointer/family               | Map Dopemux proof roots into PCP proof pointer                     | Generic proof semantics                           | Fresh proof, head SHA, artifact manifest                   |                PARTIAL |
| DCP model routing / OpenClaw contracts | Role/risk/privacy route policies                                   | Trust oracle, release authority                   | Route schema validation, benchmark certification           |         CONTRACTS_ONLY |
| Dopetask mapping                       | External execution adapter mapping                                 | Policy owner, PM truth                            | No execution unless supervised packet                      |         EXTENSION_ONLY |
| Task Orchestrator projection           | Workflow/status projection                                         | Proof truth, PM metadata authority                | Projection read proof; no live MCP write                   |         EXTENSION_ONLY |
| PR Steward readiness                   | Evidence intake and readiness classifier                           | Merge authority, semantic proof                   | Current PR metadata, checks, reviews, proof freshness      |     PROPOSED / PARTIAL |
| Action Bridge repair planning          | Future adapter planning                                            | Live mutation authority                           | Explicit live-write gate and rollback                      |                BLOCKED |
| Repo Truth Extractor integration       | Consume extraction/audit artifacts                                 | Runtime truth replacement                         | Artifact hashes, extraction proof                          |         EXTENSION_READ |
| ConPort mapping                        | Structured decisions/progress/context                              | PM metadata/workflow legality                     | Read/structured-write authority map                        | EXTENSION_READ/ADAPTER |
| dope-memory mapping                    | Chronicle/evidence receipts                                        | PM truth, ConPort truth                           | Chronicle proof refs                                       |         EXTENSION_READ |
| dope-context mapping                   | Code/docs retrieval                                                | Source truth                                      | Source refs and retrieval caveats                          |         EXTENSION_READ |
| dopecon-bridge mapping                 | Adapter/proxy/event transport                                      | Any canonical domain authority                    | Bridge route proof, upstream authority refs                |           ADAPTER_ONLY |
| ADHD Engine signals                    | Operator-support/cognitive-state hints                             | PM/memory/retrieval/DCP authority                 | Read-only signal proof                                     |         EXTENSION_READ |
| OpenClaw / OpenRouter                  | Worker/runtime/routing substrate                                   | DCP/PCP policy brain                              | Provider/model logging, local benchmark, independent audit |         CONTRACTS_ONLY |

**OBSERVED_BY_FILE:** The repository already describes these systems as split authority surfaces, not one clean platform. `dopetask` is external execution via `scripts/taskx` to `scripts/dopetask`, task-orchestrator is workflow/PM-transition, and dopecon-bridge is an adapter/proxy rather than authority. 

---

## 7. dNh CRM Extension

| Element                      | Extension role                      | Forbidden in PCP Core                   | Proof required                          | Stop condition                          |
| ---------------------------- | ----------------------------------- | --------------------------------------- | --------------------------------------- | --------------------------------------- |
| dNh project profile          | Project-specific PCP profile values | dNh-specific required core fields       | Profile fixture + authority map         | Stop if PCP Core requires dNh           |
| dNh authority docs           | Extension-provided authority refs   | Core hardcoded doc paths                | Docs inventory and freshness            | Stop if missing authority is normalized |
| dNh proof roots              | Extension proof/status mappings     | Core proof path assumptions             | Proof pointer mapping                   | Stop if proof is stale                  |
| dNh red lanes                | Domain-specific lanes               | CRM/Telegram/calendar red lanes in core | Red-lane fixture + executed traps later | Stop if red lanes are assertion-only    |
| CRM runtime                  | Runtime mapping only                | CRM concepts in PCP Core                | Artifact-only exporter first            | Stop on runtime write/import            |
| Telegram                     | Red-lane/adapter mapping            | Messaging product in core               | No-send proof, adapter policy           | Stop on send attempt                    |
| Calendar                     | Red-lane/adapter mapping            | Calendar product in core                | No-write proof, adapter policy          | Stop on calendar write                  |
| Identity                     | Domain authority mapping            | Identity system in core                 | Authority map + secret policy           | Stop on auth mutation                   |
| Policy                       | Domain policy mapping               | dNh policy fields in core               | Policy refs and approvals               | Stop on policy write                    |
| Event store                  | Runtime evidence map                | Event-store assumption in core          | Read-only artifact path                 | Stop on import/write                    |
| Runtime DB                   | Forbidden/live-write lane           | DB assumptions in core                  | DB path red-lane proof                  | Stop on DB mutation                     |
| Artifact-only exporter       | First dNh runtime-safe exporter     | Generic exporter behavior               | No import, no DB write, no send         | Stop if live adapter used               |
| Reconciliation service       | Later extension adapter             | PCP workflow engine                     | Dry-run proof and rollback              | Stop before live gates                  |
| Task Orchestrator visibility | Optional projection                 | Required PCP workflow                   | Projection-only proof                   | Stop on Task Orchestrator write         |

**OBSERVED_BY_ADJUDICATION:** dNh is cleanest when it stays in fixture/extension data: CRM, Telegram, calendar, runtime DB, identity, policy, and proof roots are extension-owned, not core-owned. 

---

## 8. PR #925 Disposition

```text
Can #925 merge as-is? No.
Can #925 merge after label/proof repair? No, not if Dopemux-specific required fields remain in PCP Core.
Should #925 be superseded? Not yet; salvage is cheaper than replacement if boundary repair is done.
Does #925 need to be de-Dopemuxed before merge? Yes.
Does #925 overclaim with ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS? Yes.
What exact labels should replace it? Use fixture/runtime-unproven labels below.
Should #925 stay draft? Yes.
```

| Label                                                                | Evaluation                                   |
| -------------------------------------------------------------------- | -------------------------------------------- |
| `PCP_CORE_FIXTURE_SHAPE_VALIDATED_RUNTIME_UNPROVEN`                  | READY as proof label                         |
| `PCP_CORE_DRY_RUN_CONTRACT_SHAPE_VALIDATED_EXPORTER_NOT_IMPLEMENTED` | READY as E2E dry-run label                   |
| `ARCHITECTURE_SHAPE_PLAUSIBLE_PENDING_EXPORTER`                      | ACCEPTABLE as report posture if scoped       |
| `ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS`                            | REJECTED, overstrong                         |
| `NEEDS_SUPERVISOR`                                                   | KEEP until proof/PR Steward readiness clears |

```text
PR925_ACTION: DEDOPEMUX_BEFORE_MERGE
```

**OBSERVED_BY_ADJUDICATION:** Label-only repair is too weak because the core still contains Dopemux-specific contract surfaces; the recommendation is to keep draft and repair #925, then add extension contract and de-Dopemux the core before exporter work. 

---

## 9. Schema Move / Rename / Repair Matrix

| Current schema/artifact               | Current location                                         | Problem                                                                               | Target owner                                  | Action                   | Priority |
| ------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------- | ------------------------ | -------: |
| `dopetask_packet_mapping.schema.json` | `schemas/project_control_plane/`                         | Names Dopetask; target executor is extension-specific                                 | Dopemux/DCP extension                         | MOVE_TO_DCP_EXTENSION    |       P0 |
| `orchestrator_item.schema.json`       | `schemas/project_control_plane/`                         | Task Orchestrator projection is Dopemux workflow surface                              | Dopemux/DCP extension                         | MOVE_TO_DCP_EXTENSION    |       P0 |
| `executor_run_request.schema.json`    | `schemas/project_control_plane/`                         | Generic runner request possible, but current executor enum may encode project runners | PCP Core + extensions                         | SPLIT_CORE_AND_EXTENSION |       P1 |
| `executor_run_result.schema.json`     | `schemas/project_control_plane/`                         | Generic result possible, extension runner fields need namespace                       | PCP Core + extensions                         | SPLIT_CORE_AND_EXTENSION |       P1 |
| `project_evidence_export.schema.json` | `schemas/project_control_plane/`                         | Requires `live_task_orchestrator_written` and `dopetask_executed`                     | PCP Core                                      | GENERALIZE_AND_RENAME    |       P0 |
| `project_profile.schema.json`         | `schemas/project_control_plane/`                         | Mostly core; active packet/proof roots too prescriptive                               | PCP Core                                      | SPLIT_CORE_AND_EXTENSION |       P1 |
| `project_red_lanes.schema.json`       | `schemas/project_control_plane/`                         | Core nucleus is good; project lanes need extension section                            | PCP Core                                      | KEEP_IN_PCP_CORE         |       P1 |
| `proof_pointer.schema.json`           | `schemas/project_control_plane/`                         | Core concept; must bind freshness/head SHA later                                      | PCP Core                                      | KEEP_IN_PCP_CORE         |       P1 |
| `audit_request.schema.json`           | `schemas/project_control_plane/`                         | Generic but auditor roles may be extension-specific                                   | PCP Core + extensions                         | SPLIT_CORE_AND_EXTENSION |       P2 |
| `audit_result.schema.json`            | `schemas/project_control_plane/`                         | Generic verdicts OK; source/tool fields need proof family                             | PCP Core                                      | KEEP_IN_PCP_CORE         |       P2 |
| `supervisor_decision.schema.json`     | `schemas/project_control_plane/`                         | Generic decision type OK; must not equal merge authority                              | PCP Core                                      | KEEP_IN_PCP_CORE         |       P2 |
| DCP schemas                           | `schemas/dcp/` or DCP inputs                             | Rich extension surface; some concepts may need core abstraction                       | Dopemux/DCP extension + PCP Core abstractions | SPLIT_CORE_AND_EXTENSION |       P1 |
| dNh fixtures                          | `reports/project-control-plane/fixtures/dnh_crm_fixture` | Correct extension fixture; no live proof                                              | dNh extension                                 | MOVE_TO_DNH_EXTENSION    |       P1 |
| OpenClaw DCP routing contracts        | `contracts/openclaw-dcp-routing` / attached policy       | DCP routing governance, not PCP core                                                  | Dopemux/DCP extension                         | MOVE_TO_DCP_EXTENSION    |       P1 |
| `extension_manifest.schema.json`      | Missing                                                  | Keystone absent                                                                       | PCP Core                                      | GENERALIZE_AND_RENAME    |       P0 |
| `authority_map.schema.json`           | Missing                                                  | Keystone absent                                                                       | PCP Core                                      | GENERALIZE_AND_RENAME    |       P0 |

---

## 10. Runtime Readiness Ladder

| Readiness state                            |    Current status | Evidence                          | Required next proof                          |
| ------------------------------------------ | ----------------: | --------------------------------- | -------------------------------------------- |
| Schema shape validated                     |           PARTIAL | JSON schemas validate in PR proof | Move extension leaks first                   |
| Fixture direction validated                |           PARTIAL | Minimal/Dopemux/dNh fixture packs | Remove Dopetask/TO from generic fixture      |
| Dry-run artifact shape validated           |           PARTIAL | E2E dry-run exists                | Replace overstrong labels                    |
| Runtime exporter implemented               | UNKNOWN / MISSING | No generic exporter               | `pcp export` or equivalent on plain Git repo |
| Runtime behavior validated                 |           UNKNOWN | No executed exporter behavior     | Command output, exit code, output artifacts  |
| Generic repo behavior validated            |           UNKNOWN | Minimal fixture only              | Run against real plain repo fixture          |
| DCP extension mapping validated            | UNKNOWN / PARTIAL | DCP schema/code materials exist   | Extension manifest + mapping tests           |
| dNh live adapter validated                 |           UNKNOWN | dNh fixture only                  | Artifact-only exporter, no runtime write     |
| Fixture-to-runtime negative traps executed |           UNKNOWN | Current negatives are asserted    | Negative runner and failure index            |
| Live-write gates validated                 |           BLOCKED | Policy only                       | Gate packet with approvals, rollback, audit  |

---

## 11. Build Roadmap

| Order | Packet ID                                       | Purpose                                              | Scope                                   | Owner/Executor                        | Validation gates                                                 | Stop conditions                                       | Output                             |
| ----: | ----------------------------------------------- | ---------------------------------------------------- | --------------------------------------- | ------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------- |
|     1 | `TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002`    | Repair #925 framing, verdict labels, proof freshness | Docs/proof/report only                  | Codex implementer + embedded auditor  | Updated PR body, labels, proof at current head, validation rerun | Runtime files, live writes, new schemas beyond repair | Draft PR becomes truthfully scoped |
|     2 | `TP-DMX-PCP-EXTENSION-CONTRACT-0001`            | Add extension manifest/registry contract             | Schemas/tests/docs                      | GPT-5.5 Pro packet, Codex implementer | Schema validation, fail-closed extension tests                   | Extension can override core invariants                | Extension mechanism exists         |
|     3 | `TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001`       | Remove Dopemux concepts from PCP Core                | Move/split schemas and fixtures         | Codex/Claude Sonnet                   | Generic fixture has no Dopetask/TO requirements                  | PCP Core still requires named systems                 | Clean core boundary                |
|     4 | `TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001`         | Implement generic exporter                           | Runtime exporter, tests                 | Codex primary, Claude fallback        | Plain Git repo fixture output, commands, exit codes, artifacts   | Requires Dopemux/dNh                                  | Runtime proof begins               |
|     5 | `TP-DMX-DCP-EXTENSION-MAPPING-0001`             | Map Dopemux systems into extension                   | DCP extension namespace                 | Codex + AGY/Gemini audit              | Extension manifest, authority map, red lanes                     | Bridge/proxy promoted to authority                    | DCP = PCP + Dopemux                |
|     6 | `TP-DNH-PCP-EXTENSION-MAPPING-0001`             | Map dNh extension                                    | dNh profile/red lanes/proof roots       | dNh implementer + independent audit   | Artifact-only export, no live writes                             | dNh runtime import/write                              | dNh = PCP + dNh                    |
|     7 | `TP-DMX-PCP-FIXTURE-TO-RUNTIME-VALIDATION-0001` | Execute negative traps                               | Runtime validation harness              | Codex/Claude                          | Failure index, computed negatives                                | Assertion-only negatives remain                       | Behavior evidence                  |
|     8 | `TP-DMX-PCP-PR-STEWARD-PROOF-READINESS-0001`    | Integrate PR Steward readiness                       | PR metadata/proof/check intake          | PR Steward packet                     | Current head SHA, checks, reviews classified                     | Unknown reviewers/bots                                | MERGE_READINESS                    |
|     9 | `TP-DMX-PCP-TASK-ORCHESTRATOR-VISIBILITY-0001`  | Projection only                                      | Read/projection mapping                 | Codex + TO owner                      | No MCP write, projection proof                                   | TO write attempted                                    | Workflow visibility                |
|    10 | `TP-DMX-PCP-LIVE-WRITE-GATES-0001`              | Define live-write gates                              | Contracts only                          | GPT-5.5 Pro supervisor                | Approval, idempotency, rollback, audit requirements              | Any live write                                        | LIVE_WRITE_READY criteria          |
|    11 | `TP-DMX-PCP-FASTAPI-BRIDGE-LAST-0001`           | Bridge/live writes last                              | Adapter implementation only after gates | Implementer after approval            | Gate proof, rollback, post-write verification                    | Bridge promoted to authority                          | Safe adapter path                  |

**Why extension contract before exporter:** the current PR’s own evidence shows missing extension/authority-map schemas and Dopemux-specific fields in core. Building the exporter first would encode the wrong boundary into code. 

---

## 12. Immediate Next Packet

```text
NEXT_PACKET_ID: TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002

NEXT_PACKET_TITLE:
Repair PR #925 PCP Parent Framing, Verdict Labels, and Proof Freshness

NEXT_PACKET_OBJECTIVE:
Make PR #925 truthfully describe fixture-only PCP architecture direction, replace overstrong verdicts, refresh proof to current head, and keep it draft until boundary repair is complete.

WHY_THIS_PACKET_NOW:
PR #925 currently overclaims and blocks clean sequencing. This is the smallest safe repair before schema movement.

MUST_NOT_DO:
No exporter implementation.
No extension contract implementation.
No Dopetask execution.
No Task Orchestrator MCP write.
No dNh runtime change.
No FastAPI bridge.
No Action Bridge mutation.
No live writes.

VALIDATION_GATES:
JSON/schema validation.
git diff --check.
pre-commit evidence.
PROOF.json after_sha equals latest PR head.
E2E dry-run/result labels repaired.
PR body and validation report use PCP parent model.
Review threads classified or explicitly marked blocking.

EXPECTED_OUTPUT:
Updated PR body, proof, E2E dry-run result, validation report, command outputs, exit codes, git diff --stat, git diff, embedded audit report, and refreshed PR Steward readiness if available.
```

---

## 13. Migration Strategy From Current Repo

**Preserve**

* Fixture packs as evidence of direction, but mark fixture-only.
* `project_profile`, `project_red_lanes`, `proof_pointer`, `audit_*`, `supervisor_decision` as candidate core schemas after cleanup.
* DCP routing/lane/red-lane materials as Dopemux extension inputs.
* dNh fixture data as first project-extension sample.
* Proof/audit contracts and task-packet proof requirements.

**Rename / split**

* Rename “Dopemux Project Control Plane core” to “PCP Core” only where the artifact is truly generic.
* Split `project_evidence_export` into generic core export and extension-owned forbidden-action confirmations.
* Split executor schemas into generic runner envelope and DCP executor mappings.
* Split workflow projection schemas into generic projection pointer and DCP Task Orchestrator mapping.

**Move into extension namespace**

* `dopetask_packet_mapping.schema.json`
* `orchestrator_item.schema.json`
* Dopetask/Task Orchestrator forbidden-action flags
* OpenClaw/DCP routing contracts
* DCP red-lane taxonomy
* dNh CRM/Telegram/calendar/identity/policy/runtime DB lanes

**Deprecate**

* `ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS`
* Any fixture-only schema version that can never validate runtime exporter output because it requires `generated_from_fixture: true`
* Any “DCP Core as generic parent” wording

**Keep as legacy DCP**

* Existing `schemas/dcp/*`
* Existing `src/dopemux/dcp/*`
* DCP routing classifier/lane materials until mapped through extension contract

**Mark SUPERSEDED**

* Generic-DCP-parent framing
* PR #925 labels claiming confirmed architecture
* Any negative-test artifact that asserts pass without execution

**Block**

* Exporter before extension boundary repair
* Live writes before gates
* Bridge/proxy authority promotion
* PR Steward READY with stale proof
* Any self-certifying audit

**Audit with Opus/Gemini**

* Extension contract schema
* De-Dopemux boundary diff
* Generic exporter behavior on plain Git repo fixture
* Negative trap runner
* DCP extension mapping

**Requires GPT-5.5 Pro again**

* Conflicting auditor findings
* Security/auth/CI/live-write changes
* PR Steward BLOCKED/NEEDS_SUPERVISOR
* Authority-boundary contradictions
* Final live-write gate approval

---

## 14. Acceptance Gates

| Gate                                   | Required artifacts                                                       | Required tests                                                      | Required proof                                    | Required audit                         | Blocking conditions                                                            |
| -------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- | ------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------ |
| PCP Core accepted                      | Core schemas, extension contract, authority map, generic exporter        | Schema tests, plain repo exporter test, negative runner             | Current head SHA, commands, exit codes, artifacts | Independent audit PASS/PASS_WITH_RISKS | Dopemux/dNh required by baseline                                               |
| DCP extension accepted                 | Extension manifest, Dopemux authority map, DCP red lanes, proof mappings | Extension validation, no authority override tests                   | Mapping proof, no live-write proof                | AGY/Gemini/Claude audit                | Bridge/proxy promoted to authority                                             |
| dNh extension accepted                 | dNh manifest, authority docs, red lanes, artifact-only exporter          | No-write/no-import tests                                            | Artifact-only output proof                        | Independent audit                      | CRM/Telegram/calendar/DB write                                                 |
| Generic exporter accepted              | Exporter command, output artifacts, docs                                 | Plain Git repo fixture, generated/vendor/secret/contradiction traps | git status, output hashes, failure index          | Embedded audit                         | Requires Dopemux/dNh                                                           |
| Fixture-to-runtime validation accepted | Negative-case runner, failure index                                      | Traps executed, not asserted                                        | Command outputs and exit codes                    | Independent audit                      | Assertion-only pass                                                            |
| Live-write readiness                   | LIVE_WRITE_READY contract, canonical writer map, rollback                | Dry-run, idempotency, rollback tests                                | Human approval, audit, PR Steward readiness       | GPT-5.5 supervisor + independent audit | Missing proof, stale proof, unknown reviewer, no rollback, no canonical writer |

**OBSERVED_BY_POLICY:** READY requires current head, current checks, proof current to head, independent audit or human approval, every review item classified, no unknown reviewers/bots, no unresolved blocking threads, and diff within allowlist. 

---

## 15. Red Flags and Failure Modes

1. **Dopemux-shaped core:** Dopetask/Task Orchestrator in PCP Core.
2. **dNh-shaped core:** CRM/Telegram/calendar/DB in PCP Core.
3. **DCP as parent of PCP:** inverted architecture.
4. **Extension weakening core invariants:** extension overrides fail-closed UNKNOWN.
5. **Asserted negative tests:** `expected_result == asserted_result` theater.
6. **Green CI treated as semantic proof:** checks are not architecture truth.
7. **PR Steward treated as authority:** advisory only.
8. **Bridge/proxy promoted to authority:** dopecon-bridge is adapter/proxy/event transport.
9. **Dopetask treated as policy owner:** it is external execution runtime.
10. **Task Orchestrator treated as proof truth:** projection/workflow surface only.
11. **Live writes before gates:** red-lane breach.
12. **FastAPI bridge too early:** adapter tentacles before contracts.
13. **Self-certifying audit:** auditor edits artifacts it audits.
14. **Stale proof:** proof head SHA differs from PR head.
15. **Unknown reviewer/bot:** blocks READY.
16. **Runtime imports in fixtures:** violates fixture-only safety.
17. **Project-specific red lanes hardcoded into core:** leaks extension surface.
18. **Schema names encoding extension systems:** e.g. `dopetask_packet_mapping` in core.
19. **Generic exporter built before extension boundary:** cements wrong model.
20. **Overstrong architecture labels:** “confirmed” when only shape validated.

---

## 16. Final Build Plan Summary

```text
TRUE_ARCHITECTURE:
- PCP Core = reusable project-control substrate for any Git repo.
- DCP = PCP Core + Dopemux extension.
- dNh CRM = PCP Core + dNh extension.
- Other projects = PCP Core + project extension.

PR925_ACTION:
- DEDOPEMUX_BEFORE_MERGE.
- Keep draft.
- Repair framing/proof now.
- Do not merge under confirmed-generic language.

NEXT_PACKET:
- TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002.

BUILD_ORDER:
- PR925 framing/proof repair.
- PCP extension contract.
- PCP core de-Dopemux boundary repair.
- PCP generic exporter.
- DCP extension mapping.
- dNh extension mapping.
- Fixture-to-runtime validation.
- PR Steward/proof readiness integration.
- Task Orchestrator visibility.
- Live-write gates.
- FastAPI bridge/live writes last.

DO_NOT_DO_NEXT:
- Do not implement exporter before extension contract and boundary repair.
- Do not run Dopetask.
- Do not write Task Orchestrator.
- Do not touch dNh runtime.
- Do not build FastAPI bridge.
- Do not mark READY.

HIGHEST_RISK_SHORTCUT:
- Building the generic exporter now, while the core still contains Dopemux-shaped required fields.

HIGHEST_LEVERAGE_SIMPLIFICATION:
- One parent substrate, one extension contract, one generic exporter, then project extensions. No fog machine. 🧯
```
