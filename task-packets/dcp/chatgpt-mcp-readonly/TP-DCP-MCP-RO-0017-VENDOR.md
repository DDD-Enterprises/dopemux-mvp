---
id: TP-DCP-MCP-RO-0017-VENDOR
title: Vendor-Live Preflight And Two-Target Isolation
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Vendor-live residual preflight and synthetic ACC-029 isolation for DCP multi-provider series.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0017-VENDOR

## Objective

Advance residual vendor-live track without inventing credentials or opening
unrestricted public tunnels.

## Outcome this packet

- ACC-029 synthetic two-target isolation: **PASS**
- ACC-024/025/026: **NOT_RUN** with explicit missing inventory
- `release_ready`: still **false**

## Required next operator inputs

See `VENDOR_LIVE_PREFLIGHT.md`.
