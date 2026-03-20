---
id: DESIGN
title: Design
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Design (explanation) for dopemux documentation and developer workflows.
---
# UBERSLICER_DESIGN

This document captures the locked architecture and workflow for Dopemux UBERSLICER. It mirrors the design summary provided during planning and should remain the source of truth for agents implementing the queued pull requests.

## 1  Executive Summary

UBERSLICER is the memory‑harvesting daemon inside **DØPEMÜX**. It consumes chat, code and logs, slices them into schema‑locked `UltraBlocks`, and updates the manifest and devlog. Version 2 refactors the older `UBERSLICER-TFE` repo into a package (`dopemux_ultraslicer`) integrated with the main CLI.

Goals:

* zero‑drift memory engineaook
* 100× dev velocity via frictionless CLI and pre‑commit hooks
* terminal goblin aesthetics with dopamine banners
* async batch processing for OpenAI summarisation

## 2  System Architecture & File Structure

```text
repo-root/
├── src/
│   ├── dopemux_core/            # config, utils, logging, manifest
│   ├── dopemux_ultraslicer/     # UBERSLICER package code
│   └── dopemux_cli.py           # entrypoint
├── tests/
├── scripts/
├── docs/
└── pyproject.toml
```

Shared helpers live in `dopemux_core`; only this module writes to the manifest.

## 3  Core Ritual Flow

```text
input file → ultraslicer.slice() → validator.validate_blocks() → manifest.update() → devlog.log_dev()
```

The optional OpenAI batch engine extends this pipeline.

## 4  Compliance & Schema Enforcement

Schemas are bundled under `schemas/`. `validator.validate_block()` raises on missing fields or `needs-review` tags.

## 5  Manifest Discipline

`manifest.py` updates only when filesystem mutations are detected via the git hook. SHA‑256 and file size are recorded for cold reloads.

## 6  Dopamine UX

Colour scheme: black background, cyan dopamine, magenta filth. Banners show before major operations. Roast templates live in `docs/DopamineRoastAndLogTemplatesmd.md`.

## 7  Extensibility & Integration Points

Plugin loader via entry points `dopemux.plugins`. Async API driver: `api_interface.process_chunks_async(chunks, phases)`. Planned textual TUI will consume the manifest JSON.

## 8  MVP vs Phase 2

| Stage | Must-Have | Nice-To-Have |
| ----- | --------- | ------------ |
| MVP   | Deduped utils, CLI `dopemux slice`, manifest update, validator, OpenAI batch phase‑1 | async OpenAI, coloured banners, devlog search |
| Phase 2 | multi-file batch, LangChain re‑chunk, PR generator, Textual TUI | cloud sync, plugin marketplace |

## 9  Risk & Drift Analysis

* duplication drift from multiple util copies
* hard-coded paths break alt-env
* merge conflicts in utils blocked by CI
* API hallucination mitigated via validator

## 10  Example Output

```bash
$ dopemux slice README.md
☠️  ULTRASLICER — MAX CONTEXT EXTRACT (2 blocks, 0 drift)  [dopamine 7/10]
```

Yields YAML blocks under `tagged/`.

## 11  Onboarding & Handoff

1. `pip install -e .`
2. `pre-commit install`
3. Never modify `schemas/` or `prompts/`
4. Update manifest for new modules and add tests
5. Log `filth_event` on hallucination or drift
