# Integration Notes

> Evidence-backed integration guidance for Leantime → PM-plane architecture.
> Analyzed ref: `555803d3da0f81ba232d5f38fc11268fdf317511` (master)
> All claims backed by source analysis documented in companion files.

---

## 1. WHAT TO KEEP AUTHORITATIVE IN LEANTIME

Leantime should remain the **system of record** for all core PM entities:

| Entity | Table | Reasoning |
|--------|-------|-----------|
| Tickets/Tasks | `zp_tickets` | Atomic PM work unit with full CRUD, status, assignment, timeline |
| Projects | `zp_projects` | Project container with state, budgets, client binding |
| Sprints | `zp_sprints` | Date-bounded iterations scoped to projects |
| Milestones | `zp_tickets` (type='milestone') | Progress aggregation over child tickets |
| Users/Roles | `zp_user` | Identity, authentication, role hierarchy (5-50 scale) |
| User-Project Relations | `zp_relationuserproject` | Access control and project membership |
| Timesheets | `zp_timesheets` | Time tracking with billing categories |
| Files/Attachments | `zp_file` + filesystem | Binary storage with polymorphic module binding |
| Comments | `zp_comment` | Threaded discussions on any entity |
| Clients | `zp_clients` | Client/company records tied to projects |
| Notifications | `zp_notifications` | Activity feed and read tracking |
| Reactions | `zp_reactions` | Social interactions (favorite, watch, etc.) |

**Evidence**: All entities have full CRUD via JSON-RPC services (`CALLABLE_SURFACE_MANIFEST.json`). Leantime's service layer provides validation, event dispatch, and permission checks. See `LEANTIME_DOMAIN_MODEL.md` for complete field inventories.

**Integration pattern**: Read from Leantime via JSON-RPC. Write back to Leantime via JSON-RPC. Do not maintain shadow copies.

---

## 2. WHAT TO SYNC INTO CONPORT

ConPort should receive **durable context** — decisions, rationale, strategic framing, and knowledge that persists beyond individual task lifecycles:

| Data | Source | Sync Strategy |
|------|--------|--------------|
| Goal canvas items (OKRs, KPIs) | `zp_canvas_items` (goalcanvas) | Periodic sync of title, description, metrics (startValue/currentValue/endValue), status |
| Wiki articles | `zp_canvas` (wiki type) + `zp_canvas_items` | Sync article content with normalization (HTML → clean text) |
| Retrospective items | `zp_canvas_items` (retroscanvas) | Sync as lessons-learned records after retro completion |
| Risk assessments | `zp_canvas_items` (riskscanvas) | Sync impact/probability/effort fields as risk registers |
| Approval decisions | `zp_approvals` | Sync approval status, requestor, approver, timestamps |
| Strategic canvas data | `zp_canvas_items` (various canvas types) | Selective sync of titled/concluded items only |
| Acceptance criteria | `zp_tickets.acceptanceCriteria` | Sync as definition-of-done records (requires HTML normalization) |
| Project descriptions | `zp_projects.details` | Sync as project framing context |

**Normalization required**: All text fields contain HTML. Must strip/convert before promotion. See §7 of `LEANTIME_PM_PLANE_MAPPING.md`.

**Evidence**: Canvas system stores strategic/planning data in `zp_canvas_items` with structured fields for metrics, impact, effort, probability — suitable for durable context after normalization. See `LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md` §2-5.

---

## 3. WHAT TO SURFACE INTO SERENA

Serena should receive **technical context** — system configuration, integration state, and tooling metadata:

| Data | Source | Reasoning |
|------|--------|-----------|
| Integration configurations | `zp_integration` | External system connections, field mappings, sync schedules |
| Plugin registry | `zp_plugins` | Installed plugin state, versions, enabled/disabled |
| System settings | `zp_settings` | Key-value config driving system behavior |
| Environment config | `config/.env` / `DefaultConfig.php` | LEAN_* variables controlling runtime |
| Schema version | `AppSettings.php` | dbVersion for migration compatibility |

**Evidence**: These are operational infrastructure data, not PM content. See `DATA_MODEL.md` §6 and `ARCHITECTURE_AND_INTENDED_USES.md` §6.

---

## 4. WHAT TASK ORCHESTRATOR SHOULD OWN

**Critical finding**: Leantime has **no workflow engine**. Ticket status transitions are completely unrestricted — any status can transition to any other status without validation. There are no dependency blockers, no required-field gates on transitions, and no auto-close/carry-over logic.

| Capability | Leantime State | Task Orchestrator Responsibility |
|------------|---------------|----------------------------------|
| Task sequencing | NOT IMPLEMENTED | Full ownership — define execution order |
| Dependency enforcement | Field exists (`dependingTicketId`) but NOT enforced | Enforce blocking relationships |
| Status transition rules | UNRESTRICTED — any → any | Define and enforce state machine |
| Sprint carry-over | NOT IMPLEMENTED | Handle incomplete work at sprint boundaries |
| Milestone gating | Progress calculated but NOT enforced | Gate releases on milestone completion |
| Automation triggers | Events fire but NO automated actions | React to status changes with workflow actions |
| Parallel/sequential work | NOT MODELED | Orchestrate multi-step task execution |

**Evidence**: `LEANTIME_WORKFLOW_AND_GATES.md` §1.2 documents that `updateTicket()` accepts any status value with no validation. `EntityRelationshipEnum` only has `Collaborator` — no blocker type exists. No auto-close or carry-over code found in sprint services.

**Implication**: Task Orchestrator should be the **workflow authority**. Leantime provides the data store; Task Orchestrator provides the rules.

---

## 5. WHAT NEEDS NORMALIZATION BEFORE MEMORY

The following data is **unsafe to promote directly** into memory without transformation:

| Data | Issue | Normalization Required |
|------|-------|----------------------|
| Ticket descriptions | HTML content, may contain embedded images/links, potentially huge | HTML → clean text, size truncation, link extraction |
| Wiki article content | HTML, may be very large | HTML → markdown/text, chunking for retrieval |
| Comment text | HTML, may contain @mentions, inline images | HTML → text, mention resolution, image extraction |
| Canvas item free-text (data1-5, assumptions, conclusion) | Unstructured, no schema | Field-level extraction, empty filtering |
| Audit log values | JSON blobs of raw change data | Schema-aware extraction, diff summarization |
| Timesheet descriptions | Free-text, often empty or terse | Filtering for non-empty, concatenation with context |
| Event names | Auto-generated from class namespace paths | Static mapping table — names change when classes move |

**Evidence**: `LEANTIME_PM_PLANE_MAPPING.md` §7. All HTML content uses Tiptap editor output (not TinyMCE per stale docs — see `DRIFT_REPORT.md` DRIFT-02).

---

## 6. RECOMMENDED PM-PLANE TOOL LAYER

Based on the analysis, the recommended integration architecture is:

```
┌─────────────────────────────────────────────────┐
│                   MCP Gateway                    │
│  (External adapter — reads/writes Leantime API)  │
├─────────────────────────────────────────────────┤
│                                                  │
│  JSON-RPC 2.0 ←→ 48 Service Classes             │
│  (leantime.rpc.{module}.{service}.{method})      │
│                                                  │
│  Auth: x-api-key (lt_{user}_{key})               │
│        OR Sanctum Bearer tokens                  │
│                                                  │
├─────────────────────────────────────────────────┤
│              Leantime Application                │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Services │→│  Repos   │→│  MySQL/PgSQL │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│       ↕ events                                   │
│  ┌──────────────┐                                │
│  │ Plugin System │ (optional Leantime plugin     │
│  │              │  for event hooks, UI widgets)  │
│  └──────────────┘                                │
└─────────────────────────────────────────────────┘
```

**Primary integration surface**: JSON-RPC 2.0 API via external MCP gateway.
- 241+ enumerated public methods across 24 key services
- Stable method routing: `leantime.rpc.{module}.{service}.{method}`
- Authentication via API keys or Sanctum tokens
- Both read and write operations available

**Secondary surface**: Leantime plugin (for capabilities that require server-side hooks).
- Event listeners for real-time reactions
- Middleware injection for request processing
- UI widget injection for custom dashboards
- Menu item injection for navigation

**Why not plugin-only**: The plugin system requires deploying PHP code into the Leantime installation. An external MCP gateway is decoupled, independently deployable, and doesn't require Leantime server access.

**Why not MCP-only**: Some capabilities (event-driven reactions, custom UI, middleware) require server-side presence that only a plugin can provide.

---

## 7. PLUGIN / EXTERNAL / HYBRID DESIGN RECOMMENDATION

| Capability | Approach | Reasoning |
|------------|----------|-----------|
| Read PM data (tickets, projects, sprints) | **External MCP** | JSON-RPC provides full read access without server deployment |
| Write PM data (create/update tickets) | **External MCP** | JSON-RPC write methods available, API-key authenticated |
| Context promotion (goals, wiki → ConPort) | **External MCP** | Read-only extraction + normalization, no server-side code needed |
| Workflow enforcement | **External MCP + Task Orchestrator** | Read status via API, enforce rules externally, write back |
| Real-time event reactions | **Leantime Plugin** | Requires server-side event listener registration |
| Custom UI widgets/dashboards | **Leantime Plugin** | Requires Blade template injection and menu registration |
| Memory-stack indexing | **External MCP** | Read + normalize + index pipeline, no server-side code needed |
| CalDAV/CardDAV sync | **External MCP** | sabre/dav is server-side, but read via its own protocol |

---

## 8. RISKS

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Event name instability** | HIGH | Event names are auto-generated from PHP class paths. Moving/renaming a class changes all its event names. Use JSON-RPC instead of events for stable integration. |
| **No API schema contract** | MEDIUM | Request/response shapes derived from service method signatures via reflection. No formal OpenAPI/JSON Schema. Build integration tests. |
| **HTML content everywhere** | MEDIUM | All rich-text fields contain HTML. Must normalize before memory promotion or cross-system sync. |
| **No workflow enforcement** | LOW (opportunity) | Leantime's lack of workflow rules means Task Orchestrator can be the sole authority — no conflict. |
| **MCP early stage** | LOW | php-mcp/laravel 3.0.0 installed but no custom tools registered. Leantime's built-in MCP may evolve — monitor but don't depend on it yet. |
| **Plugin system requires server access** | MEDIUM | Hybrid approach mitigates: use MCP for most work, plugin only for server-side hooks. |
| **No optimistic concurrency** | MEDIUM | Only one DB transaction found in entire codebase (timesheets punch-clock). Concurrent writes to the same ticket may produce inconsistent state. |
| **zp_ table prefix non-standard** | LOW | Schema uses `zp_` prefix on all tables. Direct DB access (if ever needed) must account for this. |

---

## 9. PHASED IMPLEMENTATION SEQUENCE

### Phase 1: Read-Only MCP Bridge
- External MCP gateway connecting to Leantime JSON-RPC
- Read: tickets, projects, sprints, milestones, users
- Auth: API key (lt_{user}_{key})
- ConPort promotion: goals, wiki articles (with HTML normalization)
- Memory indexing: project summaries, sprint stats
- **No writes. No plugin. Minimal risk.**

### Phase 2: Bidirectional MCP Bridge
- Add write operations: create/update tickets, log time, add comments
- Task Orchestrator integration: read ticket status, enforce workflow rules, write back
- Expanded ConPort sync: retrospectives, risk assessments, approval decisions
- **Requires careful write-safety testing.**

### Phase 3: Hybrid Plugin + MCP
- Deploy Leantime plugin for event-driven capabilities
- Real-time notifications: ticket status changes → Task Orchestrator
- Custom dashboard widgets for AI-generated summaries
- Menu integration for PM-plane tools
- **Requires Leantime server access for plugin deployment.**

### Phase 4: Deep Integration
- CalDAV/CardDAV sync (if sabre/dav is active)
- Custom canvas types via plugin for structured data capture
- Explore Leantime's evolving MCP support (php-mcp/laravel)
- AI integration surface exploration (prism-php, neuron-ai, qdrant)
- **Monitor Leantime roadmap for MCP and AI feature evolution.**

---

## 10. CONFIDENCE ASSESSMENT

| Area | Confidence | Notes |
|------|-----------|-------|
| Domain model completeness | **HIGH** | All 30 tables documented, all models/services surveyed |
| Callable surface inventory | **HIGH** | 241+ methods enumerated across 24 key services |
| Workflow/gating accuracy | **HIGH** | Confirmed: no state machine, unrestricted transitions |
| Extension surface mapping | **HIGH** | Plugin system, events, API all documented with code evidence |
| PM-plane mapping | **MEDIUM-HIGH** | Evidence-backed but integration architecture assumptions are external |
| Write-safety classification | **MEDIUM** | Based on service method analysis, not runtime testing |
| MCP surface state | **MEDIUM** | Package installed, endpoint registered, but no custom implementation found |
| AI integration state | **LOW** | Dependencies present (prism, neuron-ai, qdrant) but usage not traced |

---

RECOMMENDATION: HYBRID_PLUGIN_AND_ADAPTER
