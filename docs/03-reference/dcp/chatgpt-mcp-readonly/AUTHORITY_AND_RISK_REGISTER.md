---
id: AUTHORITY_AND_RISK_REGISTER
title: Authority And Risk Register
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-11'
last_review: '2026-06-11'
next_review: '2026-09-09'
prelude: Authority And Risk Register (reference) for dopemux documentation and developer
  workflows.
---
# Authority And Risk Register

## Secure MCP Tunnel Threat Model

A ChatGPT-facing facade must expose narrow read-only tools, not raw local MCP tools. Every response needs source, freshness, authority label, and redaction state.

## Key Risks

- Prompt injection through docs, proof bundles, or retrieved code.
- Bridge/proxy authority confusion.
- Mutable routes that look read-like because they use POST for search/replay.
- Secret exposure from proof artifacts, environment examples, compose interpolation, or local auth stores.
- Stale proof and stale branch snapshots.
- ConPort progress/custom-data mutability.
- dope-memory chronicle evidence being confused with ConPort structured decision/progress authority.
- task-orchestrator read views being confused with transition/write authority.

## Minimum Safe Phase-1 Constraints

- Local-only facade process.
- Static backend allowlist.
- No POST/PUT/PATCH/DELETE unless implementation is proven side-effect-free and wrapped as read-only.
- No raw file access; use named evidence fetchers.
- Output redaction and max-size limits.
- Explicit `authority_label`, `freshness`, and `source_path` per result.

## Implementation Stop Conditions

- Secret risk cannot be bounded.
- Surface classification requires live mutating call.
- Runtime behavior cannot be classified from source/config/tests.
- Facade design would expose raw MCP tool access.
