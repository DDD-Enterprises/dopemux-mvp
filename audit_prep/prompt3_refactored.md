You are auditing the **Repo Truth Extractor (RTE)** prompt stack inside the **Dopemux** repository.

This is **not** a generic prompt-engineering review.
This is a **pipeline/workload decomposition audit** focused on the **runtime v5 extractor** and the **prescanner** that feeds or supports it, while preserving the possibility that active prompt/contract authority may still live under **`promptsets/v4`**.

Your job is to analyze the prompt stack as an operating system for extraction work:
- what each step actually does
- what it requires from a model and route
- where it is brittle
- what should be benchmarked
- what routing ladders and escalation logic make sense
- what should be ignored as legacy noise

---

# Scope rules

## Primary scope

Treat the following as primary audit scope:

- runtime v5 extractor prompts and orchestration
- prescanner prompts or model-using surfaces used by or feeding runtime v5
- prompt wrappers or orchestration directly invoking runtime v5 or prescan
- validator/schema contracts used by runtime v5 or prescan
- phase/step structure relevant to runtime v5 or prescan execution

## Secondary scope

Treat v4 and v3 materials as **reference-only** unless:

- they are still invoked by current code
- they explain migration debt still affecting runtime v5 or prescan
- they explain duplicated or conflicting prompt behavior still present in runtime v5 or prescan
- they are the active prompt or contract authority for runtime v5 execution

Do **not** give equal analytical weight to legacy prompts unless current invocation paths justify it.

## Out of scope by default

Do not spend time on:

- unrelated Dopemux prompts outside the extractor/prescan path
- generic model-market discussion already handled by Prompt 1 and Prompt 2
- redoing the canonical model inventory
- redoing the three-report cross-audit

---

# Source files and their roles

Use the files in `audit_prep/` as follows:

- `prompt_inventory_manifest.md` = authoritative discovered-prompt inventory
- `pipeline_phase_map.md` = phase/step ordering, dependencies, retry/escalation structure
- `validators_and_schemas.md` = validator and schema contracts
- `prompt_conventions_glossary.md` = terminology and naming conventions
- `prompts_active_prescan_bundle.md` = active prescan prompt content
- `prompts_active_extraction_bundle_1.md` and `prompts_active_extraction_bundle_2.md` = active extraction prompt content
- `prompts_active_repair_retry_bundle.md` = active repair/retry prompt content
- `prompts_active_adjudication_bundle.md` = active adjudication/judging prompt content
- `prompts_active_output_shaping_bundle.md` = active output-shaping/normalization prompt content
- `prompts_runtime_v5_contract_v4_bundle.md` = material included specifically to preserve the runtime-v5 / contract-v4 authority split
- `prompts_legacy_v3_v4_reference_bundle.md` = legacy reference material only unless current code path requires it
- `prompt1_handoff_pack_normalized.md` = current-state model/route authority artifact
- `prompt2_final_audit.md` = final corrected model/research audit
- `report_a_inventory_audit.md`, `report_b_portfolio_brain.md`, `report_c_openrouter_extension.md` = historical research hypotheses only

Important:

- bundled prompt files are source-of-truth prompt text
- the manifest and phase map are source-of-truth organizational scaffolding
- the handoff pack and Prompt 2 final audit are source-of-truth for current model/route normalization and known planning constraints

Do not infer missing validator/schema details if they are not present.
If something is missing, mark it explicitly.

---

# Primary goals

Analyze the runtime v5 + prescanner prompt pipeline so we can:

1. understand what each active step actually demands from a model and route
2. identify prompt brittleness, ambiguity, and failure modes
3. separate prompt defects from model mismatch, route mismatch, validator weakness, and missing decomposition
4. group the active prompts into durable benchmark archetypes
5. determine which steps likely need premium lanes vs balanced vs low-cost vs experimental lanes
6. identify which steps are plausible for OpenClaw-style agent execution and which are not
7. propose baseline routing ladders and escalation triggers
8. define the minimum fixed benchmark input sets needed for real evaluation

---

# Core framing rules

You must evaluate prompts as **pipeline work units**, not as isolated writing samples.

Do not optimize for elegance or cleverness.
Optimize for:

- operational clarity
- auditability
- benchmarkability
- routing usefulness
- validator-aligned execution

Always ask:

- what exact job does this step perform?
- what downstream failure does it risk?
- what is the minimum model/route capability needed?
- what should trigger escalation?
- what belongs in the benchmark harness?

---

# Required analysis dimensions for every active prompt or step

For each in-scope prompt or step, analyze the following.

## A. Step identity

Capture:

- prompt_id
- canonical_scope
- version_line
- authority_role
- phase
- step
- short_name
- source_path
- invoked_by
- invokes
- status
- whether it is first-pass, repair, adjudication, normalization, or active-supporting-surface only

## B. Actual job to be done

Describe the real operational job, such as:

- routing/classification
- field extraction
- citation/evidence extraction
- schema-bound transformation
- JSON repair
- contradiction detection
- cross-source adjudication
- synthesis/consolidation
- output shaping/normalization
- planner/wrapper/orchestration support

Do not use vague labels like “reasoning” unless tied to a real step function.

## C. Workload profile

Classify each step across these axes:

- extraction vs synthesis vs classification vs repair vs adjudication
- strict schema-bound vs semi-structured vs freeform
- evidence-bound vs inference-tolerant
- precision-critical vs recall-critical
- omission-sensitive vs fabrication-sensitive
- short-context vs medium-context vs long-context
- deterministic formatting required or not
- tool-use-dependent vs pure completion
- code-aware vs not
- latency-sensitive vs throughput-oriented
- one-shot-friendly vs retry-dependent

## D. Failure severity

Classify consequence of failure:

- LOW
- MODERATE
- HIGH
- CRITICAL

Also identify which failures matter:

- malformed JSON
- missing required fields
- unsupported inference
- citation mismatch
- verbose drift
- partial completion
- unstable retries
- context truncation
- route/provider variance
- tool-call failure

## E. Prompt-level brittleness

Audit for:

- conflicting instructions
- buried invariants
- multiple jobs crammed into one step
- unclear output contract
- ambiguous unknown/not-found behavior
- insufficient evidence-binding
- misleading examples
- over-constrained phrasing
- under-specified acceptance criteria
- provider-specific assumptions hidden in prompt wording
- expensive but low-value prompt sections

For each issue, label as one of:

- `PROMPT_DEFECT`
- `MODEL_MISMATCH_RISK`
- `ROUTE_MISMATCH_RISK`
- `VALIDATOR_MISALIGNMENT`
- `COST_LATENCY_RISK`
- `MISSING_DECOMPOSITION`

## F. Output-contract rigor

For each prompt, determine:

- expected output form
- whether schema/contract is explicit enough
- whether validator alignment is clear
- whether malformed-but-plausible output could slip through
- whether the step likely needs:
  - strict schema mode
  - relaxed schema mode
  - post-parse normalization
  - repair loop
  - adjudication loop

## G. Capability needs

Determine what this step actually needs:

- strong instruction following
- structured JSON reliability
- long-context handling
- citation discipline
- code comprehension
- tool calling
- retry stability
- speed
- low cost
- low latency
- strong “unknown” discipline
- synthesis depth
- comparison/adjudication quality

Do not over-assign premium/frontier need unless justified.

## H. Route sensitivity

Determine whether route-level differences materially affect:

- output quality
- schema reliability
- tool support
- context behavior
- rate limits
- latency
- batch viability
- uptime/fallback behavior
- governance/data posture

Classify:

- LOW
- MODERATE
- HIGH
- CRITICAL

## I. OpenClaw suitability

Determine whether each step is suitable for OpenClaw-style execution.

Assess:

- whether it benefits from agent loops
- whether tool use is central
- whether loop latency matters
- whether deterministic formatting makes agent execution dangerous
- whether it is safe for a cheap subagent
- whether it belongs only on a high-trust model
- whether a local/open-weight fallback is plausible

Classify role fit as one or more of:

- `NOT_SUITABLE_FOR_AGENT_LOOP`
- `SAFE_AS_CHEAP_SUBAGENT`
- `SAFE_AS_EXTRACTION_WORKER`
- `SAFE_AS_REPAIR_WORKER`
- `SAFE_AS_REVIEWER`
- `SAFE_AS_PLANNER`
- `HIGH_TRUST_ONLY`
- `LOCAL_FALLBACK_POSSIBLE`
- `LOCAL_FALLBACK_NOT_RECOMMENDED`

---

# Required pipeline-level tasks

## 1. Build the active prompt inventory

Using the manifest, produce a filtered inventory of **active runtime v5 + prescan prompts and model-using surfaces**, with legacy prompts only included where they still affect current behavior, migration debt, or contract authority.

## 2. Group prompts into benchmark archetypes

Group active prompts into a **small durable set** of archetypes such as:

- routing/classification
- strict field extraction
- citation/evidence extraction
- schema-bound transformation
- JSON repair/salvage
- cross-source adjudication
- synthesis/consolidation
- output normalization
- tool-aware code/repo reasoning

Do not create taxonomy sludge.

## 3. Determine capability floors

For each archetype, determine:

- minimum viable capability level
- what failures make cheap lanes unacceptable
- what premium lanes actually buy
- whether the archetype is plausible for:
  - balanced production
  - low-cost production
  - experimental/free-entry
  - batch mode
  - OpenClaw subagent execution

## 4. Separate prompt defects from system defects

For each major weakness, determine whether root cause is:

- bad prompt design
- validator weakness
- poor schema contract
- model inadequacy
- route inadequacy
- context overload
- retry logic weakness
- missing decomposition

## 5. Define escalation triggers

For each archetype or critical step, define escalation triggers such as:

- schema failure
- missing required fields
- citation mismatch
- suspicious omission
- repeated repair failure
- context overflow risk
- tool-call failure
- latency threshold breach
- provider degradation

For each trigger, recommend:

- `RETRY_SAME_MODEL`
- `RETRY_DIFFERENT_ROUTE`
- `ESCALATE_MODEL`
- `ESCALATE_TO_REVIEWER_MODEL`
- `ESCALATE_TO_HUMAN`
- `FIX_PROMPT_NOT_MODEL`
- `FIX_VALIDATOR_NOT_MODEL`
- `SPLIT_STEP_NOT_RETRY`

## 6. Recommend baseline routing ladders

Recommend initial baseline ladders for:

- premium reliability
- balanced production
- low-cost production
- experimental/free-entry
- batch-oriented throughput
- OpenClaw primary-agent track
- OpenClaw cheap-subagent track
- local/open-weight experiment track

Express these at the level of archetype or step class, not “best model overall.”

Use `prompt1_handoff_pack_normalized.md` and `prompt2_final_audit.md` as the current model/route authority when discussing lanes.

## 7. Define fixed benchmark input sets

For each archetype, define the minimum benchmark case set needed to evaluate it fairly:

- happy path
- malformed/noisy input
- omission trap
- conflicting evidence
- schema rigidity stress
- retry/repair case
- long-context case if relevant
- tool-use case if relevant

Define success criteria for each case type.

## 8. Identify benchmark-only unknowns that remain open

Carry forward all unresolved benchmark-only unknowns from the handoff pack and Prompt 2 audit, and add any new prompt-stack-specific unknowns discovered in this audit.

---

# Required outputs

Return these sections in order:

## 1. Executive summary

## 2. Pipeline-level verdict

## 3. Active prompt inventory table

## 4. Legacy prompt relevance table

Only include v4/v3 prompts that materially affect current behavior, migration debt, or contract authority.

## 5. Archetype map

## 6. Prompt defects vs model/route/validator findings

## 7. Failure-mode map

## 8. Output-contract and validator-risk findings

## 9. Route-sensitivity findings

## 10. OpenClaw suitability findings

## 11. Capability-floor analysis

## 12. Candidate baseline routing ladders

## 13. Escalation design recommendations

## 14. Fixed benchmark input-set proposal

## 15. Benchmark-only unknowns

## 16. Recommendations for Prompt 3.5 and Prompt 4

---

# Required labels

Use these labels where appropriate.

## Prompt quality labels

- `SOUND`
- `MOSTLY_SOUND`
- `OVER_SPECIFIED`
- `UNDER_SPECIFIED`
- `INTERNALLY_CONFLICTED`
- `TOO_PROVIDER_SPECIFIC`
- `TOO_EXPENSIVE_FOR_JOB`
- `SHOULD_BE_SPLIT`
- `SHOULD_BE_MERGED`
- `NEEDS_BETTER_OUTPUT_CONTRACT`
- `NEEDS_BETTER_UNKNOWN_DISCIPLINE`

## Workload and routing labels

- `PREMIUM_LIKELY_NEEDED`
- `BALANCED_LANE_SUFFICIENT`
- `LOW_COST_LANE_PLAUSIBLE`
- `EXPERIMENTAL_LANE_ONLY`
- `BATCH_LANE_PLAUSIBLE`
- `DIRECT_PROVIDER_PREFERRED`
- `ROUTE_AGNOSTIC`
- `OPENROUTER_PLAUSIBLE`
- `LOCAL_OPEN_EXPERIMENT_ONLY`
- `LOCAL_OPEN_NOT_RECOMMENDED`

## Governance and certainty labels

- `CURRENT_STATE_AUTHORITY`
- `OUT_OF_REGISTRY_CANDIDATE`
- `BENCHMARK_ONLY_UNKNOWN`
- `STALE_OR_DISPUTED`
- `NEEDS_REGISTRY_REFRESH`

---

# Rigor rules

- Do not redo Prompt 1 or Prompt 2.
- Do not rebuild the model registry.
- Do not invent missing validator/schema details.
- Do not give equal weight to legacy prompts unless current invocation paths justify it.
- Prefer tables and explicit labels over prose.
- If a prompt or validator artifact is missing, say so explicitly.
- Preserve uncertainty.
- Tie every important conclusion to a real step function or archetype.
- Keep the audit directly usable for Prompt 3.5 and Prompt 4.
