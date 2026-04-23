# Repo Truth Extractor (RTE) Deep PAL Audit Report

**Audit ID:** DMX-RTE-AUDIT-2026-04-23  
**Date:** 2026-04-23  
**Verdict:** **CONDITIONAL_GO**

---

## 1. Executive Summary

The Repo Truth Extractor (RTE) implementation in `services/repo-truth-extractor/` is structurally robust and follows a modern, modular design. The canonical v5 runtime (`run_extraction_v5.py`) incorporates a mandatory pre-live validator gate that enforces strict safety, integrity, and readiness checks. The prompt architecture is mature, with explicit schemas and evidence-based extraction procedures. Model selection is appropriately tiered between logic-heavy and bulk-data tasks.

A **CONDITIONAL_GO** verdict is issued based on the presence of legacy drift in Phase S and the persistence of multiple legacy runtimes in the service directory, which pose minor operational risks but do not compromise the integrity of the v5 pipeline.

---

## 2. Audit Findings

### 2.1 Execution Logic and Runtime Path Integrity
- **Canonical Path:** The active execution path is `run_extraction_v5.py`. It correctly implements a fail-closed mechanism by requiring a PASS from the pre-live validator (`validate_pre_live_gate_v25.py`) before permitting live LLM execution.
- **Shadow Paths:** Multiple legacy runtimes (`v3`, `v4`, `run_extraction.py`) are still present in the directory. While not active in the v5 flow, they create potential for operator confusion and accidental invocation of unpatched logic.
- **Gate Behavior:** The validator enforces P0 checks including prompt integrity, API key availability, and critical test results.

### 2.2 Prompt Architecture and Canonicality
- **Canonical Surfaces:** `promptsets/v4/prompts/` contains the authoritative prompts.
- **Structure:** Prompts follow a strict template (Goal, Inputs, Outputs, Schema, Procedure) which enhances machine-readability and reduces fabrication risk.
- **Drift Risk:** Phase S still utilizes legacy prompts, whereas Phase SP uses the newer registry-backed system. This internal contradiction should be reconciled.

### 2.3 Model Selection and Routing Policy
- **Portfolio Fit:** The use of GPT-5 series models for critical extraction and Grok-4 for bulk tasks is well-aligned with their respective strengths in reasoning and data processing.
- **Routing Reliability:** Managed through `model_map.yaml`, which includes deterministic escalation ladders and comparison lanes.
- **Repair Behavior:** JSON salvage and repair mechanisms in `llm_runtime.py` are sophisticated and prioritize provenance over fabrication.

### 2.4 Operator UX and Observability
- **UX Fit:** The TUI provides excellent visibility into progress, status, and failures.
- **Observability:** Comprehensive event logging to JSONL allows for detailed post-run analysis and auditability.
- **Readiness:** Validator output is clear and provides actionable reason codes for NO_GO verdicts.

---

## 3. Blockers and Warnings

### Blockers
- **None.**

### Warnings
- **Phase S Legacy Usage:** Continued reliance on legacy prompts in Phase S creates a maintenance burden and slight drift risk.
- **Legacy Runtime Pollution:** Presence of v3/v4 scripts in the main service folder.
- **PAL Validation File Location:** The validator expects a PAL validation file which is not consistently located in the repository root.

---

## 4. Corrective Action Map

| ID | Severity | Task | Effort |
|:---|:---|:---|:---|
| CA-001 | MEDIUM | Migrate Phase S to registry-backed prompt architecture. | Low |
| CA-002 | LOW | Move legacy scripts (v3, v4, run_extraction.py) to `archive/`. | Low |
| CA-003 | MEDIUM | Define a canonical location for PAL validation artifacts. | Low |

---

## 5. Launch Readiness Checklist

- [ ] Environment variable `DPMX_LIVE_OK_ENV=1` is set.
- [ ] API keys for OpenRouter, XAI, and Gemini are verified.
- [ ] Run validator: `python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy cost`.
- [ ] Review `OFFLINE_GATE_RESULTS.json` for any unexpected conditions.
- [ ] Perform a full dry-run: `python services/repo-truth-extractor/run_extraction_v5.py --phase ALL --dry-run`.
- [ ] Verify cost preview output matches expected budget.

---

## 6. Audit Verdict

**VERDICT: CONDITIONAL_GO**

The system is ready for live execution provided that the operator follows the launch checklist and is aware of the legacy drift warnings. CA-002 should be addressed as a high-priority "housekeeping" task to prevent operational errors.
