---
id: 09_test_plan
title: 09_Test_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 09_Test_Plan (explanation) for dopemux documentation and developer workflows.
---
# Dope-Memory v1 — Test Plan

## Test Strategy
- Unit tests: redaction, promotion rules, sorting, pagination
- Integration tests: EventBus ingestion -> SQLite -> Postgres mirror -> MCP responses
- Security tests: secret leakage prevention
- Determinism tests: repeatability of ordering and recap

## Test Data Fixtures
Use deterministic UUIDs and timestamps.
- workspace_id: "11111111-1111-1111-1111-111111111111"
- instance_id: "A"
- session_id: "22222222-2222-2222-2222-222222222222"

## Unit Tests

### 1) Redaction regex replacement
Input payload contains:
- AWS key id
- JWT
- "Bearer xyz"
- private key block
Assert:
- all replaced with "[REDACTED]"

### 2) Denylist path hashing
Input linked_files includes ".env" and "secrets/api.txt"
Assert:
- stored linked_files has no raw path
- has path_hash and note "denied_path"

### 3) Payload size cap
Input payload_json > 64KB
Assert:
- stored payload_json contains truncated=true and original_size

### 4) Promotion eligibility
Events:
- decision.logged -> curated work log entry created
- file.modified -> only raw event created, no curated entry
- task.failed -> curated entry created
Assert:
- correct category/entry_type/outcome/importance_score

### 5) Tag extraction determinism
Given explicit tags list:
- preserve input order
Add inferred tags:
- sorted lexicographically
Cap at 12.

### 6) Sorting determinism
Insert 5 entries with controlled:
- importance_score
- ts
- id
Assert:
- retrieval returns stable order across runs.

### 7) Cursor pagination
Insert 10 entries.
Call memory_search top_k=3 repeatedly using next_token until exhausted.
Assert:
- no overlap
- total returned = 10
- order consistent with spec.

### 8) memory_recap deterministic rendering
Create entries:
- one decision (importance 7)
- one blocker (importance 7)
- one milestone (importance 5)
Assert:
- cards[0] is Decision
- cards[1] is Blocker
- cards[2] is suggested_next derived from last entry or blocker rule

## Integration Tests

### A) EventBus ingestion -> SQLite raw + curated
Publish to activity.events.v1:
- decision.logged
- task.failed
- file.modified
Assert:
- raw_activity_events has 3 rows
- work_log_entries has 2 rows (decision + task failed)

### B) Mirror worker idempotency
Run mirror twice.
Assert:
- Postgres tables contain exactly same number of rows, no duplicates.

### C) MCP tool end-to-end
Call memory_search(query="Decided")
Assert:
- returns max 3 items
- includes more_count and next_token
- includes only scoped workspace/instance

### D) Redaction fail-closed behavior
Simulate redaction engine error (inject exception).
Assert:
- event is not persisted unredacted
- stored payload is dropped or fully stripped.

## Security Tests

### 1) Secrets never persist in Postgres mirror
Publish event with JWT + OpenAI key pattern in data.
Assert:
- dm_raw_activity_events.payload does not contain the secret values
- dm_work_log_entries.details does not contain secret values

### 2) Path denylist enforcement
Publish event referencing ~/.ssh/id_rsa
Assert:
- no raw path stored

## Performance Tests (Phase 1 targets)
- Seed 50k work_log_entries
- Query memory_search with keyword "auth" and filters
Targets:
- p50 < 50ms
- p99 < 250ms
Measure in CI where possible, otherwise in a local perf harness.

## Determinism Tests (Must-Have)
- For a fixed dataset, run memory_search 50 times
Assert:
- identical result ordering and next_token behavior
