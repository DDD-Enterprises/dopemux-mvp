# RTE-TRUTH A3 — Prompt-Engineering Quality Review: Phases A, B, C

**Pass:** A3 (batch a of 4) · **Scope:** all 42 templates in `services/repo-truth-extractor/promptsets/v4/prompts/` for phases A (15), B (5), C (22).
**Reviewer role:** first-ever prompt-engineering *quality* review (not correctness of extracted facts).
**Authority:** template files (read directly), `PROMPTSET_RULES.md`, `promptset.yaml` step wiring, downstream R/S/Q consumer grep.
**Confidence:** high (all 42 read in full; downstream consumption verified by grep).

## Scoring rubric

Each template scored 1–5 on:
- **(a) clarity** — instruction unambiguity.
- **(b) contract** — output-contract explicitness (could a strict JSON Schema be written *from the stated format alone*?).
- **(c) inject** — injection posture (any INSTRUCTION/CONTENT separation or "treat input as data" language). *Expected: none.*
- **(d) evid** — evidence / anti-fabrication compliance with `PROMPTSET_RULES.md`.
- **(e) schema-ability** — LOW/MED/HIGH value of adding an explicit JSON Schema (weighted by downstream R/S consumption).

### Cross-cutting reality: three prompt generations

Phases A–C were clearly authored in **three generations**, and this dominates every score:

- **Gen-1** (A0–A9, A99, B0–B9, C0, C3–C6, C9): thin generic `required_item_fields` (often the boilerplate `id, component, symbol, path, line_range, evidence`), a **"Legacy Context" markdown block** embedding an *older* full prompt, and structural contradictions (see F1–F4). Contract/schema-ability LOW–MED.
- **Gen-2** (A11–A13, C1, C2, C7, C8, C12–C17): inline **Item Schema** JSON, explicit **enums**, some **worked examples**, self-canonical, domain-specific fields. Contract/schema-ability MED–HIGH; several are near-schema-ready.
- **Gen-3** (C18–C21): the only prompts that inline *domain-specific* Evidence / Determinism / Anti-Fabrication / Failure-Mode sections (satisfying `promptset.yaml required_prompt_sections` locally, not merely by reference to `PROMPTSET_RULES.md`), carry full enums, are self-canonical, **and already have JSON Schemas on disk** (`schemas/C18…C21.schema.json`). They also bypass C9's merge entirely — escaping finding F1. This is the pattern the rest of the promptset should converge on.
- **Intermediate** (A10, C10, C11): trimmed legacy, cleaner but under-specified fields.

Injection posture is **uniformly absent** across all 42 (as expected) — see F6.

---

## Phase A (15 templates)

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| A0 REPO_CONTROL_INVENTORY | 3 | 2 | 1 | 4 | LOW | Dual container shape (ItemList header vs legacy `{artifact,phase,step,generated_at,items,unknowns}`); blank input bullets. |
| A1 INSTRUCTION_SURFACES | 3 | 2 | 1 | 4 | MED | `required_item_fields: component, symbol` never populated by procedure (which extracts kind/scope/referenced_tools); canonical writer A99 downgrades. |
| A2 MCP_SERVER_DEFS | 3 | 2 | 1 | 3 | MED | Legacy "Required JSON shape" contains `generated_at: <iso8601>` — directly contradicts PROMPTSET determinism ban. |
| A3 MCP_PROXY_SURFACE | 3 | 2 | 1 | 3 | MED | `generated_at` in legacy; generic `component,symbol` fields vs rich legacy (proxy_name/endpoint/routes). |
| A4 ROUTER_SURFACE | 3 | 2 | 1 | 3 | MED | id-format contradiction: `id_rule` hash vs procedure `id (route:<stable_id>)`; `generated_at` in legacy. |
| A5 HOOKS_SURFACE | 4 | 4 | 1 | 4 | MED | **Three conflicting `hook_type` enums** (Item Schema: `git_hook|claude_hook|…`; procedure: `git-hook,pre-commit,ci-pipeline,task-hook,mcp-hook`; legacy free-form) + id-format clash. Superseded by A13. |
| A6 COMPOSE_SERVICE_GRAPH | 3 | 2 | 1 | 3 | LOW | Graph/list contradiction: `kind: json_item_list` + `merge_strategy: itemlist_by_id` but `required_item_fields: nodes, edges, schema`. |
| A7 LITELLM_SURFACE | 3 | 2 | 1 | 3 | MED | Generic `component,symbol` vs rich legacy (provider/model/env/budgets); `generated_at`. |
| A8 TASKX_SURFACE | 3 | 2 | 1 | 3 | LOW-MED | Same generic-vs-legacy mismatch; `generated_at`. |
| A9 IMPLICIT_BEHAVIOR_HINTS | 3 | 2 | 1 | 3 | LOW | Task invites inference ("silent"/"hidden"/"implicit" behaviors) — tension with anti-fabrication; generic fields. |
| A10 LEANTIME_SURFACE | 3 | 3 | 1 | 4 | LOW | Thin `required_item_fields: id, path, line_range, evidence` under-specify surfaces; canonical writer A99. |
| A11 EDITOR_INTEGRATION | 4 | 4 | 1 | 4 | MED-HIGH | No worked example; `scope` enum differs proc (workspace/project) vs schema (adds user/global). Self-canonical (A11). |
| A12 CLI_COMMAND_SURFACE | 4 | 4 | 1 | 4 | MED | `subcommands` "referencing other item IDs" but shape/example show names — id-vs-name ambiguity; no worked example. |
| A13 HOOK_CONTRACT_SURFACE | 4 | 4 | 1 | 4 | MED-HIGH | Two outputs share one procedure; no worked example; overlaps A5 (hooks) and C2 (event flow). |
| A99 MERGE + QA | 2 | 3 | 1 | 4 | LOW | Merge procedure (step 2) omits A11/A12/A13 outputs though step 1 says "A1–A13"; EDITOR/CLI/HOOK_CONTRACT/EVENT_FLOW surfaces orphaned (never merged/emitted). Best mitigation present: legacy rule #4 "Legacy examples must never override the schema" — **but only here**, not propagated to A0–A9. |

## Phase B (5 templates)

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| B0 BOUNDARY_INVENTORY | 3 | 3 | 1 | 4 | LOW | Procedure numbering skips step 8 (1–7 then 9–14); scans the most instruction-dense untrusted files (`AGENTS.md`, `.claude/settings.json`) with zero data-framing (see F6, elevated in security context). |
| B1 BOUNDARY_ENFORCEMENT_POINTS | 3 | 2 | 1 | 4 | MED | Thin contract (`id, evidence, path, line_range`) — no `assertion_logic`/`guard_type`/`protected_symbol` fields despite rich procedure. Feeds R10/R11. |
| B2 REFUSAL_GUARDRAILS_SURFACE | 3 | 2 | 1 | 4 | MED | Generic `component,symbol` fields fail to capture refusal/guard semantics (status/precedence/http_code). |
| B3 BYPASS_PATHS / WEAK_GUARDS | 4 | 3 | 1 | 4 | HIGH | `severity` field has **no enum/vocabulary** (unbounded); `location` vs `path` field split. Security-critical → R10, R11. Good arbitration rule ("only report bypass when evidenced by an alternate path or missing check"). |
| B9 MERGE + QA | 3 | 3 | 1 | 4 | MED | Solid QA fields (`status, checks, issues`); duplicates the "refusal/guardrails" concept already produced by C4 (see F5). |

## Phase C (22 templates)

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| C0 CODE_INVENTORY | 3 | 2 | 1 | 4 | LOW | Generic inventory fields + dual container shape. |
| C1 SERVICE_ENTRYPOINTS | 5 | 5 | 1 | 5 | HIGH | Gold-standard (Item Schema, 11-value `entrypoint_type` enum, worked example) — **but C9 redefines its contract to `id, service_id, type, value, …`**, discarding `entrypoint_type/invocation/module_path`. |
| C2 EVENTBUS_WIRING | 5 | 5 | 1 | 5 | HIGH | 3 Item Schemas + transport/retry/ordering enums + worked example — **but C9 redefines EVENTBUS_SURFACE to generic `component,symbol`** (downgrade at canonical writer). Feeds R9/R10/S8. |
| C3 DOPE_MEMORY_SURFACES | 3 | 2 | 1 | 3 | MED | Declares **1** output (`DOPE_MEMORY_CODE_SURFACE`) but legacy + downstream (C4/C9 inputs) expect **3** (`…_SCHEMAS`, `…_DB_WRITES`) — missing outputs break consumers. |
| C4 TRINITY_BOUNDARY_ENFORCEMENT | 3 | 2 | 1 | 3 | MED | Security-critical surface with generic `component,symbol` boilerplate; `REFUSAL_AND_GUARDRAILS_SURFACE` duplicates B2's `REFUSAL_GUARDRAILS_SURFACE` (F5). |
| C5 TASKX_INTEGRATION | 3 | 2 | 1 | 3 | LOW-MED | Generic fields; `_SURFACES` typo in procedure (F7). |
| C6 WORKFLOW_RUNNERS | 3 | 2 | 1 | 3 | LOW | Generic fields; no ordering/edge model despite "what starts what, in what order" intent. |
| C7 API_DASHBOARDS | 5 | 5 | 1 | 5 | HIGH | Item Schema + method/auth enums + worked example. Dangling "Severity Classification" block defines severities with **no `severity` field** in the schema. Self-canonical (C7). Feeds S10/S8. |
| C8 DETERMINISM/IDEMPOTENCY/CONCURRENCY/SECRETS | 5 | 5 | 1 | 5 | HIGH | 4 Item Schemas, full enums, severity thresholds, worked example. **SECRETS scan has no redaction rule** → exact-substring evidence excerpts can exfiltrate real secret values into artifacts + paid-LLM context (contrast A2 "omit values if they look like secrets"). C9 also renames DETERMINISM/IDEMPOTENCY/CONCURRENCY fields to `id, risk, severity, location`. Feeds R11. |
| C9 MERGE + NORMALIZE + QA | 2 | 2 | 1 | 3 | LOW | **Outputs declares 5 files; Schema defines ~24 contracts; procedure names `CODE_MERGED`/`CODE_QA` that are in neither.** Claims canonical-writer ownership of C12–C17 outputs produced *after* it (ordering contradiction). Degrades upstream rich schemas (C1/C2/C8). |
| C10 SERVICE_CATALOG_DEEP | 3 | 3 | 1 | 4 | MED | Canonical-writer conflict with C9 for `SERVICE_CATALOG`; `.partX.json` placeholder unexplained; 11 fields but no Item Schema/example. |
| C11 LEANTIME_INTEGRATION | 3 | 2 | 1 | 4 | LOW-MED | Under-specified `id, path, line_range, evidence` despite rich intent; feeds R9. |
| C12 AGENT_ORCHESTRATION | 4 | 4 | 1 | 4 | MED | `item_type` enum good, but conditional fields (`method_name`, `payload_shape`…) live outside `required_item_fields` → JSON Schema can't express them; no worked example. |
| C13 ADHD_ENGINE | 4 | 4 | 1 | 4 | MED | Heavy overlap/duplication with C17; conditional fields outside required list; ADHD subsystem is largely aspirational in-repo → elevated fabrication risk (relies on anti-fab + `stub|planned` status). |
| C14 CODE_HEALTH | 5 | 5 | 1 | 5 | HIGH | Full Item Schema + `issue_type`/`severity` enums + definitions. Minor: heuristic thresholds (100 lines, >5 params) baked in; `metric_value` typed as string. Feeds R7/R8. |
| C15 DEAD_CODE_INVENTORY | 5 | 5 | 1 | 4 | HIGH | Item Schema + `dead_code_type`/`confidence` enums; cross-module reference analysis exceeds single-prompt reliability but well-guarded by `confidence`. Feeds R7/R8. |
| C16 DEPENDENCY_GRAPHS | 4 | 4 | 1 | 4 | MED-HIGH | Runner-aware ("edges-as-items — no json_graph kind"); consumes `PYTHON_API_SURFACE`/`SERVICE_ENDPOINT_SURFACE` that C9 is meant to emit but never specifies constructing (F3). |
| C17 COGNITIVE_FEATURES | 4 | 4 | 1 | 3 | MED | Large overlap with C13 (both extract focus timer/dopamine/cognitive load); conditional fields outside required list; aspirational-ADHD fabrication risk. |
| C18 OBSERVABILITY_SURFACE | 5 | 4 | 1 | 5 | DONE (schema exists) | `mechanism` is a required field with **no enum defined** (Determinism section says "use stable enums for surface_type and mechanism" but only `surface_type` values are listed); "Recommended fields" live outside the required list. |
| C19 ERROR_HANDLING_PATTERNS | 5 | 4 | 1 | 5 | DONE (schema exists) | `id_rule` hashes `exception_type` but `exception_type` is not in `required_item_fields` — dedup key depends on an optional field. Excellent behavior-proof rules ("prove the final behavior", don't label `swallow` if it logs-and-reraises). |
| C20 STATE_MANAGEMENT_SURFACE | 5 | 5 | 1 | 5 | DONE (schema exists) | Evidence rule allows `state_type: UNKNOWN` but the `state_type` enum does not include `UNKNOWN` — schema/prose conflict a strict validator would reject. |
| C21 PERFORMANCE_SURFACE | 5 | 5 | 1 | 5 | DONE (schema exists) | `severity` enum present but assignment criteria thin ("directly visible blast radius") vs C8's explicit severity thresholds; minor inconsistency across risk-scoring steps. |

---

## Findings (severity-ranked)

**F1 — CRIT — C9 canonical-writer contradicts and degrades upstream rich schemas.**
`PROMPT_C9` is `canonical_writer_step_id` for most C outputs, yet its `Schema` block redefines them with degraded/renamed fields: `EVENTBUS_SURFACE` → generic `id, component, symbol` (vs C2's `event_name, channel, transport, retry_policy, ordering_guarantee`); `SERVICE_ENTRYPOINTS` → `id, service_id, type, value` (vs C1's `entrypoint_type, invocation, module_path`); `DETERMINISM/IDEMPOTENCY/CONCURRENCY_RISK_LOCATIONS` → `id, risk, severity, location` (vs C8's `risk_type, affected_symbol, non_deterministic_call, mitigation_present, path`). Because C9 is the canonical merge, the Gen-2 producers' careful schemas are overwritten at merge — the well-engineered prompts deliver no schema benefit downstream. **Any schema-expansion of C1/C2/C7/C8 is void unless C9 is reconciled first.**

**F2 — CRIT — C9 Outputs/Schema/procedure three-way mismatch + ordering contradiction.**
`Outputs:` lists 5 files; `Schema:` defines ~24 contracts; `Extraction Procedure` references `CODE_MERGED`/`CODE_QA` present in neither. C9 also declares itself canonical writer for `AGENT_ORCHESTRATION_SURFACE` (C12), `ADHD_ENGINE_SURFACE` (C13), `MODULE/SERVICE_DEPENDENCY_GRAPH` (C16), `COGNITIVE_FEATURES_SURFACE` (C17) — artifacts produced by steps that run *after* C9. A merge step cannot own outputs that do not yet exist. `PYTHON_API_SURFACE`/`SERVICE_ENDPOINT_SURFACE` are declared C9 outputs but no procedure explains their construction, yet C16 consumes them.

**F3 — CRIT (security) — C8 SECRETS_RISK_LOCATIONS has no secret-redaction rule.**
The evidence contract requires an *exact* `excerpt` (≤200 chars). For `hardcoded_secret`/`secret_in_url`/`weak_credential` items this means real secret values are copied verbatim into the norm artifact **and** into the paid-LLM prompt/response. `PROMPTSET_RULES.md` has no redaction clause; A2 has "omit values if they look like secrets" but C8 does not. Feeds R11 security synthesis → secret propagates further. Recommend a mandatory `excerpt` masking rule for `SECRETS_RISK_LOCATIONS` (e.g., replace matched secret span with `***`).

**F4 — HIGH — Gen-1 "Legacy Context" blocks embed a contradictory container shape with `generated_at`.**
Every Gen-1 A prompt (A2–A9) carries a legacy "Required JSON shape" containing `"generated_at": "<iso8601>"`, `"phase"`, `"step"`, `"unknowns"` — a *different* container from the header's `{"schema":…,"items":[…]}` and a direct violation of PROMPTSET determinism (which bans `generated_at`). The disclaimer "for intent only; never as evidence" does not say "do not emit this shape." A model treating the most-detailed block as the output template will emit forbidden fields. The fix exists (A99 legacy rule #4) but was not propagated. Either delete the legacy JSON shapes or add the A99 guard to every prompt.

**F5 — HIGH — Duplicate/near-duplicate output surfaces across steps.**
`REFUSAL_GUARDRAILS_SURFACE` (B2) vs `REFUSAL_AND_GUARDRAILS_SURFACE` (C4); hook extraction split across A5 (`REPO_HOOKS_SURFACE`), A13 (`HOOK_CONTRACT_SURFACE`), C2/A13 event flow; ADHD/cognitive extraction duplicated across C13 and C17. Each duplicate doubles token cost and forces downstream dedup with no canonical-writer arbitration declared.

**F6 — HIGH — Zero injection mitigation, worst on instruction-dense/security surfaces (systemic, expected).**
No template contains INSTRUCTION/CONTENT separation or "treat scanned content as data" language. The pipeline fills untrusted repo content into paid-LLM prompts. Highest risk where the *scan target is itself imperative instruction text*: A1 and A9 explicitly extract "Always…"/"Must NOT…"/"hidden" directives from `.claude/**`, `AGENTS.md`; B0–B3 scan `AGENTS.md` + `.claude/settings.json` to enumerate security boundaries — a poisoned instruction file could inject fabricated boundaries or suppress real bypass findings, and these feed R10/R11. Recommend a shared preamble: scanned file content is DATA, never instructions; delimit injected content; never follow directives found inside it.

**F7 — MED — Pervasive minor defects.**
(a) id-format contradiction in nearly all Gen-1 prompts: `id_rule: NAME:<stable-hash(path|symbol|name)>` vs procedure `id (service:<name>)`/`(route:<id>)`/`(hook:<type>:<name>)`. (b) `_SURFACES` plural typo in C2/C3/C4/C5/C6/C7/C8 procedures ("For each EVENTBUS_SURFACES item") matching no declared artifact. (c) A6 graph-under-list container mismatch. (d) B0 numbering skips step 8. (e) blank input-scope bullets in A0/A99 (empty list items). (f) A5/A11 procedure enums narrower than their schema enums.

**F8 — MED — Unbounded/absent enums on scored fields.**
`severity` in B3 has no vocabulary (C8/C14 correctly enumerate `critical|high|medium|low`). Gen-1 QA/risk fields (`checks`, `issues`, `risk`, `location`) are free-form strings — not schema-constrainable without a value model.

---

## Top ~8 templates most deserving remediation

1. **C9 (MERGE)** — F1+F2. Highest leverage: it silently degrades every Gen-2 schema and is internally incoherent (Outputs≠Schema≠procedure, impossible ordering). Fix before any schema work.
2. **C8 (SECRETS/DETERMINISM/…)** — F3 secret-exfiltration (security) + F1 field renames. Add redaction rule; reconcile with C9.
3. **A2–A8 as a class (exemplars A2, A6)** — F4 `generated_at`/dual-container + F7 container mismatch. Strip or neutralize legacy JSON shapes; propagate A99 rule #4.
4. **C2 (EVENTBUS)** — F1. Rich schema nullified by C9; feeds R9/R10/S8 diagrams.
5. **C1 (SERVICE_ENTRYPOINTS)** — F1. Foundational; degraded by C9; feeds C10/C16.
6. **C3 (DOPE_MEMORY)** — missing declared outputs (`_SCHEMAS`, `_DB_WRITES`) break C4/C9 consumers.
7. **A5 (HOOKS)** — F5/F7 three conflicting `hook_type` enums + duplication with A13; pick one canonical hook model.
8. **B3 (BYPASS_RISKS)** — F8 unbounded `severity` on a security output feeding R11; add enum + fold `location`→`path`.

Runners-up: **C4** (generic fields on a security surface + F5 duplicate), **A99** (orphans A11–A13 outputs).

## Best ~5 schema-expansion candidates (with rationale)

*(All are Gen-2 prompts already carrying an Item Schema + enums, so authoring a JSON Schema is near-mechanical. Rationale = high downstream cost of drift + verified synthesis-phase consumption. **Precondition: fix F1/F2 so C9 stops overwriting these contracts.**)*

1. **C8 risk locations (SECRETS/DETERMINISM/IDEMPOTENCY/CONCURRENCY)** — most security-sensitive; feeds R11 security synthesis + R8 risk register. Enums + severity thresholds already written. A strict schema (via a model_map strict-output lane) would enforce `risk_type`/`severity`/`mitigation_present` rigor and pair naturally with the F3 redaction rule.
2. **C2 EVENTBUS_SURFACE / EVENT_PRODUCERS / EVENT_CONSUMERS** — feeds R9/R10 architecture truth + S8 diagrams; three Item Schemas + transport/retry/ordering enums already present; graph correctness depends on field stability.
3. **C14 CODE_HEALTH_SURFACE** — feeds R7 conflict ledger + R8 risk register; complete Item Schema + `issue_type`/`severity` enums; severity-scored data is only trustworthy if schema-constrained.
4. **C1 SERVICE_ENTRYPOINTS** — foundational surface consumed by C10 (catalog) and C16 (dependency graph); 11-value `entrypoint_type` enum + worked example already present.
5. **C7 API_DASHBOARD_SURFACE** — feeds S10 API-surface reference + S8 diagrams; full method/auth enums + worked example; wire the dangling "Severity Classification" into an actual `severity` field or delete it.

Honorable mention: **C15 DEAD_CODE_INVENTORY** (feeds R7/R8; corroborates prior 8.2 KLoC-dead finding) and **B3 BOUNDARY_BYPASS_RISKS** (security → R11; tiny schema, just needs the F8 `severity` enum).

*Note: 4 of the 6 already-schematized steps (C18–C21) are **in this batch** and reviewed above (Gen-3 rows); G6/G7 belong to batch G. All six are risk/health-style surfaces — consistent with the recommendation to schematize C8/C14/C2/C1/C7 next, and C18–C21's inline-rules pattern is the concrete template to copy when doing so. Their remaining defects are enum-hygiene nits (C18 `mechanism` unenumerated, C19 id-key on optional field, C20 `UNKNOWN` outside enum) that should be fixed in prompt+schema together.*
