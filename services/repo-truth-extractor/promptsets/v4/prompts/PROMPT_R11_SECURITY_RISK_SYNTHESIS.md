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
