# Prompt 3 Pipeline Audit

## 1. Executive summary

The active Repo Truth Extractor stack is a **runtime v5 / contract v4** system, not a clean v5-authored prompt stack. Current repo truth shows:

- runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`
- contract authority: `services/repo-truth-extractor/promptsets/v4/`
- active supporting model surfaces: prescan embedded prompts, `phase_s`, and `FL_INT`

The stack is benchmarkable, but only if the audit preserves three separations:

- runtime authority vs contract authority
- active supporting surfaces vs main runtime phases
- legacy lineage vs currently operative prompt/contract behavior

Highest-value findings:

- `D`, `C`, `Q`, `R`, `S`, and `FL_INT` are the most capability-sensitive surfaces.
- prescan is the cheapest place to experiment, but it has the weakest validator posture.
- `phase_s` is active but comparatively under-specified because it lacks adjacent JSON schemas.
- legacy `v3` prompts matter mostly as migration-debt and same-name drift reference, not as equal-weight active surfaces.

## 2. Pipeline-level verdict

| Verdict | Labels | Evidence |
|---|---|---|
| Current system is operational but split across multiple authority layers | `CURRENT_STATE_AUTHORITY` `STALE_OR_DISPUTED` | v5 runner loads active prompt text from `promptsets/v4`, while runtime metadata still labels many of those prompts as `legacy` |
| Prompt workload decomposition is mostly usable for benchmarking | `MOSTLY_SOUND` | extraction, repair/QA, adjudication, and output shaping are separated enough to evaluate by archetype |
| Main weakness is uneven output-contract rigor | `NEEDS_BETTER_OUTPUT_CONTRACT` | promptset/v4 and FL_INT are contract-rich; prescan and `phase_s` are weaker |
| Route sensitivity is concentrated, not uniform | `BALANCED_LANE_SUFFICIENT` `PREMIUM_LIKELY_NEEDED` | cheap lanes are plausible for prescan/inventory work; strict extraction and adjudication still need stronger lanes |

## 3. Active prompt inventory table

| Scope | Active count | Authority role | Dominant jobs | Output posture | Notes |
|---|---:|---|---|---|---|
| Prescan embedded passes | 4 | `active_supporting_surface` | dedup, discovery, feasibility, optimization | structured JSON with weak validation | prompt text lives in `lib/prescan/grok_passes.py` |
| Runtime promptset/v4 | 110 | `contract_authority` | extraction, merge, QA, synthesis, shaping | mostly structured JSON; some markdown/mixed outputs | active despite v4 path naming |
| `phase_s` | 13 | `active_supporting_surface` | synthesis, drift check, readiness, packaging | mixed practical behavior, no adjacent schemas | runtime-active via registry |
| `FL_INT` | 8 | `active_supporting_surface` | design and feature synthesis, routing, normalization | schema-backed JSON / mixed outputs | separate runner with explicit ladders |
| Contract policy docs | 4 | `contract_authority` | promptset rules and manual adjudication policy | markdown policy text | active because they define contract behavior |

## 4. Legacy prompt relevance table

| Surface | Status | Why it still matters | Weight |
|---|---|---|---|
| `services/repo-truth-extractor/prompts/v3` | `legacy_reference` | direct predecessor tree for same-name drift, migration debt, and historical decomposition choices | brief but real reference |
| `services/repo-truth-extractor/archive/legacy_prompts` | out of active path | useful only if a current defect traces back to older prompt structure | minimal |
| `promptsets/v4` prompt text | current contract authority, not legacy | current runtime still executes against this contract source | full weight |

If a v3/v4 artifact is not currently invoked and does not explain active migration debt or contract behavior, it should stay in the legacy table and receive no further analysis budget.

## 5. Archetype map

| Archetype | Representative surfaces | Workload profile | Capability floor |
|---|---|---|---|
| Routing / classification | prescan `P1-P4`, `A0-A4`, `H0-H3` | classification, bounded JSON, low-to-medium context | balanced structured model |
| Strict field extraction | `D1-D3`, `C1-C8`, `G1-G5`, `X1-X4` | extraction, evidence-bound, omission-sensitive, schema-heavy | premium or strong balanced lane |
| Merge / QA / repair | `Q0-Q11`, `D4`, `C9`, `T9`, `Z9` | repair/adjudication, precision-critical, retry-dependent | strong structured model with repair stability |
| Cross-source adjudication | `R0-R11`, `FL_INT F1/F2/L3/L4` | synthesis/adjudication, evidence-sensitive, medium/long context | premium synthesis lane |
| Output shaping / normalization | `T0-T5`, `Z0-Z2`, `S4-S12` | shaping, normalization, packaging, mixed format | balanced lane, sometimes premium |
| Tool-aware repo reasoning | `E*`, `W*`, `A11-A13`, `C10-C17` | code-aware, repo-aware, omission-sensitive | balanced lane with code comprehension |

## 6. Prompt defects vs model/route/validator findings

| Finding | Primary label | Secondary label | Affected scopes | Assessment |
|---|---|---|---|---|
| Runtime-active promptset/v4 prompts still show `source=legacy` in runtime metadata | `STALE_OR_DISPUTED` | `VALIDATOR_MISALIGNMENT` | active promptset/v4 runtime prompts | metadata drift risks underweighting active contract authority during audits |
| `phase_s` has active registry control but no adjacent JSON schemas | `VALIDATOR_MISALIGNMENT` | `NEEDS_BETTER_OUTPUT_CONTRACT` | `S0-S12` | prompt family is active and important, but formal contract rigor is weaker than FL_INT |
| Prescan only validates parseability and top-level keys | `VALIDATOR_MISALIGNMENT` | `COST_LATENCY_RISK` | prescan `P1-P4` | cheap lanes are feasible, but malformed-yet-plausible outputs can slip through |
| Merge/QA responsibilities are distributed across local phase merges and dedicated `Q` | `MISSING_DECOMPOSITION` | `SHOULD_BE_SPLIT` | `D4`, `C9`, `Q*`, `T9`, `Z9` | benchmark design must distinguish local merge from global repair/doctor work |
| Some bulk/general routes are heavily route-driven without equally explicit step-local rationale | `ROUTE_MISMATCH_RISK` | `MODEL_MISMATCH_RISK` | bulk/general phases, `S`, `FL_INT` | route choice matters, but justification is clearer in `model_map.yaml` than in prompt text |

## 7. Failure-mode map

| Failure mode | Severity | Archetypes | Most likely root cause |
|---|---|---|---|
| malformed JSON / invalid envelope | CRITICAL | strict extraction, merge/QA, FL_INT | route mismatch, weak repair handling, or validator gap |
| missing required fields | CRITICAL | extraction, repair, normalization | model inadequacy, prompt under-specification, or schema weakness |
| unsupported inference / evidence drift | HIGH | docs/code extraction, adjudication | prompt defect or weak evidence-binding |
| citation mismatch | HIGH | `D`, `R`, FL_INT | model mismatch or missing evidence checks |
| partial completion disguised as success | HIGH | prescan, bulk/general extraction | weak validator contracts and cheap-lane drift |
| unstable retries | MODERATE | `Q`, prescan optimize, FL_INT | retry policy weakness or no route escalation |
| context truncation / omission | HIGH | `C`, `D`, `E`, `W`, `R` | context overload or decomposition weakness |
| provider / route variance | MODERATE to HIGH | prescan optimize, strict extraction, adjudication | route sensitivity and uneven structured-output support |

## 8. Output-contract and validator-risk findings

| Scope | Contract strength | Risks |
|---|---|---|
| promptset/v4 runtime phases | strong | best-defined surface; still vulnerable to metadata drift and mixed markdown/json outputs in `R/T/Z` |
| Prescan | weak-to-moderate | top-level-key validation is insufficient for high-confidence automation |
| `phase_s` | moderate | active registry and outputs exist, but schema-backed falsifiability is limited |
| FL_INT | strong | registry + schemas + fail-closed runner make it one of the clearest benchmark surfaces |
| Mixed markdown/json runtime phases | moderate | useful operator output, but weaker machine-verifiable acceptance criteria |

## 9. Route-sensitivity findings

| Scope | Sensitivity | Why |
|---|---|---|
| Prescan `P1-P3` | LOW to MODERATE | cheap structured lanes are plausible; validator weakness is the main risk |
| Prescan `P4` optimize | HIGH | output directly influences routing and cost/quality policy |
| `D` / `C` extraction | HIGH | structured JSON reliability, evidence discipline, and context handling materially affect downstream artifacts |
| `Q` repair / QA | HIGH | route quality determines whether retries repair or merely restate failure |
| `R` / FL_INT | HIGH | contradiction handling and synthesis quality vary meaningfully by route/model |
| `A` / `H` inventory | MODERATE | balanced lanes usually suffice if contract enforcement stays intact |
| `T` / `Z` shaping | MODERATE | route matters, but less than extraction/adjudication |

## 10. OpenClaw suitability findings

| Scope | Suitability | Rationale |
|---|---|---|
| Prescan dedup/discover/feasibility | `SAFE_AS_CHEAP_SUBAGENT` `SAFE_AS_EXTRACTION_WORKER` | bounded classification work with acceptable cheap-lane failure surface |
| Prescan optimize | `SAFE_AS_PLANNER` | planning-style loop fits, but output should still be reviewed |
| Strict extraction (`D`,`C`) | `HIGH_TRUST_ONLY` | deterministic, evidence-bound JSON makes cheap loop execution risky |
| `Q` repair / QA | `SAFE_AS_REPAIR_WORKER` | useful fit for targeted recovery with explicit escalation thresholds |
| `R` / FL_INT synthesis | `SAFE_AS_REVIEWER` `HIGH_TRUST_ONLY` | reviewer/planner role fits better than cheap autonomous execution |
| `T` / `Z` shaping | `SAFE_AS_PLANNER` `SAFE_AS_REVIEWER` | packaging/synthesis work is less dangerous than first-pass extraction |
| Local/open-weight fallback | `LOCAL_FALLBACK_POSSIBLE` only for prescan and some inventory work | not recommended for strict extraction, repair, or adjudication without benchmark proof |

## 11. Capability-floor analysis

| Archetype | Minimum viable capability | Cheap-lane disqualifier | Premium-lane gain |
|---|---|---|---|
| Routing/classification | reliable small structured model | repeated misclassification or unstable JSON | better drift detection and fewer false positives |
| Strict extraction | strong structured model with code/docs comprehension | missing required keys, unsupported inference, citation loss | better recall without contract breakage |
| Merge/QA/repair | strong structured model with retry stability | repeated invalid envelopes after retry | better repair targeting and conflict handling |
| Cross-source adjudication | premium synthesis lane | shallow contradiction handling or generic summaries | materially better prioritization and escalation logic |
| Output shaping | balanced synthesis lane | bloated or under-structured outputs | more concise operator-ready packaging |

## 12. Candidate baseline routing ladders

| Track | Recommended baseline | Scope | Labels |
|---|---|---|---|
| Premium reliability | repo-local strict routes already favored in `model_map.yaml`, plus FL_INT `reasoned_plan` ladders | strict extraction, `Q`, `R`, FL_INT, higher-risk `S` work | `PREMIUM_LIKELY_NEEDED` |
| Balanced production | current balanced lanes in `model_map.yaml` | `A`,`H`,`E`,`W`,`G`,`X`,`T`,`Z`, lower-risk `S` work | `BALANCED_LANE_SUFFICIENT` |
| Low-cost production | prescan cheap passes and selected inventory-style tasks | prescan `P1-P3`, low-risk inventory work | `LOW_COST_LANE_PLAUSIBLE` |
| Experimental/free-entry | local/open-weight only for prescan or low-risk inventory trials | no strict extraction, no repair, no adjudication | `EXPERIMENTAL_LANE_ONLY` `LOCAL_OPEN_EXPERIMENT_ONLY` |
| Batch-oriented throughput | prescan batching plus bulk/general runtime lanes | prescan, broad inventory/extraction passes | `BATCH_LANE_PLAUSIBLE` |
| OpenClaw primary-agent track | planning/reviewer roles for prescan optimize, `R`, `S`, FL_INT | synthesis/review rather than contract-critical first pass | `OPENROUTER_PLAUSIBLE` |
| OpenClaw cheap-subagent track | early prescan classification and bounded helper work | helper-only tasks | `LOW_COST_LANE_PLAUSIBLE` |

## 13. Escalation design recommendations

| Trigger | Recommendation | Why |
|---|---|---|
| invalid envelope / schema failure | `ESCALATE_MODEL` or `RETRY_DIFFERENT_ROUTE` | same-route retries are low value on structural failure |
| repeated repair failure in `Q` | `ESCALATE_TO_REVIEWER_MODEL` | prevents silent looping on bad structure |
| citation mismatch / unsupported inference | `FIX_PROMPT_NOT_MODEL` or `FIX_VALIDATOR_NOT_MODEL` | usually evidence-binding or contract weakness, not only model quality |
| context overflow / omitted partitions | `SPLIT_STEP_NOT_RETRY` | decomposition failure should not be normalized as retry noise |
| unstable prescan optimize recommendations | `ESCALATE_TO_HUMAN` | this pass influences downstream routing policy |
| provider degradation / route instability | `RETRY_DIFFERENT_ROUTE` | route diversity already exists; use it intentionally |

## 14. Fixed benchmark input-set proposal

| Archetype | Minimum cases | Success criteria |
|---|---|---|
| Prescan routing/classification | happy path, duplicate trap, stale-doc drift, ghost-file recovery, optimization-routing case | valid JSON, correct top-level keys, plausible skip/routing recommendations |
| Strict docs/code extraction | happy path, omission trap, conflicting evidence, schema rigidity stress, long-context case | required fields present, evidence anchored, no fabricated claims |
| Merge/QA/repair | malformed JSON, duplicate-ID collision, drift diff, repeated retry case | valid repaired contract output or correct escalation |
| Cross-source adjudication | conflicting evidence, migration-debt conflict, current-vs-historical ambiguity | explicit contradiction handling and preserved uncertainty |
| Output shaping | packaging case, mixed markdown/json case, freeze/proof-pack case | operator-usable structure without contract loss |

## 15. Benchmark-only unknowns

- `prompt1_handoff_pack_normalized.md` and `prompt2_final_audit.md` are present in `audit_prep/`, but this rerun did not independently re-audit them. If they diverge from repo-local runtime truth, current runtime/contract files should win.
- `phase_s` still lacks adjacent JSON schemas, so benchmark evaluation there must emphasize usefulness and boundedness, not only formal conformance.
- prescan cheap-pass defaults are visible in code, but quality under those defaults remains unproven until fixed-case benchmarks are run.
- FL_INT is clearly schema-backed, but its exact operational priority relative to the main runtime remains a supporting-surface inference rather than a main-PHASES fact.

## 16. Recommendations for Prompt 3.5 and Prompt 4

- Keep the runtime-v5 / contract-v4 split explicit in all downstream prompts and reports.
- Benchmark by archetype and step class, not by “best overall model.”
- Treat prescan, `phase_s`, and FL_INT as separate routing and validator-strength problems.
- Add an explicit check for active-but-not-schema-backed surfaces, especially `phase_s`.
- Keep legacy prompt analysis bounded to invocation truth, same-name drift, migration debt, and contract-authority relevance.
