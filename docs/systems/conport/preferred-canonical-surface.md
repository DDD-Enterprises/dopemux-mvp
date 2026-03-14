---
id: conport-preferred-canonical-surface
title: ConPort Preferred Canonical Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Preferred ConPort integration surface for PM-plane use, with transport roles for REST, FastMCP, and JSON-RPC.
---
# ConPort Preferred Canonical Surface

## Decision

The preferred canonical ConPort integration surface for the PM plane is **HTTP REST `/api/*`**.

## Why REST is preferred

- It exposes the broadest operational contract in one place.
- It is the surface the FastMCP wrappers are already translating into.
- It keeps PM-plane integrations tied to canonical resource routes instead of tool-wrapper naming drift.
- It makes payload/default alignment auditable and testable at the source contract.

## How the other surfaces fit

### FastMCP SSE and stdio

FastMCP remains the preferred **agent transport wrapper** over the same logical REST contract.

That means:

- agents may still consume FastMCP tools
- FastMCP wrappers must stay semantically aligned to REST
- wrapper drift is a bug, not a reason to create a second canonical contract

### JSON-RPC `/mcp`

JSON-RPC remains **compatibility-only** until tool discovery and payload parity are tightened.

It is not the preferred PM-plane integration contract because:

- discovery parity is incomplete
- some operations are dark or underdocumented
- callable parity is weaker than REST

## PM-plane implication

Any PM-plane adapter that needs ConPort should:

1. treat REST `/api/*` as the canonical backend contract
2. treat FastMCP as a wrapper over that contract
3. avoid choosing JSON-RPC as the primary integration seam until parity gaps are closed
