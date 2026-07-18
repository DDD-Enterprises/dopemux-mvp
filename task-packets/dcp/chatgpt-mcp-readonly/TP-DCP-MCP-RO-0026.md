---
id: TP-DCP-MCP-RO-0026
title: V1 Project-Id Surface Retirement (Optional)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: Consumer sweep then removal or quarantine of the v1 facade modules; intentional-deletion labelled.
---

# TP-DCP-MCP-RO-0026 - V1 Project-Id Surface Retirement (Optional)

Objective: Retire the v1 project_id facade surface (OPTIONAL cleanup; not on the READY critical path): confirm no remaining consumers of registry.py/resolver.py/tools.py v1 modules beyond tests, mark them internal-legacy or remove them with their v1-only tests, and record the migration completion in REGISTRY_V2_CONTRACT.md.

Depends on: TP-DCP-MCP-RO-0020. Executor: codex.

See the JSON load packet for invariants, validation commands, and step detail.
