---
id: 07_mcp_contracts
title: 07_Mcp_Contracts
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 07_Mcp_Contracts (explanation) for dopemux documentation and developer workflows.
---
# Dope-Memory v1 — MCP Tool Contracts

## Global Constraints
- All responses default Top-3.
- All inputs and outputs are ASCII normalized.
- All IDs are strings at MCP boundary (even if UUID inside).
- All timestamps returned are ISO8601 UTC strings.

## Tool: memory_search

### Request
```json
{
  "query": "string",
  "workspace_id": "string",
  "instance_id": "string",
  "session_id": "string|null",
  "filters": {
    "category": "string|null",
    "entry_type": "string|null",
    "workflow_phase": "string|null",
    "tags_any": ["string"],
    "time_range": "today|week|month|all"
  },
  "top_k": 3,
  "cursor": "string|null"
}
```

### Response
```json
{
  "items": [
    {
      "id": "string",
      "ts_utc": "string",
      "summary": "string",
      "category": "string",
      "entry_type": "string",
      "workflow_phase": "string|null",
      "outcome": "string",
      "importance_score": 1,
      "tags": ["string"],
      "links": {
        "decisions": ["string"],
        "files": [{"path":"string","action":"string"}],
        "commits": ["string"]
      }
    }
  ],
  "more_count": 0,
  "next_token": "string|null"
}
```

## Tool: memory_store

### Request
```json
{
  "workspace_id": "string",
  "instance_id": "string",
  "session_id": "string|null",
  "category": "planning|implementation|review|debugging|research|deployment|architecture|documentation",
  "entry_type": "manual_note|decision|blocker|resolution|milestone",
  "workflow_phase": "planning|implementation|review|audit|deployment|maintenance|null",
  "summary": "string",
  "details": "object|null",
  "reasoning": "string|null",
  "outcome": "success|partial|blocked|abandoned|in_progress|failed",
  "importance_score": 1,
  "tags": ["string"],
  "links": {
    "decisions": ["string"],
    "files": [{"path":"string","action":"string"}],
    "commits": ["string"],
    "chat_range": {"source":"string","pointer":"string"}
  }
}
```

### Response
```json
{
  "entry_id": "string",
  "created": true
}
```

## Tool: memory_recap

### Request
```json
{
  "workspace_id": "string",
  "instance_id": "string",
  "scope": "session|today|last_2_hours",
  "session_id": "string|null",
  "top_k": 3
}
```

### Response (Top-3 recap cards)
```json
{
  "trajectory": "string",
  "cards": [
    {"title":"string","summary":"string","entry_ids":["string"]}
  ],
  "more_count": 0
}
```

## Tool: memory_mark_issue
Marks a curated entry as an issue (or caused_issue).

### Request
```json
{
  "workspace_id": "string",
  "instance_id": "string",
  "issue_entry_id": "string",
  "description": "string",
  "confidence": 0.7,
  "evidence_window_min": 30,
  "tags": ["string"]
}
```

### Response
```json
{
  "issue_marked": true
}
```

## Tool: memory_link_resolution
Links an issue to a resolution entry.

### Request
```json
{
  "workspace_id": "string",
  "instance_id": "string",
  "issue_entry_id": "string",
  "resolution_entry_id": "string",
  "confidence": 0.8,
  "evidence_window_min": 30
}
```

### Response
```json
{
  "linked": true
}
```

## Tool: memory_replay_session
Returns a chronological replay of curated entries for a session with Top-3 default.

### Request
```json
{
  "workspace_id": "string",
  "instance_id": "string",
  "session_id": "string",
  "top_k": 3,
  "cursor": "string|null"
}
```

### Response
```json
{
  "items": [
    {
      "id": "string",
      "ts_utc": "string",
      "summary": "string",
      "category": "string",
      "entry_type": "string",
      "importance_score": 1
    }
  ],
  "more_count": 0,
  "next_token": "string|null"
}
```

## Output Determinism Notes
- memory_search ordering is deterministic per retrieval spec.
- memory_recap uses deterministic selection:
  - choose top 3 entries in scope by (importance_score desc, ts desc, id asc),
  - then render:
    - card1 = highest decision if present else highest entry
    - card2 = highest blocker/error if present else next
    - card3 = suggested_next derived from last entry_type:
      - if blocker/error exists -> "Resolve blocker: {summary}"
      - else -> "Continue: {summary}"
No LLM involvement in Phase 1 recap rendering.
