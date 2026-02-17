---
id: PROMPT_G_DOCS_DEEP_EXTRACTION
title: Prompt G Docs Deep Extraction
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt G Docs Deep Extraction (explanation) for dopemux documentation and
  developer workflows.
---
# Prompt G (v2): Docs deep extraction (claims, boundaries, workflows, supersession)

> [!WARNING]
> **DEPRECATED:** This single-pass approach has been replaced by the **Phased Documentation Extraction Pipeline** (D0→D1→D2→D3→M1→QA→CL).
> 
> **Why replaced:**
> - Single-pass hits context limits on large corpora (~2,585 files)
> - No explicit tracking of skipped/truncated docs (silent detail loss)
> - No partitioning for parallel execution
> 
> **Use instead:**
> - See `PHASED_PIPELINE_GUIDE.md` for complete extraction pipeline
> - See `DOC_PARTITION_PLAN.md` for 17-partition execution plan
> - This file retained for reference only

---

# LEGACY: Single-Pass Docs Extraction

**Outputs:** `DOC_INDEX.json`, `DOC_CLAIMS.json`, `DOC_BOUNDARIES.json`, `DOC_WORKFLOWS.json`, `DOC_SUPERSESSION.json`, `DOC_GLOSSARY.json`

---

## TASK

Produce SIX JSON files: `DOC_INDEX.json`, `DOC_CLAIMS.json`, `DOC_BOUNDARIES.json`, `DOC_WORKFLOWS.json`, `DOC_SUPERSESSION.json`, `DOC_GLOSSARY.json`.

## TARGET

dopemux doc corpus at `/Users/hue/code/dopemux-mvp`

### Primary doc directories (exclude node_modules, .venv, .git):
- `docs/**`
- `.claude/docs/**`
- `services/adhd_engine/docs/**`
- `services/task-orchestrator/docs/**`
- `services/working-memory-assistant/docs/**`
- `docker/mcp-servers/docs/**`
- `_audit_out/**/*.md`
- `quarantine/2026-02-04/docs/**`
- `scripts/docs_audit/**`

**Total markdown files:** ~2585 files

## DOC_INDEX.json

- `path`, `sha256`, `title`, `headings` (H1-H3), `dates`, `status markers`, 3 anchor quotes with line ranges.

## DOC_CLAIMS.json

- Extract atomic claims containing: MUST, MUST NOT, SHOULD, REQUIRED, INVARIANT, SINGLE SOURCE OF TRUTH, FAIL-CLOSED, APPEND-ONLY, DEFAULT, DETERMINISTIC.
- Emit items:
  - `domain=doc_claim`
  - `kind=doc_claim`
  - `name=<short label derived from first 8 words>`
  - `strings` include keywords matched.

## DOC_BOUNDARIES.json

- Extract explicit ownership/boundary statements (authoritative, only X may, forbidden overlaps, etc.)
- `domain=doc_boundary`

## DOC_WORKFLOWS.json

- Extract step sequences under workflow headings.
- `domain=doc_workflow`

## DOC_SUPERSESSION.json

- Extract "supersedes", "deprecated", version chains, dates.
- `domain=doc_meta`

## DOC_GLOSSARY.json

- Extract defined terms and their definitions with citations.
- `domain=doc_meta`

## RULES

- No deciding which doc wins.
- Universal schema + deterministic sorting.
