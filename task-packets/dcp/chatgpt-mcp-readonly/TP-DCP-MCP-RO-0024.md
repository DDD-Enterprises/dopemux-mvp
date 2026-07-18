---
id: TP-DCP-MCP-RO-0024
title: Vendor-Live Acceptance And Release Readiness
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: ChatGPT connector proof battery over an authenticated tunnel, real two-target isolation, release_ready evaluation.
---

# TP-DCP-MCP-RO-0024 - Vendor-Live Acceptance And Release Readiness

Objective: Execute the vendor-live acceptance residual (TP-0017/0017-VENDOR ACC-024..026 + real ACC-029): operator-consented authenticated HTTPS tunnel to the loopback ingress, ChatGPT Web connector discovery and the full connector proof battery (list_targets, target repo snapshot, proof listing, memory query, blocked wrong-project query, blocked mutation, redaction verification, no infrastructure identifiers), real two-target isolation, optional Grok/Gemini secondary routes, and flip release_ready only if every blocking gate passes.

Depends on: TP-DCP-MCP-RO-0019, TP-DCP-MCP-RO-0023. Executor: shell.

See the JSON load packet for invariants, validation commands, and step detail.
