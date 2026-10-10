---
id: onepager-docs-system
title: One-Pager — Dopemux Docs System
type: tutorial
owner: @hu3mann
status: active
last_review: 2025-09-19
next_review: 2025-12-18
---

**Goal:** A tiny, durable set of docs that always loads the right context in Claude Code.

**Shelves (Diátaxis):**
- Tutorials — onboarding paths.
- How-to — task recipes (imperative names).
- Reference — APIs, schemas, CLI, invariants (one per concept).
- Explanation — concepts & **Feature Hubs** (each hub links RFCs, ADRs, How-tos, Reference).

**Design/Architecture:** arc42 sections + C4 diagrams under `94-architecture/`.

**Decisions:** one ADR per decision; link from touching docs.

**Workflow by phase:**
- Brainstorm: create an **RFC** under `91-rfc/` (+ raw notes in `_research-log/` with 30-day TTL).
- Design: finalize ADR; update arc42 & C4; update Reference.
- Implementation: add/modify **How-to**; run `/doc:pull "<ticket>"`.
- Ship: Conventional Commits → curate **CHANGELOG.md** (Keep a Changelog).
- Operate: **Runbooks** short & specific; link dashboards.

**Rules to avoid bloat:**
- One Reference per concept; one How-to per task (+ platform variants).
- Every doc has `owner` + `next_review`. Stale? fix or archive.
- Reorgs via `/doc:move` so links & indexes update.
- Everything cross-links through the **Feature Hub** + `_manifest.yaml`.

**Daily loop:** `/doc:pull` → code → update ADR/How-to → `pre-commit run -a` → commit.
