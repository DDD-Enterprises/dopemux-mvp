---
id: AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001
supersedes: AIR-DMX-PCP-DCP-ARCHITECTURE-0001
title: PCP Core / DCP / dNh + DCP Routing Architecture Intent Record
type: reference
owner: '@hu3mann'
author: gpt-5.5-pro
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: >-
  Build-planning architecture intent record extending
  AIR-DMX-PCP-DCP-ARCHITECTURE-0001 with the DCP routing / OpenClaw extension
  dimension. PCP Core is the parent substrate; DCP and dNh are extensions.
  Runtime code and live GitHub state outrank this document.
---

<!--
EDITORIAL NOTE (added on save, body unaltered):
  - This file is the AIR authored by GPT-5.5 Pro, saved verbatim below the frontmatter.
  - The frontmatter above was added only to satisfy docs/ standards (id/title/type/owner/date)
    and to match the sibling AIR-DMX-PCP-DCP-ARCHITECTURE-0001.md convention.
  - No content of the AIR body was changed. Corrections identified during audit live in the
    companion Opus audit report, NOT in this file.
  - Authority: build-planning only. Runtime/GitHub/PR evidence outranks this AIR (AGENTS.md §2).
-->

# AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001

## 0. Relationship & Supersession

```text
RELATIONSHIP: SUPERSEDES (canonical for routing) + BUILDS_ON (foundation)
SUPERSEDES: AIR-DMX-PCP-DCP-ARCHITECTURE-0001
BASIS: AIR-DMX-PCP-DCP-ARCHITECTURE-0001 (identical PCP-parent boundary model)
DELTA: DCP routing architecture (§8) + Opus correction set
```

**OBSERVED_BY_FILE:** `AIR-DMX-PCP-DCP-ARCHITECTURE-0001.md` already exists, committed on the PR #925 branch `codex/tp-dmx-pcp-architecture-validation-0001` (not yet on `main`), with status `ACCEPTED_FOR_BUILD_PLANNING` and the identical boundary model: PCP Core parent, DCP = PCP Core + Dopemux extension, dNh = PCP Core + dNh extension.

**PROPOSED:** This AIR (`AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001`) is the canonical build-planning artifact for PCP / DCP / **routing** work and **supersedes** `AIR-DMX-PCP-DCP-ARCHITECTURE-0001` for that purpose. It does not contradict the base AIR; it is a strict superset that (a) adds the DCP routing / OpenClaw extension dimension (§8) absent from the base AIR, and (b) folds in the independent Opus audit corrections. The base AIR is retained as the foundational/historical record this one builds on.

**BLOCKED:** Full supersession takes effect only once both AIRs are reconciled on `main`. Until then, if the base AIR and this AIR conflict on a shared claim, prefer this AIR for the routing dimension and the corrected build order; on every other claim they agree. Runtime / GitHub / PR evidence still outranks both (AGENTS.md §2).

## 1. Status
```text
AIR_STATUS: ACCEPTED_WITH_CORRECTIONS
CAN_WRITE_TASK_PACKETS_FROM_THIS_AIR: YES_WITH_LIMITS
ARCHITECTURE_VERDICT: PCP_PARENT_MODEL_ACCEPTED_WITH_CORRECTIONS
```
**OBSERVED_BY_FILE:** The strongest architecture is accepted with corrections: PCP Core is the parent substrate, DCP is a Dopemux extension, dNh is a project extension, and PR #925 is salvageable but not merge-ready. (Re-grounded: corroborated by the committed sibling `AIR-DMX-PCP-DCP-ARCHITECTURE-0001` and by PR #925 branch schema evidence — not by an out-of-repo adjudication.)
**PROPOSED:** This AIR is valid for build sequencing, not for live execution.
**BLOCKED:** It does not authorize exporter work yet, because the current core still contains Dopemux-shaped fields and fixture-only constraints.
**BLOCKED:** It does not authorize Task Orchestrator writes, Dopetask execution, dNh runtime mutation, OpenClaw production routing, FastAPI bridge work, PR merges, or live writes.
**CLAIMED_ONLY (prior regeneration audit, not in-repo) / OBSERVED_BY_FILE (companion audit):** The prior Opus audit reportedly said `WRITE_AIR` after corrections; that document is not attached and not in git, so the claim is unverified. It is independently re-grounded by the committed companion audit `docs/05-audit-reports/project-control-plane/air-dmx-pcp-dcp-routing-architecture-0001-opus-audit.md`, which reaches `ACCEPT_AIR_WITH_CORRECTIONS` / `PATCH_AIR_THEN_WRITE_PACKETS` with: PCP Core intended/proposed, authority-map and extension-manifest as co-keystones, `generated_from_fixture: const true` and runtime `head_sha` as explicit gates, and PR #925 repair scoped to remaining items only.
**UNKNOWN:** I did not re-pull live PR #925 or #931 state in this chat. Any state after the uploaded bundles is stale/unknown until a packet performs live GitHub evidence capture.
**READY:** Task packets may be written from this AIR only for planning-safe scopes and only if they preserve the corrected build order.
**NEEDS_SUPERVISOR:** Any conflicting live PR evidence, unknown reviewer/bot state, security/auth/CI change, live-write design, or authority-boundary contradiction must escalate before implementation.

---
## 2. Decision Summary
**PROPOSED / ACCEPTED_WITH_CORRECTIONS:** PCP Core is the parent substrate for generic project-control behavior.
**OBSERVED_BY_FILE / INFERRED:** DCP is PCP Core plus a Dopemux extension, not the parent model, because the Dopemux repo authority surface is split across operator, execution, PM, memory, retrieval, bridge, ADHD/operator support, and repo-truth systems.
**OBSERVED_BY_FILE / INFERRED:** dNh CRM is PCP Core plus a dNh extension; CRM, Telegram, calendar, identity, policy, event store, runtime DB, and dNh proof roots stay extension-owned.
**OBSERVED_BY_FILE:** OpenClaw/OpenRouter/model routing belongs to the DCP/Dopemux extension as contracts-only routing material unless later runtime evidence generalizes it.
**OBSERVED_BY_PROOF / OBSERVED_BY_DIFF:** PR #925 is salvageable but not merge-ready; label-only repair is too weak because Dopetask and Task Orchestrator concepts still leak into generic PCP surfaces.
**BLOCKED:** The exporter must not be built before extension contract plus authority map, then de-Dopemux boundary repair.
**BLOCKED:** Live writes remain blocked until canonical writer, allowlist, rollback, approval, independent audit, dry-run proof, and post-write verification are defined and proven.
**PROPOSED:** The build order is: repair #925 framing, add extension contract plus authority map, de-Dopemux PCP Core, then build the exporter.
**INFERRED:** The biggest shortcut trap is exporter-first theater. It would fossilize the exact Dopemux-shaped core the architecture is trying to remove. 🧯

---
## 3. Evidence Ledger

| Evidence                                            | Label                                        | What it proves                                                                                                                                                                          | What it does not prove                                                     | AIR use                                                |
| --------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------ |
| `DCP_PCP_ARCHITECTURE_REGENERATION_GPT55.md`        | CLAIMED_ONLY / DESIGN_INPUT (not in-repo)    | Establishes the PCP parent model, DCP/dNh extension model, PR #925 repair direction, and schema migration matrix.                                                                       | Runtime PCP exporter correctness; live PR freshness.                       | Basis, corrected by Opus.                              |
| `DCP_PCP_OPUS_AUDIT_OF_REGENERATION.md`             | CLAIMED_ONLY / AUDIT_OF_RECORD (not in-repo) | Accepts Pro result with corrections, says `WRITE_AIR`, fixes build order, and forces authority-map into packet 2.                                                                       | It does not execute implementation or validate post-bundle PR state.       | Governing correction layer.                            |
| `DCP_PROMPT5_CHAT_HISTORY_EXTRACT.md`               | CLAIMED_ONLY / PRESERVATION                  | Preserves older Prompt 5 architecture history.                                                                                                                                          | Runtime truth or current PR state.                                         | Background only; never outranks current audit/runtime. |
| `DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md`         | EXTERNAL_PROPOSED / CONTRADICTION_INPUT      | Preserves pre-synthesis authority leaks and contradictions.                                                                                                                             | Final architecture by itself.                                              | Carry-forward risk discipline.                         |
| `DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md`             | EXTERNAL_PROPOSED / VENDOR_DOCS              | Provides external constraint gates such as GitHub merge authority, MCP write discipline, proof pointer-first posture.                                                                   | Repo runtime authority.                                                    | Constraint walls only; no authority promotion.         |
| `DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md`       | SUPERSEDED-IN-PART / AUTHORITATIVE_FOR_DELTA | Supersedes older DCP synthesis where contract floor/provenance differ; mandates provenance tags, provisional external field lists, static fixture insufficiency, auditor ≠ implementer. | PCP/DCP final build order after PR #925 evidence.                          | Preserve provenance discipline.                        |
| `DCP_ARCHITECTURE_SYNTHESIS_GPT55.md`               | SUPERSEDED-IN-PART                           | Earlier DCP architecture decision.                                                                                                                                                      | Contract-floor scope where revised delta differs.                          | Historical context only where not superseded.          |
| `DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md`             | OBSERVED_BY_FILE (mvp/palette branch, not on main) / AUDIT_INPUT | Identifies provenance-tagging, circular fixture validation, subprocess scope, and self-certifying audit risks.                                                                          | Current PR #925 state after June 2026 bundle.                              | Reinforces red lines and provenance gates.             |
| `DCP_5_5_SYNTHESIS_INPUT_PACK.md`                   | EXTERNAL_PROPOSED / INPUT_PACK               | Shows DCP evidence campaign, Task Orchestrator split, proof fragmentation, memory split, routing constraints, contradictions.                                                           | Architecture decision by itself.                                           | Evidence baseline and contradiction carry-forward.     |
| PR #925 input pack                                  | OBSERVED_BY_FILE / OBSERVED_BY_PROOF         | Proves fixture/dry-run architecture direction and Dopemux leaks in generic schemas.                                                                                                     | Merge readiness or exporter runtime.                                       | Source for PR #925 disposition.                        |
| Supplemental inputs zip                             | OBSERVED_BY_FILE / PARTIAL                   | Adds Pack 2 evidence and gaps.                                                                                                                                                          | Clean repo-wide tests or offline-safe runtime confidence.                  | Use with blocker caveats.                              |
| `openclaw-routing.zip` / Multi-model routing policy | OBSERVED_BY_FILE / PROPOSED                  | Provides route schemas, proof requirements, cost/benchmark/human-gate policy, and OpenRouter-free restrictions.                                                                         | Production readiness, benchmark pass, current model/provider availability. | DCP routing extension input.                           |
| Repo authority docs                                 | OBSERVED_BY_FILE                             | Confirm split authority and non-monolithic workspace.                                                                                                                                   | Target PCP implementation.                                                 | Boundary guardrails.                                   |
| Governance/proof/PAL/task/handoff contracts         | OBSERVED_BY_FILE                             | Define expected proof, handoff, packet evidence, and audit structure.                                                                                                                   | Runtime behavior by themselves.                                            | Build acceptance grammar.                              |

---
## 4. Architecture Tree
```text
PCP Core
  repo discovery
  project identity
  project profile
  authority map
  evidence export
  red-lane policy / engine
  proof/status pointer
  validation harness
  negative-case runner
  extension contract
  generic exporter
  baseline no-extension operation
Extensions
  DCP / Dopemux Extension
  dNh CRM Extension
  Other Project Extensions
Planes
  Execution Plane
  Routing Plane
  Audit Plane
  Proof Plane
  Workflow / Projection Plane
  Runtime Boundary
  Live-Write Gates
```
**PCP Core** is the reusable project-control substrate for any Git repo. It must operate from `.git`, conservative defaults, generic identity/profile/export, fail-closed `UNKNOWN`, and no required named systems.
**Repo discovery** discovers root, branch/ref, dirty state, file inventory, proof roots, and evidence roots without assuming Dopemux or dNh.
**Project identity** establishes stable generic identity: repo, root marker, project kind, branch/ref, and source provenance.
**Project profile** records generic project facts plus extension slots. Named systems belong in extension slots, not core required fields.
**Authority map** is a machine-checkable ownership map: domain, action, canonical authority owner, canonical writer, projection/mirror/cache distinction, proof requirements, and stop conditions.
**Evidence export** emits observed facts with labels, provenance, freshness, source refs, and extension-owned sections.
**Red-lane policy / engine** defines generic risk gates and allows project extensions to contribute stricter lanes without bypassing core fail-closed behavior.
**Proof/status pointer** binds evidence to repo/head/proof family/status/freshness without inlining every proof body.
**Validation harness** validates schemas, fixtures, exported artifacts, provenance coverage, and fail-closed behavior.
**Negative-case runner** executes traps rather than asserting expected failure. No more “expected_result == asserted_result” puppet show.
**Extension contract** declares how named systems attach without weakening core.
**Generic exporter** is a future runtime command, not present today. It must run against a plain Git repo with no named extension.
**Baseline no-extension operation** proves PCP Core can work without Dopemux, dNh, OpenClaw, Dopetask, Task Orchestrator, or any other mascot in the machinery.
**DCP / Dopemux Extension** maps Dopemux CLI/startup/routing, DCP classifier/lane engine, Dopetask, Task Orchestrator projection, Leantime, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, Repo Truth Extractor, PR Steward, OpenClaw/OpenRouter, and model routing into extension-owned mappings.
**dNh CRM Extension** maps dNh profile, authority docs, proof roots, CRM, Telegram, calendar, identity, policy, event store, runtime DB, red lanes, artifact-only exporter, reconciliation service, and optional Task Orchestrator visibility.
**Other Project Extensions** provide project profile values, authority maps, red lanes, proof/status paths, adapters, and project-specific runtime mappings.
**Execution Plane** maps generic runner envelopes to extension-specific runner backends.
**Routing Plane** classifies work, risk, privacy, authority, model/provider eligibility, human gates, benchmark status, and proof obligations.
**Audit Plane** enforces independence. Creator cannot be sole final auditor.
**Proof Plane** binds repo, branch, head SHA, commands, exit codes, diffs, artifacts, auditor verdict, and validation state.
**Workflow / Projection Plane** presents views and status. It is not proof truth, merge truth, PM truth, or live-write authority.
**Runtime Boundary** prevents PCP/DCP from mutating project runtime surfaces before live-write gates.
**Live-Write Gates** come last. No canonical writer, rollback, approval, independent audit, dry-run proof, and post-write verification, no write. Period.

---
## 5. PCP Core Definition

| Capability                      | Definition                                                                                                       | Required artifact/schema                                | Current status          | Build packet                                       | Acceptance gate                                                                         |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Generic repo discovery          | Find repo root, ref, dirty state, file inventory, proof roots, and source docs without named-system assumptions. | `repo_discovery` section or schema                      | MISSING / PARTIAL       | `TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001`            | Runs on plain Git fixture; no Dopemux/dNh required.                                     |
| Project identity                | Stable generic project identity with `.git` baseline and optional extension hints.                               | `project_identity` inside `project_profile.schema.json` | PARTIAL                 | `TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001`          | No `.dopetaskroot` or dNh marker required for baseline.                                 |
| Project profile                 | Generic profile plus extension slots.                                                                            | `project_profile.schema.json`                           | PARTIAL                 | Boundary repair                                    | Core required fields do not name Dopemux/dNh systems.                                   |
| Authority map                   | Machine-checkable owner/writer/projection/mirror/cache/source map.                                               | `authority_map.schema.json`                             | MISSING                 | `TP-DMX-PCP-EXTENSION-CONTRACT-AUTHORITY-MAP-0001` | Must ship with extension manifest; fail-closed unknown owner.                           |
| Evidence export                 | Export observed project facts and extension sections with labels/provenance.                                     | `project_evidence_export.schema.json`                   | PARTIAL / CONFLICTING   | Boundary repair                                    | Relax `generated_from_fixture: const true` (verified the real exporter blocker); move Dopetask/Task-Orchestrator confirmations to extension-owned export. |
| Red-lane engine                 | Generic risk taxonomy plus extension-contributed lanes.                                                          | `project_red_lanes.schema.json`, evaluator              | PARTIAL                 | Boundary repair + validation packet                | Project lanes additive; no extension weakens core.                                      |
| Proof/status pointer            | Generic pointer to proof family, freshness, head SHA, validation state, auditor verdict.                         | `proof_pointer.schema.json`                             | PARTIAL                 | Boundary repair + exporter                         | Runtime `head_sha` computed, not placeholder.                                           |
| Validation harness              | Schema validation plus provenance and negative tests.                                                            | validation reports + tests                              | PARTIAL                 | Fixture-to-runtime validation                      | Static fixture validation not enough; provenance checked.                               |
| Negative-case runner            | Executes fail-closed traps.                                                                                      | `negative_case_result.schema.json` / failure index      | MISSING / ASSERTED_ONLY | Fixture-to-runtime validation                      | Negative cases executed with outputs and exit codes.                                    |
| Extension contract              | Defines how named systems attach safely.                                                                         | `extension_manifest.schema.json`                        | MISSING                 | Extension contract / authority map                 | Additive only; cannot override core deny/fail-closed behavior.                          |
| Generic exporter                | Runtime exporter for arbitrary Git repo.                                                                         | `pcp export` or equivalent                              | UNKNOWN / MISSING       | Generic exporter                                   | Plain repo output, commands, exit codes, artifacts, no extension required.              |
| Baseline no-extension operation | Minimal control plane output without any extension.                                                              | baseline fixture + runtime proof                        | UNKNOWN                 | Generic exporter                                   | Passes with `.git` only and all named systems absent.                                   |

**OBSERVED_BY_FILE:** `authority_map.schema.json` and `extension_manifest.schema.json` are co-keystones; both are verified absent from `schemas/project_control_plane/` on the PR #925 branch (`git ls-tree`), so treating either as “later garnish” is how the architecture turns into soup.

---
## 6. Extension Contract and Authority Map
**PROPOSED:** The extension contract and authority map are one architectural seam, not two unrelated schema chores.
```yaml
extension_manifest:
  schema_version: pcp.extension_manifest.v0
  status: PROPOSED
  extension_id: string
  extension_kind:
    enum:
      - DOPEMUX_DCP
      - DNH_CRM
      - PROJECT
      - UNKNOWN
  compatible_pcp_core_versions: []
  extension_identity:
    project_id_patterns: []
    repo_markers: []
    discovery_hints: []
  capabilities:
    authority_map_contributions: []
    red_lane_contributions: []
    evidence_export_sections: []
    proof_status_mappings: []
    runtime_mappings: []
    adapter_mappings: []
  schemas:
    owned_schema_ids: []
    core_schema_extensions: []
    forbidden_core_overrides: []
  invariants:
    cannot_override_core_fail_closed: true
    cannot_weaken_proof_gates: true
    cannot_weaken_audit_gates: true
    cannot_promote_adapter_to_authority: true
    cannot_require_extension_for_baseline_core: true
```
**PROPOSED / REQUIRED:** `authority_map.schema.json` must encode:
* `domain`
* `action`
* `canonical_authority_owner`
* `canonical_writer`
* `reader_or_projection_surface`
* `mirror/cache/index status`
* `source_truth_refs`
* `proof_required`
* `live_write_allowed`
* `approval_required`
* `rollback_required`
* `unknown_behavior = BLOCK_OR_ESCALATE`

| Seam element                               | AIR decision                                                                 |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| Extension manifest                         | PROPOSED schema draft, validated in packet 2.                                |
| Authority map                              | Co-keystone with extension manifest, not optional.                           |
| Extension identity                         | Identifies named repo/project systems without changing PCP identity.         |
| Extension capabilities                     | Additive only.                                                               |
| Extension-owned schemas                    | Namespaced under extension. Never pretend named systems are PCP Core.        |
| Extension-owned red lanes                  | Feed core engine but cannot bypass generic blocks.                           |
| Extension-owned evidence paths             | Add evidence roots without making baseline PCP depend on them.               |
| Extension-owned proof/status mappings      | Map project proof roots to generic proof pointers.                           |
| Extension-owned adapters                   | Declare read/projection/write class and canonical upstream authority.        |
| Extension-owned runtime mappings           | Runtime-facing only after proof gates.                                       |
| Canonical authority owner                  | The upstream system that owns the domain. Extension is a mapper, not a king. |
| Canonical writer                           | The only surface allowed to mutate the owned domain after gates.             |
| Projection/mirror/cache/source distinction | Mandatory. Never flatten derived outputs into authority.                     |
| Cannot weaken core fail-closed behavior    | Hard invariant.                                                              |
| Cannot weaken proof/audit gates            | Hard invariant.                                                              |
| Cannot promote itself to authority         | Hard invariant.                                                              |
| Cannot be required for baseline PCP        | Hard invariant.                                                              |

**PROPOSED / OBSERVED_BY_FILE:** The `extension_manifest` YAML and its `extension_kind` enum (`DOPEMUX_DCP`, `DNH_CRM`, `PROJECT`, `UNKNOWN`) are PROPOSED, not settled; the enum spelling is verified correct and the manifest is authored/validated in packet 2.

---
## 7. DCP / Dopemux Extension Definition

| Component                       | Extension role                                                      | Must not own                                                 | Required proof                                                    | Runtime readiness        | Packet                         |
| ------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------ | ------------------------------ |
| Dopemux CLI/startup/routing     | Provides Dopemux profile and operator-control evidence.             | PCP Core, PM truth, memory truth, retrieval truth.           | Runtime pointers, commands, config, entrypoints.                  | PARTIAL                  | DCP extension mapping          |
| DCP routing classifier          | Dopemux-specific classification and routing inputs.                 | PCP generic contract.                                        | Classifier inputs/outputs, fail-closed tests.                     | PARTIAL                  | DCP routing extension          |
| DCP lane engine                 | Dopemux-specific lane assignment, action eligibility, stop reasons. | Merge authority, live writes.                                | Lane decision logs, proof plan, red-lane checks.                  | PARTIAL / PROPOSED       | DCP routing extension          |
| DCP proof family                | Maps Dopemux proof roots to PCP proof pointer.                      | Generic proof semantics.                                     | Fresh proof, head SHA, artifact manifest.                         | PARTIAL                  | DCP extension mapping          |
| DCP model routing               | Role/risk/privacy/provider route policy.                            | Trust oracle, release authority.                             | Route schemas, benchmark ledger, provider logs.                   | CONTRACTS_ONLY           | DCP routing extension          |
| OpenClaw / OpenRouter contracts | Worker/runtime/routing substrate mapping.                           | PCP Core, DCP policy brain, release authority.               | Provider/model logging, local benchmark, independent audit.       | CONTRACTS_ONLY           | DCP routing extension          |
| Dopetask mapping                | External execution adapter mapping.                                 | PM truth, policy owner, PCP Core validation.                 | No execution unless supervised packet explicitly permits it.      | EXTENSION_ONLY           | DCP extension mapping          |
| Task Orchestrator projection    | Workflow/status projection.                                         | Proof truth, PM metadata authority, live workflow authority. | Projection proof; no MCP write.                                   | EXTENSION_ONLY           | Task Orchestrator visibility   |
| PR Steward                      | Readiness intake.                                                   | Merge authority, semantic proof, final release judgment.     | Current PR metadata, checks, reviews, proof freshness.            | PROPOSED / PARTIAL       | PR Steward proof-readiness     |
| Action Bridge                   | Repair/action-plan compiler until later gates.                      | Live mutation authority.                                     | Explicit live-write gate and rollback.                            | BLOCKED                  | Live-write gates / bridge-last |
| Repo Truth Extractor            | Consumes extraction/audit artifacts.                                | Runtime truth replacement.                                   | Artifact hashes, extraction proof.                                | EXTENSION_READ           | DCP extension mapping          |
| ConPort                         | Structured decisions/progress/context mapping.                      | PM metadata, workflow legality, chronicle, retrieval.        | Authority map, read refs, structured-write proof if ever allowed. | EXTENSION_READ / ADAPTER | DCP extension mapping          |
| dope-memory                     | Chronicle/evidence receipt mapping.                                 | PM truth, ConPort truth.                                     | Chronicle proof refs.                                             | EXTENSION_READ           | DCP extension mapping          |
| dope-context                    | Code/docs retrieval mapping.                                        | Source truth.                                                | Source refs and retrieval caveats.                                | EXTENSION_READ           | DCP extension mapping          |
| dopecon-bridge                  | Adapter/proxy/event transport mapping.                              | Any canonical authority.                                     | Upstream authority refs; transport proof.                         | ADAPTER_ONLY             | DCP extension mapping          |
| ADHD Engine                     | Operator-support/cognitive-state hints.                             | PM/memory/retrieval/DCP authority.                           | Read-only signal proof.                                           | EXTENSION_READ           | DCP extension mapping          |
| GitHub / CI readiness           | Evidence and checks intake.                                         | Semantic proof, merge authority replacement.                 | Current checks, head SHA, PR state, reviewer classification.      | PARTIAL                  | PR Steward proof-readiness     |
| Leantime                        | PM metadata + sprint/project snapshot mapping.                      | Workflow legality/transitions, decision context, chronicle, technical context. | PM read receipts (canonical_backend=leantime).                    | PARTIAL                  | DCP extension mapping          |

**OBSERVED_BY_FILE:** Dopemux is a mixed workspace, not a single-service monolith, and authority is split by function across dopemux, dopetask, Leantime, task-orchestrator, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, and Repo-Truth-Extractor.

---
## 8. DCP Routing Architecture

### 8.1 Generic vs extension split

| Layer                          | Owner                    | Contents                                                                                                                                         |
| ------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| PCP generic interfaces         | PCP Core                 | Generic classification envelope, authority/risk/privacy concepts, proof requirements, runner abstraction, audit requirement slot, approval slot. |
| DCP-specific routing extension | DCP / Dopemux Extension  | DCP classifier, lane engine, route roles, model pools, Dopetask/Task Orchestrator/PR Steward/OpenClaw/OpenRouter mappings.                       |
| Runner/provider adapters       | Extension-owned adapters | Codex, Claude Code, AGY/Gemini, OpenClaw, OpenRouter, direct APIs, manual app capture, Dopetask where allowed.                                   |

### 8.2 Routing input model
**PROPOSED:** A DCP route decision input must include:
* task description
* repo/project identity
* worktree/ref/head SHA if known
* expected files touched
* privacy class
* risk class
* authority boundary
* required tools
* structured output requirement
* command execution requirement
* edit/write requirement
* estimated context/token size
* cost ceiling
* provider/model availability
* prior failure state
* audit requirement
* human approval status
* proof requirement
* runner compatibility
* secret scan state
* local benchmark certification state
### 8.3 Classification model
**PROPOSED:** Classification dimensions:

| Dimension  | Values / behavior                                                                                                                                    |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Risk       | R0 read, R1 draft, R2 test-only, R3 local edit, R4 multi-file edit, R5 security/authority, R6 release/production, UNKNOWN.                           |
| Privacy    | Public sandbox, public repo, private repo no secrets, possible secrets, secret-bearing, client data, security-sensitive, release-authority, UNKNOWN. |
| Authority  | PCP core, DCP extension, dNh extension, repo authority, bridge/proxy, runner, model/provider, unknown.                                               |
| Complexity | Scope size, file count, cross-plane impact, reversibility, runtime risk.                                                                             |
| Provenance | Runtime/proof/file/GitHub/CI/adjudication/claim/inference/external. Provenance may lower trust, never raise it magically.                            |

### 8.4 Trusted input-provenance contract
**PROPOSED:** Caller-asserted JSON is never enough for execution eligibility. Execution eligibility requires:
* evidence refs
* source labels
* validation state
* proof requirement
* allowed action set
* stop conditions
* human approval if required
* benchmark status if model/provider route matters
* independent audit when R4+ or authority-sensitive
### 8.5 Lane engine
**PROPOSED:** The lane engine converts classification into:
* allowed actions
* forbidden actions
* runner pool candidates
* proof envelope
* audit route
* approval gate
* escalation triggers
* stop reasons
**BLOCKED:** No lane may select a live-write runner until live-write gates exist.

### 8.6 Allowed and forbidden actions

| Class   | Allowed actions                                                     | Forbidden actions                                                           |
| ------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| R0/R1   | Read, summarize, draft, classify.                                   | Claim final proof, mutate runtime, merge.                                   |
| R2      | Generate tests, run offline-safe tests if allowed.                  | Treat tests as semantic proof by themselves.                                |
| R3/R4   | Local edits with git proof, diff, tests, embedded audit.            | Skip proof, self-audit, hidden scope expansion.                             |
| R5/R6   | Supervisor/release/security routing, independent audit, human gate. | OpenRouter-free, implementer sole audit, stale proof, unknown reviewer/bot. |
| UNKNOWN | Safe classification only.                                           | Write, release, schema-authority, security judgment.                        |

### 8.7 Runner backend mapping

| Runner/provider         | DCP role                                                       | Authority status                                          |
| ----------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| Codex                   | Bounded implementer / packet executor.                         | Helper, not authority.                                    |
| Claude Code Sonnet/Opus | Implementer or audit fallback depending on packet.             | Helper, not authority.                                    |
| AGY / Gemini            | Embedded audit or broad-context reviewer where available.      | Auditor/helper, not authority.                            |
| OpenClaw                | Worker/runtime substrate.                                      | DCP extension material, contracts-only until benchmarked. |
| OpenRouter              | Model routing transport.                                       | Router, not trust oracle.                                 |
| Dopetask                | External execution runtime through explicit supervised packet. | Extension-owned mapping, not PCP Core validation.         |
| PR Steward              | Readiness evidence intake.                                     | Advisory, not merge authority.                            |
| GitHub/CI               | Evidence spine and merge authority.                            | Not semantic proof by itself.                             |

### 8.8 OpenClaw/OpenRouter integration
**OBSERVED_BY_FILE / PROPOSED:** OpenClaw and OpenRouter stay in the DCP extension. OpenClaw is a worker/runtime substrate, OpenRouter is a routing/control layer, and neither becomes PCP Core or authority. OpenRouter-free is forbidden for private, secret, security, release, and schema-authority work.
### 8.9 Benchmark certification
**PROPOSED:** No production/high-trust OpenClaw/DCP route is accepted without local benchmark certification. Minimums include 100% valid JSON, 100% schema validity, 100% fail-closed unsupported-route blocking, evidence-grounding precision at least 98%, unsupported-claim rate at most 1%, contradiction recall at least 90%, and core-field stability at least 95%.
### 8.10 Human approval gates
Human approval is required for:
* R5 security/authority
* R6 release/production
* privacy override
* cost escalation
* benchmark bypass
* unknown provider/model in private/high-risk route
* live write
* destructive mutation
* scope expansion
* security/CI/auth changes
* auditor conflict
* stale proof with release impact
### 8.11 Proof bundle requirements
Proof must include:
* route decision ID
* task ID
* model/provider/runner requested and actual
* prompt/response hashes
* files read/changed
* git status before/after for write tasks
* diff stat and full diff
* commands, stdout/stderr refs, exit codes
* structured schema ID and validation result
* cost estimate and actual usage where model routing is involved
* audit decision
* approval event where required
* redaction report if private/sensitive
### 8.12 Embedded audit requirements
Embedded audit must record:
* auditor tool/model/runner/session
* invocation
* exit code if available
* verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR / SKIPPED
* findings
* fixes applied
* remaining risks
* skip reason if skipped
**BLOCKED:** Implementer cannot be the sole final auditor.
### 8.13 PR Steward readiness
PR Steward must harvest:
* PR metadata
* head SHA
* changed files
* commits
* reviews
* review comments
* review threads
* issue comments
* checks/CI state
* proof freshness
READY is blocked by stale proof, failed/stale checks, unknown reviewers/bots, unclassified review items, unresolved blocking threads, diff outside allowlist, or security/release approval gaps.

---
## 9. dNh CRM Extension Definition

| Component                    | Extension role                                                  | Forbidden in PCP Core            | Required proof                             | Stop condition                           | Packet                |
| ---------------------------- | -------------------------------------------------------------- | -------------------------------- | ------------------------------------------ | ---------------------------------------- | --------------------- |
| dNh project profile          | Project-specific PCP profile values.                            | dNh required core fields.        | Profile fixture + authority map.           | Stop if PCP Core requires dNh.           | dNh extension mapping |
| Authority docs               | Extension-provided authority refs.                              | Hardcoded dNh doc paths in core. | Docs inventory/freshness.                  | Stop if missing authority is normalized. | dNh extension mapping |
| Proof roots                  | Map dNh proof/status paths.                                     | Core proof path assumptions.     | Proof pointer mapping.                     | Stop if stale proof treated as ready.    | dNh extension mapping |
| Red lanes                    | Domain lanes for CRM, Telegram, calendar, identity, runtime DB. | Project lanes in core.           | Red-lane fixture and later executed traps. | Stop if lanes are assertion-only.        | dNh extension mapping |
| CRM runtime                  | Runtime mapping only.                                           | CRM concepts in PCP Core.        | Artifact-only export first.                | Stop on CRM write/import.                | dNh extension mapping |
| Telegram                     | Red-lane/adapter mapping.                                       | Messaging product in core.       | No-send proof.                             | Stop on send attempt.                    | dNh extension mapping |
| Calendar                     | Red-lane/adapter mapping.                                       | Calendar product in core.        | No-write proof.                            | Stop on calendar write.                  | dNh extension mapping |
| Identity                     | Domain authority mapping.                                       | Identity system in core.         | Authority map + secret policy.             | Stop on identity merge/mutation.         | dNh extension mapping |
| Policy                       | Domain policy mapping.                                          | dNh policy fields in core.       | Policy refs + approvals.                   | Stop on policy write.                    | dNh extension mapping |
| Event store                  | Runtime evidence map.                                           | Event-store assumption in core.  | Read-only artifact path.                   | Stop on import/write.                    | dNh extension mapping |
| Runtime DB                   | Forbidden/live-write lane.                                      | DB assumptions in core.          | DB path red-lane proof.                    | Stop on DB mutation.                     | dNh extension mapping |
| Artifact-only exporter       | First dNh-safe exporter.                                        | Generic exporter behavior.       | No import, no DB write, no send.           | Stop if live adapter used.               | dNh extension mapping |
| Reconciliation service       | Later extension adapter.                                        | PCP workflow engine.             | Dry-run proof + rollback.                  | Stop before live gates.                  | Later, after gates    |
| Task Orchestrator visibility | Optional projection.                                            | Required PCP workflow.           | Projection-only proof.                     | Stop on Task Orchestrator write.         | TO visibility         |

---
## 10. PR #925 Disposition
```text
PR925_STATUS: DRAFT / SALVAGEABLE / NOT_MERGE_READY / LIVE_STATE_AFTER_BUNDLE_UNKNOWN
PR925_ACTION: DEDOPEMUX_BEFORE_MERGE
PR925_MERGE_READY: NO
PR925_NEXT_REPAIR: REMAINING_SCOPING_VERDICT_PAL_REVIEW_THREAD_REPAIR_ONLY
```
**Preserve**
* Fixture packs as direction evidence.
* `project_profile`, `project_red_lanes`, `proof_pointer`, `audit_*`, `supervisor_decision` as candidate core schemas after cleanup.
* Existing DCP routing/lane/red-lane materials as Dopemux extension inputs.
* dNh fixture data as first project-extension sample.
* Proof/audit contracts and task-packet proof expectations.
**Repair**
* Downgrade overstrong `ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS`.
* Keep `NEEDS_SUPERVISOR` until PR Steward readiness and proof freshness clear.
* Classify unresolved review threads.
* Record PAL codereview/precommit as `NOT_RUN` or attach actual transcript.
* Re-pull PR #925 before packet execution.
**Do not re-repair unless live evidence regresses**
* `after_sha` orphan.
* dNh `policy_ref`.
**Move**
* `dopetask_packet_mapping.schema.json` to DCP extension.
* `orchestrator_item.schema.json` to DCP extension.
* Dopetask / Task Orchestrator forbidden-action confirmations to extension-owned export.
* OpenClaw/DCP routing contracts to DCP extension.
* dNh CRM/Telegram/calendar/identity/policy/runtime DB lanes to dNh extension.
**Rename / split**
* “Dopemux Project Control Plane core” to “PCP Core” only where actually generic.
* `project_evidence_export` into generic core export plus extension-owned confirmations.
* Executor schemas into generic runner envelope plus extension runner mappings.
* Workflow projection schemas into generic projection pointer plus DCP Task Orchestrator mapping.
**Supersede**
* Generic-DCP-parent framing.
* PR #925 labels claiming confirmed architecture.
* Any negative-test artifact that asserts pass without execution.
* Any fixture-only schema version that can never validate runtime exporter output because it requires `generated_from_fixture: true`.
**Must remain draft**
* Until core no longer requires Dopetask/Task Orchestrator.
* Until proof freshness is satisfiable and current.
* Until review threads are classified.
* Until PR Steward readiness is clean.
* Until embedded audit is independent and current.

---
## 11. PR #931 / OpenClaw Routing Disposition
```text
PR931_STATUS: OBSERVED_BY_GITHUB: CLOSED (verified 2026-06-19T22:25Z; not merged; head codex/openclaw-dcp-routing-contracts-0005r)
PR931_ACTION: DO_NOT_MERGE_FROM_AIR
PR931_MERGE_READY: NO (CLOSED)
OPENCLAW_ROUTING_AIR_USE: DCP_EXTENSION_INPUT_FOR_FUTURE_ROUTING_PACKET_ONLY
```
**OBSERVED_BY_FILE / OBSERVED_BY_GITHUB:** OpenClaw routing contracts exist as contracts/policy material, not production readiness. The supplied architecture regeneration says the PR #931 bundle claims no production routing and no benchmark execution; PR #931 is now live-verified **CLOSED** (not merged) via `gh pr view 931`, which reinforces the contracts-only posture rather than weakening it.
**AIR decision:** OpenClaw routing feeds the DCP routing extension as **future input only**, not PCP Core; it is not production-ready and remains gated by §8.9 benchmark certification.
**BLOCKED:** OpenClaw routing is not accepted for production until:
* contract schemas parse and validate
* benchmark harness runs
* route certification ledger exists
* provider/model identity is logged
* OpenRouter-free blocks are enforced
* human approval gates work
* proof bundle requirements are tested
* independent audit rules are enforced
* live PR #931 state is re-pulled if needed

---
## 12. Schema / Artifact Migration Matrix

| Current artifact                      | Current owner/location           | Target owner/location                     | Problem                                                            | Action                   | Packet                             |
| ------------------------------------- | -------------------------------- | ----------------------------------------- | ------------------------------------------------------------------ | ------------------------ | ---------------------------------- |
| `dopetask_packet_mapping.schema.json` | `schemas/project_control_plane/` | DCP extension                             | Names Dopetask; extension-specific executor.                       | MOVE_TO_DCP_EXTENSION    | Boundary repair                    |
| `orchestrator_item.schema.json`       | `schemas/project_control_plane/` | DCP extension                             | Task Orchestrator is Dopemux workflow/projection surface.          | MOVE_TO_DCP_EXTENSION    | Boundary repair                    |
| `executor_run_request.schema.json`    | PCP-ish core                     | PCP Core + extensions                     | Generic envelope possible; runner enum may encode project runners. | SPLIT_CORE_AND_EXTENSION | Boundary repair                    |
| `executor_run_result.schema.json`     | PCP-ish core                     | PCP Core + extensions                     | Generic result possible; extension fields need namespace.          | SPLIT_CORE_AND_EXTENSION | Boundary repair                    |
| `project_evidence_export.schema.json` | PCP Core candidate               | PCP Core + extension export sections      | Blocker = `generated_from_fixture` required + `const true` (rejects real runtime output); Dopetask/Task-Orchestrator concepts leak via `forbidden_action_confirmation` + sibling executor/orchestrator schemas — not necessarily top-level `dopetask_executed`/`live_task_orchestrator_written`. | GENERALIZE_AND_RENAME    | Boundary repair                    |
| `project_profile.schema.json`         | PCP Core candidate               | PCP Core + extension slots                | Mostly core; packet/proof roots too prescriptive.                  | SPLIT_CORE_AND_EXTENSION | Boundary repair                    |
| `project_red_lanes.schema.json`       | PCP Core candidate               | PCP Core with extension lane section      | Core nucleus useful; project lanes must be extension-owned.        | KEEP_IN_PCP_CORE         | Boundary repair                    |
| `proof_pointer.schema.json`           | PCP Core candidate               | PCP Core                                  | Generic concept; must bind freshness/head SHA later.               | KEEP_IN_PCP_CORE         | Boundary repair / exporter         |
| `audit_request.schema.json`           | PCP Core candidate               | PCP Core + extensions                     | Generic request, extension auditor roles need namespace.           | SPLIT_CORE_AND_EXTENSION | Boundary repair                    |
| `audit_result.schema.json`            | PCP Core candidate               | PCP Core                                  | Generic verdicts OK; source/tool fields need proof-family caution. | KEEP_IN_PCP_CORE         | Boundary repair                    |
| `supervisor_decision.schema.json`     | PCP Core candidate               | PCP Core                                  | Generic decision type OK; must not imply merge authority.          | KEEP_IN_PCP_CORE         | Boundary repair                    |
| `authority_map.schema.json`           | Missing                          | PCP Core                                  | Keystone absent.                                                   | ADD_NEW                  | Extension contract / authority map |
| `extension_manifest.schema.json`      | Missing                          | PCP Core                                  | Keystone absent.                                                   | ADD_NEW                  | Extension contract / authority map |
| DCP schemas                           | `schemas/dcp/` / DCP inputs      | DCP extension + possible PCP abstractions | Rich Dopemux surface; not PCP parenthood.                          | SPLIT_CORE_AND_EXTENSION | DCP extension mapping              |
| OpenClaw routing contracts            | routing bundle / policy files    | DCP routing extension                     | Contracts-only, benchmark not complete.                            | MOVE_TO_DCP_EXTENSION    | DCP routing extension              |
| dNh fixtures                          | project-control fixtures         | dNh extension                             | Correct extension fixture; no live adapter proof.                  | MOVE_TO_DNH_EXTENSION    | dNh extension mapping              |

---
## 13. Build Sequence

| Order | Packet ID                                          | Purpose                                                   | Scope                                                                 | Validation gates                                                                                                            | Stop conditions                                                                                 | Output                                 |
| ----: | -------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------- |
|     1 | `TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002`       | Re-scope PR #925 truthfully (RECONCILE existing `-0002` packet, do not recreate). | PR body/proof/report/review-thread/PAL evidence only.                 | JSON/schema validation, diff check, proof labels, review-thread classification.                                             | Runtime files, new schemas, exporter, live writes, already-fixed after_sha/dNh policy_ref redo. | Draft PR truthfully scoped.            |
|     2 | `TP-DMX-PCP-EXTENSION-CONTRACT-AUTHORITY-MAP-0001` | Add extension manifest and authority map as co-keystones. | Schemas/tests/docs.                                                   | Schema validation, no-override tests, fail-closed UNKNOWN tests.                                                            | Extension weakens core or promotes adapter to authority.                                        | Extension seam exists.                 |
|     3 | `TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001`          | Remove named Dopemux systems from PCP Core.               | Move/split schemas/fixtures; prepare exporter gates.                  | No Dopetask/TO required in generic fixture; `generated_from_fixture: const true` relaxed; runtime `head_sha` gate prepared. | PCP Core still requires named systems.                                                          | Clean PCP boundary.                    |
|     4 | `TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001`            | Implement generic exporter.                               | Runtime exporter/tests.                                               | Plain Git repo fixture output, commands, exits, artifacts, runtime `head_sha`.                                              | Requires Dopemux/dNh/OpenClaw/TO/Dopetask.                                                      | Runtime proof begins.                  |
|   4.5 | `TP-DMX-PCP-FIXTURE-TO-RUNTIME-VALIDATION-0001`    | Execute negative traps (MOVED UP — prove exporter fail-closed before extensions build on it). | Runtime validation harness.                                          | Failure index, computed negatives, command outputs, exit codes.                                                            | Assertion-only negatives remain.                                                                | Behavior evidence on the core exporter. |
|     5 | `TP-DMX-DCP-EXTENSION-MAPPING-0001`                | Map Dopemux systems into extension.                       | DCP extension namespace.                                              | Extension manifest, authority map, read/projection mappings.                                                                | Bridge/proxy promoted to authority.                                                             | DCP = PCP + Dopemux.                   |
|     6 | `TP-DMX-DCP-ROUTING-EXTENSION-MAPPING-0001`        | Map classifier/lane/model routing/OpenClaw/OpenRouter.    | Routing schemas, route decisions, proof/audit policies.               | Schema validation, benchmark harness spec, OpenRouter-free blocks, audit independence.                                      | Provider/model/router promoted to authority; benchmark claims without run.                      | DCP routing extension.                 |
|     7 | `TP-DNH-PCP-EXTENSION-MAPPING-0001`                | Map dNh extension.                                        | dNh profile/red lanes/proof roots/artifact-only exporter constraints. | No-write/no-import proof, red-lane fixture.                                                                                 | CRM/Telegram/calendar/DB write.                                                                 | dNh = PCP + dNh extension.             |
|     8 | `TP-DMX-PCP-PR-STEWARD-PROOF-READINESS-0001`       | Integrate PR Steward readiness.                           | PR metadata/proof/check intake.                                       | Current head SHA, checks, reviews classified.                                                                               | Unknown reviewer/bot, stale proof/checks, unresolved blocker.                                   | `MERGE_READINESS`.                     |
|     9 | `TP-DMX-PCP-TASK-ORCHESTRATOR-VISIBILITY-0001`     | Projection-only TO visibility.                            | Read/projection mapping.                                              | No MCP write, projection proof.                                                                                             | Task Orchestrator write attempted.                                                              | Workflow visibility.                   |
|    10 | `TP-DMX-PCP-LIVE-WRITE-GATES-0001`                 | Define live-write criteria.                               | Contracts only.                                                       | Approval, idempotency, rollback, dry-run proof, audit requirements.                                                         | Any live write.                                                                                 | `LIVE_WRITE_READY` criteria.           |
|    11 | `TP-DMX-PCP-FASTAPI-BRIDGE-LAST-0001`              | Bridge/live writes last.                                  | Adapter implementation only after gates.                              | Gate proof, rollback, post-write verification.                                                                             | Bridge promoted to authority.                                                                   | Safe adapter path, if still justified. |

**Correction applied:** Packet 2 includes both `extension_manifest.schema.json` and `authority_map.schema.json`. Packet 3 includes `generated_from_fixture: const true` relaxation and runtime `head_sha` gate preparation. Exporter stays after packets 2 and 3. Executed fixture-to-runtime validation (`TP-DMX-PCP-FIXTURE-TO-RUNTIME-VALIDATION-0001`) is sequenced as **step 4.5** — immediately after the generic exporter and before the DCP/dNh extension mappings — so extensions build on a behavior-proven core; the subsequent packets are renumbered 8–11.

---
## 14. Acceptance Gates

| Gate                                        | Required artifacts                                                                     | Required tests                                                              | Required proof                                                   | Required audit                             | Blocking conditions                                                                |
| ------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| PCP Core accepted                           | Core schemas, authority map, extension contract, generic exporter, baseline fixture.   | Schema tests, plain repo exporter, negative runner.                         | Current head SHA, command outputs, exits, artifacts.             | Independent audit PASS/PASS_WITH_RISKS.    | Requires named systems; stale proof; self-audit.                                   |
| Extension contract / authority map accepted | `extension_manifest.schema.json`, `authority_map.schema.json`, docs.                   | No-override, fail-closed unknown, additive-only tests.                      | Schema validation, diff, proof bundle.                           | Embedded audit distinct from implementer.  | Extension can weaken core, self-promote, or bypass proof/audit.                    |
| DCP extension accepted                      | DCP manifest, Dopemux authority map, mappings for named systems.                       | Extension validation, bridge-not-authority tests.                           | Mapping proof, no-live-write proof.                              | AGY/Gemini/Claude audit.                   | Bridge/proxy/mirror promoted to authority.                                         |
| DCP routing extension accepted              | Routing classifier/lane/model policy schemas, route decision schema, forbidden routes. | Route schema validation, fail-closed fixtures, OpenRouter-free block tests. | Route logs, provider/model requested/actual, proof requirements. | Independent routing audit.                 | Provider/model/router treated as authority; benchmark missing for high-trust.      |
| OpenClaw routing accepted                   | OpenClaw/OpenRouter contracts, benchmark ledger, provider probe spec.                  | Benchmark harness: JSON/schema/fail-closed thresholds.                      | Actual benchmark outputs, provider/model logs.                   | Independent audit.                         | Contracts-only claims; OpenRouter-free in protected lanes; provider drift.         |
| dNh extension accepted                      | dNh manifest, authority docs, red lanes, proof roots.                                  | No-write/no-import tests.                                                   | Artifact-only output proof.                                      | Independent audit.                         | CRM/Telegram/calendar/DB write.                                                    |
| Generic exporter accepted                   | Exporter command, output artifacts, docs.                                              | Plain Git repo fixture, generated/vendor/secret/contradiction traps.        | Git status, output hashes, failure index.                        | Embedded audit.                            | Requires Dopemux/dNh/OpenClaw/Dopetask/TO.                                         |
| Fixture-to-runtime validation accepted      | Negative-case runner, failure index.                                                   | Executed traps, not asserted traps.                                         | Command outputs and exit codes.                                  | Independent audit.                         | Assertion-only pass.                                                               |
| PR Steward proof-readiness accepted         | PR metadata, reviews, threads, checks, proof bundle.                                   | Current-head checks and classification tests.                               | Head SHA, proof freshness, review classification.                | PR Steward intake + supervisor if blocked. | Unknown reviewer/bot, stale proof/check, failed check, unresolved blocker.         |
| Task Orchestrator visibility accepted       | Projection mapping, read-only adapter docs.                                            | Read/projection tests.                                                      | No MCP write proof.                                              | Embedded audit.                            | Any write attempt or TO as proof truth.                                            |
| Live-write readiness accepted               | `LIVE_WRITE_READY` contract, canonical writer map, rollback plan.                      | Dry-run, idempotency, rollback, post-write verify tests.                    | Human approval, audit, PR readiness, dry-run proof.             | GPT-5.5 supervisor + independent audit.    | Missing canonical writer, stale proof, unknown reviewer, no rollback, no approval. |

---
## 15. Red Lines
1. **No live writes before gates.**
2. **No Dopetask execution in PCP Core validation.**
3. **No Task Orchestrator MCP write before write contract.**
4. **No dNh runtime mutation.**
5. **No FastAPI bridge before artifact/exporter/proof gates.**
6. **No bridge/proxy/mirror/cache/index promoted to authority.**
7. **No PR Steward as merge authority.**
8. **No green CI as semantic proof.**
9. **No self-certifying audit.**
10. **No extension weakening core fail-closed behavior.**
11. **No exporter before extension contract and boundary repair.**
12. **No provider/model/router promoted to authority.**
13. **No OpenRouter-free security/proof/release/schema-authority work.**
14. **No generic schema requiring named extension systems.**
15. **No `queue_drain.py execute=True` or `scripts/batch_resolve_and_merge.py` wiring.**
16. **No static fixture validation as sufficient proof.**
17. **No `generated_from_fixture: const true` runtime exporter trap.**
18. **No proof freshness gate that requires a commit to contain its own SHA.**
19. **No `OBSERVED_BY_ADJUDICATION` claim unless independently grounded in inspected files/proof/runtime.**
20. **No “DCP parent” framing. That beast is dead; do not taxidermy it. 🪦**
---
## 16. Next Packet Recommendation
```text
NEXT_PACKET_ID:
TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002
ALREADY_EXISTS_ON_PR925_BRANCH:
YES — task-packets/generated/TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002.json
(verified on codex/tp-dmx-pcp-architecture-validation-0001 via `gh pr diff 925 --name-only`).
ACTION = RECONCILE/verify the existing artifact; do NOT blind-create a duplicate.
NEXT_PACKET_TITLE:
Repair PR #925 PCP Parent Framing, Verdict Labels, Review Threads, and PAL Evidence
NEXT_PACKET_OBJECTIVE:
Make PR #925 truthfully describe fixture-only PCP architecture direction, downgrade overstrong verdict language, classify remaining unresolved review threads, record PAL codereview/precommit evidence as NOT_RUN or attach transcript, and keep PR #925 draft until extension contract and boundary repair are complete.
WHY_THIS_PACKET_NOW:
PR #925 currently blocks clean sequencing because its framing overclaims and its generic core still carries Dopemux-shaped required fields. The safe first move is proof/framing repair only, not schema movement or exporter work.
MUST_NOT_DO:
No exporter implementation.
No extension contract implementation.
No authority-map implementation.
No schema movement beyond docs/proof/report repair.
No Dopetask execution.
No Task Orchestrator MCP write.
No dNh runtime change.
No FastAPI bridge.
No Action Bridge mutation.
No live writes.
No redoing after_sha orphan or dNh policy_ref repair unless live PR evidence shows regression.
VALIDATION_GATES:
Re-pull PR #925 before execution.
JSON/schema validation for touched proof/report artifacts.
git diff --check.
PR body and validation report use PCP parent model with fixture/runtime-unproven labels.
AAA-B verdict-label downgrade complete.
Review threads classified or explicitly marked blocking.
PAL codereview/precommit evidence recorded as NOT_RUN or attached.
Proof-freshness gate is satisfiable and does not require after_sha == self-writing commit.
EXPECTED_OUTPUT:
Updated PR body/proof/report artifacts, review-thread classification, PAL evidence note, command outputs, exit codes, git diff --stat, git diff, embedded audit report, and refreshed PR Steward readiness if available.
```
This is a recommendation, not a full task packet. **OBSERVED_BY_DIFF:** `task-packets/generated/TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002.json` already exists on the PR #925 branch — the packet step must reconcile and verify that existing generated packet (re-pull PR #925 first), not recreate it.

---
## 17. AIR Use Policy
**READY_WITH_LIMITS:** This AIR is authoritative for build sequencing after runtime/GitHub truth and repo authority docs.
**OBSERVED_BY_POLICY:** Runtime code, config, compose wiring, tests, active entrypoints, and live PR evidence outrank this AIR.
**UNKNOWN:** Live PR #925/#931 state after the uploaded bundles must be re-pulled before any packet executes.
**NEEDS_SUPERVISOR:** If this AIR conflicts with RULES, SYSTEM_BOUNDARIES, AGENTS, runtime evidence, or live GitHub state, escalate.
**BLOCKED:** This AIR does not authorize live writes.
**BLOCKED:** This AIR does not make PR #925 merge-ready.
**BLOCKED:** This AIR does not make OpenClaw routing production-ready.
**BLOCKED:** This AIR does not authorize a FastAPI bridge.
**BLOCKED:** This AIR does not authorize Dopetask execution.
**BLOCKED:** This AIR does not authorize Task Orchestrator writes.
**BLOCKED:** This AIR does not turn PR Steward into merge authority.

---
## 18. Final Summary
```text
TRUE_ARCHITECTURE:
PCP Core is the reusable parent substrate.
DCP = PCP Core + Dopemux extension.
dNh CRM = PCP Core + dNh extension.
OpenClaw/OpenRouter/model routing = DCP routing extension material, contracts-only until benchmarked and proven.
NEXT_ACTION:
Write only TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002 next, scoped to remaining PR #925 framing/verdict/thread/PAL evidence repair.
DO_NOT_DO:
Do not build exporter first.
Do not implement extension contract inside the PR #925 repair packet.
Do not execute Dopetask.
Do not write Task Orchestrator.
Do not touch dNh runtime.
Do not build FastAPI bridge.
Do not mark PR #925 READY.
Do not treat OpenClaw routing as production-ready.
HIGHEST_RISK_SHORTCUT:
Building the generic exporter against the current Dopemux-shaped core, thereby baking Dopetask/Task-Orchestrator and generated_from_fixture constraints into runtime.
HIGHEST_LEVERAGE_SIMPLIFICATION:
One parent substrate, one extension contract + authority map seam, one de-Dopemux boundary repair, one generic exporter, then project extensions. No fog machine.
```
