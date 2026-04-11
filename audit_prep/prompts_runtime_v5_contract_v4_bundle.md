# Prompt Bundle: Runtime v5 / Contract v4 Authority Bundle

## Prompt
- prompt_id: rte_contract_promptset_rules
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: CONTRACT
- step: UNKNOWN
- short_name: Promptset Rules
- source_path: services/repo-truth-extractor/promptsets/v4/PROMPTSET_RULES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/promptsets/v4/
- invokes: Promptset policy interpretation
- status: active
- authority_role: contract_authority
- prompt_kind: template
- category: tool_orchestration
- purpose: Contract/policy text that shapes the active v4 promptset used by the v5 runtime.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Included to preserve the runtime-v5 / contract-v4 authority split explicitly.

### Full prompt text
# REPO TRUTH EXTRACTOR — V5 PROMPTSET RULES

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

---

## Prompt
- prompt_id: rte_contract_manual_pro_collision_policy
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: CONTRACT
- step: UNKNOWN
- short_name: Manual Pro Collision Policy
- source_path: services/repo-truth-extractor/promptsets/v4/manual/MANUAL_PRO_COLLISION_POLICY.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/promptsets/v4/
- invokes: Promptset policy interpretation
- status: active
- authority_role: contract_authority
- prompt_kind: template
- category: tool_orchestration
- purpose: Contract/policy text that shapes the active v4 promptset used by the v5 runtime.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Included to preserve the runtime-v5 / contract-v4 authority split explicitly.

### Full prompt text
# MANUAL_PRO_COLLISION_POLICY

ROLE: GPT-5.2-pro artifact collision policy judge.
MODE: JSON-only ruling, deterministic, short.

INPUT:
- Artifact collision context.
- Candidate writer steps.
- Risk/conflict anchors from R7 and R8.

RULES:
1) Output JSON only.
2) Choose a policy that is mechanically enforceable.
3) Include acceptance tests with expected signals.
4) Use `UNKNOWN` values when evidence is missing.

OUTPUT SCHEMA:
{
  "artifact_name": "XYZ.json",
  "policy": "LATEST_WINS|APPEND_LEDGER|MERGE_BY_ID|UNKNOWN",
  "canonical_key": "id",
  "required_item_keys": ["id", "path", "line_range"],
  "dedup_rule": "KEEP_MOST_EVIDENCED|KEEP_NEWEST|KEEP_HIGHEST_CONFIDENCE|UNKNOWN",
  "acceptance_tests": [
    {"test": "...", "expected_signal": "..."}
  ],
  "risks": [
    {"risk": "...", "evidence": ["R8_RISK_REGISTER_TOP20.md#..."]}
  ]
}

---

## Prompt
- prompt_id: rte_contract_manual_pro_conflict_ruling
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: CONTRACT
- step: UNKNOWN
- short_name: Manual Pro Conflict Ruling
- source_path: services/repo-truth-extractor/promptsets/v4/manual/MANUAL_PRO_CONFLICT_RULING.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/promptsets/v4/
- invokes: Promptset policy interpretation
- status: active
- authority_role: contract_authority
- prompt_kind: template
- category: tool_orchestration
- purpose: Contract/policy text that shapes the active v4 promptset used by the v5 runtime.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Included to preserve the runtime-v5 / contract-v4 authority split explicitly.

### Full prompt text
# MANUAL_PRO_CONFLICT_RULING

ROLE: GPT-5.2-pro appellate conflict judge.
MODE: JSON-only ruling, terse, evidence-bounded.

INPUT:
- One conflict entry from `R7_CONFLICT_LEDGER.md`.
- Exact evidence snippets/anchors for both sides.

RULES:
1) Output JSON only. No prose outside JSON.
2) If evidence is insufficient, return `decision: "DEFER"`.
3) Every reason bullet must include one or more evidence anchors.
4) Never invent artifacts, anchors, or side claims.

OUTPUT SCHEMA:
{
  "conflict_id": "CONFLICT-...",
  "decision": "ACCEPT_DOC|ACCEPT_CODE|SPLIT_SCOPE|DEFER",
  "winner": {
    "side": "DOC|CODE|BOTH|NONE",
    "reason_bullets": [
      {"bullet": "...", "evidence": ["R?.md#..."]}
    ]
  },
  "scope_notes": ["..."],
  "required_followups": [
    {"need": "...", "missing_evidence": ["R?.md#..."]}
  ]
}

---

## Prompt
- prompt_id: rte_contract_manual_pro_risk_rerank
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: CONTRACT
- step: UNKNOWN
- short_name: Manual Pro Risk Rerank
- source_path: services/repo-truth-extractor/promptsets/v4/manual/MANUAL_PRO_RISK_RERANK.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/promptsets/v4/
- invokes: Promptset policy interpretation
- status: active
- authority_role: contract_authority
- prompt_kind: template
- category: tool_orchestration
- purpose: Contract/policy text that shapes the active v4 promptset used by the v5 runtime.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Included to preserve the runtime-v5 / contract-v4 authority split explicitly.

### Full prompt text
# MANUAL_PRO_RISK_RERANK

ROLE: GPT-5.2-pro risk rerank judge.
MODE: JSON-only output, short, evidence-bounded.

INPUT:
- Risk rows and evidence anchors from `R8_RISK_REGISTER_TOP20.md`.

RULES:
1) Output JSON only.
2) Re-rank severity only when evidence supports change.
3) If insufficient evidence, keep prior severity and mark rationale as `UNKNOWN`.
4) Keep bullets concise and anchor-cited.

OUTPUT SCHEMA:
{
  "rerank": [
    {
      "risk_id": "RISK-...",
      "new_severity": "low|med|high|critical|unknown",
      "why_bullets": [
        {"bullet": "...", "evidence": ["R?.md#..."]}
      ]
    }
  ],
  "notes": ["..."]
}

---
