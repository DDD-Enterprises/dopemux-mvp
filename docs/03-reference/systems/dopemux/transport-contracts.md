---
id: transport-contracts
title: TUI Transport Contracts (U1.2-U1.7)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
decision_packet: 'TP-DMX-TUI-TRANSPORT-ARCHITECTURE-005'
---

# Transport Contracts: Seven Backend Services (U1.2-U1.7)

**Date**: 2026-04-23
**Status**: LOCKED (Immutable)
**Scope**: HTTP/RPC surface specifications for seven services: dope-context, task-orchestrator, leantime, conport, dope-memory, dopecon-bridge, dopetask
**Impact**: Multi-backend source wiring is unblocked. Build step 3 and build step 8 can proceed with frozen contracts.

---

## Overview

All seven service transports follow a **common contract envelope** with service-specific endpoint and semantics definitions:

### Common Contract Elements (All Seven Services)

| Element | Value | Rationale |
|---------|-------|-----------|
| **Protocol** | HTTP/JSON over HTTPS | TLS encryption required for production |
| **Authentication** | Bearer token | DOPEMUX_<SERVICE>_API_KEY from environment |
| **Pagination** | Cursor-based | page_token and max_results for scalable result streaming |
| **Idempotency** | X-Idempotency-Key header | Retry-safe; TUI state machine requires exactly-once semantics |
| **Error Format** | {error: string, code: string} | Consistent error handling across all seven services |

---

## U1.2: task-orchestrator Transport

**Purpose**: Workflow state transitions and state queries

**Authority**: Canonical source for work-item state machine (transitions, current state)

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **POST** | `/transitions/{id}` | Trigger state transition | Yes |
| **GET** | `/work-items/{id}/workflow` | Query current state and state history | N/A (read) |

### Request/Response Specification

#### POST /transitions/{id}
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "action": "string (e.g., 'start', 'pause', 'complete')",
  "metadata": {
    "triggered_by": "string (e.g., 'tui-packet-PKT-0481')",
    "reason": "string (optional)"
  }
}

Response (200 OK):
{
  "id": "string",
  "state": "string",
  "previous_state": "string",
  "timestamp": "ISO8601",
  "transitions_pending": integer
}

Response (409 Conflict):
{
  "error": "State transition not allowed from {current} to {requested}",
  "code": "INVALID_STATE_TRANSITION"
}

Response (400 Bad Request):
{
  "error": "X-Idempotency-Key header required",
  "code": "MISSING_IDEMPOTENCY_KEY"
}
```

#### GET /work-items/{id}/workflow
```json
Request headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "id": "string",
  "current_state": "string",
  "available_transitions": ["string"],
  "state_history": [
    {
      "state": "string",
      "timestamp": "ISO8601",
      "triggered_by": "string"
    }
  ],
  "pagination": {
    "page_token": "string (next page token, null if last page)",
    "page_size": integer
  }
}
```

### Pagination

- Use `?page_token=<token>&max_results=100` for state history pagination
- null page_token indicates end of result set
- Default max_results: 50

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 404: Work item not found
- 409: Invalid state transition
- 500: Service error

---

## U1.3: leantime Transport

**Purpose**: Task metadata updates and queries

**Authority**: Canonical source for task metadata (title, description, custom fields, tags)

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **PATCH** | `/tickets/{id}` | Update metadata | Yes |
| **GET** | `/tickets/{id}/metadata` | Query metadata | N/A (read) |

### Request/Response Specification

#### PATCH /tickets/{id}
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "title": "string (optional)",
  "description": "string (optional)",
  "custom_fields": {
    "[field_name]": "string (optional, repeated per field)"
  },
  "tags": ["string (optional)"]
}

Response (200 OK):
{
  "id": "string",
  "title": "string",
  "description": "string",
  "custom_fields": { ... },
  "tags": ["string"],
  "updated_at": "ISO8601"
}

Response (409 Conflict):
{
  "error": "Concurrent modification detected; ticket was updated by another source",
  "code": "CONCURRENT_MODIFICATION"
}
```

#### GET /tickets/{id}/metadata
```json
Request headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "id": "string",
  "title": "string",
  "description": "string",
  "custom_fields": {
    "[field_name]": "string"
  },
  "tags": ["string"],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "updated_by": "string"
}
```

### Pagination

- No pagination needed for metadata (single record per ticket)
- For multi-ticket operations, use GET /tickets?page_token=<token>&max_results=100

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 404: Ticket not found
- 409: Concurrent modification or invalid custom field
- 500: Service error

---

## U1.4: ConPort Transport

**Purpose**: Decision and progress entry writes; work-item context queries

**Authority**: Canonical source for decisions, progress tracking, and knowledge graph

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **POST** | `/progress-entries` | Create progress entry | Yes |
| **POST** | `/decisions` | Create decision entry | Yes |
| **GET** | `/work-items/{id}/context` | Query work-item context (linked decisions, progress, patterns) | N/A (read) |

### Request/Response Specification

#### POST /progress-entries
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "status": "string (TODO|IN_PROGRESS|DONE|BLOCKED)",
  "description": "string",
  "work_item_id": "string",
  "parent_id": "string (optional)",
  "linked_item_type": "string (optional, e.g., 'decision')",
  "linked_item_id": "string (optional)"
}

Response (201 Created):
{
  "id": "string",
  "status": "string",
  "description": "string",
  "created_at": "ISO8601",
  "work_item_id": "string",
  "linked_items": [...]
}
```

#### POST /decisions
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "summary": "string",
  "rationale": "string",
  "implementation_details": "string",
  "tags": ["string"],
  "linked_work_items": ["string (optional)"]
}

Response (201 Created):
{
  "id": "string",
  "summary": "string",
  "rationale": "string",
  "implementation_details": "string",
  "tags": ["string"],
  "created_at": "ISO8601"
}
```

#### GET /work-items/{id}/context
```json
Request headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "id": "string",
  "progress_entries": [
    {
      "id": "string",
      "status": "string",
      "description": "string",
      "created_at": "ISO8601"
    }
  ],
  "linked_decisions": [
    {
      "id": "string",
      "summary": "string",
      "relationship_type": "string"
    }
  ],
  "patterns": [
    {
      "id": "string",
      "name": "string"
    }
  ]
}
```

### Pagination

- GET /work-items/{id}/context: Use ?page_token=<token>&max_results=100 for large result sets
- Semantic search queries: POST /search with query and top_k parameters

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 404: Work item or decision not found
- 409: Duplicate entry (same idempotency key, different payload)
- 500: Service error

---

## U1.5: dope-memory Transport

**Purpose**: Append-only chronicle entries and timeline queries

**Authority**: Canonical source for immutable audit trail and event chronicle

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **POST** | `/chronicle-entries` | Append new chronicle entry (only operation) | Yes |
| **GET** | `/chronicle/{id}` | Query timeline entries | N/A (read) |

### Request/Response Specification

#### POST /chronicle-entries
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "event_type": "string (e.g., 'state_change', 'metadata_update', 'correction')",
  "content": "object (event-specific data)",
  "packet_id": "string (optional, link to PKT/PKB)",
  "work_item_id": "string",
  "supersedes_id": "string (optional, for corrections; points to prior entry being corrected)"
}

Response (201 Created):
{
  "id": "string",
  "event_type": "string",
  "content": { ... },
  "created_at": "ISO8601",
  "packet_id": "string (optional)",
  "work_item_id": "string",
  "supersedes_id": "string (optional)"
}

Response (409 Conflict):
{
  "error": "Invalid supersedes_id; referenced entry not found",
  "code": "INVALID_SUPERSEDES_REFERENCE"
}
```

#### GET /chronicle/{id}
```json
Request headers:
  Authorization: Bearer <token>

Response (200 OK):
{
  "id": "string",
  "timeline": [
    {
      "id": "string",
      "event_type": "string",
      "content": { ... },
      "created_at": "ISO8601",
      "packet_id": "string (optional)",
      "supersedes_id": "string (optional)"
    }
  ],
  "pagination": {
    "page_token": "string (next page token, null if last page)",
    "page_size": integer
  }
}
```

### Pagination

- Use ?page_token=<token>&max_results=100 for timeline pagination
- Results ordered by created_at (newest first)

### Append-Only Semantics

- **No PATCH or DELETE operations**. All corrections are new entries with supersedes_id.
- Clients must read the latest entry per packet_id to determine current pinned state (via supersedes_id chain).
- Example correction flow:
  1. Original entry: `{id: "E-1", event_type: "pin", packet_id: "PKT-0481", pinned_at: "2026-04-23T10:00:00Z"}`
  2. Correction entry: `{id: "E-2", event_type: "pin", packet_id: "PKT-0481", pinned_at: null, supersedes_id: "E-1"}`
  3. Current state: packet PKT-0481 is unpinned (E-2 supersedes E-1)

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 404: Chronicle not found
- 409: Invalid supersedes_id or event_type
- 500: Service error

---

## U1.6: dopecon-bridge Transport

**Purpose**: Policy-wrapped proxy to ConPort; adapter-only (not canonical)

**Authority**: None (adapter). Routes to canonical ConPort backend with role-gating enforcement.

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **POST** | `/proxy/conport` | Policy-wrapped forwarding to canonical ConPort | Yes |

### Request/Response Specification

#### POST /proxy/conport
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "action": "string (e.g., 'log_decision', 'log_progress')",
  "payload": { ... },
  "required_role": "string (optional; e.g., 'shift-Y' for operator)"
}

Response (200 OK):
{
  "result": { ... },  // Result from canonical ConPort
  "forwarded_to": "canonical-conport-backend",
  "proxy_timestamp": "ISO8601"
}

Response (403 Forbidden):
{
  "error": "Insufficient permissions; required role not present in session",
  "code": "PERMISSION_DENIED",
  "required_role": "string"
}

Response (422 Unprocessable Entity):
{
  "error": "Policy rejection; action not permitted by role-gating rules",
  "code": "POLICY_VIOLATION"
}
```

### Role-Gating Policy

- All writes require explicit role checking (e.g., shift-Y for operator permissions)
- dopecon-bridge enforces role constraints BEFORE forwarding to canonical ConPort
- No unauthorized escalation; adapter is stateless (no cached permissions)

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 403: Insufficient permissions (role-gating failure)
- 404: Action not found in canonical ConPort
- 422: Policy violation (adapter-enforced constraints)
- 500: Service error or canonical backend error (propagated from ConPort)

---

## U1.7: dopetask Transport

**Purpose**: Task execution and health probing (execution-only, no state mutations)

**Authority**: None (execution service). No canonical state writes. Health status only.

### Endpoints

| Method | Path | Purpose | Idempotent |
|--------|------|---------|-----------|
| **GET** | `/health` | Direct health probe | N/A (read) |
| **POST** | `/execute` | Execute task command | Yes |
| **POST** | `/heartbeat` | Report task status (heartbeat) | Yes |

### Request/Response Specification

#### GET /health
```json
Request headers:
  (none)

Response (200 OK):
{
  "status": "string (healthy|degraded|critical)",
  "uptime": integer (seconds),
  "workers_active": integer,
  "timestamp": "ISO8601"
}

Response (503 Service Unavailable):
{
  "status": "degraded|critical",
  "uptime": integer,
  "workers_active": integer,
  "timestamp": "ISO8601"
}

Response (500 Internal Server Error):
{
  "status": "critical",
  "timestamp": "ISO8601"
}
```

**SLA**: Response time < 50ms. No external dependencies (self-contained). HTTP status codes: 200 (healthy), 503 (degraded), 500 (critical).

#### POST /execute
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "task_id": "string",
  "command": "string (e.g., 'start', 'pause', 'resume', 'cancel')",
  "parameters": { ... } (optional)
}

Response (202 Accepted):
{
  "task_id": "string",
  "status": "string (queued|running)",
  "execution_id": "string (for tracking)",
  "started_at": "ISO8601"
}

Response (400 Bad Request):
{
  "error": "Unknown command or invalid parameters",
  "code": "INVALID_COMMAND"
}
```

#### POST /heartbeat
```json
Request headers:
  Authorization: Bearer <token>
  X-Idempotency-Key: <uuid>
  Content-Type: application/json

Request body:
{
  "execution_id": "string",
  "task_id": "string",
  "status": "string (running|completed|failed)",
  "progress": {
    "completed": integer,
    "total": integer
  },
  "timestamp": "ISO8601"
}

Response (200 OK):
{
  "acknowledged": true,
  "received_at": "ISO8601"
}
```

### Pagination

- No pagination for health or heartbeat endpoints
- POST /execute results use execution_id for tracking; separate status query endpoint available if needed

### Execution-Only Semantics

- **No canonical state writes**. dopetask is a worker executor; state transitions are ConPort's responsibility.
- Health endpoint is direct (no aggregation via task-orchestrator).
- Heartbeat is for progress tracking only; does not write to work-item state.

### Error Handling

- 400: Missing required header or malformed payload
- 401: Invalid or missing bearer token
- 404: Task or execution not found
- 409: Invalid command for current task status
- 500: Service error

---

## Summary: Transport Contract Lifecycle

### Immutability

All seven contracts are **FROZEN** as of 2026-04-23. Changes require:
1. A new decision packet (e.g., TP-DMX-TUI-TRANSPORT-ARCHITECTURE-006)
2. Update to this document with version bump
3. Release notes documenting breaking changes
4. Client version negotiation support (if backward compatibility needed)

### Implementation Order

1. **Build Step 3**: Source trait concrete implementations for all seven backends
2. **Build Step 8**: Integration tests for multi-backend source wiring
3. **Build Step 9+**: Downstream consumers (state machine, metadata writer, etc.) use locked contracts

### Testing Requirements

Each transport must pass:
- Protocol compliance (HTTP/JSON, Bearer auth, pagination, idempotency)
- Error handling (all specified error codes and messages)
- Pagination correctness (cursor-based, null termination)
- Idempotency validation (same request twice produces same result)
- Latency SLAs (dopetask /health < 50ms; others < 200ms target)

---

**Locked By**: Packet TP-DMX-TUI-TRANSPORT-ARCHITECTURE-005  
**Date**: 2026-04-23  
**Author**: @hu3mann  
**Status**: IMMUTABLE (changes require new decision packet)
