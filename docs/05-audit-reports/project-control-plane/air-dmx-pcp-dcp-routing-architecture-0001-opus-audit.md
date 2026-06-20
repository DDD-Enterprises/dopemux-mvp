---
id: AUDIT-AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001-OPUS
title: "Opus Audit \u2014 AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001"
type: reference
owner: '@hu3mann'
author: claude-opus-4-8
date: '2026-06-19'
prelude: 'Adversarial Opus audit of the GPT-5.5 Pro AIR for PCP Core / DCP / dNh /
  DCP routing architecture. Grounded against live PR #925/#931 state and the PR #925
  branch schemas/proof. Decides whether the AIR is safe as the canonical build-planning
  artifact and whether task packets may be written from it.'
last_review: '2026-06-19'
next_review: '2026-09-17'
---
# Opus Audit — AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001

> Auditor: Claude Opus 4.8 (independent of GPT-5.5 Pro, the AIR author — auditor ≠ author satisfied).
> Grounding performed: live `gh pr view 925/931`; `git show`/`git grep` against
> `origin/codex/tp-dmx-pcp-architecture-validation-0001` (the PR #925 branch) for schemas, proof, fixtures, and the sibling AIR.
> The AIR is the target artifact; runtime + GitHub evidence outrank it.

## 1. Audit Verdict

```text
OPUS_AIR_AUDIT_VERDICT: ACCEPT_AIR_WITH_CORRECTIONS
CAN_WRITE_TASK_PACKETS_FROM_AIR: YES_WITH_CORRECTIONS
NEXT_ACTION: PATCH_AIR_THEN_WRITE_PACKETS
```

The AIR's spine is correct and, unusually, independently verifiable: I confirmed against the PR #925 branch that `project_evidence_export.schema.json` makes `generated_from_fixture` a top-level **required** field pinned to `const: true`, which means a real runtime exporter (emitting `false`) can never validate — so the AIR's central "exporter is blocked until boundary repair" thesis is file-true, not rhetoric (`OBSERVED_BY_FILE`). I confirmed `authority_map.schema.json` and `extension_manifest.schema.json` are genuinely absent, making the AIR's "co-keystones missing" correction load-bearing and right. I confirmed `dopetask_packet_mapping.schema.json` and `orchestrator_item.schema.json` sit inside the generic `schemas/project_control_plane/` directory, so the "PCP Core is Dopemux-shaped" claim is real, not stylistic. PR #925 is live OPEN + **draft** (`OBSERVED_BY_GITHUB`), so "salvageable, not merge-ready" is correct. The boundary model — PCP Core parent, DCP = PCP+Dopemux, dNh = PCP+project, routing/OpenClaw inside the DCP extension, Dopetask/Task-Orchestrator out of core — is coherent and consistently applied across every table. The build order correctly refuses exporter-first and puts live writes/FastAPI bridge last. The reasons this is ACCEPT_WITH_CORRECTIONS rather than ACCEPT: the AIR leans on two adjudication documents (`DCP_PCP_OPUS_AUDIT_OF_REGENERATION.md`, `DCP_PCP_ARCHITECTURE_REGENERATION_GPT55.md`) that are not attached and not in git, so several `OBSERVED_BY_ADJUDICATION` labels are unverifiable to me and trip the AIR's own Red Line #19; the new AIR shares a `-0001` ordinal and scope with the already-committed `AIR-DMX-PCP-DCP-ARCHITECTURE-0001.md` without declaring supersession; one migration-matrix cell overstates the evidence-export schema's required fields; and the placement of *executed* negative-trap validation after the exporter and all extension mappings is a real (non-blocking) sequencing weakness. None of these break the architecture; they are patches to apply before or alongside packet writing.

### Core decisions (direct answers)

| # | Question | Answer |
|---|---|---|
| 1 | PCP Core stated as parent? | YES |
| 2 | DCP = PCP Core + Dopemux extension? | YES |
| 3 | dNh = PCP Core + dNh extension? | YES |
| 4 | DCP routing / OpenClaw / model routing kept inside DCP extension? | YES |
| 5 | Dopetask / Task Orchestrator kept out of PCP Core? | YES (mandated to move; they currently leak — AIR is correcting, not endorsing) |
| 6 | Extension contract + authority map paired as co-keystones? | YES (packet 2) |
| 7 | De-Dopemux boundary repair before exporter? | YES (packet 3 before packet 4) |
| 8 | `generated_from_fixture: const true` relaxation an explicit gate? | YES (packet 3) — and file-verified as a real blocker |
| 9 | Avoids unsatisfiable proof-freshness requirements? | YES (Red Line #18; runtime `head_sha` computed, not self-referential) |
| 10 | PR #925 preserved as draft / not merge-ready? | YES (matches live state) |
| 11 | Avoids claiming a runtime exporter exists? | YES (exporter = UNKNOWN/MISSING throughout) |
| 12 | Enough build sequencing to write packets safely? | YES (12 ordered packets w/ scope, gates, stops) |
| 13 | Live writes blocked until gates exist? | YES (Red Lines #1–5, packet 11 before 12) |
| 14 | Preserves prior DCP revised-delta constraints? | PARTIAL — provenance/auditor≠implementer carried; source delta doc not inspectable here |
| 15 | Needs correction before packets are written? | YES — minor patches (see §3), none blocking the first packet |

## 2. Agreement Ledger

| AIR claim | Opus status | Evidence | Notes |
|---|---|---|---|
| PCP Core is the parent substrate | AGREE | `OBSERVED_BY_FILE` (sibling AIR + boundary model self-consistent) | Architecture is sound and consistently applied |
| DCP = PCP Core + Dopemux extension | AGREE | `OBSERVED_BY_FILE` | Split-authority workspace supports extension framing |
| dNh = PCP Core + dNh extension | AGREE | `OBSERVED_BY_AIR` + `INFERRED` | Consistent; dNh runtime not in this repo to verify |
| DCP routing extension placement | AGREE | `OBSERVED_BY_AIR` | Classifier/lane/model-routing correctly extension-owned |
| OpenClaw / model routing = extension, contracts-only | AGREE | `OBSERVED_BY_GITHUB` (PR #931 CLOSED) | Live state strengthens the "not production" posture |
| PR #925 not merge-ready (draft) | AGREE | `OBSERVED_BY_GITHUB` (isDraft=true, OPEN, reviewDecision empty) | Live-confirmed 2026-06-19T23:30Z |
| Extension contract + authority map are co-keystones | AGREE | `OBSERVED_BY_FILE` (both schemas absent on branch) | Correctly bundled into packet 2 |
| De-Dopemux before exporter | AGREE | `OBSERVED_BY_FILE` (Dopemux schemas in core dir; `const true` trap) | This is the single highest-value sequencing call |
| Generic exporter after boundary repair | AGREE | `OBSERVED_BY_FILE` | Exporter is MISSING; nothing claims it exists |
| Live writes blocked until gates | AGREE | `OBSERVED_BY_AIR` | Red Lines + packet 11→12 enforce it |
| FastAPI bridge last | AGREE | `OBSERVED_BY_AIR` | Packet 12, gated on packet 11 |
| `OBSERVED_BY_ADJUDICATION` provenance on regeneration/opus-audit docs | PARTIAL / CONFLICTING | `UNKNOWN` (docs not attached, not in git) | Conclusions corroborated elsewhere; label provenance unverifiable → trips AIR Red Line #19 |
| `project_evidence_export.schema.json` *requires* `dopetask_executed`/`live_task_orchestrator_written` | PARTIAL | `OBSERVED_BY_FILE` (top-level required = …`forbidden_action_confirmation`,`workflow_list`; those exact names not top-level) | Substantive Dopemux-shaping TRUE; exact field claim imprecise |

## 3. Correction Ledger

| Issue | AIR position | Opus correction | Severity | Required fix |
|---|---|---|---|---|
| Supersession vs committed sibling AIR | New AIR is `…ROUTING-ARCHITECTURE-0001`; silent on relationship to committed `AIR-DMX-PCP-DCP-ARCHITECTURE-0001.md` | Two `-0001` AIRs with overlapping scope = authority ambiguity. Declare this AIR as `Supersedes`/`Extends` the committed one (the routing dimension is the delta). | HIGH | Add `Supersedes:`/`Extends:` line naming `AIR-DMX-PCP-DCP-ARCHITECTURE-0001`; or re-number to a non-colliding ordinal |
| Unverifiable adjudication provenance | §1/§3/§5 cite `DCP_PCP_OPUS_AUDIT_OF_REGENERATION.md` + `…REGENERATION_GPT55.md` as `OBSERVED_BY_ADJUDICATION` | Those docs are not attached and not in git; per AIR Red Line #19 the label is not independently grounded for this audit. Downgrade to `CLAIMED_ONLY`/`UNKNOWN` where the source is not committed, OR commit the source docs into the repo so the label holds. | MEDIUM | Re-label or commit sources; conclusions stand regardless |
| Executed-validation sequence | Packet 8 (executed negative traps) runs after exporter (4) + extension mappings (5,6,7) | Exporter fail-closed behavior is only schema/fixture-asserted until packet 8; extensions then build on a behavior-unproven core. Move executed fixture-to-runtime validation to immediately after the exporter. | MEDIUM | Reorder: 4 → (executed validation) → 5,6,7 |
| `project_evidence_export` required-fields claim | §12: "Requires `live_task_orchestrator_written` and `dopetask_executed`" | Top-level `required` is `…forbidden_action_confirmation, workflow_list` — Dopemux concepts are nested, not top-level-named. Cite the real mechanism: `generated_from_fixture: const true` + `forbidden_action_confirmation` block + sibling `dopetask_packet_mapping`/`orchestrator_item` schemas. | LOW | Reword the matrix cell to the verified mechanism |
| PR #931 status precision | §11: `UNKNOWN_CURRENT / LOCAL_BUNDLE_SAYS_CLOSED` | Live-verified **CLOSED** (2026-06-19T22:25Z). Disposition unchanged (DO_NOT_MERGE_FROM_AIR, contracts-only). | LOW | Sharpen to `OBSERVED_BY_GITHUB: CLOSED` |
| Next packet already exists | §16 recommends authoring `TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002` | That packet already exists as `task-packets/generated/TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002.json` on the PR #925 branch. Packet step must reconcile/verify the existing artifact, not blind-create a duplicate. | INFO | Note "verify/extend existing" in packet instructions |
| Frontmatter + typo | No frontmatter; `DOPMUX_DCP` typo (self-noted) | Frontmatter added on save; fix typo to `DOPEMUX_DCP` when the manifest is authored in packet 2. | INFO | Mechanical |

## 4. Boundary Audit

| Concept | AIR owner | Correct owner | Verdict | Notes |
|---|---|---|---|---|
| PCP Core | PCP Core | PCP Core | CORRECT | Parent substrate; baseline `.git`-only operation required |
| Repo discovery | PCP Core | PCP Core | CORRECT | Generic, no named systems |
| Project identity | PCP Core | PCP Core | CORRECT | `.git` baseline + extension hints |
| Project profile | PCP Core (+ extension slots) | same | CORRECT | Named systems in slots only |
| Authority map | PCP Core | PCP Core | CORRECT | Currently MISSING (`OBSERVED_BY_FILE`); co-keystone |
| Evidence export | PCP Core (+ extension sections) | same | CORRECT-W/-REPAIR | Schema is Dopemux-shaped + `const true`-locked today |
| Red-lane engine | PCP Core (+ ext lanes) | same | CORRECT | Additive extension lanes; core fail-closed preserved |
| Proof/status pointer | PCP Core | PCP Core | CORRECT | Must bind runtime `head_sha` |
| Extension contract | PCP Core | PCP Core | CORRECT | MISSING today; co-keystone |
| Generic exporter | PCP Core (future) | PCP Core | CORRECT | MISSING; not claimed to exist |
| DCP routing classifier | DCP extension | DCP extension | CORRECT | Out of generic core |
| DCP lane engine | DCP extension | DCP extension | CORRECT | No merge/live-write authority |
| OpenClaw routing | DCP extension (contracts-only) | DCP extension | CORRECT | PR #931 CLOSED reinforces |
| OpenRouter / model routing | DCP extension | DCP extension | CORRECT | Router ≠ trust oracle |
| Dopetask mapping | DCP extension | DCP extension | CORRECT (mandated move) | Currently leaks into core schema dir |
| Task Orchestrator projection | DCP extension (projection-only) | DCP extension | CORRECT (mandated move) | Currently leaks into core schema dir; no MCP write |
| PR Steward | DCP extension (advisory) | DCP extension | CORRECT | Not merge authority |
| Action Bridge | DCP extension (BLOCKED until gates) | DCP extension | CORRECT | No live mutation pre-gate |
| Repo Truth Extractor | DCP extension (read) | DCP extension | CORRECT | Artifact consumer, not runtime truth |
| ConPort | DCP extension (read/adapter) | DCP extension | CORRECT | Not PM/workflow authority |
| dope-memory | DCP extension (read) | DCP extension | CORRECT | Chronicle, not PM truth |
| dope-context | DCP extension (read) | DCP extension | CORRECT | Retrieval, not source truth |
| dopecon-bridge | DCP extension (adapter-only) | DCP extension | CORRECT | Never canonical authority |
| ADHD Engine | DCP extension (read) | DCP extension | CORRECT | Operator hints only |
| dNh CRM | dNh extension | dNh extension | CORRECT | Not a template |
| Telegram | dNh extension (adapter/red-lane) | dNh extension | CORRECT | No-send proof |
| Calendar | dNh extension (adapter/red-lane) | dNh extension | CORRECT | No-write proof |
| Runtime DB | dNh extension (forbidden/live-write lane) | dNh extension | CORRECT | DB mutation = stop |
| FastAPI bridge | Plane/runtime boundary, packet 12 last | same | CORRECT | Gated on live-write criteria |

No boundary is mis-assigned. The only boundary risk is operational, not definitional: the *current code* (PR #925 branch) still has Dopetask/Task-Orchestrator schemas in the generic dir and a fixture-locked export schema — exactly what packet 3 exists to fix, and exactly why exporter-first would bake the wrong boundary into runtime.

## 5. Build Order Audit

```text
BUILD_ORDER_VERDICT: ACCEPT_WITH_REORDERING
```

One reorder, otherwise accept. Corrected order:

```text
1  PR925 framing/proof repair          (docs/proof only; reconcile EXISTING -0002 packet)
2  extension contract + authority map  (co-keystones together)
3  de-Dopemux boundary repair          (move Dopetask/TO schemas out; relax generated_from_fixture const; prep runtime head_sha)
4  generic exporter                    (plain-repo runtime output)
4.5 fixture-to-runtime validation      (EXECUTED negative traps — MOVED UP from #8)
5  DCP extension mapping
6  DCP routing extension mapping
7  dNh extension mapping
8  PR Steward proof-readiness          (was 9)
9  Task Orchestrator visibility        (was 10; projection-only)
10 live-write gates                    (was 11; contracts only)
11 FastAPI bridge last                 (was 12; gated on live-write criteria)
```

Checklist:

| Check | Verdict |
|---|---|
| PR925 repair first, scoped to docs/proof | PASS |
| Extension contract + authority map paired | PASS (packet 2) |
| De-Dopemux boundary repair before exporter | PASS (3 before 4) |
| Generic exporter after boundary repair | PASS |
| DCP extension mapping after exporter | PASS |
| DCP routing extension mapping placement | PASS |
| dNh extension mapping placement | PASS |
| Fixture-to-runtime (executed) validation placement | REORDER — move to immediately after exporter (4.5), before extensions build on it |
| PR Steward proof readiness before any merge posture | PASS |
| Task Orchestrator visibility = projection-only | PASS |
| Live-write gates before any live write | PASS |
| FastAPI bridge last | PASS |

## 6. Proof / Governance Audit

```text
PROOF_GOVERNANCE_VERDICT: PASS_WITH_RISKS
```

| Invariant | Preserved? | Evidence |
|---|---|---|
| auditorVerdict ≠ validationState | YES | §1, §8.12, acceptance gates separate auditor verdict from validation state |
| proof freshness ≠ lifecycle status | YES | Red Line #18; runtime `head_sha` computed; PR925 PROOF before/after SHAs distinct (`a05ebf77`→`9e00d5aa`) |
| green CI ≠ semantic proof | YES | Red Line #8; PR Steward READY blocked on substance |
| PR Steward ≠ merge authority | YES | Red Line #7; §7/§8.13 advisory-only |
| external research ≠ repo authority | YES | Evidence ledger caps external docs at "constraint walls" |
| model output ≠ authority | YES | §17 — AIR is build-planning only, runtime/GitHub outrank it |
| implementer ≠ final auditor | YES | Red Line #9, §8.12 "implementer cannot be sole final auditor" |
| no self-certification | YES | Independent-audit gates throughout |

Risks: (a) the AIR's own `OBSERVED_BY_ADJUDICATION` labels rest on documents not inspectable in this audit, which is precisely the self-certification-by-citation smell Red Line #19 forbids — the labels should be downgraded or the sources committed; (b) PROOF.json for the underlying PR #925 work shows only `json.tool`/`jsonschema` validation — **no** pytest, **no** PAL codereview/precommit, **no** executed negative traps — so the AIR's instruction to record PAL evidence as `NOT_RUN` and to treat current negatives as assertion-only is not just defensible, it is required by the proof state I observed.

## 7. PR #925 / PR #931 Handling Audit

| PR | AIR handling | Correct? | Notes | Required action |
|---|---|---|---|---|
| #925 | DRAFT / SALVAGEABLE / NOT_MERGE_READY; de-Dopemux before merge; repair scoped to remaining framing/verdict/threads/PAL | YES | Live: OPEN, **isDraft=true**, MERGEABLE, base `main`, head `codex/tp-dmx-pcp-architecture-validation-0001`, reviewDecision empty, updated 2026-06-19T23:30Z (`OBSERVED_BY_GITHUB`). "Do not re-do after_sha/policy_ref" is correct — PROOF before/after SHAs are already distinct and valid. | Re-pull at execution time (state moves); reconcile the already-present `-0002` generated packet rather than recreating it |
| #931 | `UNKNOWN_CURRENT / LOCAL_BUNDLE_SAYS_CLOSED`; DO_NOT_MERGE_FROM_AIR; contracts-only DCP-extension input | YES (over-hedged) | Live: **CLOSED**, base `main`, head `codex/openclaw-dcp-routing-contracts-0005r`, updated 2026-06-19T22:25Z (`OBSERVED_BY_GITHUB`). Closed not-merged supports contracts-only posture. | Sharpen label to `OBSERVED_BY_GITHUB: CLOSED`; keep OpenClaw as future routing-extension input pending benchmark |

## 8. Missing Evidence

| Missing evidence | Blocks AIR? | Blocks task packets? | Required before implementation? |
|---|---|---|---|
| Live current PR #925 state | NO (verified: draft/open) | NO | YES — re-pull at packet execution (mutable) |
| Live current PR #931 state | NO (verified: closed) | NO | Recommended at routing-packet time |
| `DCP_PCP_OPUS_AUDIT_OF_REGENERATION.md` (governing audit) | PARTIAL — weakens adjudication labels | NO | Commit to repo OR downgrade the labels citing it |
| `DCP_PCP_ARCHITECTURE_REGENERATION_GPT55.md` (design input) | PARTIAL | NO | Same as above |
| Generic PCP exporter runtime | NO (correctly absent) | NO | YES for exporter packet (packet 4) |
| `authority_map.schema.json` | NO (correctly MISSING) | NO | YES — authored in packet 2 |
| `extension_manifest.schema.json` | NO (correctly MISSING) | NO | YES — authored in packet 2 |
| DCP extension manifest | NO | NO | YES for packet 5 |
| dNh extension manifest | NO | NO | YES for packet 7 |
| OpenClaw benchmark certification | NO | NO | YES before any production/high-trust routing acceptance |
| Live-write gate proof | NO | NO | YES before packet 11/12 |
| Task Orchestrator write contract | NO | NO | YES before any TO write (visibility packet is read-only) |

## 9. Final Recommendation

```text
OPUS_FINAL:
  The AIR is a sound, verifiable build-planning artifact. Its spine — PCP Core parent,
  DCP/dNh as extensions, routing/OpenClaw in the DCP extension, Dopetask/Task-Orchestrator
  out of core, exporter blocked behind boundary repair — is correct and file-corroborated.
  Accept it with a short patch set, then write packets. Do not let it authorize anything live.

AIR_ACTION: PATCH_AIR (supersession header naming AIR-DMX-PCP-DCP-ARCHITECTURE-0001;
  downgrade/commit adjudication-doc provenance; fix the evidence-export required-fields cell;
  sharpen PR #931 to CLOSED; move executed validation to step 4.5; fix DOPMUX_DCP typo)

PACKET_ACTION: WRITE_TASK_PACKET_SERIES after the patch — the first packet is conservative
  enough (docs/proof only) to begin in parallel with the AIR patch.

FIRST_PACKET: TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002
  (RECONCILE the existing generated packet on the PR #925 branch; do not blind-create.
   Scope = PR body/proof/report/review-thread/PAL evidence only. Re-pull PR #925 first.)

DO_NOT_DO_NEXT: Do not build the generic exporter; do not implement the extension contract or
  authority map inside the PR #925 repair packet; do not move schemas yet; do not execute
  Dopetask; do not write Task Orchestrator; do not touch dNh runtime; do not build the FastAPI
  bridge; do not mark PR #925 READY; do not treat OpenClaw routing as production-ready.

HIGHEST_RISK_SHORTCUT: Building the generic exporter against today's Dopemux-shaped, fixture-locked
  core — fossilizing Dopetask/Task-Orchestrator schemas and the `generated_from_fixture: const true`
  trap into runtime. (File-verified that this trap is real.) The AIR correctly forbids it; the risk is
  an implementer skipping packets 2–3 to "just ship export."
```
