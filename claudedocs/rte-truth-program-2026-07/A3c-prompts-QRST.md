# RTE-TRUTH A3 (batch c) — Prompt-Engineering QUALITY Review: Phases Q, R, S, T

**Auditor:** subagent (worktree focused-mahavira-5bd29b) · **Date:** 2026-07-10
**Scope:** 38 templates in `services/repo-truth-extractor/promptsets/v4/prompts/` — `PROMPT_Q*` (6), `PROMPT_R*` (12), `PROMPT_S*` (13), `PROMPT_T*` (7).
**Rules baseline:** `promptsets/v4/PROMPTSET_RULES.md` (Evidence / Determinism / Anti-Fabrication / Failure Modes).
**Mode:** READ-ONLY. No live LLM calls. Confidence: `high` (all 38 files + rules read directly; downstream runner behavior NOT_RUN).

## Scoring key (1–5, higher = better)
- **(a) instruction clarity** — is the task unambiguous and operationalized?
- **(b) output-contract explicitness** — are outputs, fields, and containers pinned?
- **(c) injection posture** — defense against untrusted repo/artifact content reaching a paid LLM.
- **(d) evidence / anti-fabrication + grounding** — for R/S synthesis: does it require citing *which upstream artifact* each claim came from?
- **(e) schema-ability value** — payoff of adding a JSON Schema (none in this batch has one).

---

## Phase Q — pipeline QA / collision (6 templates)

| Step | a | b | c | d | e | Notes |
|------|---|---|---|---|---|-------|
| Q0 PIPELINE_COMPLETENESS/MANIFEST | 3 | 4 | 1 | 3 | 4 | Boilerplate body; "scan relevant files for domain-specific patterns" is vague. Clean output contract. |
| Q1 MISSING_ARTIFACTS/RECOVERY | 3 | 4 | 1 | 3 | 4 | As Q0; itemlist_by_id, id/status/checks/issues/evidence. |
| Q2 DUPLICATE_IDS/COLLISIONS | 3 | 4 | 1 | 3 | 4 | As Q0. |
| Q3 DRIFT_DETECTION/NORM_DIFFS | 3 | 4 | 1 | 3 | 3 | Legacy names raw-vs-norm counts + truncation flags; normalized body never operationalizes them. |
| Q9 MERGE/QA | 3 | 4 | 1 | 3 | 4 | Two outputs, mixed merge strategies (itemlist_by_id + single_payload) correctly distinguished. |
| Q11 ARTIFACT_COLLISION_REPORT | **5** | **5** | 1 | **4** | **5** | Hand-authored gold: explicit item shape, `risk`/`recommendation` enums, "filesystem presence ≠ canonical writer" guard, per-writer evidence, UNKNOWN handling. |

## Phase R — arbitration / synthesis (12 templates)

| Step | a | b | c | d | e | Notes |
|------|---|---|---|---|---|-------|
| R0 CONTROL_PLANE_TRUTH_MAP | 3 | 2 | 1 | 3 | 2 | MD, only `id,evidence` required for a "truth map". (Procedure numbering clean 1→14.) |
| R1 DOPE_MEMORY_IMPL_TRUTH | 3 | 3 | 1 | 3 | 3 | IMPLEMENTED/PLANNED/GAPS + verify-cmds (legacy). 3 outputs (2 JSON w/ path+line_range). Dup-numbering bug. |
| R2 EVENTBUS_WIRING_TRUTH | 3 | 2 | 1 | 3 | 3 | Event/Producers/Consumers/Adapter table is highly tabular but declared MD-only. Dup bug. |
| R3 TRINITY_BOUNDARY_TRACE | 3 | 2 | 1 | 3 | 3 | Good IMPLEMENTED-vs-PLANNED split. Dup bug. |
| R4 TASKX_INTEGRATION_TRUTH | 3 | 2 | 1 | 3 | 2 | Dup bug. |
| R5 WORKFLOWS_TRUTH_GRAPH | 3 | 3 | 1 | 3 | 3 | **Container mismatch:** `required_item_fields: nodes, edges, schema` but `kind: markdown / markdown_concat`. Dup bug. |
| R6 PORTABILITY_RISK_LEDGER | 3 | 3 | 1 | 3 | 3 | `id/risk/severity/location/evidence` rows — ledger is schema-able. Dup bug. |
| R7 CONFLICT_LEDGER *(synth)* | 3 | 2 | 1 | **4** | 2 | Strong arbitration (code>docs, DOC_SUPERSESSION, cite both sides) but **no per-claim upstream-artifact citation** despite aggregating 10 inputs. Dup bug. |
| R8 RISK_REGISTER_TOP20 *(synth)* | 3 | 3 | 1 | 3 | 3 | Aggregates 11 upstream artifacts; grounding relies on repo-file evidence only, no upstream-item attribution. Dup bug. |
| R9 LEANTIME_INTEGRATION_TRUTH *(synth)* | 4 | 4 | 1 | 4 | 3 | Hand-authored: required_sections + order + Evidence Index (path/line_range/excerpt). No dup bug. |
| R10 TWO_PLANE_ARCH_TRUTH *(synth)* | 4 | 4 | 1 | 4 | 3 | Hand-authored: ownership matrix rows (surface/owner_plane/evidence), Evidence Index. |
| R11 SECURITY_RISK_SYNTHESIS *(synth)* | **5** | **5** | 1 | **5** | 4 | **Gold.** `[SEC-XXX] ← ARTIFACT:item_id` traceability, inline anti-fab ("no new evidence — synthesis step"), severity caps, deterministic risk-ID sort, explicit failure modes. |

## Phase S — Opus synthesis (13 templates)

| Step | a | b | c | d | e | Notes |
|------|---|---|---|---|---|-------|
| S0 ARCHITECTURE_SYNTHESIS | 3 | 2 | 1 | 3 | 2 | **Contract bug:** schema "Required output content contracts" lists 9 *upstream inputs* as outputs; only 2 real outputs. Dual-alias duplication. `EVIDENCE: artifact#anchor` citation is good. |
| S1 MCP_TO_HOOKS_MIGRATION | 4 | 3 | 1 | 3 | 3 | Eligibility gate, no-go triggers, rollback. Dual alias. |
| S2 DECISION_DOSSIER | 4 | 4 | 1 | 3 | **4** | Explicit decision row fields (decision_id/context/options/recommendation/evidence/risk_ids/verification/stop). Dual alias. |
| S3 ARCH_PROOF_HOOKS | 4 | 4 | 1 | **4** | **4** | Claim→proof row fields + "avoid implying commands were executed" anti-fab. Dual alias. |
| S4 TWO_PLANE_ARCHITECTURE *(synth)* | 3 | 3 | 1 | **2** | 2 | Required sections only; **no citation shape** — "strict evidence anchors" prose. Dual alias. |
| S5 TASK_ORCHESTRATOR *(synth)* | 3 | 3 | 1 | **2** | 2 | As S4; weak grounding. Dual alias. |
| S6 LEANTIME_ANALYSIS *(synth)* | 3 | 3 | 1 | **2** | 2 | Has Security/Authorization section but no grounding requirement. Dual alias. |
| S7 OVERSEER_AGENT_FLOW | **1** | **1** | 1 | **1** | 1 | **Self-admitted STUB** ("rewrite deferred to Opus… structural stub to pass v5 linting"), "highly unstructured markdown", 4 vague steps, no citation, no anti-fab. Feeds S11 + S12. |
| S8 ARCHITECTURE_DIAGRAMS | 4 | 4 | 1 | 4 | 3 | 5 named Mermaid sections, per-section source ID, `EVIDENCE:#id`, missing-artifact path. |
| S9 DEPENDENCY_GRAPH_SUMMARY | **5** | 4 | 1 | 4 | 3 | Algorithmic: density formula, instability index Ce/(Ca+Ce), DFS cycle detection, `EVIDENCE:#edge_id`. |
| S10 API_SURFACE_REFERENCE | 4 | 4 | 1 | 4 | 3 | 4 sections + cross-ref matrix, `EVIDENCE:#item_id`. |
| S11 DOCUMENTATION_GENERATION *(synth)* | 4 | 4 | 1 | 3 | 3 | 10 mapped sections + provenance table, but `SOURCE: filename` only (coarser than item_id). Consumes S7 stub → inherits fabrication risk. |
| S12 STABILITY_SIGNATURE | 4 | **5** | 1 | 4 | **5** | Concrete JSON example, FAIL_CLOSED, deterministic hashing. Nearly already-schema'd. |

## Phase T — task-packet factory (7 templates)

| Step | a | b | c | d | e | Notes |
|------|---|---|---|---|---|-------|
| T0 TASK_PACKET_FACTORY | 2 | 2 | 1 | 3 | 3 | **Contract marooned in Legacy block** (C2, below). `canonical_writer_step_id: T9` on T0's *own* outputs → multi-writer collision. Legacy schema requires `run_id`,`generated_at` — **violates PROMPTSET_RULES determinism**. |
| T1 EMIT_PACKETS_TOP10 | 2 | 2 | 1 | 3 | 3 | Rich packet header/sections live only in Legacy. TP_BACKLOG_TOPN canonical=T9 collision; `generated_at` in index schema. |
| T2 PACKET_SCHEMA/AUTHORITY | 3 | 3 | 1 | 3 | **4** | This step *defines* the packet schema + authority hierarchy (R>X>policy). High schema value. Goal boilerplate mismatch. |
| T3 PACKET_GENERATION_BATCHED | 2 | 3 | 1 | 3 | 3 | Real contract (8 required sections, commit plan) in Legacy only. |
| T4 PACKET_DEDUP/COLLISION | 3 | 3 | 1 | 3 | 3 | Good deterministic tie-breaks (evidence density / blast radius / dependency) — in Legacy. |
| T5 PACKET_ORDERING/RUN_PLAN | 3 | 2 | 1 | 3 | 3 | Topo-sort plan. TP_BACKLOG_TOPN canonical=T9 collision (3rd writer). |
| T9 MERGE/QA | 3 | 3 | 1 | 3 | **4** | 5 outputs; TP_QA (status/checks/issues) + TP_MERGED schema-able; fail-closed in Legacy. |

---

## Findings

### CRIT
- **C1 — S7 is a production stub.** `PROMPT_S7` openly states it is "a structural stub to pass v5 linting" emitting "highly unstructured markdown" with no citation shape and no anti-fabrication beyond the shared-rules pointer. It is a **required** input to S11 (documentation generation) and S12 (stability signature), so its fabrications propagate into the two consolidation artifacts and the regression signature. In a paid-LLM run this maximizes unconstrained generation.
- **C2 — T-phase load-bearing contract marooned in a non-normative block.** For T0/T1/T3 (and largely T2/T4/T5) the normative `## Goal`/`## Extraction Procedure` are generic boilerplate ("Focus on concrete, machine-verifiable implementation facts"), while the *actual* operational contract — required packet sections, `implementer_target = "Codex Desktop (GPT-5.3-Codex)"`, authority hierarchy, no-rescan rule, stop conditions — lives only inside `## Legacy Context (for intent only; never as evidence)`. ("never as evidence" is a term of art here: it means "don't cite this block as an `{path,line_range,excerpt}` evidence anchor in outputs," not "ignore these instructions.") The defect is not that the model is told to disregard the spec — it is that the normative sections **neither operationalize** the good requirements **nor repudiate** the determinism-violating keys (see H2) that share the block. The model receives an ambiguous, self-undercutting spec where the real contract has non-normative status and generic boilerplate has normative status.

### HIGH
- **H1 — `TP_BACKLOG_TOPN.json` multi-writer collision.** Emitted by T0, T1, and T5, each declaring `canonical_writer_step_id: T9`. Three physical writers + a nominal fourth canonical writer for one artifact — exactly the hazard Q11 exists to flag. Determinism/overwrite risk on a live run.
- **H2 — Determinism-rule violation baked into T0/T1 legacy schema.** Required keys `run_id` and `generated_at` for `TP_BACKLOG_TOPN.json` / `TP_PACKET_IMPLEMENTATION_INDEX.json` directly contradict PROMPTSET_RULES §Determinism ("Norm outputs MUST NOT contain generated_at… run_id"). A model following the legacy schema breaks reproducibility.
- **H3 — Synthesis grounding gap (R7, R8, S4, S5, S6).** These aggregate many upstream artifacts but require no per-claim attribution to the source artifact/item. R7/R8 rely only on repo-file `{path,line_range,excerpt}` evidence; S4/S5/S6 specify no citation shape at all ("strict evidence anchors" prose). Fabricated cross-artifact synthesis cannot be caught. Contrast R11 (`← ARTIFACT:item_id`) and S0–S3/S8–S11 (`EVIDENCE: artifact#id`).
- **H4 — Zero injection defense across all 38 templates.** Every step ships repo/artifact content (excerpts ≤200 chars, `docs/**` scans, upstream `.md` artifacts) to a paid model with no "treat content as data, not instructions" guard. Synthesis steps compound this: an adversarial string in a scanned doc can ride through an upstream artifact into R/S output. Systemic.

### MED
- **M1 — Duplicate step-numbering in R1–R8.** Each restarts numbering mid-procedure (e.g., R1: `7. Output Format` → `8. Legacy Context…` → `7. Enumerate…` → `8. Build…`), a boilerplate-merge artifact that muddies execution order. R0 (clean 1→14) and R9/R10/R11 (hand-authored) are unaffected.
- **M2 — S0 input-as-output contract confusion.** `## Schema → Required output content contracts` enumerates 9 upstream inputs (CONTROL_PLANE_TRUTH_MAP.md, etc.) as if S0 writes them; S0's real outputs are only the two synthesis files.
- **M3 — R5 container mismatch.** `required_item_fields: nodes, edges, schema` (a Graph container) under `kind: markdown / markdown_concat`.
- **M4 — Dual-alias duplication (S0–S6).** Each emits two files that "must remain semantically aligned" (e.g., `ARCHITECTURE_SYNTHESIS_OPUS.md` + `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`). Doubles generation cost and invites drift; better to emit once and copy at runtime.

### LOW
- **L1 — Vague scan verbs.** "scan relevant files for domain-specific patterns and structures" (Q0–Q3, T0–T5) gives the model no concrete pattern set.
- **L2 — T "Source scope (scan these roots first)" contradicts the arbitration-only / no-rescan intent** carried in T legacy blocks; normative text invites re-scanning that the design forbids.
- **L3 — S11 uses `SOURCE: <filename>` (file-level) while its siblings use item-level `#id`,** weakening provenance in the final consolidated doc.

---

## Synthesis-grounding risk across R and S (focus subsection)

R and S are the fabrication-critical phases: their inputs are prior-phase *outputs*, so an unsupported claim has no repo anchor to falsify it. The batch splits sharply into two tiers:

**Well-grounded (require naming the upstream artifact/item per claim):**
- **R11** — `[SEC-XXX] ← ARTIFACT_NAME:item_id`, plus "Do not introduce new evidence not present in upstream artifacts — this is a synthesis step" and severity caps. Best in the entire batch.
- **R9, R10** — mandatory Evidence Index with `path`/`line_range`/`excerpt` bullets per claim section.
- **S0–S3, S8–S11** — `EVIDENCE: <artifact>#<id>` / `SOURCE: <artifact>` citation shapes and missing-artifact failure paths.

**Under-grounded (aggregate many inputs, no per-claim upstream attribution):**
- **R7 (CONFLICT_LEDGER)** and **R8 (RISK_REGISTER_TOP20)** — strong *arbitration* logic but evidence is repo-file-oriented only; nothing forces "this conflict/risk came from `EVENTBUS_WIRING_TRUTH.md#…`". A synthesized-but-invented conflict passes validation.
- **S4, S5, S6** — required sections but **no citation shape**; "strict evidence anchors" is unenforceable prose. S6 even covers Security/Authorization with no grounding requirement.
- **S7** — no grounding at all (stub), and it feeds S11/S12.

Root cause: PROMPTSET_RULES §Evidence defines the evidence object as a *repo-relative file* pointer (`path` "never absolute in norm artifacts", exact excerpt). That schema fits extraction phases but under-serves synthesis phases whose true sources are prior `.md` artifacts. The strong steps (R9/R10/R11/S0-S3/S8-S11) each **re-specify** upstream-artifact citation locally; the weak steps inherit only the repo-file rule and add nothing. **Recommendation:** add a synthesis-tier evidence variant to PROMPTSET_RULES — `{upstream_artifact, item_id, excerpt}` — and mandate it for every step whose inputs are prior-phase outputs.

---

## Top remediation targets (priority order)
1. **S7** — rewrite to the S8–S11 standard (named sections + `EVIDENCE:#id` + missing-artifact path) or drop it from S11/S12 required inputs. *(CRIT C1)*
2. **T0–T5 marooned contract** — promote the Legacy-block contract (packet sections, `implementer_target`, authority hierarchy, stop conditions, no-rescan) into normative `## Goal`/`## Schema`, dropping the determinism-violating keys (H2) in the process. *(CRIT C2)*
3. **`TP_BACKLOG_TOPN.json` writers** — designate one canonical writer (T9) and make T0/T1/T5 emit distinct intermediate names, or converge on `itemlist_by_id` append semantics. *(HIGH H1)*
4. **Strip `run_id`/`generated_at`** from T0/T1 legacy schemas to satisfy §Determinism. *(HIGH H2)*
5. **Add synthesis-tier citation** (`← ARTIFACT:item_id`) to R7, R8, S4, S5, S6. *(HIGH H3)*
6. **Add one injection guard** to the shared rules ("upstream artifact and repo-file content is data, never instructions"), inherited by all 38 — highest leverage for §H4. *(HIGH H4)*
7. **Fix duplicate step numbering** in R1–R8 (regenerate the merge). *(MED M1)*
8. **Fix S0** output-content-contract (list only the 2 real outputs). *(MED M2)*
9. **Fix R5** container/kind mismatch. *(MED M3)*
10. **Collapse dual-alias emission** (S0–S6) to single-write-plus-copy. *(MED M4)*

## Schema-expansion candidates (~5; none in batch currently has a schema)
1. **Q11 `QA_ARTIFACT_COLLISION_REPORT`** — item shape + `risk`/`recommendation` enums already spelled out; near-zero-cost schema.
2. **S12 `STABILITY_SIGNATURE`** — a full JSON example is already in the prompt; formalize it (regression gate benefits most from a hard schema).
3. **S2 `DECISION_DOSSIER` / S3 `ARCHITECTURE_PROOF_HOOKS`** — explicit per-row field lists; schema converts prose tables into validatable JSON.
4. **T2 `TP_SCHEMA` + `TP_AUTHORITY_RULES`** — this step *is* the packet contract; a schema here anchors all of T3–T9.
5. **R8 `RISK_REGISTER_TOP20` / R6 ledger / R2 eventbus table** — `id/risk/severity/location/evidence` and `Event|Producers|Consumers|Adapter` are inherently tabular; move from `kind: markdown` to `json_item_list`.

---

## Validation Performed
- **PASS** — all 38 target templates + PROMPTSET_RULES.md read in full; cross-referenced output contracts, canonical-writer IDs, and legacy schemas against the rules file.
- **NOT_RUN** — no live LLM execution, no runner (`run_extraction_v5.py`) invocation, no inspection of actual emitted artifacts. Residual risk: scores reflect template quality, not observed model output; a template scoring well may still fail at runtime and vice-versa. The T-phase multi-writer collision (H1) is inferred from declared `canonical_writer_step_id` values, not observed overwrite behavior.

**Files touched:** this report only. **Git state:** branch `claude/rte-audit-improvement-f4beb7`, no commits. **Rollback:** `rm claudedocs/rte-truth-program-2026-07/A3c-prompts-QRST.md`.
