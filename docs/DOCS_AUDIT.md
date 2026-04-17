# Docs Audit Report

**Date:** 2026-04-15
**Auditor:** Gemini CLI
**Target:** Dopemux MVP User-Facing Documentation

## Objective
To align user-facing documentation with the strict repository truth established by `ARCHITECTURE.md`, `PM_PLANE.md`, `PROJECT.md`, `BRAND_SYSTEM.md`, `SERVICE_CATALOG.md`, and `SYSTEM_BOUNDARIES.md`.

## Summary of Changes

### Files Updated/Created

1. **`README.md`**
   - **Action:** Completely rewritten from scratch.
   - **Rationale:** The old README contained massive amounts of visionary fluff ("AI magic", "supercharged"), blurred the lines of authority, claimed a unified single platform, and presented inaccurate routing details. The new README reflects the composed multi-system workspace, correctly names the planes (Leantime, ConPort, task-orchestrator, dope-memory, dopecon-bridge, adhd_engine, repo-truth-extractor), and enforces the brand system's literal, calm tone.

2. **`QUICKSTART.md`**
   - **Action:** Created/Rewritten to replace `QUICK_START.md`.
   - **Rationale:** The old `QUICK_START.md` was highly specific to a narrow ADHD-stack testing loop that relied on manually injecting Redis events. The new `QUICKSTART.md` provides a broader, credible path to starting the `compose.yml` stack, running health audits against the bridge and orchestrator, and testing core boundaries.

3. **`docs/marketing/FEATURES_AND_BENEFITS.md`**
   - **Action:** Created new marketing material.
   - **Rationale:** The user requested marketing collateral that adheres strictly to repo truth without hype. This document outlines the value of a split-plane architecture, chronicle memory, and bridge-mediated integration, targeting system operators.

### Files Intentionally Left Alone / Removed
- **`QUICK_START.md` (Legacy):** Marked for deletion/deprecation in favor of the unified `QUICKSTART.md`.
- **`docs/03-reference/systems/*`**: Left alone as they are the source of truth used to inform this audit.
- **`TRUTH_*.md` files**: Left alone as they are the foundational extraction artifacts.

## Contradictions and Drift Found

During the audit, the following contradictions were identified between the old documentation and the runtime truth:
- **Monolith Illusion:** Old docs implied a single unified Dopemux engine. Truth: Dopemux is a composed workspace with fragmented authority (PM is split across Leantime, task-orchestrator, ConPort).
- **Dopecon-Bridge Authority:** Old docs sometimes treated the bridge as the source of truth for custom data. Truth: It is an adapter/proxy only.
- **Statusline Fluff:** Old README contained extensive, overly conversational breakdowns of statusline icons. This violated the `BRAND_SYSTEM.md` mandate for precise, technical language.
- **Extractor Reality:** Old docs pointed to `dopemux truth` as the primary path. Truth: `run_extraction_v5.py` is the canonical extractor runtime; `dopemux truth` relies on legacy `PipelineRunner`.

## Unresolved Truth Gaps (Requires Human Adjudication)

The following areas remain ambiguous in the repository and cannot be definitively documented until runtime code is resolved:

1. **Agent System Ownership:** Authority is split across `services/agents`, `src/dopemux/agent_orchestrator.py`, and `services/task-orchestrator/task_orchestrator/agents`. There is no single canonical agent runtime.
2. **Serena Implementation:** Operational compose wiring uses the Docker wrapper (`docker/mcp-servers/serena/`), while substantial implementation code exists in `services/serena`. Canonical authority is ambiguous.
3. **Task-Orchestrator Runtime Path:** Deployment authority is heavily conflicted. Code points to `app/main.py`, Docker targets point elsewhere, and legacy `task_orchestrator/app.py` is hard-failing.
4. **ConPort Access Contracts:** PM layers split their read contracts between port `3004` (ConPortAdapter) and port `3005` (ConPortClient), representing an internal integration fracture.
5. **Legacy Systems:** Status of `services/dope-query`, `services/taskmaster`, and `dopemux truth` (v4 PipelineRunner vs v5) require formal deprecation or removal.
