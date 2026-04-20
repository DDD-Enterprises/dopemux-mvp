---
id: docs__DMPX IMPORT__dopemux-docs__architecture__09-decisions__ADR-011-local-first-data
title: Docs  Dmpx Import  Dopemux Docs  Architecture  09 Decisions  Adr 011 Local
  First Data
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-20'
last_review: '2026-04-20'
next_review: '2026-07-19'
prelude: Docs  Dmpx Import  Dopemux Docs  Architecture  09 Decisions  Adr 011 Local
  First Data (explanation) for dopemux documentation and developer workflows.
---
# ADR: Local-first core and sandboxed commands

Status: Accepted
Date: 2025-09-17

Decision
- Dopemux operates local-first by default; commands execute in a sandbox with least-privilege and explicit elevation for risky actions.

Context
- Users need privacy, offline capability, and safety. Many actions touch local files and tools.

Options
- Cloud-first orchestration; Hybrid; Local-first with sandbox (chosen).

Consequences
- Better privacy and responsiveness; requires clear elevation UX and audit trails; increased complexity for permission management.

Links
- V1 Architecture (Constraints, Crosscutting); V4 Security; V2 TUI (guardrail prompts)

Sources: docs/product/system-overview.md, docs/security/stride.md
