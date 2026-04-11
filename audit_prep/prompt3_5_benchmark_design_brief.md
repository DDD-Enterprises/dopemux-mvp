# Prompt 3.5 Benchmark System Design Brief

## 1. Executive summary

This brief recommends a **gate-first, archetype-scoped benchmark system** for the Repo Truth Extractor, built on the workload decomposition already established by Prompt 3.

The key design choice is to benchmark **case-attempts at the step/archetype level**, not whole-repo runs and not “best model overall” leaderboards. That is the smallest unit that preserves contract validity, workload meaning, route/surface separation, and operator explainability.

Repo-truth constraints carried forward:

- runtime authority is `v5`
- prompt/contract authority may still live under `promptsets/v4`
- legacy `v4`/`v3` materials are reference-only unless still invoked or still causing migration debt
- Prompt 3 is the authoritative workload decomposition layer
- Prompt 1 / Prompt 2 unknowns remain benchmark-only unknowns until measured

## 2. Recommended benchmark unit of comparison

| Decision | Status | Confidence | Rationale | Evidence basis |
|---|---|---|---|---|
| Primary unit of comparison = `benchmark_case_attempt` | `RECOMMENDED` | `HIGH_CONFIDENCE` | A single model/route/profile run against one fixed case, one archetype, one contract surface, and one prompt/contract version preserves falsifiability | Prompt 3 archetypes and Prompt 1 unknowns are step-sensitive, not repo-run-global |
| Required rollup hierarchy = case attempt -> case-set -> archetype -> profile -> portfolio view | `RECOMMENDED` | `HIGH_CONFIDENCE` | Prevents a single scalar from hiding contract failures or surface mismatches | Prompt 2 explicitly warns against flattening surfaces and routing claims |
| Whole-repo run as primary benchmark unit | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | Too many confounders: decomposition quality, context size, retry policy, and mixed archetypes collapse together | Prompt 3 shows route sensitivity is concentrated by phase family |

### Required fields for each `benchmark_case_attempt`

| Field group | Required fields | Status | Confidence |
|---|---|---|---|
| Identity | `case_id`, `archetype_id`, `surface_class`, `phase_or_step_family`, `profile_id`, `model_id`, `route_id`, `provider_surface` | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Contract | `runtime_version`, `contract_version`, `schema_id`, `strict_schema_expected`, `validator_id` | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Execution | `attempt_number`, `retry_policy`, `temperature_or_equivalent`, `max_tokens_or_budget`, `tool_mode`, `batch_mode` | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Outcome | `contract_pass`, `validator_pass`, `error_type`, `latency_ms`, `token_counts`, `cost_estimate`, `output_artifact_ref` | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Evidence | `golden_eval_ref`, `control_delta_ref`, `benchmark_run_id`, `timestamp_utc` | `RECOMMENDED` | `HIGH_CONFIDENCE` |

## 3. Recommended archetype framework

| Archetype | Scope | Status | Confidence | Notes |
|---|---|---|---|---|
| `routing_classification` | prescan `P1-P4`, `A*`, `H*` classification-heavy paths | `RECOMMENDED` | `HIGH_CONFIDENCE` | cheapest admission and drift-detection family |
| `strict_evidence_extraction` | `D*`, `C*`, `G*`, `X*` and other schema-heavy evidence extraction | `RECOMMENDED` | `HIGH_CONFIDENCE` | highest contract sensitivity |
| `repair_and_merge_qa` | `Q*`, local merge/QA steps like `D4`, `C9`, `T9`, `Z9` | `RECOMMENDED` | `HIGH_CONFIDENCE` | must stay separate from first-pass extraction |
| `cross_source_adjudication` | `R*`, FL_INT synthesis/adjudication steps | `RECOMMENDED` | `HIGH_CONFIDENCE` | premium lane candidate family |
| `output_shaping_packaging` | `T*`, `Z*`, later `S*` packaging and operator-facing shaping | `RECOMMENDED` | `MEDIUM_CONFIDENCE` | `phase_s` belongs here provisionally because schema rigor is weaker |
| `tool_aware_repo_reasoning` | `E*`, `W*`, repo/code-aware helper work | `RECOMMENDED_WITH_CAVEAT` | `MEDIUM_CONFIDENCE` | keep separate only while tool/code sensitivity remains distinct in real runs |

### Archetype decisions

| Decision | Status | Confidence | Rationale |
|---|---|---|---|
| Keep the archetype count at six | `RECOMMENDED` | `HIGH_CONFIDENCE` | Small enough to operate; rich enough to preserve workload differences already found in Prompt 3 |
| Split `repair_and_merge_qa` from `strict_evidence_extraction` | `RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 3 identified repair behavior and retry stability as separate failure surfaces |
| Give `phase_s` its own top-level archetype now | `NOT_RECOMMENDED` | `MEDIUM_CONFIDENCE` | Active and important, but not yet contract-rigorous enough to justify a separate top-level family |

## 4. Recommended scoring framework

| Layer | Decision | Status | Confidence | Rule |
|---|---|---|---|---|
| Gate 1 | contract validity gate | `RECOMMENDED` | `HIGH_CONFIDENCE` | If contract/validator fails, the case cannot be considered successful regardless of prose quality |
| Gate 2 | archetype success score | `RECOMMENDED` | `HIGH_CONFIDENCE` | Score task success only after structural validity is established |
| Gate 3 | operational modifier | `RECOMMENDED` | `HIGH_CONFIDENCE` | Cost, latency, and retry burden affect profile fit, not correctness |
| Global leaderboard score | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | Hides surface differences and encourages unsafe score-first optimization |

### Recommended score dimensions

| Dimension | Applies to | Status | Confidence | Notes |
|---|---|---|---|---|
| `contract_score` | all archetypes | `RECOMMENDED` | `HIGH_CONFIDENCE` | based on first-pass valid JSON %, validator pass %, malformed output rate |
| `evidence_score` | extraction, adjudication, repo reasoning | `RECOMMENDED` | `HIGH_CONFIDENCE` | anchored evidence, citation fidelity, unsupported-inference avoidance |
| `completeness_score` | extraction, shaping, synthesis | `RECOMMENDED` | `HIGH_CONFIDENCE` | omission sensitivity matters more than eloquence |
| `stability_score` | repair, prescan optimize, batch runs | `RECOMMENDED` | `HIGH_CONFIDENCE` | retries per success, variance, provider drift |
| `economics_score` | profile rollups only | `RECOMMENDED_WITH_CAVEAT` | `MEDIUM_CONFIDENCE` | must never override contract failure |
| `governance_score` | onboarding and promotion decisions | `RECOMMENDED` | `MEDIUM_CONFIDENCE` | residency/logging/route posture is a gate, not just a note |

### Scoring rules

| Rule | Status | Confidence |
|---|---|---|
| No candidate can rank above a control anchor within an archetype if its contract gate fails more often | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Use control-delta comparisons against fixed anchors, not free-floating cross-market averages | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Allow archetype-specific weights, but keep the weight set small and versioned | `RECOMMENDED_WITH_CAVEAT` | `MEDIUM_CONFIDENCE` |

## 5. Recommended routing philosophy

| Decision | Status | Confidence | Rationale |
|---|---|---|---|
| Routing should be archetype-first, not model-first | `RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 3 found route sensitivity concentrated by workload family |
| Surface class must stay explicit: direct-provider, routed, chat/subscription, local/open-weight | `RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 2 made this a non-negotiable separation |
| Preserve fixed control anchors in every comparative run | `RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 1 / Prompt 2 both require anchored controls |
| Auto-rewrite routing policy from metadata alone | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | docs and catalogs do not resolve benchmark-only unknowns |
| Treat local/open-weight and hosted routed surfaces as equivalent families | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 1 and Prompt 2 both keep those surfaces distinct |

### Routing philosophy statement

| Principle | Status | Confidence |
|---|---|---|
| Use benchmark evidence to assign a candidate to a profile within an archetype, not to crown a universal winner | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Use cheap lanes for prescan and bounded helper work only after contract and drift risk are measured | `RECOMMENDED_WITH_CAVEAT` | `HIGH_CONFIDENCE` |
| Keep premium lanes focused on strict extraction, repair, and cross-source adjudication | `RECOMMENDED` | `HIGH_CONFIDENCE` |

## 6. Recommended profile taxonomy

### Core profiles

| Profile | Purpose | Status | Confidence | Notes |
|---|---|---|---|---|
| `control_anchor` | stable comparison baseline only | `RECOMMENDED` | `HIGH_CONFIDENCE` | includes fixed OpenAI controls from Prompt 1 |
| `premium_reliability` | contract-critical and adjudication-heavy work | `RECOMMENDED` | `HIGH_CONFIDENCE` | default target for strict extraction, repair, and high-risk synthesis |
| `balanced_production` | default production work with bounded cost | `RECOMMENDED` | `HIGH_CONFIDENCE` | most `A/H/E/W/G/X/T/Z`-style work should land here if evidence supports it |
| `low_cost_bounded` | cheap work with explicit scope limits | `RECOMMENDED_WITH_CAVEAT` | `HIGH_CONFIDENCE` | prescan and inventory-style helpers only until benchmarked further |
| `experimental_lab` | out-of-registry, free-tier, local/open-weight, and churn-risk trials | `RECOMMENDED` | `HIGH_CONFIDENCE` | never auto-promotes into production |

### Execution overlays

| Overlay | Status | Confidence | Notes |
|---|---|---|---|
| `batch_capable` | `OPTIONAL` | `MEDIUM_CONFIDENCE` | only after cost/latency and artifact timing are measured |
| `agent_reviewer` | `OPTIONAL` | `MEDIUM_CONFIDENCE` | suitable for prescan optimize, review, and synthesis assistance |
| `local_open_overlay` | `OPTIONAL` | `LOW_CONFIDENCE` | allowed only inside `experimental_lab` until parity evidence exists |

### Taxonomy rules

| Rule | Status | Confidence |
|---|---|---|
| Keep the core profile count at five | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Make overlays orthogonal to core profiles | `RECOMMENDED` | `MEDIUM_CONFIDENCE` |
| Add a distinct “free” production profile now | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` |

## 7. Recommended benchmark rigor and cadence

| Benchmark stage | Scope | Status | Confidence | Governance |
|---|---|---|---|---|
| Admission smoke | one or two fixed cases per relevant archetype plus contract sanity checks | `RECOMMENDED` | `HIGH_CONFIDENCE` | `AUTO` |
| Comparative benchmark | full case-set against control anchors inside the target archetype/profile | `RECOMMENDED` | `HIGH_CONFIDENCE` | `SEMI_AUTO` |
| Regression benchmark | fixed control anchors plus current production candidates | `RECOMMENDED` | `HIGH_CONFIDENCE` | `AUTO` |
| Promotion benchmark | repeated comparative run plus governance review | `RECOMMENDED` | `HIGH_CONFIDENCE` | `HUMAN_REVIEW_REQUIRED` |
| Full-market rerun for every model change | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | `NEVER_AUTO` |

### Recommended cadence

| Cadence | Status | Confidence | Notes |
|---|---|---|---|
| on candidate intake: admission smoke | `RECOMMENDED` | `HIGH_CONFIDENCE` | cheap falsification first |
| on prompt/contract/schema change: targeted regression for affected archetypes | `RECOMMENDED` | `HIGH_CONFIDENCE` | protects runtime-v5 / contract-v4 drift surfaces |
| scheduled weekly: comparative runs for active production profiles | `RECOMMENDED_WITH_CAVEAT` | `MEDIUM_CONFIDENCE` | exact weekly budget remains operator-dependent |
| scheduled monthly: experimental-lab intake sweep | `RECOMMENDED_WITH_CAVEAT` | `MEDIUM_CONFIDENCE` | only if operator budget supports it |

## 8. Recommended governance boundaries

| Decision area | Governance | Status | Confidence | Rule |
|---|---|---|---|---|
| run admission smoke automatically | `AUTO` | `RECOMMENDED` | `HIGH_CONFIDENCE` | safe because it does not change production routing |
| quarantine a candidate that repeatedly fails the contract gate | `AUTO` | `RECOMMENDED` | `HIGH_CONFIDENCE` | fail-closed behavior is preferable |
| change score weights or archetype definitions | `HUMAN_REVIEW_REQUIRED` | `RECOMMENDED` | `HIGH_CONFIDENCE` | these are policy changes, not routine operations |
| promote a candidate into `balanced_production` or `premium_reliability` | `HUMAN_REVIEW_REQUIRED` | `RECOMMENDED` | `HIGH_CONFIDENCE` | operator trust and governance matter more than automation speed |
| allow local/open-weight routes into strict extraction or adjudication production lanes | `NEVER_AUTO` | `RECOMMENDED` | `HIGH_CONFIDENCE` | no evidence currently supports that move |
| auto-select a new “best model overall” from aggregate scores | `NEVER_AUTO` | `RECOMMENDED` | `HIGH_CONFIDENCE` | contradicts the archetype-first design |

## 9. Metadata vs empirical evidence boundary

| Claim or decision | Metadata alone allowed? | Empirical evidence required? | Status | Confidence |
|---|---|---|---|---|
| classify provider surface and declared capabilities | yes | no | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| decide whether a candidate is eligible for admission smoke | yes | no | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| assign a production profile | no | yes | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| claim cost-per-success superiority | no | yes | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| claim local/open-weight parity with hosted routed surfaces | no | yes | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| use docs or registry claims to bypass contract testing | no | yes | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` |

### Boundary statement

| Decision | Status | Confidence | Rationale |
|---|---|---|---|
| Metadata is an intake and governance filter, not a substitute for benchmark evidence | `RECOMMENDED` | `HIGH_CONFIDENCE` | directly aligned with Prompt 1 unknowns and Prompt 2 corrections |
| Benchmark-only unknowns should remain explicitly unresolved until measured | `RECOMMENDED` | `HIGH_CONFIDENCE` | prevents design drift from turning hypotheses into policy |

## 10. Recommended model-onboarding policy

| Stage | Decision | Status | Confidence | Governance |
|---|---|---|---|---|
| Stage 0 | metadata intake and surface classification | `RECOMMENDED` | `HIGH_CONFIDENCE` | `AUTO` |
| Stage 1 | admission smoke in `experimental_lab` only | `RECOMMENDED` | `HIGH_CONFIDENCE` | `AUTO` |
| Stage 2 | archetype-limited comparative benchmark versus control anchors | `RECOMMENDED` | `HIGH_CONFIDENCE` | `SEMI_AUTO` |
| Stage 3 | candidate profile recommendation with explicit caveats | `RECOMMENDED` | `HIGH_CONFIDENCE` | `SEMI_AUTO` |
| Stage 4 | operator promotion into production profile | `RECOMMENDED` | `HIGH_CONFIDENCE` | `HUMAN_REVIEW_REQUIRED` |

### Onboarding rules

| Rule | Status | Confidence |
|---|---|---|
| Do not fully benchmark every newly discovered model | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Require fixed control-anchor comparison before any production recommendation | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Keep free-tier and local/open-weight candidates inside `experimental_lab` until they pass archetype-specific evidence thresholds | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Treat stale/disputed lifecycle candidates as watchlist items, not normal candidates | `RECOMMENDED` | `HIGH_CONFIDENCE` |

## 11. Minimum explainability requirements

| Requirement | Status | Confidence | Notes |
|---|---|---|---|
| Every profile recommendation must name the archetype, surface, control anchor, and benchmark run it depends on | `RECOMMENDED` | `HIGH_CONFIDENCE` | no anonymous score-driven routing decisions |
| Every rejection or quarantine must identify the failing gate or metric | `RECOMMENDED` | `HIGH_CONFIDENCE` | especially contract failures and governance exclusions |
| Every operator-facing rollup must link back to case-level evidence | `RECOMMENDED` | `HIGH_CONFIDENCE` | preserves auditability |
| Every routing/profile output must state whether it is based on metadata, benchmark evidence, or both | `RECOMMENDED` | `HIGH_CONFIDENCE` | prevents evidence drift |
| Natural-language summaries without machine-readable evidence links | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | unacceptable for this system |

### Minimum evidence bundle per recommendation

| Required evidence | Status | Confidence |
|---|---|---|
| benchmark run id and timestamp | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| contract version and validator version | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| case-set and archetype ids | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| control-anchor delta | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| failure summary and escalation notes | `RECOMMENDED` | `HIGH_CONFIDENCE` |

## 12. Resolved decisions

| Decision | Status | Confidence |
|---|---|---|
| Benchmark at the case-attempt level, not whole-run level | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Keep six workload archetypes | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Use gate-first scoring instead of a single universal leaderboard | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Keep provider surface isolation mandatory | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Use five core profiles plus optional overlays | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Require operator review for production promotion and scoring-policy changes | `RECOMMENDED` | `HIGH_CONFIDENCE` |
| Keep metadata as intake/governance support, not proof of suitability | `RECOMMENDED` | `HIGH_CONFIDENCE` |

## 13. Unresolved decisions requiring operator choice

| Decision | Status | Confidence | Why unresolved |
|---|---|---|---|
| exact promotion thresholds per archetype | `REQUIRES_OPERATOR_CHOICE` | `CANNOT_BE_RESOLVED_WITHOUT_LIVE_DATA` | Prompt 1 and Prompt 2 explicitly classify these as benchmark-only unknowns |
| exact weekly/monthly benchmark budget and cadence | `REQUIRES_OPERATOR_CHOICE` | `MEDIUM_CONFIDENCE` | depends on cost tolerance and operational load |
| whether `phase_s` should be benchmark-gated as a separate policy lane before contract strengthening | `REQUIRES_OPERATOR_CHOICE` | `MEDIUM_CONFIDENCE` | active surface, but schema posture is weaker than FL_INT |
| whether any local/open-weight route may graduate beyond `experimental_lab` in the near term | `REQUIRES_OPERATOR_CHOICE` | `LOW_CONFIDENCE` | no current empirical evidence supports production equivalence |
| whether OpenClaw reviewer overlay can write operator-visible outputs directly or only review/propose | `REQUIRES_OPERATOR_CHOICE` | `LOW_CONFIDENCE` | Prompt 3 found reviewer fit, but governance policy is not yet explicit |

## 14. Design principles for Prompt 4

| Principle | Status | Confidence | Implementation consequence |
|---|---|---|---|
| Build storage around case-attempt records and rollups | `RECOMMENDED` | `HIGH_CONFIDENCE` | schema should preserve case-level evidence and aggregate views separately |
| Preserve runtime-v5 / contract-v4 separation in metadata | `RECOMMENDED` | `HIGH_CONFIDENCE` | benchmark records need both runtime and contract version fields |
| Keep archetype logic explicit and versioned | `RECOMMENDED` | `HIGH_CONFIDENCE` | routing/profile synthesis must not infer families implicitly |
| Separate governance gates from performance scoring | `RECOMMENDED` | `HIGH_CONFIDENCE` | onboarding and promotion workflows need explicit gate stages |
| Keep control anchors first-class citizens in storage and reporting | `RECOMMENDED` | `HIGH_CONFIDENCE` | deltas matter more than vanity leaderboards |

## 15. Anti-patterns to avoid

| Anti-pattern | Status | Confidence | Why |
|---|---|---|---|
| one global “best model” ranking | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | destroys workload and surface distinctions |
| mixing direct-provider, routed, chat, and local/open-weight results in one benchmark family | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | contradicts Prompt 2 surface-isolation requirement |
| auto-promoting experimental candidates after a single promising run | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | unsafe and non-auditable |
| using metadata claims as substitutes for measured contract performance | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | directly conflicts with Prompt 1 benchmark-only unknowns |
| treating legacy prompt trees as equal-weight active benchmark surfaces | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | Prompt 3 bounded legacy analysis for good reason |
| hiding contract failures behind blended scalar scores | `NOT_RECOMMENDED` | `HIGH_CONFIDENCE` | encourages unsafe routing decisions |
