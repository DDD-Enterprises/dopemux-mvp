---
id: claude-mem-phase0
title: Claude Mem Phase0
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: Claude Mem Phase0 (reference) for dopemux documentation and developer workflows.
---
Dope-Memory v1 Phase 0 Audit Plan
Dopemux Paths to Scan
Based on the extracted Dopemux repository, the following directories are candidates for inspection of memory/context functionality. These include services and tools related to memory management, context portal, and persistence:
services/conport/ – Context Portal service
services/conport_kg_ui/ – Context Portal (Knowledge Graph UI) service
services/shared/conport_client/ – Shared client for Context Portal
services/working-memory-assistant/ – Working memory assistant (Dope-Memory) service and subfolders (e.g. /ui/, /mcp/)
services/dope-context/ – Semantic archive (DopeContext) service
services/dope-query/ – Structured query/graph (DopeQuery) service
services/mcp-client/ – MCP client service (used by memory tools)
src/dopemux/mcp/ – Internal MCP server implementations
tools/ – Utility tools directory (might contain scripts related to memory)
scripts/memory/ – Memory-related scripts (test or utility scripts)
services/dddpg/storage/migrations/sqlite/ – SQLite migration scripts (canonical schema)
Each of these paths should be scanned for classes, functions, and data models implementing the memory/context logic (e.g. chronicle storage, context linking, memory querying, etc.).
Claude-Mem Web Query Plan
To understand Claude-Mem’s architecture and patterns, we will run targeted web searches. Key queries include:
“thedotmack claude-mem 3-layer workflow”
“claude-mem implementation details GitHub”
“claude-mem token-efficient memory pipeline”
“claude-mem data model schema”
“claude-mem memory retrieval ranking algorithm”
“claude-mem deterministic outputs stable ordering”
“claude-mem integration boundaries”
“anthropic claude memory context design”
“olivaw claude-mem GitHub fork”
“claude-mem persistent memory architecture”
These queries aim to uncover Claude-Mem’s GitHub or documentation pages, technical write-ups, design patterns (e.g. “4 MCP tools” or “3-layer workflow”), data schemas, assumptions about determinism, and any known forks (such as “olivaw/claude-mem”).
Phase 0 Next Actions
Prepare code inspection: Unzip the repository and use code-browser or Python to navigate into each identified path. For example, run a Python script to list files under those directories for review.
Search for key terms: In each candidate path, search for occurrences of keywords like memory, context, chronicle, redact, persist, etc., to locate relevant implementations.
Examine architecture docs: Review the repository’s architecture documentation (e.g. 01_architecture.md) to understand component interactions and identify where memory/context modules plug in.
Plan Phase 1 deep scan: Based on the above, outline specific files and classes to open in Phase 1, such as context storage schemas, memory query handlers, and any integration with MCP tools.
(If needed) Use tools: If automated analysis is required, prepare commands (e.g. Python scripts using zipfile to parse source) to extract and examine code from the zip.
No immediate findings are reported at this stage; these steps set up the detailed code review and Claude-Mem research for Phase 1.
