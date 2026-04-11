# Prompt Bundle: Active Adjudication and FL_INT Bundle

## Prompt
- prompt_id: rte_r_r0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R0
- short_name: Control Plane Truth Map
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: CONTROL_PLANE_TRUTH_MAP.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R0 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R0

## Goal
Produce `R0` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CONTROL_PLANE_TRUTH_MAP.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R0`
    - `id_rule`: `CONTROL_PLANE_TRUTH_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase A, H, D, and C normalized artifacts from `extraction/**/norm/`.
2. Map **Repo Control Plane**: Extract `instruction_surfaces`, `hooks`, `compose`, `router`, `litellm`, and `mcp` definitions from Phase A/C.
3. Map **Home Control Plane**: Extract `configs`, `router`, `litellm`, `mcp`, and `sqlite` metadata from Phase H.
4. Construct **Invocation Graph**: Trace triggers from repo instructions to service startup (Compose/Tmux).
5. Identify **Coupling Points**: Match control-plane configs to code entrypoints (Phase C).
6. Flag **Portability Risks**: Identify hardcoded machine paths or non-portable environment dependencies.
7. Arbitration: If A/D (Intent) conflicts with C (Implementation), mark `status: conflict` and cite both.
8. Legacy Context is intent guidance only and is never evidence.
<<<<<<< HEAD
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.
=======
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.
>>>>>>> 12f30a09d (feat(prompts): rewrite Phase R, B, G, and E extraction procedures (Pass 4) - concrete instructions for synthesis, boundaries, governance, and execution)

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: CONTROL_PLANE_TRUTH_MAP.md

ROLE: Supervisor/Auditor. Evidence-first.
HARD RULE: Reason only from Phase A/H/D/C normalized artifacts. If evidence is missing, write UNKNOWN and name the missing artifact.

TASK:
Produce the repo/home control-plane truth map.

MUST INCLUDE:
- Repo control plane surfaces (instructions, hooks, compose, router, litellm, mcp)
- Home control plane surfaces (configs, router, litellm, mcp, sqlite state)
- Invocation graph (what starts what)
- Control-plane to runtime coupling points
- Portability risks

RULES:
- Cite every claim with REPOCTRL:/HOMECTRL:/CODE:/DOC references.
- No repo rescans. No implementation changes.
- Label unevidenced statements UNKNOWN.
```

---

## Prompt
- prompt_id: rte_r_r1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R1
- short_name: Dope Memory Implementation Truth
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R1 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R1

## Goal
Produce `R1` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_IMPLEMENTATION_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOPE_MEMORY_SCHEMAS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_SCHEMAS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_DB_WRITES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_DB_WRITES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `DOPE_MEMORY_SCHEMAS.json`, `DOPE_MEMORY_DB_WRITES.json`, and Phase A/H/C/D artifacts.
2. Inventory **Memory Adapters**: Identify SQLite/Postgres usage and connection logic from Phase C.
3. Map **Schemas & Writes**: Align `DOPE_MEMORY_SCHEMAS.json` and `DOPE_MEMORY_DB_WRITES.json` to code symbols in Phase C.
4. Trace **Retention/TTL**: Locate data expiration logic in `C` or `A` phases.
5. Map **Control-Plane Links**: Bind memory configurations to env vars or Compose wiring from Phase A.
6. Arbitration: Resolve intent conflicts via Phase D `DOC_SUPERSESSION`; if implementation differs from docs, mark as `GAPS/CONFLICTS`.
7. Output Format: Organize by 1) IMPLEMENTED (CODE), 2) PLANNED (DOC), 3) GAPS/CONFLICTS.
8. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce memory implementation truth for current system behavior.

MUST INCLUDE:
- Stores/adapters (sqlite/postgres/other)
- Schema objects from DOPE_MEMORY_SCHEMAS.json
- Write paths from DOPE_MEMORY_DB_WRITES.json
- Retention/TTL enforcement points
- Replay/re-derive surfaces (if present)
- Control-plane dependencies (env vars, compose wiring, home DBs)

FORMAT:
1) IMPLEMENTED (CODE evidence)
2) PLANNED (DOC evidence)
3) GAPS/CONFLICTS (both sides cited)
4) Minimal verification command suggestions

RULES:
- Cite statements for tables/triggers/enforcement points.
- If docs conflict, use DOC_SUPERSESSION then recency tie-breaker.
```

---

## Prompt
- prompt_id: rte_r_r10
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R10
- short_name: Two Plane Architecture Truth
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R10_TWO_PLANE_ARCHITECTURE_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: TWO_PLANE_ARCHITECTURE_TRUTH.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R10 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R10

## Goal
Produce a deterministic, evidence-backed architecture truth report for the two-plane model currently implemented in the repository.
Focus on explicit boundaries, authority ownership, and integration edges proven by code/config/docs.

## Inputs
- Upstream normalized artifacts:
  - `SERVICE_CATALOG.json`
  - `TRINITY_ENFORCEMENT_SURFACE.json`
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
  - `BOUNDARY_MERGED.json`
  - `EVENTBUS_SURFACE.json`
  - `DOPE_MEMORY_CODE_SURFACE.json`
  - `LEANTIME_INTEGRATION_TRUTH.md`
  - `RISK_REGISTER_TOP20.md`
- Supporting source/doc paths for disambiguation:
  - `src/dopemux/**`
  - `services/**`
  - `docs/90-adr/**`
  - `docs/04-explanation/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `TWO_PLANE_ARCHITECTURE_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `TWO_PLANE_ARCHITECTURE_TRUTH.md`
    - `canonical_writer_step_id`: `R10`
    - `required_sections`: `Plane Definitions, Authority Ownership Matrix, Cross-Plane Integration Paths, Boundary Enforcement and Failure Rails, Current Drift and Risks, Evidence Index`
- Required section order:
  1. `## Plane Definitions`
  2. `## Authority Ownership Matrix`
  3. `## Cross-Plane Integration Paths`
  4. `## Boundary Enforcement and Failure Rails`
  5. `## Current Drift and Risks`
  6. `## Evidence Index`
- Ownership matrix rows must include:
  - `surface`
  - `owner_plane`
  - `evidence`

## Extraction Procedure
1. Load `SERVICE_CATALOG.json`, `TRINITY_ENFORCEMENT_SURFACE.json`, and Boundary artifacts from upstream.
2. Map **Plane Definitions**: Extract explicit plane definitions (e.g., Control vs. Runtime) from ADRs and Explanation docs (Phase D).
3. Build **Authority Ownership Matrix**: Match each service surface to an evidenced owner plane based on code location and config authority.
4. Trace **Cross-Plane Integration**: Identify events or API calls that cross plane boundaries with direct evidence.
5. Identify **Drift & Failure Rails**: Document evidenced cases where authority ownership is violated or boundaries are bypassed (Phase R3).
6. Arbitration: If plane ownership is ambiguous, mark as `UNKNOWN` and cite the conflicting or missing evidence.
7. Emit required sections in deterministic order as defined in the schema.
8. Legacy Context is intent guidance only and is never evidence.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R10 - Two Plane Architecture Truth
Phase: R
Step: R10
Outputs:
- TWO_PLANE_ARCHITECTURE_TRUTH.md
Mode: synthesis
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_r_r11
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R11
- short_name: Security Risk Synthesis
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R11_SECURITY_RISK_SYNTHESIS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: SECURITY_RISK_SYNTHESIS.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R11 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R11

## Goal
Produce `R11` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Synthesize a unified security risk assessment by aggregating findings from governance secrets (G4), authentication flows (G5), boundary assertions (B1), refusal guardrails (B2), and bypass paths (B3) into a single security truth memo. Identify cross-cutting security gaps, unprotected attack surfaces, and risk prioritization.

## Inputs
- Upstream normalized artifacts consumed by this synthesis:
- `GOV_SECRETS_SURFACE.json` (from G4)
- `AUTH_FLOW_SURFACE.json` (from G5)
- `BOUNDARY_ASSERTIONS_SURFACE.json` (from B1)
- `REFUSAL_AND_GUARDRAILS_SURFACE.json` (from B2)
- `BYPASS_PATHS_SURFACE.json` (from B3)
- Supporting context artifacts:
- `API_DASHBOARD_SURFACE.json` (from C7)
- `SERVICE_ENTRYPOINTS.json` (from C1)
- `SECRETS_RISK_LOCATIONS.json` (from C8)
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SECURITY_RISK_SYNTHESIS.md`

## Schema
- Output is a markdown document (not JSON). Use the following structure:
  - `SECURITY_RISK_SYNTHESIS.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R11`

### Document Structure
The output must follow this exact section structure:

```markdown
# Security Risk Synthesis

## Executive Summary
<!-- 3-5 sentence overview: total findings, critical count, top risk area, overall posture assessment -->

## Risk Matrix

| Risk ID | Category | Severity | Source Artifacts | Description | Affected Services |
|---------|----------|----------|-----------------|-------------|-------------------|
| SEC-001 | ... | critical|high|medium|low | G4, B3 | ... | ... |

## 1. Authentication & Authorization Gaps
<!-- Cross-reference G5 (auth flows) with C7 (API endpoints) -->
<!-- Identify: unprotected endpoints, weak auth mechanisms, missing role checks -->

### 1.1 Unprotected Endpoints
<!-- API routes in C7 with no corresponding auth flow in G5 -->

### 1.2 Weak Authentication Patterns
<!-- Auth flows with is_optional=true, silent_skip fallback, or manual_inline enforcement -->

### 1.3 Missing Authorization Checks
<!-- Routes with auth but no role/permission enforcement for sensitive operations -->

## 2. Secrets & Credential Exposure
<!-- Cross-reference G4 (secrets surface) with C8 (secrets risk locations) -->
<!-- Identify: hardcoded secrets, unprotected env vars, secrets in logs -->

### 2.1 Hardcoded Credentials
<!-- Secrets risk locations with risk_type=hardcoded_secret -->

### 2.2 Secret Leakage Vectors
<!-- Secrets risk locations with risk_type=secret_in_log or secret_in_url -->

### 2.3 Credential Management Gaps
<!-- Missing rotation, missing encryption at rest, missing vault integration -->

## 3. Boundary & Guardrail Integrity
<!-- Cross-reference B1 (boundary assertions) with B2 (guardrails) and B3 (bypass paths) -->
<!-- Identify: bypassed guards, inconsistent enforcement, missing guardrails -->

### 3.1 Bypass Paths
<!-- B3 findings: paths that circumvent auth, validation, or guardrails -->

### 3.2 Inconsistent Boundary Enforcement
<!-- Boundaries declared in B1 but not enforced in code -->

### 3.3 Guardrail Coverage Gaps
<!-- Expected guardrails (from B2) missing for critical operations -->

## 4. Cross-Cutting Risks
<!-- Patterns that span multiple categories -->

### 4.1 Service-to-Service Trust
<!-- Internal services communicating without auth or with implicit trust -->

### 4.2 Error Handling Security
<!-- Error responses leaking internal state, stack traces, or secrets -->

### 4.3 Configuration Security
<!-- Sensitive config in plain text, missing env isolation, default credentials -->

## 5. Risk Prioritization & Recommendations

### Critical (Must Fix Before Production)
<!-- List with specific artifact references and remediation steps -->

### High (Fix Within Sprint)
<!-- List with specific artifact references and remediation steps -->

### Medium (Track as Tech Debt)
<!-- List with artifact references -->

### Low (Monitor)
<!-- List with artifact references -->

## Evidence Traceability
<!-- For each finding, cite source artifact ID and evidence path -->
<!-- Format: [SEC-XXX] ← G4:item_id + B3:item_id -->

## Coverage Notes
<!-- What was and wasn't analyzed; known gaps in upstream data -->
```

## Extraction Procedure
1. Load all upstream artifacts: G4 (GOV_SECRETS_SURFACE), G5 (AUTH_FLOW_SURFACE), B1 (BOUNDARY_ASSERTIONS_SURFACE), B2 (REFUSAL_AND_GUARDRAILS_SURFACE), B3 (BYPASS_PATHS_SURFACE).
2. Load supporting artifacts: C7 (API_DASHBOARD_SURFACE), C1 (SERVICE_ENTRYPOINTS), C8 (SECRETS_RISK_LOCATIONS).
3. **Auth gap analysis**: For each endpoint in API_DASHBOARD_SURFACE, check if a corresponding AUTH_FLOW_SURFACE item exists. Flag endpoints where `auth_required=false` or no auth flow found, especially for POST/PUT/DELETE methods or endpoints handling user data.
4. **Secrets exposure analysis**: Merge G4 items (governance-level secrets) with C8 SECRETS_RISK_LOCATIONS items. Group by severity. Identify secrets with both governance policy violations AND code-level exposure.
5. **Boundary integrity analysis**: For each B1 boundary assertion, verify enforcement exists in code (B2 guardrails). Cross-reference B3 bypass paths to identify boundaries that are declared but circumventable.
6. **Cross-cutting pattern detection**: Identify services that appear in multiple risk categories. Flag services with compounding risks (e.g., both unprotected endpoints AND hardcoded secrets).
7. Assign deterministic risk IDs using format `SEC-NNN` ordered by severity (critical first) then by affected service count (most affected first).
8. For each risk, trace evidence back to source artifact IDs — every finding must reference at least one upstream item ID.
9. Write risk prioritization based on severity thresholds: critical = production data exposure or auth bypass; high = exploitable in authenticated context; medium = defense-in-depth gap; low = best-practice deviation.
10. Document coverage gaps: list any upstream artifacts that were empty or missing, and note which sections have incomplete analysis as a result.
11. Emit exactly `SECURITY_RISK_SYNTHESIS.md` and no additional files.

## Evidence Rules
- Every risk finding must reference at least one upstream artifact item by ID.
- Use format: `[SEC-XXX] ← ARTIFACT_NAME:item_id` for traceability.
- Include exact evidence excerpts from upstream artifacts (max 200 chars each).
- Every cited evidence object must preserve `path` and `line_range` from the upstream source item. Do not emit evidence citations that omit either field.
- In `## Evidence Traceability`, each finding must include concrete source anchors using this shape: `path: <repo-relative-path>`, `line_range: [start, end]`, `excerpt: <trimmed text>`.
- If upstream artifact was empty or missing, note in Coverage Notes and mark affected findings as `needs_review`.
- Do not introduce new evidence not present in upstream artifacts — this is a synthesis step.

## Determinism Rules
- Risk IDs must be deterministic: sort by (severity_rank, affected_service_count DESC, first_evidence_path ASC).
- Severity rank: critical=0, high=1, medium=2, low=3.
- Identical upstream inputs must produce identical output.
- Do not include timestamps, run IDs, or generation dates in the output.

## Anti-Fabrication Rules
- Do not invent security risks not supported by upstream artifact evidence.
- Do not speculate about attack scenarios beyond what the code evidence demonstrates.
- If a risk category has no upstream findings, write "No findings from upstream artifacts" rather than omitting the section.
- Do not escalate severity beyond what the evidence supports — a theoretical risk without code evidence is at most "low" severity.
- Never include actual secret values in the synthesis — reference paths and patterns only.

## Failure Modes
- Missing upstream artifacts: emit the document with affected sections containing "Upstream artifact [NAME] not available — section incomplete" and note in Coverage Notes.
- Empty upstream artifacts: emit section with "No items found in [NAME] — either no risks exist or extraction coverage was incomplete."
- Conflicting upstream data: when G4 and C8 disagree on severity for the same secret, include both assessments with evidence and note the discrepancy.
- Partial coverage: clearly state which services/endpoints were analyzed vs. which were not covered by upstream extraction.

---

## Prompt
- prompt_id: rte_r_r2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R2
- short_name: Eventbus Wiring Truth
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R2_EVENTBUS_WIRING_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: EVENTBUS_WIRING_TRUTH.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R2 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R2

## Goal
Produce `R2` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EVENTBUS_WIRING_TRUTH.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EVENTBUS_WIRING_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R2`
    - `id_rule`: `EVENTBUS_WIRING_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase A, H, D, and C artifacts, focusing on `EVENTBUS_WIRING_TRUTH_SURFACES.json`.
2. Map **Implementations**: Identify event bus adapters (e.g., local, redis, file-based) from Phase C.
3. Trace **Producers**: Map event names to code locations where events are emitted.
4. Trace **Consumers**: Map event names to handler functions or subscriber classes.
5. Link **Dispatch Paths**: Connect producer calls to consumer execution via the identified adapter.
6. Arbitration: If event names are computed dynamically, mark as `(computed)` and cite the calculation logic.
7. Output Format: Produce a table: `Event | Producers (CODE) | Consumers (CODE) | Adapter (CODE)`.
8. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: EVENTBUS_WIRING_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce event bus wiring truth.

MUST INCLUDE:
- Event bus implementations/adapters
- Event names/topics (literal where evidenced)
- Producer mapping: event -> producers
- Consumer mapping: event -> handlers/subscribers
- Dispatch paths from producer call to consumer execution
- Control-plane impacts on routing

OUTPUT TABLE:
Event | Producers (CODE refs) | Consumers (CODE refs) | Adapter/Bus (CODE refs)

RULES:
- If event name is computed, mark as (computed) with evidence.
- No guessing missing event names.
```

---

## Prompt
- prompt_id: rte_r_r3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R3
- short_name: Trinity Boundary Enforcement Trace
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R3 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R3

## Goal
Produce `R3` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R3`
    - `id_rule`: `TRINITY_BOUNDARY_ENFORCEMENT_TRA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase A, B, C, and D artifacts, focusing on `TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.json`.
2. Trace **Enforcement Points**: Identify exact symbols/files where boundary checks (FastAPI `Depends`, etc.) are implemented.
3. Map **Refusal Rails**: Trace how authorization failures propagate to the user/caller.
4. Identify **Bypass Paths**: Document any evidenced routes that circumvent boundary checks.
5. Arbitration: Explicitly separate IMPLEMENTED checks (Phase C) from PLANNED rules (Phase D).
6. Output Format: 1) Boundary list with enforcement status, 2) Guardrail pipeline diagram (text), 3) Bypass risks.
7. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce boundary enforcement trace.

MUST INCLUDE:
- Evidenced boundaries only
- Enforcement points (exact symbols/files)
- Refusal rails and propagation paths
- Bypass paths only when evidenced

OUTPUT:
- Boundary list with enforcement checks
- Guardrail pipeline diagram (text)
- Known bypass risks with evidence

RULES:
- Separate IMPLEMENTED checks from PLANNED doc rules.
- Do not invent boundaries.
```

---

## Prompt
- prompt_id: rte_r_r4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R4
- short_name: Taskx Integration Truth
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R4_TASKX_INTEGRATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: TASKX_INTEGRATION_TRUTH.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R4 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R4

## Goal
Produce `R4` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TASKX_INTEGRATION_TRUTH.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TASKX_INTEGRATION_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R4`
    - `id_rule`: `TASKX_INTEGRATION_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase A, C, and D artifacts, specifically `TASKX_SURFACE.json` and `TASKX_INTEGRATION_SURFACES.json`.
2. Trace **Invocation**: Identify how TaskX is triggered (scripts, hooks, CI) from Phase A/C.
3. Map **I/O Paths**: Locate where TaskX packets are read from and written to.
4. Identify **Instruction Surface**: Map how operator instructions are compiled and injected.
5. Resolve **Coupling**: Link TaskX behavior to `~/.config/taskx` and repo-local `.taskx` surfaces.
6. Arbitration: Cross-reference `REPO_TASKX_SURFACE` and `TASKX_INTEGRATION_SURFACE` evidence.
7. Output Format: Organize by 1) IMPLEMENTED, 2) PLANNED, 3) GAPS/RISKS.
8. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: TASKX_INTEGRATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce TaskX integration truth.

MUST INCLUDE:
- How taskx is invoked (scripts/hooks/ci)
- Where packets are read/written
- Operator instruction compile/injection surfaces
- Coupling to ~/.config/taskx and repo .taskx surfaces

OUTPUT:
- IMPLEMENTED integration map
- PLANNED integration map
- GAPS/RISKS

RULES:
- Cite REPO_TASKX_SURFACE and TASKX_INTEGRATION_SURFACE evidence.
```

---

## Prompt
- prompt_id: rte_r_r5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R5
- short_name: Workflows Truth Graph
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: WORKFLOWS_TRUTH_GRAPH.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R5 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R5

## Goal
Produce `R5` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOWS_TRUTH_GRAPH.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOWS_TRUTH_GRAPH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R5`
    - `id_rule`: `WORKFLOWS_TRUTH_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`

## Extraction Procedure
1. Load Phase A, C, and W (Workflow) artifacts, specifically `WORKFLOW_RUNNER_SURFACE.json`, `HOME_TMUX_WORKFLOW_SURFACE.json`, and `COMPOSE_SERVICE_GRAPH.json`.
2. Map **Bootstrap Flows**: Identify how the system starts via Tmux, Docker Compose, or standalone scripts from Phase A/W.
3. Trace **Multi-Service Workflows**: Connect services into a dependency graph, identifying order of execution and state triggers.
4. Extract **I/O & Artifacts**: Identify explicit file inputs, outputs, and intermediate artifacts for each workflow step.
5. Identify **Instruction-Driven Steps**: Map how `.md` or `.json` instruction files drive specific runner behaviors (Phase W).
6. Arbitration: Resolve conflicts between `W` (Workflow Inventory) and `C` (Code Implementation) by prioritizing evidenced code paths.
7. Output Format: Produce a Markdown graph with nodes (steps/services) and edges (triggers/dependencies), plus a list of workflows (W1..Wn) with literal citations.
8. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: WORKFLOWS_TRUTH_GRAPH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce workflow truth graph.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows with order/dependencies
- Inputs/outputs/artifacts where explicit
- Instruction-file-driven workflow steps

OUTPUT:
- Workflow list (W1..Wn) with literal steps + citations
- Services involved per workflow
- UNKNOWN markers where evidence is missing

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph evidence.
```

---

## Prompt
- prompt_id: rte_r_r6
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R6
- short_name: Portability And Migration Risk Ledger
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R6 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R6

## Goal
Produce `R6` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R6`
    - `id_rule`: `PORTABILITY_AND_MIGRATION_RISK_L:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`

## Extraction Procedure
1. Load Phase A, H, G (Governance), and C artifacts from `extraction/**/norm/`.
2. Identify **Home-Only Dependencies**: Scan for absolute paths or hardcoded references to `~/.config`, `~/.gemini`, or `~/.dopemux` in Phase H/A.
3. Inventory **Required Env Vars**: Extract mandatory environment variables from `compose.yml`, `.env.template`, and Phase C code surfaces.
4. Assess **MCP vs. Hooks**: Compare current MCP server definitions (Phase A) against potential Hook implementation patterns in Phase C.
5. Identify **Migration Risks**: Document specific code or config patterns that would break if migrated to a different runner or hook system.
6. Arbitration: Cite every risk with evidence from Phase A (Architecture) or Phase C (Code).
7. Output Format: Produce a ledger table: `ID | Risk | Severity | Location | Evidence`.
8. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce portability and migration risk ledger.

MUST INCLUDE:
- Home-only dependencies
- Required env vars
- MCP dependencies vs hooks opportunities
- Evidence-based "what breaks if moved to hooks"

RULES:
- Cite every risk.
- No broad refactor proposals.
```

---

## Prompt
- prompt_id: rte_r_r7
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R7
- short_name: Conflict Ledger
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R7_CONFLICT_LEDGER.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: CONFLICT_LEDGER.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R7 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R7

## Goal
Produce `R7` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
- `CODE_HEALTH_SURFACE.json`
- `DEAD_CODE_INVENTORY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CONFLICT_LEDGER.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CONFLICT_LEDGER.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R7`
    - `id_rule`: `CONFLICT_LEDGER:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase D (Docs), Phase C (Code), and Phase A (Architecture) artifacts from upstream norm results.
2. Identify **Doc-vs-Code Conflicts**: Compare architectural claims in `docs/**/*.md` against actual implementations in Phase C artifacts.
3. Identify **Doc-vs-Doc Conflicts**: Scan for contradictory statements within documentation files (Phase D).
4. Apply **Arbitration Rules**:
    - Code (Phase C) always overrides Documentation (Phase D).
    - For Doc-vs-Doc, apply `DOC_SUPERSESSION` logic (newer/higher-authority docs win).
5. Document **Authority Decisions**: Explicitly state which source was chosen as "truth" and why, citing both sides.
6. Output Format: List each conflict with "Side A", "Side B", "Resolution", and "Rationale", citing evidence for all claims.
7. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: CONFLICT_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce conflict ledger across docs/code/control planes.

MUST INCLUDE:
- doc claim vs code truth
- doc vs doc conflicts
- authority decisions using evidence hierarchy

RULES:
- Use DOC_SUPERSESSION first, then recency tie-breaker for doc-vs-doc only.
- Never override code reality with docs.
- Cite both sides for each conflict.
```

---

## Prompt
- prompt_id: rte_r_r8
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R8
- short_name: Risk Register Top20
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R8_RISK_REGISTER_TOP20.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: RISK_REGISTER_TOP20.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R8 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R8

## Goal
Produce `R8` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
- `CONFLICT_LEDGER.md`
- `CODE_HEALTH_SURFACE.json`
- `DEAD_CODE_INVENTORY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `RISK_REGISTER_TOP20.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `RISK_REGISTER_TOP20.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R8`
    - `id_rule`: `RISK_REGISTER_TOP20:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`

## Extraction Procedure
1. Load Phase R6 (Portability Risks), R7 (Conflicts), B (Boundaries), and C (Code Health/Dead Code) artifacts.
2. Extract **Quality Risks**: Pull from `CODE_HEALTH_SURFACE.json` (complexity) and `DEAD_CODE_INVENTORY.json`.
3. Extract **Integrity Risks**: Identify non-deterministic logic, concurrency issues, or idempotency failures from Phase C8 scans.
4. Extract **Security Risks**: Map boundary bypasses identified in Phase R3 (Trinity) or B3 (Bypass Paths).
5. Perform **Severity Ranking**: Assign risk levels (Critical/High/Medium/Low) based on evidence impact.
6. Output Format: List Top-20 risks with `ID | Risk | Severity | Location | Evidence`.
7. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: RISK_REGISTER_TOP20.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce top-20 risk register.

MUST INCLUDE:
- Determinism/idempotency/concurrency risks
- Boundary bypass risks
- Code quality risks (high-complexity hotspots, dead code, missing error handling from CODE_HEALTH_SURFACE and DEAD_CODE_INVENTORY)
- Severity ranking with evidence
- Minimal mechanical bounding mechanisms

RULES:
- Cite every risk item.
- No large refactor recommendations.
```

---

## Prompt
- prompt_id: rte_r_r9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: R
- step: R9
- short_name: Leantime Integration Truth
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R9_LEANTIME_INTEGRATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("R")
- invokes: LEANTIME_INTEGRATION_TRUTH.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: R phase step R9 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_R9

## Goal
Synthesize a deterministic, evidence-anchored truth memo that describes how Leantime integration is implemented across the repository today.
This is a reconciliation step over upstream norm artifacts, not freeform analysis.

## Inputs
- Upstream normalized artifacts:
  - `REPO_LEANTIME_SURFACE.json`
  - `LEANTIME_INTEGRATION_SURFACE.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `SERVICE_CATALOG.json`
  - `RISK_REGISTER_TOP20.md`
- Supporting source files when needed for disambiguation:
  - `services/leantime-bridge/**`
  - `src/dopemux/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `LEANTIME_INTEGRATION_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `LEANTIME_INTEGRATION_TRUTH.md`
    - `canonical_writer_step_id`: `R9`
    - `required_sections`: `Scope, Confirmed Integration Surfaces, Data and Event Flows, Configuration and Runtime Contracts, Gaps and Unknowns, Evidence Index`
- Required section order:
  1. `## Scope`
  2. `## Confirmed Integration Surfaces`
  3. `## Data and Event Flows`
  4. `## Configuration and Runtime Contracts`
  5. `## Gaps and Unknowns`
  6. `## Evidence Index`
- Every claim section must include explicit evidence bullets (`path`, `line_range`, `excerpt`).

## Extraction Procedure
1. Load `REPO_LEANTIME_SURFACE.json`, `LEANTIME_INTEGRATION_SURFACE.json`, and EventBus/Service artifacts.
2. Confirm **Integration Surfaces**: Identify exact API endpoints, database schemas, or symbols used for Leantime integration from Phase C.
3. Map **Data & Event Flows**: Trace events from production points to Leantime handlers/consumers identified in `EVENT_CONSUMERS.json`.
4. Verify **Runtime Contracts**: Extract environment variables and configuration keys (Phase A/H) required for the Leantime bridge.
5. Identify **Gaps & Unknowns**: Flag any integration points declared in documentation (Phase D) but lacking implementation evidence (Phase C).
6. Arbitration: Resolve conflicts by prioritizing direct Code evidence (Phase C) over Architectural Surface definitions (Phase A).
7. Emit required sections in the exact order defined in the schema.
8. Legacy Context is intent guidance only and is never evidence.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R9 - Leantime Integration Truth
Phase: R
Step: R9
Outputs:
- LEANTIME_INTEGRATION_TRUTH.md
Mode: synthesis
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_fl_int_f0
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: F0
- short_name: F0 Design Claims Raw
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/F0_design_claims_raw.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: DESIGN_CLAIMS_RAW.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step F0 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder structure; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative design-claims extractor. Output JSON only.

USER
Produce `F0` outputs from supplied Phase D extraction artifacts only.

Rules:
- Use only supplied evidence and upstream artifact content.
- Preserve distinct claims when they may later classify differently.
- Every row in `DESIGN_CLAIMS_RAW.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Prefer upstream repo evidence paths and line ranges; if a claim comes only from a markdown artifact, use the artifact path and cited line range from the supplied numbered content.
- Do not resolve contradictions, infer implementation completeness, or collapse historical and current claims.
- Sort items deterministically by `id`.

Return JSON matching schema `F0`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_f1
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: F1
- short_name: F1 Design Claims Classified
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/F1_design_claims_classified.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: DESIGN_CLAIMS_CLASSIFIED.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step F1 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder reasoned_plan; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative design-claims classifier. Output JSON only.

USER
Produce `F1` outputs from supplied `F0` claims plus Phase C and Phase R artifacts.

Rules:
- Classify claims using supplied evidence only.
- Keep `evidence_class` and `temporal_status` separate.
- Misclassifying partial or target-state work as `REPO_PROVEN_CURRENT` is worse than leaving ambiguity.
- Preserve unresolved ambiguity as `UNKNOWN`, `MIXED`, or `needs_review` rather than smoothing it away.
- Every row in `DESIGN_CLAIMS_CLASSIFIED.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `F1`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_f2
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: F2
- short_name: F2 Design Contradictions
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/F2_design_contradictions.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: DESIGN_CONTRADICTIONS.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step F2 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder reasoned_plan; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative contradiction detector. Output JSON only.

USER
Produce `F2` outputs from supplied classified claims only.

Rules:
- Surface contradictions instead of resolving them.
- Group only when the contradiction is directly supported by supplied claims.
- Use deterministic contradiction ids.
- Every row in `DESIGN_CONTRADICTIONS.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `F2`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_f4
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: F4
- short_name: F4 Canonical Design
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/F4_canonical_design.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: CANONICAL_DESIGN.md, CANONICAL_DESIGN_META.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step F4 for design/feature synthesis and routing.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder reasoned_plan; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative canonical design synthesizer. Output JSON only.

USER
Produce `F4` outputs from supplied `F0`, `F1`, and `F2` results.

Rules:
- `CANONICAL_DESIGN.md` section content must preserve temporal separation.
- Do not place non-`REPO_PROVEN_CURRENT` claims into the current-state section.
- Contradictions must remain visible and unresolved.
- Missing evidence must remain explicit.
- Keep markdown operator-readable and machine summary deterministic.

Return JSON matching schema `F4`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_l0
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: L0
- short_name: L0 Feature Candidates Raw
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/L0_feature_candidates_raw.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: FEATURE_CANDIDATES_RAW.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step L0 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder structure; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative feature harvester. Output JSON only.

USER
Produce `L0` outputs from supplied Phase D, Phase C, optional Phase X, and classified-claim inputs.

Rules:
- Harvest candidate features only from supplied evidence.
- If Phase X is absent, continue using D/C/F1 evidence only.
- Keep PM-plane features; do not filter them out because they are governance or workflow oriented.
- Every row in `FEATURE_CANDIDATES_RAW.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `L0`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_l1
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: L1
- short_name: L1 Feature Candidates Normalized
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/L1_feature_candidates_normalized.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: FEATURE_CANDIDATES_NORMALIZED.json, FEATURE_MERGE_LOG.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step L1 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder structure; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative feature normalizer. Output JSON only.

USER
Produce `L1` outputs from supplied raw feature candidates only.

Rules:
- Normalize naming conservatively.
- Under-merge is safer than over-merge.
- Never merge across different evidence classes unless the supplied evidence directly supports it.
- Preserve upstream evidence, temporal, and plane signals in normalized rows.
- `FEATURE_MERGE_LOG.json` must explain each merge deterministically.
- Sort all emitted items deterministically by `id`.

Return JSON matching schema `L1`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_l3
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: L3
- short_name: L3 Feature Ledger Routing
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/L3_feature_ledger_routing.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: FEATURE_LEDGER_ROUTING.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step L3 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder reasoned_plan; routing tier qa; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative ledger router. Output JSON only.

USER
Produce `L3` outputs from supplied normalized feature candidates and classified claim context.

Rules:
- Route each candidate to exactly one bucket: `canonical`, `historical_appendix`, `uncertain_appendix`, or `excluded_non_feature`.
- Keep this as the explicit v1 routing step; do not invent a hidden `L2`.
- Preserve PM-plane items whenever the evidence supports them.
- Use supplied evidence/status signals; do not silently upgrade historical or uncertain items into canonical.
- Sort items deterministically by `id`.

Return JSON matching schema `L3`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---

## Prompt
- prompt_id: rte_fl_int_l4
- canonical_scope: rte_fl_int
- version_line: registry_v1
- phase: FL_INT
- step: L4
- short_name: L4 Master Feature Ledger
- source_path: services/repo-truth-extractor/prompts/phase_fl_int/L4_master_feature_ledger.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/fl_int/run_fl_int.py:run_fl_int
- invokes: MASTER_FEATURE_LEDGER.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: FL_INT registry step L4 for design/feature synthesis and routing.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Ladder reasoned_plan; routing tier synthesis; separate runner from main PHASES list.

### Full prompt text
SYSTEM
You are a conservative feature-ledger assembler. Output JSON only.

USER
Produce `L4` outputs from supplied routing results and contradiction context.

Rules:
- Keep canonical, historical appendix, uncertain appendix, and excluded non-feature sections separate.
- Preserve contradiction references from `F2`.
- Include deterministic statistics, including `statistics.by_plane`.
- If PM-plane items are present upstream, `statistics.by_plane.pm` must remain non-zero.
- Keep missing evidence explicit.

Return JSON matching schema `L4`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}

---
