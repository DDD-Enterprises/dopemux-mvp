---
id: DCP_PCP_OPUS_AUDIT_OF_REGENERATION
title: Dcp Pcp Opus Audit Of Regeneration
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: Dcp Pcp Opus Audit Of Regeneration (reference) for dopemux documentation
  and developer workflows.
---
# Opus Audit of GPT-5.5 Pro PCP/DCP Architecture Regeneration

> [!NOTE]
> **Provenance**: `INTERNAL_AUDIT`
> **Status**: Audit of record
> **Auditor**: Claude Opus (adversarial systems architect / governance auditor), 2026-06-19
> **Target**: `DCP_PCP_ARCHITECTURE_REGENERATION_GPT55.md` (GPT-5.5 Pro decision artifact)
> **Evidence base**: `audit_inputs/pcp_dcp_full_architecture_regeneration.zip` (PR #925 GitHub state, leaking
> schemas, minimal/dopemux/dNh fixtures, E2E dry-run, AUDITOR_REPORT, repo authority docs) + the target doc
> **OPUS_AUDIT_VERDICT**: `ACCEPT_WITH_CORRECTIONS`
> **NEXT_ACTION**: `WRITE_AIR` (apply §6 corrections; this audit does NOT write the AIR)
>
> This audits the *regeneration decision*, not a re-audit of every evidence file. Runtime/source truth
> outranks this artifact (AGENTS.md §2). Standalone prior Opus/Pro/reconciliation adjudications cited by the
> target are MISSING per the bundle's own `MISSING_OR_UNKNOWN.md`; their substance was re-grounded here on the
> schemas and proof directly inspected.

## 1. Audit Verdict

**OPUS_AUDIT_VERDICT: ACCEPT_WITH_CORRECTIONS**
**NEXT_ACTION: WRITE_AIR** (with the mandatory corrections in §6 applied)

Pro's core architectural thesis is correct and, unusually, it is directly corroborated by the runtime/file evidence rather than resting only on prose: `project_evidence_export.schema.json` genuinely requires `forbidden_action_confirmation.{live_task_orchestrator_written, dopetask_executed}` and pins `generated_from_fixture: const true`, so the "generic" PCP Core is provably Dopemux-shaped today (OBSERVED_BY_FILE). Pro correctly treats PCP Core as the reusable parent, DCP and dNh as additive extensions, rejects DCP-as-parent, and correctly rules that PR #925 is salvageable but not merge-ready and needs structural de-Dopemux, not label-only repair (OBSERVED_BY_DIFF, OBSERVED_BY_PROOF). Pro's most important and correct move is overriding the prior Opus audit-of-record, which recommended "build the generic exporter next" — that prior recommendation is SUPERSEDED because the prior pass never inspected `evidence_export.json` (its own I2 caveat) and judged the schema generic while missing the required Dopetask/TO fields and the fixture-only `const`. Building an exporter against the current core schema is not merely risky, it is impossible without schema change, which vindicates Pro's "contract and boundary before exporter" ordering. The defects are real but non-blocking: Pro's analysis is partially STALE (commit `68b8fd17` already repaired the `after_sha` orphan and the dNh `policy_ref`, yet Pro's framing-repair packet still treats both as pending), `authority_map.schema.json` is named a P0 keystone but assigned to no build packet, the validation gate "`after_sha` equals latest PR head" is structurally unsatisfiable within the proof-writing commit, and the `generated_from_fixture: const true` removal is mentioned only in the deprecate list rather than as an exporter-packet gate. Pro also leans heavily on `OBSERVED_BY_ADJUDICATION` labels whose source artifacts (standalone Opus/Pro/reconciliation adjudications) are themselves MISSING per the bundle's own `MISSING_OR_UNKNOWN.md`, so those provenance claims are technically unverifiable even though their substance independently checks out against the schemas and proof I read. None of this rises to NEEDS_PRO_REWRITE or NEEDS_ADDITIONAL_EVIDENCE for the architecture decision itself; the model is sound enough to become the AIR basis once the scoping and staleness corrections in §6 are applied. Bluntly: Pro got the architecture right, got the sequencing right, and is honest about what is unproven — it just shipped a slightly stale PR-repair plan and left two keystone gaps under-wired.

## 2. Agreement Ledger

| Pro claim | Opus status | Evidence | Notes |
|---|---|---|---|
| PCP Core is reusable parent substrate | AGREE | INPUT_SUMMARY hypothesis; minimal_fixture `project_kind:GENERIC`, `root_marker:.git` | PCP Core is INTENT/PROPOSED — no runtime exists; correctly labeled PARTIAL/MISSING |
| DCP = PCP Core + Dopemux extension | AGREE | dopemux_fixture `project_kind:DOPEMUX`, `root_marker:.dopetaskroot`, lanes `dopetask-exec`/`task-orchestrator-live-write`; AGENTS.md §6 | OBSERVED_BY_FILE |
| dNh = PCP Core + project extension | AGREE | dnh red_lanes: crm-write/telegram-send/calendar-write/runtime-db PROJECT-scoped, fixture-only | OBSERVED_BY_FILE; runtime UNKNOWN |
| Reject DCP-as-parent framing | AGREE | AGENTS.md §6 split authority (dopecon-bridge transport-only, etc.) | Monolithic DCP parent contradicts repo boundaries |
| PR #925 not merge-ready | AGREE | GITHUB_PR925_STATE `isDraft:true`, AUDITOR_REPORT `NEEDS_SUPERVISOR` | OBSERVED_BY_GITHUB / OBSERVED_BY_PROOF |
| PR #925 needs de-Dopemux before merge (not label-only) | AGREE | `project_evidence_export.schema.json` requires `dopetask_executed`/`live_task_orchestrator_written`; `dopetask_packet_mapping` + `orchestrator_item` under `project_control_plane/` | Strongest verified claim (OBSERVED_BY_FILE) |
| Extension contract before generic exporter | AGREE | `generated_from_fixture: const true` blocks runtime validation; prior Opus "exporter next" was schema-blind | SUPERSEDES prior Opus audit-of-record recommendation |
| Dopetask/Task Orchestrator are extension concepts | AGREE | schema $ids + E2E chain steps "Dopetask packet mapping dry-run", "Task Orchestrator note item dry-run"; AGENTS.md §6 | OBSERVED_BY_FILE/DIFF |
| Generic authority-map schema missing | AGREE | MISSING_OR_UNKNOWN.md; no `authority_map.schema.json` in schema set | Confirmed MISSING |
| Generic extension contract missing | AGREE | MISSING_OR_UNKNOWN.md; no `extension_manifest.schema.json` | Confirmed MISSING |
| Runtime exporter unproven | AGREE | E2E `generated_from_fixture:true`, `head_sha:"...PLACEHOLDER-not-computed"`, `generic_exporter_claim` disclaims live impl | OBSERVED_BY_PROOF |
| Negative cases asserted, not executed | AGREE | minimal `negative_cases.json` `expected_result==asserted_result`; AUDITOR_REPORT Q5 | OBSERVED_BY_PROOF |
| Live writes blocked next | AGREE | E2E all forbidden flags false; profiles `export_mode:ARTIFACT_ONLY`, `allow_live_writes:false` | const-enforced |
| `ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS` overstrong | AGREE | AUDITOR_REPORT M3/AAA-B; multi-model consensus converged | Structured field still reads CONFIRMED |

## 3. Disagreement / Correction Ledger

| Issue | Pro position | Opus correction | Severity | Required AIR treatment |
|---|---|---|---|---|
| Framing-repair packet staleness | Packet 1 must repair `after_sha` freshness and (implicitly) dNh fixture | `68b8fd17` ALREADY fixed `after_sha` orphan (→`84149bced`) and dNh `policy_ref`; only AAA-B verdict-label, review-thread classification, and PAL-chain evidence remain | HIGH | Re-scope packet 1 to remaining-only items; do not re-do completed repairs |
| `after_sha == head` gate | Listed as a validation gate | Unsatisfiable: the commit that writes PROOF cannot contain its own SHA (one-commit lag is structural) | MEDIUM | Restate gate as "after_sha = proof-writing commit's parent + reachable note" or "freshness checker tolerant of proof commit" |
| `authority_map.schema.json` unassigned | P0 keystone in matrix; no owning packet | Keystone with no build packet will fall through | HIGH | Assign authority-map schema to packet 2 alongside extension manifest |
| `generated_from_fixture: const true` removal | Only in deprecate list | Exporter packet is blocked until this `const` is relaxed; not a gate | MEDIUM | Make `const` relaxation + runtime `head_sha` computation explicit acceptance gates in de-Dopemux (P0) and exporter packets |
| Extension-contract vs de-Dopemux co-dependency | Strict sequence: contract (#2) then de-Dopemux (#3) | Core boundary and extension contract are mutually defining; strict serialization risks contract churn | MEDIUM | AIR should pair #2/#3 as co-designed (contract drafted, core cut, contract finalized) |
| OBSERVED_BY_ADJUDICATION provenance | Cited as observed | Standalone Opus/Pro/reconciliation adjudications are MISSING (bundle's own ledger); only AUDITOR_REPORT exists (adversarial, not architectural) | MEDIUM | Downgrade those to INFERRED/CLAIMED_ONLY unless re-grounded on schemas/proof verified here |
| `DOPMUX` typo propagated | extension_kind enum `DOPMUX_DCP`; reuses misspelling | AUDITOR_REPORT L2 flagged `DOPMUX`→`DOPEMUX`; Pro re-encodes it | LOW | Fix enum spelling in AIR |
| extension_manifest YAML | Presented as the contract shape | It is PROPOSED/invented, not validated; fine as draft but must not be treated as settled | LOW/INFO | Mark as proposed starting point, subject to packet-2 validation |
| Live PR currency | Treats bundle PR state as authoritative | Bundle captured ~`68b8fd17` (06-19); anything later is UNKNOWN/STALE | INFO | Re-pull PR #925 head before packet 1 executes |

## 4. Architecture Boundary Audit

| Concept | Pro owner | Correct owner | Verdict | Notes |
|---|---|---|---|---|
| PCP Core | PCP Core (parent substrate) | PCP Core | CORRECT | Aspirational/PROPOSED — no runtime yet |
| Project profile | PCP Core (split core/ext fields) | PCP Core | CORRECT | `project_profile.schema.json` mostly core; packet/proof roots too prescriptive |
| Authority map | PCP Core (MISSING) | PCP Core | CORRECT but UNASSIGNED | Keystone with no build packet — §3 HIGH |
| Evidence export | PCP Core (generalize, strip Dopetask/TO) | PCP Core | CORRECT | Verified leak: requires `dopetask_executed`/`live_task_orchestrator_written` + `const true` |
| Red-lane engine | PCP Core generic + extension lanes | PCP Core | CORRECT | Core nucleus good; project lanes extension-owned |
| Proof/status pointer | PCP Core | PCP Core | CORRECT | Must bind head SHA/freshness; currently asserted |
| Extension contract | PCP Core (MISSING keystone) | PCP Core | CORRECT | Genuinely absent (OBSERVED_BY_FILE) |
| Generic exporter | PCP Core (after boundary repair) | PCP Core | CORRECT | Blocked by `const true` + Dopemux fields |
| DCP routing classifier | Dopemux/DCP extension | Dopemux/DCP extension | CORRECT | `src/dopemux/dcp/routing_classifier.py` is Dopemux runtime |
| DCP lane engine | Dopemux/DCP extension | Dopemux/DCP extension | CORRECT | dopemux_fixture references `schemas/dcp/` |
| Dopetask mapping | DCP extension (EXTENSION_ONLY) | dopetask runtime via DCP extension | CORRECT | AGENTS.md §6: external execution runtime |
| Task Orchestrator projection | DCP extension (projection only) | task-orchestrator via DCP extension | CORRECT | AGENTS.md §6: workflow transitions; projection not proof truth |
| PR Steward | DCP extension (readiness, not authority) | Dopemux/DCP extension | CORRECT | Advisory; not merge authority |
| Action Bridge | DCP extension (BLOCKED) | Dopemux/DCP extension | CORRECT | Live-mutation; correctly deferred |
| OpenClaw routing | DCP extension (CONTRACTS_ONLY) | Dopemux/DCP extension | CORRECT | PR #931 closed-not-merged; contracts-only |
| dNh CRM | dNh extension | dNh extension | CORRECT | Fixture-only; runtime UNKNOWN |
| Telegram | dNh extension (red-lane/adapter) | dNh extension | CORRECT | `telegram-send` PROJECT lane |
| Calendar | dNh extension | dNh extension | CORRECT | `calendar-write` PROJECT lane |
| Runtime DB | dNh extension (forbidden/live lane) | dNh extension | CORRECT | `runtime-db` PROJECT lane |
| ConPort | DCP extension (read/structured-write map) | ConPort canonical (decisions/progress/context) | CORRECT | Extension maps to it, does not own it (AGENTS.md §6) |
| dope-memory | DCP extension (chronicle map) | dope-memory canonical | CORRECT | Chronicle/receipts |
| dope-context | DCP extension (retrieval map) | dope-context canonical | CORRECT | Code/docs retrieval |
| dopecon-bridge | DCP extension (ADAPTER_ONLY) | bridge/proxy/transport only | CORRECT | AGENTS.md §6: not canonical authority |
| Repo Truth Extractor | DCP extension (read artifacts) | RTE audit/extraction only | CORRECT | Evidence artifacts, not runtime truth |
| ADHD Engine | DCP extension (read-only signals) | ADHD Engine operator/cognitive state only | CORRECT | Hooks/recommendations only |

No boundary mis-assignments found. Pro's ownership map is consistent with AGENTS.md §6 throughout.

## 5. Build Order Audit

**BUILD_ORDER_VERDICT: ACCEPT_WITH_REORDERING**

The macro order is correct: contract/boundary before exporter, extensions after core, validation before live gates, FastAPI bridge/live writes last. Corrected order:

1. **PR #925 framing/verdict repair — RE-SCOPED.** Only: downgrade structured `architecture_verdict` field (AAA-B), classify the two outdated-but-unresolved review threads, record PAL codereview/precommit as `NOT_RUN` or attach transcript (AAA-A). Drop the already-completed `after_sha`/dNh `policy_ref` work. Keep draft.
2. **Extension contract + authority-map schema (co-keystone).** Add `extension_manifest.schema.json` AND `authority_map.schema.json` together (fix Pro's unassigned-keystone gap). Fail-closed/no-override tests.
3. **PCP Core de-Dopemux boundary repair.** Move `dopetask_packet_mapping`/`orchestrator_item` to DCP namespace; strip `forbidden_action_confirmation` Dopemux fields from core export; **relax `generated_from_fixture: const true`** and add runtime `head_sha` (explicit gates). Co-validate against the packet-2 contract.
4. Generic exporter on plain Git repo (now unblocked).
5. DCP extension mapping.
6. dNh extension mapping (artifact-only).
7. Fixture-to-runtime negative-trap execution.
8. PR Steward proof-readiness integration.
9. Task Orchestrator visibility (projection-only).
10. Live-write gates (contracts).
11. FastAPI bridge / live writes (last).

## 6. AIR Readiness

**AIR_READY: YES_WITH_CORRECTIONS**

The AIR writer must apply exactly these corrections:

1. State PCP Core as **intended/PROPOSED architecture**, not existing runtime; no PCP Core exporter exists.
2. Re-scope the PR #925 first packet to remaining items only (verdict-field downgrade, review-thread classification, PAL-evidence); record that `after_sha` orphan and dNh `policy_ref` were already fixed in `68b8fd17`.
3. Assign `authority_map.schema.json` to the extension-contract packet (co-keystone with `extension_manifest.schema.json`).
4. Make `generated_from_fixture: const true` relaxation + runtime `head_sha` computation explicit acceptance gates of the de-Dopemux (P0) and exporter packets.
5. Restate the proof-freshness gate so it is satisfiable (no "after_sha == self-commit" requirement).
6. Downgrade `OBSERVED_BY_ADJUDICATION` claims to `INFERRED`/`CLAIMED_ONLY` unless re-grounded on the schemas/proof directly verified here; note the source adjudications are MISSING.
7. Fix `DOPMUX`→`DOPEMUX` in the extension-kind enum.
8. Mark the extension_manifest YAML as a proposed draft to be validated in packet 2, not a settled contract.
9. Pair packets 2 and 3 as co-designed rather than strictly serial.

## 7. Missing Evidence

| Missing evidence | Decision affected | Blocks AIR? | Blocks implementation? |
|---|---|---|---|
| Standalone Opus/Pro/reconciliation adjudication artifacts | Provenance of OBSERVED_BY_ADJUDICATION claims | No (substance corroborated by schemas/proof) | No |
| Generic PCP exporter runtime | Runtime/negative-case behavior proof | No | Yes (it is the exporter packet deliverable) |
| `extension_manifest.schema.json` | Core/extension boundary definition | No (AIR specifies it) | Yes (packet 2 keystone) |
| `authority_map.schema.json` | Machine-checkable ownership | No | Yes (clean boundary) |
| DCP / dNh extension manifests | Extension mapping validation | No | Yes (packets 5/6) |
| Live PR #925 head after bundle capture (post-`68b8fd17`) | Packet-1 scoping accuracy | No | Partial — re-pull before packet 1 |
| dNh live repo/exporter | Live adapter validation | No | No (out of scope until packet 6) |
| Root `RULES.md` / `SYSTEM_BOUNDARIES.md` | Authority cross-check | No (docs/03-reference equivalents present) | No |
| Externally-run PAL chain transcript | AAA-A closure | No | Partial — packet-1 evidence item |

## 8. Final Recommendation

**OPUS_FINAL:** Pro's architecture regeneration is substantively correct, evidence-aligned, and safe to use as the canonical basis after applying the §6 corrections; it correctly and defensibly supersedes the prior Opus audit-of-record's "exporter next" recommendation because that recommendation was made without inspecting the evidence-export schema. The only real defects are a stale PR-repair plan and two under-wired keystones (authority-map packet assignment, `const`-removal gating), all of which are doc-level fixes.

**AIR_ACTION:** WRITE_AIR now, encoding the corrected three-layer model (PCP Core parent; DCP and dNh as additive, non-overriding extensions) and the corrected 11-step build order from §5, with the §6 corrections mandatory.

**NEXT_PACKET_AFTER_AIR:** The re-scoped PR #925 verdict/thread/PAL repair (TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR — remaining-items-only), immediately followed by the co-designed extension-contract + authority-map keystone packet.

**DO_NOT_DO_NEXT:** Do not implement the generic exporter; do not build the FastAPI/Action bridge; do not execute Dopetask; do not write Task Orchestrator or any MCP/live state; do not mark PR #925 READY; do not re-do the `after_sha`/dNh `policy_ref` repairs already landed in `68b8fd17`.

**HIGHEST_RISK_SHORTCUT:** Building the generic exporter against the current `project_evidence_export.schema.json` — it would bake `dopetask_executed`/`live_task_orchestrator_written` and the unsatisfiable `generated_from_fixture: const true` into runtime code, cementing the exact Dopemux-shaped core the whole regeneration exists to remove.
