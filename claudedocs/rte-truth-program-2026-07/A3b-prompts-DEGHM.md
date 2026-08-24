# A3b — Prompt-Engineering Quality Review: RTE v4 Templates, Phases D / E / G / H / M

**Audit pass**: RTE-TRUTH A3, batch b of 4
**Scope**: 40 templates in `services/repo-truth-extractor/promptsets/v4/prompts/` (D×6, E×8, G×9, H×9, M×7 — G5 included; it exists in the G phase and is load-bearing for the batch's conclusions)
**Method**: full read of every template + `PROMPTSET_RULES.md`, `promptset.yaml`, `schemas/G6_*.schema.json`, `schemas/G7_*.schema.json`, and the runtime linter (`lib/promptgen/template_renderer.py`, `run_extraction_v4.py`)
**Date**: 2026-07-10. No live LLM calls made.

Scoring: **(a)** instruction clarity · **(b)** output-contract explicitness · **(c)** injection posture (expected: none — exceptions noted) · **(d)** evidence/anti-fabrication compliance · **(e)** schema-ability value (LOW/MED/HIGH). Scales 1–5 except (e).

---

## Cross-cutting context (read first)

Three template generations coexist in this batch:

1. **Gold standard (hand-authored)**: G5, G6, G7. Domain-specific goals, enums, inline Evidence/Determinism/Anti-Fabrication/Failure-Mode sections tailored to the domain, and (G5) a full item schema + worked example.
2. **Hardened scaffold**: D0, D1 (and partially D2–D5). Generic procedure, but with a "Hard Output Contract", "Hard Requirements", and a "Minimal Example" JSON envelope.
3. **Bare scaffold**: all of E, G0–G4, G9, all of H, all of M. Generic 12-step procedure with duplicated step numbers, no Hard Output Contract, no example, and a one-line pointer: "Refer to PROMPTSET_RULES.md".

**Confirmed by maintainer comment** (`run_extraction_v4.py:104–110`): `promptset.yaml`'s `required_prompt_sections` has **zero runtime readers** — sections are not enforced against prompt bodies — and the "Legacy Context (for intent only; never as evidence)" guard is **inert** (the runtime injects no block by that name). A section validator exists (`template_renderer.py:20–37`, `validate:215–249`) but is not wired to the v4 promptset. Consequence: for bare-scaffold templates, the only binding anti-fabrication text the model may ever see is the unenforced pointer, and `PROMPTSET_RULES.md` is **not listed among the runner context artifacts** in any template's Inputs — whether the rules ever reach the paid model's context is unverified.

**Two-contract problem**: bare-scaffold templates carry a Legacy Context block that is often the *only* place field-level output formats live — and those legacy formats contradict the binding rules (`generated_at` ISO timestamps vs. determinism rule "MUST NOT contain generated_at"; `"line_range": "Lx-Ly"` strings vs. `[start, end]` integers). The model must pick between contradictory specifications. Worst in phase H, endemic in M.

---

## Phase D — Documentation plane (6 templates)

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| D0 INVENTORY+PARTITION | 4 | 5 | 2 | 4 | MED | Legacy fields (size, mtime, tags) absent from binding contract; procedure generic |
| D1 CLAIMS/BOUNDARIES/SUPERSESSION | 4 | 5 | 2 | 4 | HIGH | Highest-value artifacts (CONTRACT_CLAIMS, BOUNDARIES, SUPERSESSION) have thinnest contract: `required_item_fields: id, evidence` only |
| D2 DEEP_EXTRACTION | 3 | 4 | 2 | 4 | MED | No Minimal Example (unlike D0/D1); procedure references undefined "DOC_DEEP item"; 4 outputs share `id, evidence`-only fields |
| D3 CITATION/REFERENCE GRAPH | 3 | 3 | 2 | 3 | MED | Container contradiction: `required_item_fields: nodes, edges, schema` (Graph shape) declared with `kind: json_item_list` + `merge_strategy: itemlist_by_id` |
| D4 MERGE/NORMALIZE/COVERAGE_QA | 3 | 4 | 2 | 3 | MED | Emits `DOC_TOPIC_CLUSTERS.json` whose declared `canonical_writer_step_id` is **D5** — dual ownership; legacy dedup rule "prefer newer timestamps" contradicts determinism rules |
| D5 DOC_TOPIC_CLUSTERS | 3 | 4 | 2 | 3 | LOW | Clusters are derived aggregates, yet contract demands per-item `path, line_range` evidence — incoherent for cluster rows; duplicate ownership with D4; inputs list all 20 upstream D artifacts (token waste) |

Phase note: D is the best bare/hardened phase — D0/D1's "Hard Output Contract + Hard Requirements + Minimal Example" trio (evidence[0] must match row path/line_range; excerpt-local line numbers; fail-closed empty envelope) is the pattern the whole promptset should inherit. It notably includes the only true output-format failure instruction in the batch ("emit valid artifact envelope with `items: []`").

## Phase E — Execution plane (8 templates)

Systemic: none of E0–E9 have a Hard Output Contract or example; all rely on the unenforced Shared Rules pointer. E1–E6 procedures were authored against a different naming generation and contradict their own declared contracts. All of E1–E6 have broken duplicate step numbering (custom steps end at "6."/"7.", then the generic block restarts at "6.").

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| E0 EXEC INVENTORY+PARTITION | 4 | 4 | 2 | 3 | MED | Legacy scan targets (package.json, tools/, justfile, *.mk) exceed declared Inputs scope — ambiguity about authority |
| E1 BOOTSTRAP_COMMANDS | 3 | 3 | 2 | 3 | HIGH | Procedure orders emission of `BOOTSTRAP_COMMANDS_SURFACE.json`; contract declares `EXEC_BOOTSTRAP_COMMANDS.json`. Also loads `EXECUTION_INVENTORY.json` (doesn't exist; real name `EXEC_INVENTORY.json`) |
| E2 ENV_LOADING/CONFIG_CHAIN | 3 | 3 | 2 | 3 | HIGH | Procedure emits `ENV_LOADING_CONFIG_CHAIN.json` vs. declared `EXEC_ENV_CHAIN.json`; rich metadata spec (name/default/is_required) not reflected in `id, evidence`-only contract |
| E3 SERVICE_STARTUP_GRAPH | 3 | 2 | 2 | 3 | HIGH | Triple defect: emits `SERVICE_STARTUP_GRAPH.json` vs. `EXEC_STARTUP_GRAPH.json`; Graph fields (`nodes, edges, schema`) declared under itemlist kind/merge; DAG-validation instruction good but lands in wrong artifact name |
| E4 RUNTIME_MODES+DELTA | 3 | 3 | 2 | 3 | MED | Two outputs declared, procedure builds one thing and emits a third name (`RUNTIME_MODES_DELTA.json`); no instruction distinguishing MODES vs. DELTA content |
| E5 ARTIFACT_OUTPUTS/LOGS/STATE | 3 | 2 | 2 | 3 | MED | Emits `EXEC_ARTIFACT_IO_MAP.json` vs. `EXEC_ARTIFACT_SURFACE.json`; contract requires `component, symbol`, procedure builds `artifact_path, persistence_type, component_owner` — field sets disjoint |
| E6 EXECUTION_RISKS | 3 | 2 | 2 | 3 | HIGH | Emits `EXECUTION_RISKS_REGISTER.json` vs. `EXEC_RISK_FACTS.json`; contract requires `risk, severity, location`, procedure builds `risk_type, severity, mitigation_evidence`; severity assignment has no rubric |
| E9 MERGE/NORMALIZE/QA | 3 | 3 | 2 | 3 | MED | Merges heterogeneous artifacts (incl. a graph) into one itemlist; legacy QA fields (`counts_by_filekind`, `suspicious_empty[]`) never promoted into the binding contract |

## Phase G — Governance plane (9 templates)

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| G0 GOV INVENTORY+PARTITION | 4 | 4 | 2 | 3 | MED | Duplicated step "7."; procedure scan list (`.pre-commit-config.yaml`, CODEOWNERS, LICENSE, .gitignore) exceeds declared Inputs roots |
| G1 CI_GATES | 4 | 4 | 2 | 3 | HIGH | Gate semantics (job, trigger, blocking behavior) never contracted — `id, evidence, path, line_range` only |
| G2 HYGIENE/ALLOWLISTS | 3 | 4 | 2 | 3 | MED | Step 5 ("flag any files in the repo that violate .gitignore/CODEOWNERS") requires whole-repo knowledge the excerpt context can't provide — fabrication invitation |
| G3 POLICY_FILES/ENFORCEMENT | 3 | 4 | 2 | 3 | MED | "Apply the most restrictive rule" is a judgment call with no rubric or tie-break procedure |
| G4 SECURITY/SECRETS | 4 | 4 | **3** | 4 | HIGH | Positive exception: explicit "never extract secret contents; paths/patterns/loaders only" in binding body. Defect: duplicated step "7."; `component, symbol` required without definition |
| G5 AUTH_FLOW_SURFACE | 5 | 5 | **3** | 5 | HIGH | Gold standard (full item schema, 4 enum vocabularies with definitions, worked example, domain failure modes incl. dynamic/transitive auth). Defect: **no JSON Schema file exists despite the template containing a complete, immediately liftable item schema**; cross-phase inputs (`API_DASHBOARD_SURFACE.json`, `SERVICE_ENTRYPOINTS.json`) availability at G-time unstated; template's `"line_range": [0, 0]` placeholder conflicts with the D-phase `start > 0` convention |
| G6 DEPENDENCY_HEALTH | 5 | 5 | 3 | 5 | HIGH | See §G6/G7 below. Minor: "absence signal in the note or item context" references a `note` field no schema defines |
| G7 TECHNICAL_DEBT_REGISTER | 5 | 5 | 3 | 5 | HIGH | See §G6/G7 below. Minor: `id_rule` uses `symbol`/`line_start`, neither a schema-validated field |
| G9 MERGE/QA | 3 | 3 | 2 | 3 | MED | **Merge scope omits G5/G6/G7 outputs entirely** — upstream list stops at `GOV_SECRETS_SURFACE.json`, so `AUTH_FLOW_SURFACE`, `DEPENDENCY_HEALTH_SURFACE`, `TECHNICAL_DEBT_REGISTER` (the three best artifacts in the phase) are orphaned from phase merge and QA coverage |

## Phase H — Home control plane (9 templates)

Systemic: (1) scans `$HOME` dotfiles — the most sensitive, most attacker-influenceable content in the program (private configs, key names, session data); (2) H1–H7 declare `canonical_writer_step_id: H9` for artifacts they themselves write — writer attribution contradicts the step's own role; (3) the only field-level output formats live in Legacy Context and mandate `generated_at` + `"Lx-Ly"` line ranges, both violating binding rules; (4) `component, symbol` required fields fit code symbols, not config surfaces (an MCP server entry has neither).

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| H0 INVENTORY+PARTITION | 3 | 3 | **1** | 3 | MED | Home-scope sensitivity with zero binding redaction language; legacy format (generated_at, size/mtime) contradicts determinism rules |
| H1 KEYS+REFERENCES | 2 | 3 | 2 | **2** | HIGH | **"Never print actual secret values" exists only in Legacy Context — the block labeled "never as evidence".** Binding body says only "extract keys and credential references facts" with no redaction requirement |
| H2 MCP_SURFACE | 3 | 3 | 2 | 3 | HIGH | `component, symbol` ill-fit MCP server entries; useful `confidence: hint_only` vocabulary trapped in legacy block |
| H3 ROUTER+PROVIDER_LADDERS | 3 | 3 | 2 | 3 | MED | Same pattern; ladder semantics only in legacy |
| H4 LITELLM_SURFACES | 3 | 3 | 2 | 3 | MED | Same pattern |
| H5 PROFILES+SESSIONS | 3 | 3 | 2 | 3 | MED | Same pattern; session data is privacy-adjacent, no binding redaction |
| H6 TMUX+WORKFLOW_HELPERS | 3 | 3 | 2 | 3 | MED | Same pattern |
| H7 SQLITE+STATE_DB_METADATA | 3 | 3 | 2 | 3 | MED | "Metadata only, no contents" rule legacy-only; schema_hints structure legacy-only |
| H9 MERGE+QA | 2 | 3 | 2 | **2** | MED | **`required_item_fields: ... sha256 ...` on HOMECTRL_NORM_MANIFEST — an LLM cannot compute file hashes; the contract mandates a value the model must fabricate or UNKNOWN-out.** Also re-emits all 9 upstream artifacts (canonical-rewrite of the entire phase in one completion — unbounded output) |

## Phase M — Runtime export (optional; 7 templates)

Systemic and disqualifying as written: every M procedure instructs "**query live state**, sanitize sensitive values" and "compile extracted data **with timestamps** and provenance". A text-in/text-out LLM cannot query live SQLite/ConPort/MCP state, and timestamps are explicitly forbidden by the determinism rules the same template invokes. If phase M runs as an LLM step, its outputs are fabricated by construction. The legacy blocks describe what should be **runner-executed export scripts** whose outputs an LLM might then summarize.

| Template | a | b | c | d | e | Top defect |
|---|---|---|---|---|---|---|
| M0 RUNTIME_EXPORT_INVENTORY | 2 | 3 | 2 | 2 | LOW | Infeasible live-state query; Inputs scope (`services/**, docker/**, extraction/**`) contradicts legacy allowlist (`~/.dopemux/**` etc.) |
| M1 SQLITE_SCHEMA_SNAPSHOTS | 2 | 3 | 2 | 2 | LOW | Requires PRAGMA output an LLM can't obtain; timestamp mandate vs. determinism ban |
| M2 SQLITE_TABLE_COUNTS | 2 | 3 | 2 | 2 | LOW | `count(*)` requires DB execution; same contradictions |
| M3 CONPORT_EXPORT_SAFE | 2 | 3 | 2 | 2 | LOW | Hardcoded `implementer="GPT-5.3-Codex"` — bakes false provenance into output when any other model runs the step; good redaction/sha-truncation rules are legacy-only |
| M4 DOPE_CONTEXT_EXPORT_SAFE | 2 | 3 | 2 | 2 | LOW | Identical to M3 incl. fabricated implementer metadata |
| M5 MCP_HEALTH_EXPORT_SAFE | 3 | 3 | 2 | 3 | MED | Best M rules (no network probes, env keys only, truncation markers) — all legacy-only; same implementer hardcode |
| M6 RUNTIME_EXPORT_INDEX | 3 | 3 | 2 | 3 | LOW | Index of exports requires knowing runner-side success/failure the model can't observe |

---

## Injection posture (expected: none — exceptions)

Confirmed: **no template in the batch contains any injection hardening** — no "treat scanned repo content as data, not instructions", no delimiter discipline around untrusted excerpts, no instruction-priority statement. This matches expectation for the promptset generation; recorded here as the systemic baseline (MED finding, program-level).

Exceptions (all mitigating in the *exfiltration-impact* direction, not the instruction-following direction):
- **G4, G5** (binding body): never extract secret values — limits blast radius if injected content tries to elicit secrets.
- **H1, H7, M0–M5** (legacy-only, non-binding): redaction/no-secrets/no-network rules exist but live in the "never as evidence" block.
- **Highest-exposure surface**: phase H (home dotfiles — personal data, key names, MCP/router configs) has the *weakest* binding posture of the whole batch. The one prompt family most likely to encounter both secrets and adversarial content has its safety rules in the non-binding block.

---

## Special section: G6/G7 schema–template fit

Verdict: **the two best-aligned schema/template pairs plausible in the promptset — near-exact fit, with one shared structural hole.**

Fit (both):
- `required_item_fields` in template = `required` array in schema, exactly (G6: `id, issue_type, package_name, path, line_range, evidence`; G7: `id, debt_type, description, path, line_range, evidence`).
- Enum vocabularies match **verbatim and completely** (G6 `issue_type`: 5 values; G7 `debt_type`: 6 values) — template and schema cannot drift silently on classification without a diff showing in both files.
- Envelope matches: `{"schema": "<TITLE>@v1", "items": [...]}` with top-level `additionalProperties: false` and the `const` schema tag; template's ItemList declaration names the exact const string.
- `items.additionalProperties: true` correctly permits the template's richer optional fields (G7's `symbol`, G6's contextual notes) without validation failure.

Gaps (both, same hole):
1. **Evidence objects are unvalidated**: schema says only `"evidence": {"type": "array", "minItems": 1}` — no item schema. The promptset's core evidence contract (`path` + `line_range` + `excerpt` ≤200 chars, exact substring) is enforceable in JSON Schema but isn't. A fabricated `{"note": "seen somewhere"}` evidence entry passes validation. This is the single highest-value 10-line schema fix in the batch.
2. **`line_range` under-constrained**: two integers required, but no `minimum: 1` or start≤end assertion (start>0 is expressible; ordering needs a validator step).
3. **`id` unpatterned**: `id_rule` prefixes (`DEPENDENCY_HEALTH_SURFACE:`, `TECHNICAL_DEBT_REGISTER:`) are stated in templates but no `pattern` in schema.
4. G7-only: `id_rule` hashes `(path|debt_type|symbol|line_start)` where `symbol` is not schema-defined; two items differing only by an unvalidated field can collide or split nondeterministically.
5. G6-only: evidence rule for missing lockfiles references a "note or item context" location that neither schema nor required fields define.

---

## Findings

### CRIT
- **F-1 (M0–M6)**: Phase M procedures mandate live-state querying and timestamped output — infeasible for the LLM and contrary to the invoked determinism rules. Any M run produces fabricated runtime "truth". Recast as runner-executed exports with LLM summarization only, or gate the phase off.
- **F-2 (H9)**: `HOMECTRL_NORM_MANIFEST` requires per-item `sha256` — a value the model cannot compute. Contract-mandated fabrication in the phase's canonical manifest.

### HIGH
- **F-3 (E1, E2, E3, E4, E5, E6)**: procedures command emission of artifact filenames that do not exist in the declared contracts (6 distinct mismatches: `BOOTSTRAP_COMMANDS_SURFACE`, `ENV_LOADING_CONFIG_CHAIN`, `SERVICE_STARTUP_GRAPH`, `RUNTIME_MODES_DELTA`, `EXEC_ARTIFACT_IO_MAP`, `EXECUTION_RISKS_REGISTER`), plus nonexistent upstream names (`EXECUTION_INVENTORY.json`). E5/E6 additionally have disjoint required-field sets between contract and procedure.
- **F-4 (G9)**: phase merge/QA excludes G5/G6/G7 outputs — the three schema-backed artifacts bypass phase QA entirely.
- **F-5 (program)**: `required_prompt_sections` unenforced (zero runtime readers — maintainer-confirmed at `run_extraction_v4.py:104–110`) and `PROMPTSET_RULES.md` is not among any template's declared runner-context artifacts. For ~30/40 templates in this batch, the anti-fabrication regime is a pointer to a file that may not be in context, checked by nothing.
- **F-6 (H1; pattern across H, M)**: secrets-redaction rules live exclusively in the "Legacy Context (for intent only; never as evidence)" block. The binding body of H1 instructs credential-reference extraction with no redaction constraint.
- **F-7 (H0–H9, M0–M5)**: two-contract conflict — legacy formats mandate `generated_at` and `"Lx-Ly"` string ranges, binding rules forbid/contradict both, and for H the legacy block is the only field-level format available.

### MED
- **F-8 (D3, E3)**: graph outputs declared with `kind: json_item_list` + `itemlist_by_id` merge while requiring `nodes, edges, schema` — container contradiction.
- **F-9 (D4/D5)**: `DOC_TOPIC_CLUSTERS.json` emitted by D4 but canonically written by D5 — dual ownership; D4's legacy timestamp-preference dedup contradicts determinism rules.
- **F-10 (E1–E6, G0, G4)**: duplicated/broken step numbering (two "6."s, two "7."s) — mechanical scaffold-merge artifact that degrades instruction-following on exactly the anti-fabrication steps.
- **F-11 (D1, D2, E2, G1 et al.)**: highest-value artifacts carry thinnest contracts (`id, evidence` or `id, evidence, path, line_range`), leaving claim/gate/env semantics uncontracted and merge-unstable.
- **F-12 (G2)**: repo-wide violation-flagging demanded from excerpt-scoped context — fabrication invitation.
- **F-13 (M3, M4, M5)**: hardcoded `implementer="GPT-5.3-Codex"` metadata — false provenance whenever another model executes the step.
- **F-14 (program)**: zero injection hardening in any template while prompts are filled with untrusted repo/home content (expected for this generation; highest exposure in phase H).

### LOW
- **F-15**: `PROMPTSET_RULES.md` is titled "V5 PROMPTSET RULES" inside `promptsets/v4/` — version-label drift.
- **F-16**: boilerplate weight — each template ships 8–20 lines of runner-context Inputs and the identical 7-line generic step tail; D5/H9 additionally enumerate 20+/11 upstream artifacts. ~30–40% of tokens per prompt are invariant scaffold on a paid API.
- **F-17**: `Minimal Example` and `Hard Output Contract` exist only in D-phase (D0/D1 fully; D2–D5 contract only) — the strongest known format-compliance device in the promptset is absent from 30+ templates.

---

## Top remediation targets (ranked)

1. **Recast phase M** as runner-executed export scripts + LLM summarization of provided export files; delete the timestamp mandate (F-1).
2. **Remove `sha256` from H9's required fields** (runner computes hashes) (F-2).
3. **Fix the six E-phase emit-name/field mismatches** to match declared contracts — mechanical, high-yield (F-3).
4. **Add G5/G6/G7 outputs to G9's upstream and merge scope** (F-4).
5. **Wire the existing section validator** (`template_renderer.py`) to the v4 promptset and inline (or verifiably inject) PROMPTSET_RULES content into bare-scaffold prompts (F-5).
6. **Promote secrets-redaction from Legacy Context into binding Hard Requirements** for H1, H7, and M-phase safe-exports (F-6).
7. **Reconcile or strip legacy output formats** that contradict binding rules (generated_at, Lx-Ly) — for H, promote the legacy field structures into real contracts first, since they are the only field-level spec (F-7).
8. **Propagate D0/D1's Hard Output Contract + Minimal Example** to all E/G/H scaffolds (F-17, F-10 fix rides along).
9. **Declare D3/E3 as Graph kind** with graph-appropriate merge strategy (F-8).
10. **Resolve DOC_TOPIC_CLUSTERS ownership** (single canonical writer, D5) (F-9).

## Best schema-expansion candidates (~5)

1. **G5 `AUTH_FLOW_SURFACE`** — the template already contains a complete item schema with four enum vocabularies and a worked example; converting to a `.schema.json` is transcription, not design. Highest value: security-relevant downstream consumption.
2. **E6 `EXEC_RISK_FACTS`** — natural enums (`risk_type`, `severity`) already sketched in the procedure; schema would simultaneously force resolution of its contract/procedure field mismatch.
3. **E2 `EXEC_ENV_CHAIN`** — procedure defines `name/default/is_required/source` metadata; heavily consumed for runtime-config truth; currently contracted as bare `id, evidence`.
4. **H2 `HOME_MCP_SURFACE`** — legacy block already defines `servers[]/clients[]` shape with a `confidence` enum incl. `hint_only`; MCP wiring is a primary consumer surface for this program.
5. **E1 `EXEC_BOOTSTRAP_COMMANDS`** — literal command strings + `interpreter` + `is_idempotent` are enum/type-friendly and feed the "what starts what" operator surface.
6. *(Bonus, cheapest)*: **extend G6/G7 schemas with an evidence-object subschema** (`path`/`line_range`/`excerpt` required, excerpt `maxLength: 200`) — closes the shared validation hole in the only two schema-backed artifacts of the batch.
