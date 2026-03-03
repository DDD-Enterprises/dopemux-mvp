---
id: CODEX
title: Codex
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-25'
last_review: '2026-02-25'
next_review: '2026-05-26'
prelude: Codex (explanation) for dopemux documentation and developer workflows.
---
# CODEX Instructions

<!-- TASKX:BEGIN -->
<!-- directive-pack:taskx@v1 -->
## TaskX Directives (Base)

1. Task packets are law.
2. Perform only actions explicitly authorized by the active task packet.
3. Scope is strict: no drive-by refactors, no opportunistic cleanup, no hidden extra work.
4. Treat allowlists, file scopes, and verification gates as hard requirements.
5. Use evidence-first reasoning for every claim.
6. Never fabricate command runs, outputs, file states, tests, or approvals.
7. If evidence is missing, mark the claim `UNKNOWN` and define a deterministic check.
8. Verification is mandatory for completion.
9. Record verification with the exact commands run and raw outputs.
10. Do not summarize away failing output; include failure details and exit codes.
11. Deterministic operation is required:
12. Do not claim a command was run unless its output is present in logs.
13. Do not claim a file changed unless the diff reflects it.
14. Use minimal diffs and localized edits.
15. Keep behavior stable unless the packet explicitly authorizes a behavior change.
16. Keep assumptions explicit and testable.
17. Do not invent requirements, contracts, schemas, or policy text.
18. Respect stop conditions exactly as written in the packet.
19. Escalate immediately when blocked by missing artifacts, permissions, or contradictory instructions.
20. Escalation must include:
21. What is blocked.
22. Why it is blocked.
23. The smallest packet change needed to proceed.
24. Completion requires an Implementer Report with:
25. Summary of changes.
26. Files changed and added.
27. Verification commands and raw outputs.
28. Deviations from packet instructions (if any).
29. Explicit stop-condition confirmation.
30. If any required gate was not run, report incomplete and stop.
<!-- TASKX:END -->
<!-- CHATX:BEGIN -->
<!-- directive-pack:chatx@v1 -->
## ChatX Directives (Add-on, Minimal)

This pack is additive.
This pack does not override TaskX pack; if conflict, TaskX wins.

1. Case Bundle audit mode requirements:
2. Perform deep audit of recent packets, runs, evidence artifacts, and repo logs.
3. Diagnose systemic issues, including repeated failures, policy drift, and verification gaps.
4. Prefer deterministic diagnosis first (counts, diffs, missing files, failed gates) before LLM inference.
5. Produce sequential task packets that target root causes, not symptoms.
6. Keep packet scopes narrow and verification steps explicit.
7. Supervisor must maintain these outputs:
8. `CASE_AUDIT_REPORT.md` for human-readable diagnosis.
9. `CASE_FINDINGS.json` for structured findings.
10. `PACKET_RECOMMENDATIONS.json` for deterministic next steps.
11. Packet queue sequencing:
12. Order recommendations so prerequisites execute before dependent fixes.
13. Avoid parallel packet recommendations when they touch the same ownership boundary.
14. Meta hygiene:
15. Never rewrite existing packet contract text unless explicitly authorized.
16. Localize changes to meta-layer guidance and audit artifacts.
17. Do not weaken TaskX verification and evidence requirements.
18. If evidence is insufficient:
19. Mark `UNKNOWN`.
20. List missing artifacts.
21. Recommend deterministic bundle re-export requirements.
22. Optional prompt-pack output is allowed only as additive guidance with no contract override.
<!-- CHATX:END -->

## Dopemux MCP Servers

Codex interfaces with Dopemux via the local MCP fabric listed in `docker/mcp-servers/SERVER_REGISTRY.md`. The servers below are grouped by their defined roles so you can target the right authority when issuing MCP calls.

### Critical Path
- **PAL apilookup** (`mcp-pal`, port `3003`, `/health`): authoritative documentation + API reference tool; mandatory first call for anything code-related.
- **PAL (multi-model orchestration)** (`mcp-pal`, port `3003`, `/health`): orchestrates GPT-5, Gemini, DeepSeek, and other models for complex reasoning and planning.
- **Sequential Thinking** (`mcp-mas-sequential-thinking`, port `3001`, port liveness check): multi-agent reasoning engine for architectural analysis and debugging.

### Workflow Servers
- **ConPort** (`mcp-conport`, port `3004`, `/health`): project memory/knowledge graph + decision authority.
- **Task Master AI** (`mcp-task-master-ai`, port `3005`, `/health`): PRD parsing, task breakdown, and requirements interpretation.
- **Task Orchestrator** (`mcp-task-orchestrator`, port `3014`, `/health`): dependency analysis, scheduling, and task planning with 37 specialized tools.
- **Serena** (`mcp-serena`, port `3006`, `/health`): ADHD-optimized LSP for code navigation, complexity scoring, and working memory.
- **Claude Context** (`mcp-claude-context`, port `3007`, `/health`): semantic code search and vector-based context retrieval.

### Research Servers
- **GPT Researcher (MCP)** (`mcp-gptr-mcp`, port `3009`, `/health`): autonomous deep research with multi-agent exploration and report generation.
- **GPT Researcher (STDIO proxy)** (`mcp-gptr-stdio`, stdio exec): lightweight helper container that spawns the STDIO-facing researcher MCP.
- **Exa** (`mcp-exa`, port `3008`, `/health`): fallback web research provider (use only when PAL apilookup lacks info).
- **MorphLLM Fast Apply** (`mcp-morphllm-fast-apply`, port `3011`, `/health`): pattern-based bulk edits and style/model migrations.
- **Desktop Commander** (`dopemux-mcp-desktop-commander`, port `3012`, `/health`): desktop automation, window/focus control, and screenshot capture for ADHD workflows.

### External Integrations
- **DopeconBridge** (`mcp-dopecon-bridge`, port `3016`, `/health`): two-plane coordination layer linking PM-plane (Task Master/Orchestrator/Leantime) with the cognitive plane (Serena/ConPort).
- **Leantime Bridge** (`dopemux-mcp-leantime-bridge`, port `3015`, `/health`): status authority and team coordination with the Leantime PM system.
- **Plane Coordinator** (`dopemux-mcp-plane-coordinator`, port `8090`, `/health`): API surface for cross-plane coordination, conflict detection, and metrics.
- **Leantime (project management)** (external network `leantime-net`, port `8080`): companion PM UI integrated through the Leantime Bridge.

Agent-specific rules are inserted in sentinel blocks only.
