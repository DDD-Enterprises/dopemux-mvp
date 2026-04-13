---
id: ADR-011-local-first-data
title: Adr 011 Local First Data
type: explanation
owner: '@hu3mann'
last_review: '2025-09-26'
next_review: '2025-12-25'
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
