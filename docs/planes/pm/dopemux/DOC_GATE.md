---
id: DOC_GATE
title: Doc Gate
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-14'
prelude: Doc Gate (explanation) for dopemux documentation and developer workflows.
---
# Doc Gate Spec (v0 skeleton)

## Purpose
Define a mechanical gate that prevents doc drift, broken references, and responsibility leakage across the TaskX vs Dopemux Supervisor boundary.

## Scope
- Verifies the doc bundle under: docs/planes/pm/dopemux/
- Enforces research requirements in: docs/planes/pm/dopemux/research/
- Enforces headings, links, UNKNOWN discipline, and boundary rules
- Does not attempt semantic correctness beyond simple regex rules in v0

## Non-negotiable invariants
- Gate failure stops implementation work.
- No invented facts: unknowns must be labeled and listed.
- TaskX remains deterministic and "boring" (no policy/memory/MCP intelligence ownership).

## Inputs
- Docs in docs/planes/pm/dopemux/
- Optional config (future): docs/planes/pm/dopemux/doc_gate_rules.json

## Checks

### 1) Presence
- All required files exist (00..10)
- No extra “shadow” copies in other roots unless explicitly linked from 00_INDEX

### 2) Headings (exact)
Every doc must include:
- ## Purpose
- ## Scope
- ## Non-negotiable invariants
- ## FACT ANCHORS (Repo-derived)
- ## Open questions

### 3) Title uniqueness
- Parse first line "# ..." from each doc
- Titles must be unique

### 4) Link integrity
- Parse markdown links in 00_INDEX.md
- Every relative link resolves to an existing file
- No link points outside docs/planes/pm/dopemux/ unless explicitly allowed in allowlist

### 5) UNKNOWN discipline
- "UNKNOWN" may appear only under:
- "## FACT ANCHORS (Repo-derived)"
- "## Open questions"
- For every UNKNOWN token, Open questions must contain a bullet that describes:
- what is unknown
- how to resolve (file path or command to run)

### 6) Boundary enforcement (regex v0)
Hard rule: TaskX must not be described as owning any of these responsibilities:
- memory, conport writes, promotion logic
- routing intelligence, cost optimization, limit tracking policy
- MCP lifecycle management

Implementation: grep/rg for "TaskX" in docs and fail if "TaskX" appears within N lines of any forbidden ownership verbs:
- "owns", "manages", "decides", "chooses", "optimizes", "persists", "starts MCP", "tracks limits"
Exception: 07_TASKX_INTEGRATION.md may mention these only to explicitly deny ownership.

### 7) FACT ANCHORS hygiene (v0)
- FACT ANCHORS section must be non-empty in every doc
- Each bullet should include at least one of:
- component name
- service directory
- config path
- env var
- CLI surface
- port/offset info
- Encourage `path:line-range` pointers when available (warning if absent, not hard fail in v0)

### 8) Open questions are actionable
- Open questions section must be non-empty
- Each open question should specify a resolution action:
- command to run, or file to inspect

## Outputs
- Human-readable report:
- PASS/FAIL
- Failed checks list
- File/heading that failed
- Machine output (future):
- docs/planes/pm/dopemux/DOC_GATE_REPORT.json (canonical JSON)

## Stop conditions
- If presence or headings fail: stop immediately.
- If boundary enforcement fails: stop immediately.
- If link integrity fails: stop immediately.

## Acceptance criteria
- A new contributor can run the gate and know exactly what to fix.
- Gate prevents accidental responsibility creep into TaskX.
- Gate prevents "UNKNOWN sprawl" and forces actionable research tasks.
