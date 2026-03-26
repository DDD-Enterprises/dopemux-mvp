# INTEGRATION_NOTES.md

## For MCP Routing, Contract Gates, and AI Agent Integration
## Analyzed Ref: 99023a9 HEAD-at-time-of-analysis

---

## Critical: Choose Your Module Before Integrating

> Two deployable modules exist. Pick one and stick to it. Their tool sets are incompatible.

|                     | clockwork (v2)                    | current (v3)                 |
| ------------------- | --------------------------------- | ---------------------------- |
| **Docker target**   | `runtime-v2`                      | `runtime-current`            |
| **Compose service** | `mcp-task-orchestrator` (default) | requires `--profile current` |
| **Tool count**      | 14                                | 13                           |
| **Transport**       | stdio only                        | stdio or http                |
| **Database file**   | `data/tasks.db`                   | `data/current-tasks.db`      |
| **Status**          | Deprecated                        | Active                       |

---

## MCP Routing Configuration

Use tool name as the routing key. All tool names are unique within their module.

### v2 (clockwork) Routing Table
```
query_container      → READ  (PROJECT/FEATURE/TASK)
manage_container     → WRITE (PROJECT/FEATURE/TASK)
query_sections       → READ
manage_sections      → WRITE
query_templates      → READ
manage_template      → WRITE
apply_template       → WRITE
query_dependencies   → READ
manage_dependencies  → WRITE
get_next_task        → READ (advisory)
get_blocked_tasks    → READ (advisory)
get_next_status      → READ (advisory)
request_transition   → WRITE (status machine)
query_role_transitions → READ (audit)
```

### v3 (current) Routing Table
```
query_items          → READ
manage_items         → WRITE
query_notes          → READ
manage_notes         → WRITE
query_dependencies   → READ
manage_dependencies  → WRITE
get_next_item        → READ (advisory)
get_blocked_items    → READ (advisory)
get_next_status      → READ (advisory)
advance_item         → WRITE (workflow advance)
get_context          → READ (rich context)
create_work_tree     → WRITE (compound)
complete_tree        → WRITE (compound)
```

---

## Contract Gate Validation Rules

### Parameter Validation (from source code)

For `query_container`:
- `operation` MUST be one of: `get`, `search`, `export`, `overview`
- `containerType` MUST be one of: `project`, `feature`, `task`
- `id` required for `get` and `export`; MUST be valid UUID otherwise rejected with `VALIDATION_ERROR`
- `status` accepts multi-value OR (`pending,in-progress`) and negation (`!completed`)
- `tags` comma-separated (no UUID validation required)

For `manage_container`:
- `operation` MUST be one of: `create`, `update`, `delete`
- `containers` required for create/update; max 100 items; missing items → `VALIDATION_ERROR`
- `ids` required for delete; max 100 UUIDs
- `complexity` for task: MUST be 1–10
- `summary` for any entity: MUST be ≤ 500 chars
- `title` (task) / `name` (project/feature): MUST be non-blank

For `query_sections`:
- `entityType` MUST be one of: `PROJECT`, `FEATURE`, `TASK` (exact uppercase)
- `entityId` MUST be valid UUID
- Entity MUST exist or returns `RESOURCE_NOT_FOUND`

For `manage_sections`:
- `operation` MUST be one of: `add`, `update`, `updateText`, `updateMetadata`, `delete`, `reorder`, `bulkCreate`, `bulkUpdate`, `bulkDelete`
- `add`: requires `entityType`, `entityId`, `title`, `usageDescription`, `content`, `ordinal`
- `ordinal` MUST be ≥ 0 integer
- UUID fields validated server-side; invalid format → `VALIDATION_ERROR`

For `query_templates`:
- `operation` MUST be one of: `get`, `list`
- `get`: requires valid UUID in `id`
- `list.targetEntityType` MUST be `TASK` or `FEATURE` (2-value set, not including PROJECT)

### Response Contract
ALL tools return the same envelope:
```
{success, message, data, error, metadata}
```
Gate check: if `success == false`, the error is in `error.code` and `error.details`.

---

## Read/Write Permission Separation

By convention (enforced by `toolAnnotations` hints):

| Pattern         | Tools                              | MCP Annotation                             |
| --------------- | ---------------------------------- | ------------------------------------------ |
| Read-only tools | `query_*`, `get_*`                 | `readOnlyHint=true, destructiveHint=false` |
| Write tools     | `manage_*`, `apply_*`, `request_*` | `readOnlyHint=false, destructiveHint=true` |

Use this for permission-tiered routing (e.g., read-only AI vs. read-write AI).

---

## Token Optimization Patterns

These patterns are code-documented in tool descriptions:

1. **Scan first, fetch selectively**:
   - `query_sections(includeContent=false)` → metadata only, returns 85-99% fewer tokens
   - Then `query_sections(sectionIds=[id1, id2])` → fetch only needed sections

2. **Minimal search results**:
   - `query_container(search)` returns ~30 tokens per task (only id, title, status, priority)
   - Do NOT use `get` or `export` for listing — use `search` with filters

3. **Scoped overview**:
   - `query_container(overview, id=<projectId>)` returns tasks+features in one call instead of many `get` calls

4. **Batch operations**:
   - `manage_container(create, containers=[...])` — up to 100 items per call
   - `manage_sections(bulkCreate)` — multiple sections in one call

---

## Status String Normalization (Input)

The server normalizes incoming status strings before validation:

| Input               | Normalized To       |
| ------------------- | ------------------- |
| `in-progress`       | `IN_PROGRESS`       |
| `in_progress`       | `IN_PROGRESS`       |
| `inprogress`        | `IN_PROGRESS`       |
| `in-review`         | `IN_REVIEW`         |
| `changes-requested` | `CHANGES_REQUESTED` |
| `on-hold`           | `ON_HOLD`           |
| `ready-for-qa`      | `READY_FOR_QA`      |
| `canceled` (US)     | `CANCELLED`         |

Integration recommendation: **Always send UPPERCASE_UNDERSCORE** to avoid relying on normalization behavior.

---

## Known Issues / Not-Yet-Verified

1. `manage_template` and `apply_template` schemas not extracted — callers must query the tool's `parameterSchema` directly or read the source files
2. `query_dependencies`, `manage_dependencies`, `get_next_task/status/blocked` schemas not extracted
3. `request_transition`, `query_role_transitions` schemas not extracted
4. v3 (current module) schemas not extracted — treat all v3 tools as UNKNOWN contract until extracted
5. `VerificationGateService` behavior under `requiresVerification=true` is UNKNOWN
6. Workflow config (`.taskorchestrator/config.yaml`) format is UNKNOWN — transition rules are dynamic
