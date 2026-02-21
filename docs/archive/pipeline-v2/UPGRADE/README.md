---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Gemini Flash v2 Prompt Pack - Dopemux Comprehensive Extraction

This directory contains upgraded prompts for Gemini Flash 2.0 that enforce:
- **Single universal item schema** (kills normalization headaches)
- **Strict line_range discipline** (kills traceability gaps)
- **Bounded extraction** (caps at 200 items/file, deterministic ordering)
- **No-judgment language constraints** (forbidden words list)
- **Domain tags** (makes normalize trivial)

## What This Fixes

### Three Big Failure Modes (SOLVED):
1. ✅ **Inconsistent item shapes across batches** → Universal schema enforced
2. ✅ **Missing line ranges / missing symbols** → Confidence + missing_fields tracking
3. ✅ **Accidental inference** → Forbidden words: "means", "likely", "should", "correct", "wrong", "best", "problem", "bug"

## Files in This Pack

### Core Schema
- **`00_UNIVERSAL_SCHEMA_HEADER.md`** - Include at top of EVERY Flash job

### Code Extraction Prompts (A-F)
- **`PROMPT_A_STRUCTURE_SERVICES_ENTRYPOINTS.md`** - Structure map, services, entrypoints
- **`PROMPT_B_INTERFACES.md`** - CLI, API, MCP, Hooks surfaces
- **`PROMPT_C_EVENTS.md`** - Event emitters, consumers, envelope fields
- **`PROMPT_D_DB_SURFACE.md`** - DB tables, migrations, DAOs
- **`PROMPT_E_ENV_CONFIG_SECRETS.md`** - Env vars, config loaders, secrets risks
- **`PROMPT_F_RISK_SCAN.md`** - Determinism, concurrency, idempotency risks

### Documentation Extraction (Phased Pipeline)
- **`PHASED_PIPELINE_GUIDE.md`** - Complete execution guide for doc extraction
- **`DOC_PARTITION_PLAN.md`** - 17-partition plan with concrete folder mappings
- **`DOC_OUTPUT_SCHEMAS.md`** - All JSON output schemas
- **`PROMPT_D0_INDEX_PARTITION.md`** - Phase 0: Inventory & partition
- **`PROMPT_D1_NORMATIVE_EXTRACTION.md`** - Phase 1: Claims, boundaries (per partition)
- **`PROMPT_D2_DEEP_EXTRACTION.md`** - Phase 2: Interfaces, workflows (CAP_NOTICES only)
- **`PROMPT_D3_CITATION_GRAPH.md`** - Phase 3: Cross-doc references
- **`PROMPT_M1_MERGE_NORMALIZE.md`** - Merge all partNN.json files
- **`PROMPT_QA_COVERAGE_REPORT.md`** - Coverage verification & quality gates
- **`PROMPT_CL_TOPIC_CLUSTERS.md`** - Token-based topic clustering
- **`PROMPT_G_DOCS_DEEP_EXTRACTION.md`** - ⚠️ DEPRECATED (single-pass approach)

### Priority Phases (Run First)
- **`PROMPT_I1_INSTRUCTION_INDEX.md`** - Index LLM instruction/control plane files
- **`PROMPT_I2_TOOLING_REFERENCES.md`** - Extract MCP/tool/server references
- **`PROMPT_I3_POLICY_GATES.md`** - Extract policy gates from instruction files
- **`PROMPT_W1_OPS_WORKFLOW_SURFACE.md`** - Extract compose/script workflows
- **`PROMPT_W2_LLM_WORKFLOW_CUES.md`** - Extract workflow sequences from instructions
- **`PROMPT_W3_WORKFLOW_GRAPH.md`** - Build global workflow graph
- **`PROMPT_H_HOME_CONFIG.md`** - Extract home configs with redaction

### Executable Prompts (Ready to Run)
- **`EXEC_I1_INSTRUCTION_INDEX.md`** - ✨ Standalone I1 prompt
- **`EXEC_I2_TOOLING_REFERENCES.md`** - ✨ Standalone I2 prompt
- **`EXEC_W1_OPS_WORKFLOWS.md`** - ✨ Standalone W1 prompt
- **`EXEC_H_HOME_CONFIG.md`** - ✨ Standalone H prompt (with redaction)

### Automation
- **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
- **`RUNNER_README.md`** - Runner script documentation
- **`QUICKSTART.md`** - Quick start guide for manual execution
- **`COMPLETE_PIPELINE_GUIDE.md`** - Full pipeline with priority phases integrated

## Suggested Run Order (Fastest)

Run these in parallel batches if possible, or sequentially:

```
1. Prompt A (structure/services/entrypoints)
2. Prompt B (interfaces)
3. Prompt C (events)
4. Prompt D (db/migrations/dao)
5. Prompt E (env/config/secrets-risk)
6. Prompt F (determinism risks)
7. Prompt G (docs deep extraction)
```

Then run your Normalize pack (N1–N4) and hand to GPT-5.2.

## Target Paths (Dopemux-Specific)

All prompts are pre-configured for:
- **Working tree:** `/Users/hue/code/dopemux-mvp`
- **Baseline zip:** `dopemux-mvp-llm-20260206-074421.zip` (if present)
- **Doc corpus:** ~2,585 markdown files across:
  - `docs/**`
  - `.claude/docs/**`
  - `services/*/docs/**`
  - `docker/mcp-servers/docs/**`
  - `_audit_out/**/*.md`
  - `quarantine/2026-02-04/docs/**`

## Key Improvements

### 1. Deterministic IDs
```
id = domain + ":" + path + ":" + line_range[0] + ":" + name
```
No hashing, no UUIDs, no timestamps. Reruns are stable.

### 2. Cap Rule
If a single file yields >200 items, keep first 200 by line order and add:
```json
{
  "domain": "doc_meta",
  "kind": "cap_notice",
  "name": "cap_reached",
  "strings": ["kept:200", "dropped:<n>"]
}
```

### 3. Confidence Tracking
```json
{
  "confidence": "high|medium|low",
  "missing_fields": ["line_range"]
}
```

### 4. Forbidden Words
Never use: "means", "likely", "should", "correct", "wrong", "best", "problem", "bug"

## Usage

For each prompt:
1. Copy the **Universal Schema Header** (00_UNIVERSAL_SCHEMA_HEADER.md)
2. Append the specific prompt (A-G)
3. Paste into Gemini Flash 2.0
4. Save output JSON to your extraction directory

## Output Artifacts

### From Prompts A-F (Code):
- `STRUCTURE_MAP.json`
- `SERVICE_MAP.json`
- `ENTRYPOINTS.json`
- `CLI_SURFACE.json`
- `API_SURFACE.json`
- `MCP_SURFACE.json`
- `HOOKS_SURFACE.json`
- `EVENT_EMITTERS.json`
- `EVENT_CONSUMERS.json`
- `EVENT_ENVELOPE_FIELDS.json`
- `DB_SURFACE.json`
- `MIGRATIONS.json`
- `DAO_SURFACE.json`
- `ENV_VARS.json`
- `CONFIG_LOADERS.json`
- `SECRETS_RISK_LOCATIONS.json`
- `DETERMINISM_RISKS.json`

### From Prompt G (Docs):
- `DOC_INDEX.json`
- `DOC_CLAIMS.json`
- `DOC_BOUNDARIES.json`
- `DOC_WORKFLOWS.json`
- `DOC_SUPERSESSION.json`
- `DOC_GLOSSARY.json`

## Next Steps

After extraction, run your normalization pipeline (N1-N4) to:
1. Deduplicate across batches
2. Resolve conflicts
3. Build canonical maps
4. Hand to GPT-5.2 for arbitration

---

**Created:** 2026-02-15  
**Target:** dopemux-mvp comprehensive extraction  
**Flash Version:** Gemini Flash 2.0
