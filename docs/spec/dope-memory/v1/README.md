---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Dope-Memory v1 Specification

Complete specification for the Dope-Memory temporal chronicle and working-context manager.

## Documents

| File | Description |
|------|-------------|
| [00_overview.md](./00_overview.md) | Purpose, principles, and cognitive tiers |
| [01_architecture.md](./01_architecture.md) | Service responsibilities and component diagram |
| [02_data_model_sqlite.md](./02_data_model_sqlite.md) | SQLite canonical schema (local-first) |
| [03_data_model_postgres.md](./03_data_model_postgres.md) | Postgres mirror schema |
| [04_event_taxonomy.md](./04_event_taxonomy.md) | Event types and envelope format |
| [05_promotion_redaction.md](./05_promotion_redaction.md) | Redaction rules and promotion logic |
| [06_retrieval_ranking.md](./06_retrieval_ranking.md) | Search and deterministic ranking |
| [07_mcp_contracts.md](./07_mcp_contracts.md) | MCP tool request/response schemas |
| [08_phased_roadmap.md](./08_phased_roadmap.md) | Phase 0-4 delivery plan |
| [09_test_plan.md](./09_test_plan.md) | Unit, integration, and security tests |
| [10_risk_register.md](./10_risk_register.md) | Risk identification and mitigations |

## Quick Reference

**Memory Trinity:**
- DopeContext → Semantic archival ("What did we do last month?")
- DopeQuery → Structured graph ("Why are these connected?")
- Dope-Memory → Temporal chronicle ("What am I doing right now?")

**Non-Negotiables:**
1. No duplication across Trinity
1. Top-3 default, explicit expand only
1. Redact before persist (fail closed)
1. SQLite canonical, Postgres mirror
1. Deterministic outputs (stable ordering)

## Version History
- v1: Initial specification (2026-02-02)
