# Leantime → PM-Plane Integration Mapping

> **Purpose**: Maps every Leantime concept/entity into the correct integration category for the PM-plane architecture. Each mapping is evidence-backed with code citations.
>
> **Architecture Components**:
> | Component | Role |
> |-----------|------|
> | **Leantime** | PM system — source of truth for project management data |
> | **ConPort** | Durable project memory — decisions, rationale, persistent context |
> | **Serena** | Technical context — code/project/tooling context |
> | **Task Orchestrator** | Workflow engine — task execution, dependencies, orchestration |
> | **Memory Stack** | AI memory — promotable summaries + workbench-only ephemeral data |

---

## 1. LEANTIME_OPERATIONAL_AUTHORITY

Data that **remains authoritative in Leantime** as the PM system of record. These are the core CRUD entities that Leantime owns — any integration should read from and write back to Leantime for these.

### 1.1 Tickets / Tasks

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_tickets` |
| **Model** | `app/Domain/Tickets/Models/Tickets.php` |
| **Repository** | `app/Domain/Tickets/Repositories/Tickets.php` |
| **Service** | `app/Domain/Tickets/Services/Tickets.php` |

**Key fields**: `id`, `headline`, `type` (task/subtask/story/bug/milestone), `description`, `projectId`, `status`, `priority` (1=Critical → 5=Lowest), `date`, `dateToFinish`, `editFrom`/`editTo`, `editorId` (assignee), `userId` (creator), `storypoints` (0.5–13), `planHours`, `hourRemaining`, `sprint`, `dependingTicketId`, `milestoneid`, `acceptanceCriteria`, `tags`, `sortindex`, `kanbanSortIndex`, `modified`.

**Status values** (default, customizable per project via `zp_settings` key `projectsettings.{projectId}.ticketlabels`):
- `3` = NEW, `1` = BLOCKED, `4` = IN_PROGRESS, `2` = WAITING_FOR_APPROVAL, `0` = DONE, `-1` = ARCHIVED

**Reasoning**: Tickets are the atomic unit of PM work. Leantime provides full CRUD, status tracking, assignment, priority, timeline, and sprint association. All ticket mutations should flow through Leantime.

**Caveat**: Ticket `description` and `acceptanceCriteria` contain HTML content — see §7 UNSAFE_WITHOUT_NORMALIZATION for promotion considerations.

### 1.2 Projects

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_projects` |
| **Model** | `app/Domain/Projects/Models/Project.php` |
| **Repository** | `app/Domain/Projects/Repositories/Projects.php` |
| **Service** | `app/Domain/Projects/Services/Projects.php` |

**Key fields**: `id`, `name`, `clientId` (FK → `zp_clients`), `start`, `end`, `state` (0=OPEN, 1=CLOSED), `type`, `psettings` (visibility: 'all'/'clients'/project-specific), `hourBudget`, `dollarBudget`, `progress`, `sortIndex`, `parent` (sub-projects), `avatar`, `cover`, `created`, `modified`.

**Reasoning**: Projects are the organizational container for all PM work. Budget, timeline, client association, and state are core PM data. Leantime is the CRUD authority.

### 1.3 Sprints

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_sprints` |
| **Model** | `app/Domain/Sprints/Models/Sprints.php` |
| **Repository** | `app/Domain/Sprints/Repositories/Sprints.php` |

**Key fields**: `id`, `name`, `projectId`, `startDate`, `endDate`, `modified`.

**Key methods**: `getCurrentSprint()` (where `now()` between start/end), `getUpcomingSprint()`, `getAllFutureSprints()`.

**Reasoning**: Sprint definitions (date ranges, ticket assignments) are PM planning data. Leantime owns the sprint lifecycle.

**Caveat — No auto-close or carry-over**: When a sprint ends, tickets remain assigned. No automatic transition to next sprint. Manual reassignment required. This is relevant for Task Orchestrator (§4).

### 1.4 Milestones

**Milestones are NOT a separate entity** — they are tickets with `type='milestone'`.

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_tickets` (where `type='milestone'`) |
| **Service methods** | `quickAddMilestone()`, `quickUpdateMilestone()` in `Tickets` service |

**Milestone-specific usage**: `editFrom` (start date), `editTo` (end date), `headline` (name). Regular tickets reference milestones via `milestoneid` FK. Completion is derived from child ticket completion.

**Reasoning**: Milestones represent PM timeline anchors. Since they're stored as tickets, they follow the same CRUD authority.

### 1.5 Users / Roles

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_user` |
| **Auth Model** | `app/Domain/Auth/Models/CurrentUser.php` |
| **Roles** | `app/Domain/Auth/Models/Roles.php` |
| **Repository** | `app/Domain/Users/Repositories/Users.php` |

**Role hierarchy** (hard-coded numeric codes):
| Code | Role | Legacy Name |
|------|------|-------------|
| 5 | `readonly` | — |
| 10 | `commenter` | `client` |
| 20 | `editor` | `developer` |
| 30 | `manager` | `clientmanager` |
| 40 | `admin` | `manager` |
| 50 | `owner` | `admin` |

**Key fields**: `id`, `username`, `firstname`, `lastname`, `mail`, `role`, `clientId`, `status` ('a'=active, 'i'=inactive, 'invited'), `twoFAEnabled`, `lastlogin`, `source`.

**User-Project assignment**: `zp_relationuserproject` table (userId, projectId, role).

**Reasoning**: Identity, roles, and permissions are foundational PM system data. Leantime authenticates, authorizes, and manages user lifecycle.

### 1.6 Timesheets

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_timesheets` |
| **Repository** | `app/Domain/Timesheets/Repositories/Timesheets.php` |
| **Service** | `app/Domain/Timesheets/Services/Timesheets.php` |

**Key fields**: `id`, `userId`, `ticketId`, `workDate`, `hours`, `description`, `kind` (GENERAL_BILLABLE, GENERAL_NOT_BILLABLE, PROJECTMANAGEMENT, DEVELOPMENT, BUGFIXING_NOT_BILLABLE, TESTING), `invoicedEmpl`, `invoicedComp`, `paid`, `rate`, `modified`.

**Unique constraint**: `(userId, ticketId, workDate, kind)`.

**Reasoning**: Time tracking is core PM/billing data. Leantime owns the permanent records. See §6 for the ephemeral punch-clock timer.

### 1.7 Files / Attachments

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_file` |
| **Repository** | `app/Domain/Files/Repositories/Files.php` |

**Key fields**: `id`, `module` (project/ticket/client/user/lead/export/private), `moduleId`, `userId`, `extension`, `encName`, `realName`, `date`.

**Reasoning**: File metadata and storage are PM operational data. Leantime manages uploads, access control, and association with entities.

### 1.8 Comments

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_comment` |
| **Repository** | `app/Domain/Comments/Repositories/Comments.php` |

**Key fields**: `id`, `module` (ticket/project/canvas/etc.), `moduleId`, `userId`, `commentParent` (0=top-level, >0=reply), `date`, `text`, `status`.

**Reasoning**: Threaded discussions on PM entities are operational data. Leantime owns the comment lifecycle.

**Caveat**: Comment `text` is HTML — see §7 for promotion considerations.

### 1.9 Client Records

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_clients` |
| **Repository** | `app/Domain/Clients/Repositories/Clients.php` |

**Key fields**: `id`, `name`, `street`, `zip`, `city`, `state`, `country`, `phone`, `internet`, `email`, `published`, `modified`.

**Relationship**: 1-to-many with projects via `zp_projects.clientId`.

**Reasoning**: Client records are PM organizational data. Projects belong to clients; users belong to clients.

### 1.10 Calendar Events

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_calendar` |
| **Repository** | `app/Domain/Calendar/Repositories/Calendar.php` |

**Key fields**: `userId`, `dateFrom`, `dateTo` (plus event metadata).

**Reasoning**: Internal calendar events are PM scheduling data. Leantime owns the event lifecycle. (GCal link configs are ephemeral — see §6.)

### 1.11 Reactions

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_reactions` |
| **Repository** | `app/Domain/Reactions/Repositories/Reactions.php` |
| **Model** | `app/Domain/Reactions/Models/Reactions.php` |

**Key fields**: `id`, `userId`, `moduleId`, `module`, `reaction` (like/anger/love/support/celebrate/interesting/sad/funny/upvote/downvote/favorite/watch), `date`.

**Reasoning**: Reactions are user engagement data attached to PM entities. Leantime owns the reaction state.

### 1.12 Entity Relationships

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_entity_relationship` |
| **Enum** | `app/Core/Support/EntityRelationshipEnum.php` |

**Key fields**: `id`, `entityA`, `entityAType`, `entityB`, `entityBType`, `relationship`, `createdOn`, `createdBy`, `meta`.

**Currently defined types**: Only `Collaborator` exists. The enum has a comment: *"Add other relationship types as needed."* **No blocker type exists.**

**Reasoning**: Relationship metadata between PM entities is operational. Currently used for ticket-user collaborator relationships.

**Critical caveat for Task Orchestrator**: The `dependingTicketId` field on tickets represents parent-child (subtask) relationships, NOT dependency/blocker semantics. Combined with the single `Collaborator` enum value, Leantime has **no blocker enforcement mechanism** (see §4).

### 1.13 Ticket History

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_tickethistory` |
| **Repository** | `app/Domain/Tickets/Repositories/TicketHistory.php` |

**Reasoning**: Change tracking on tickets is PM audit data owned by Leantime.

---

## 2. CONPORT_DURABLE_CONTEXT

Data that should be **promoted into ConPort** as durable project memory — decisions, rationale, strategic context, and lessons learned that persist beyond active work.

### 2.1 Goal Canvas Items

| Attribute | Evidence |
|-----------|----------|
| **Tables** | `zp_canvas` (board), `zp_canvas_items` (items with `box='goal'`) |
| **Repository** | `app/Domain/Goalcanvas/Repositories/Goalcanvas.php` |
| **Service** | `app/Domain/Goalcanvas/Services/Goalcanvas.php` |
| **Canvas type** | `goalcanvas` (CANVAS_NAME = 'goal') |

**Goal-specific fields**: `assumptions` (what are you measuring), `data` (current value), `conclusion` (goal value), `startValue`, `currentValue`, `endValue` (decimal metrics), `metricType`, `startDate`, `endDate`, `kpi` (parent KPI), `setting` (reporting: linkonly/linkAndReport/nolink).

**Status labels**: `status_ontrack`, `status_atrisk`, `status_miss`.

**Key methods**: `getChildGoalsForReporting()`, `getGoalsByMilestone()`, `pollGoals()`.

**Reasoning**: Goals represent strategic objectives and KPIs — the "why" behind project work. These are decisions about what success looks like and should persist as durable context in ConPort. Goal status changes over time but the goal definition itself is a strategic decision.

### 2.2 Wiki Articles

| Attribute | Evidence |
|-----------|----------|
| **Tables** | `zp_canvas` (wiki containers, type='wiki'), `zp_canvas_items` (articles, box='article') |
| **Models** | `app/Domain/Wiki/Models/Wiki.php`, `app/Domain/Wiki/Models/Article.php` |
| **Repository** | `app/Domain/Wiki/Repositories/Wiki.php` (extends Canvas base) |

**Article fields**: `id`, `title`, `description` (content), `data`, `parent` (hierarchy), `tags`, `status` (draft/published), `featured`, `milestoneId`.

**Reasoning**: Wiki articles are the primary vehicle for documenting decisions, processes, and knowledge. Published articles represent the team's shared understanding and should be promoted as durable context. However, content is HTML — see §7 for normalization requirements.

### 2.3 Retrospective Canvas Items

| Attribute | Evidence |
|-----------|----------|
| **Tables** | `zp_canvas` / `zp_canvas_items` |
| **Repository** | `app/Domain/Retroscanvas/Repositories/Retroscanvas.php` |
| **Canvas type** | `retroscavas` (CANVAS_NAME = 'retros') |

**Box types**: `well` (what went well / continue doing), `notwell` (what didn't go well / stop doing), `startdoing` (what to start doing).

**Data labels**: `conclusion` is the primary description field.

**Reasoning**: Retrospective items capture lessons learned and action items — the most classically "durable context" data. These represent team decisions about process improvements and should be promoted to ConPort as-is (after normalization).

### 2.4 Strategic Canvas Items (All Variants)

All 18 canvas types share `zp_canvas` / `zp_canvas_items` tables via the Canvas base domain.

| Canvas | Type Constant | Box Types (Key) | Evidence File |
|--------|--------------|-----------------|---------------|
| **SWOT** | `swotcanvas` | strengths, weaknesses, opportunities, threats | `app/Domain/Swotcanvas/Repositories/Swotcanvas.php` |
| **Risks** | `riskscanvas` | impact/probability matrix (low-low, low-high, high-low, high-high) | `app/Domain/Riskscanvas/Repositories/Riskscanvas.php` |
| **Lean Canvas** | `leancanvas` | problem, solution, keymetrics, uniquevalue, customersegment, revenue, cost, etc. | `app/Domain/Leancanvas/Repositories/Leancanvas.php` |
| **DBM Canvas** | `dbmcanvas` | 15 boxes covering customer, value prop, activities, financials | `app/Domain/Dbmcanvas/Repositories/Dbmcanvas.php` |
| **Value Canvas** | `valuecanvas` | value proposition mapping | `app/Domain/Valuecanvas/Repositories/Valuecanvas.php` |
| **Empathy Map** | `emcanvas` | empathy mapping | `app/Domain/Emcanvas/Repositories/Emcanvas.php` |
| **Min Empathy** | `minempathycanvas` | minimal empathy canvas | `app/Domain/Minempathycanvas/Repositories/Minempathycanvas.php` |
| **OBM** | `obmcanvas` | operating business model | `app/Domain/Obmcanvas/Repositories/Obmcanvas.php` |
| **LBM** | `lbmcanvas` | lean business model | `app/Domain/Lbmcanvas/Repositories/Lbmcanvas.php` |
| **EA Canvas** | `eacanvas` | enterprise architecture | `app/Domain/Eacanvas/Repositories/Eacanvas.php` |
| **Scenario** | `sbcanvas` | scenario planning | `app/Domain/Sbcanvas/Repositories/Sbcanvas.php` |
| **Strategy Questions** | `sqcanvas` | strategy questions | `app/Domain/Sqcanvas/Repositories/Sqcanvas.php` |
| **Competitive Pos.** | `cpcanvas` | competitive positioning | `app/Domain/Cpcanvas/Repositories/Cpcanvas.php` |
| **Strategy Messaging** | `smcanvas` | strategy messaging | `app/Domain/Smcanvas/Repositories/Smcanvas.php` |
| **Insights** | `insightscanvas` | insights analysis | `app/Domain/Insightscanvas/Repositories/Insightscanvas.php` |

**Strategy domain aggregator**: `app/Domain/Strategy/Controllers/ShowBoards.php` — aggregates all canvas types with `getBoardProgress()` and `getLastUpdatedCanvas()`.

**Common canvas item fields**: `title`, `description`, `assumptions`, `data`, `conclusion`, `data1`–`data5`, `status`, `relates`, `milestoneId`, `tags`.

**Reasoning**: All canvas types capture strategic analysis and decisions. SWOT analyses, risk assessments, lean canvases, business models — these are durable project context that should persist in ConPort as decision records. The structured box types provide categorization.

**Caveat**: The free-text fields (`data1`–`data5`, `assumptions`, `conclusion`) are MEDIUMTEXT and can contain arbitrary content — see §7 for normalization requirements.

### 2.5 Approval Records

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_approvals` |
| **Schema** | `app/Domain/Install/Services/SchemaBuilder.php` (lines creating the table) |

**Fields**: `id`, `module` (e.g., 'goalcanvasitem'), `entityId`, `requestorId`, `approverId`, `approvalStatus`, `requestedOn`, `lastStatusChange`.

**Note**: No dedicated repository found — the table exists in schema but appears to be a future/extensible feature. Currently referenced primarily by goal canvas items.

**Reasoning**: Approval records represent formal decision points — who approved what and when. This is quintessential durable context: a decision trail that should be preserved in ConPort.

### 2.6 Project Metadata (Strategic Framing)

While the project record itself is operational (§1.2), certain project attributes represent strategic decisions:

- **`hourBudget` / `dollarBudget`** — resource allocation decisions
- **`start` / `end`** — timeline commitments
- **`psettings`** — access/visibility decisions
- **`parent`** — organizational hierarchy decisions

**Reasoning**: These attributes, when they change, represent strategic decisions worth recording in ConPort. The project record stays in Leantime, but decision snapshots (e.g., "budget increased from X to Y on date Z") should be promoted.

### 2.7 Ticket Acceptance Criteria

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_tickets.acceptanceCriteria` |
| **Model** | `app/Domain/Tickets/Models/Tickets.php` |

**Reasoning**: Acceptance criteria define "done" — they are decisions about quality and scope. While the ticket itself is operational, the AC represents agreed-upon requirements that should be captured as durable context.

### 2.8 Risk Canvas Items (Specific)

In addition to being part of the general canvas family (§2.4), risk items have specific fields worth highlighting:

**Risk-specific data labels**: `conclusion` (risk description), `data` (risk details), `assumptions` (mitigation strategy).

**Risk matrix**: Box types encode impact × probability (`risks_imp_low_pro_low` through `risks_imp_high_pro_high`).

**Reasoning**: Risk assessments and their mitigations are durable decisions. The impact/probability matrix provides structured risk categorization that should persist in ConPort.

---

## 3. SERENA_TECHNICAL_CONTEXT

Data that belongs in **Serena** as code/project/tooling context — configuration, integration setup, and technical system state.

### 3.1 Integration / Connector Configurations

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_integration` |
| **Model** | `app/Domain/Connector/Models/Integration.php` |
| **Service** | `app/Domain/Connector/Services/Connector.php` |
| **Repository** | `app/Domain/Connector/Repositories/Integrations.php` |

**Key fields**: `id`, `providerId`, `method` (import/sync), `entity`, `fields` (JSON field mapping), `schedule` (sync schedule), `auth` (encrypted credentials), `meta`, `lastSync`.

**Additional models**: `Entity.php`, `Provider.php`, `Field.php`, `FieldTypes.php` — define the integration schema.

**Reasoning**: Integration configurations are technical setup — how systems connect, what fields map where, authentication details. This is tooling context that Serena should understand to manage data flows.

### 3.2 Plugin Configurations

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_plugins` |
| **Model** | `app/Domain/Plugins/Models/InstalledPlugin.php` |
| **Repository** | `app/Domain/Plugins/Repositories/Plugins.php` |

**Key fields**: `id`, `name`, `enabled`, `description`, `version`, `installdate`, `foldername`, `homepage`, `authors` (JSON), `license`, `format` (phar/folder).

**Reasoning**: Installed plugins and their state are part of the technical environment. Serena needs this to understand what capabilities are active and what extensions modify system behavior.

### 3.3 System Settings

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_settings` |
| **Repository** | `app/Domain/Setting/Repositories/Setting.php` |
| **Service** | `app/Domain/Setting/Services/Setting.php` |
| **Cache** | `app/Domain/Setting/Services/SettingCache.php` |

**Structure**: Key-value store (`key` VARCHAR 175, `value` MEDIUMTEXT).

**Known keys include**: `db-version`, `companysettings.telemetry.active`, `projectsettings.{projectId}.ticketlabels` (custom status labels per project).

**Reasoning**: System settings define the technical configuration of the Leantime instance — feature flags, custom status labels, company settings. This is technical context.

**Caveat**: Some settings (like ticket status labels) have PM implications. The raw key-value data belongs in Serena, but the semantic meaning (e.g., "project X uses custom statuses") may also be relevant to ConPort.

### 3.4 Environment Configuration

| Attribute | Evidence |
|-----------|----------|
| **Files** | `app/Core/Configuration/DefaultConfig.php`, `app/Core/Configuration/Environment.php`, `config/.env.sample` |
| **Config loader** | `app/Core/Bootstrap/LoadConfig.php` |
| **Laravel config** | `app/Core/Configuration/laravelConfig.php` |

**Priority order**: Environment Variables > `.env` file > PHP config > DefaultConfig defaults.

**Key properties**: `sitename`, `language`, `appUrl`, `defaultTheme`, `defaultTimezone`, SMTP settings, LDAP config, OIDC config.

**Reasoning**: Environment configuration defines how the instance is deployed and connected. This is pure technical context for Serena.

### 3.5 Technical Architecture Decisions (Wiki Subset)

While wiki articles generally belong in ConPort (§2.2), articles that document:
- System architecture
- API integration patterns
- Deployment procedures
- Technical standards

...are relevant to Serena as technical context. The determination depends on article content, not structure.

**Reasoning**: Serena needs to understand technical decisions documented in the wiki. A content-based classifier would be needed to route wiki articles to ConPort vs. Serena (or both).

---

## 4. TASK_ORCHESTRATOR_WORKFLOW_AUTHORITY

Data or behavior that **Task Orchestrator owns** because Leantime lacks the capability.

### 4.1 Critical Finding: Leantime Has NO Workflow Engine

**Evidence chain**:

1. **No state machine**: Ticket status transitions are unrestricted. Any status can transition to any other status. Custom status labels are stored in `zp_settings` as `projectsettings.{projectId}.ticketlabels` but only define labels, CSS classes, and type categories (NEW/INPROGRESS/DONE) — **not transition rules**.
   - Source: `app/Domain/Tickets/Repositories/Tickets.php` — `getStateLabels()` returns label/class metadata only.

2. **No blocker enforcement**: `EntityRelationshipEnum` (at `app/Core/Support/EntityRelationshipEnum.php`) defines only `Collaborator`. The enum explicitly comments: *"Add other relationship types as needed."* There is no `Blocker`, `DependsOn`, or `Precedes` type.

3. **`dependingTicketId` is subtask-parent only**: The `dependingTicketId` field on `zp_tickets` represents parent-child (subtask) relationships, not dependency/blocking semantics. A subtask's `dependingTicketId` points to its parent ticket.

4. **No sprint auto-management**: Sprints are date-bounded only. When a sprint ends:
   - Tickets remain assigned (no carry-over)
   - No automatic status transition
   - No velocity-based planning
   - Source: `app/Domain/Sprints/Repositories/Sprints.php` — `getCurrentSprint()` is a simple date range query.

### 4.2 What Task Orchestrator Should Own

Given the above findings, Task Orchestrator is the authority for:

| Capability | Why Not Leantime | Evidence |
|-----------|-----------------|----------|
| **Task sequencing / dependency enforcement** | No blocker relationship type; no transition constraints | `EntityRelationshipEnum` has only `Collaborator` |
| **Workflow state machines** | Status changes are free-form | No transition validation in `Tickets` service |
| **Sprint carry-over** | No auto-close logic | `Sprints` repository has no end-of-sprint handler |
| **Cross-entity orchestration** | No workflow triggers | No event-driven status propagation found |
| **Dependency graph resolution** | `dependingTicketId` is subtask-parent, not DAG | Model field is parent reference, not dependency |
| **Approval workflows** | `zp_approvals` exists but has no enforcement logic | No repository, no service, table only in schema |

**Reasoning**: Leantime deliberately keeps ticket management flexible — any status can move to any other status. This is a design choice for non-project-manager users. But a PM-plane integration requires orchestration logic (sequencing, blocking, dependency enforcement) that must come from Task Orchestrator, not Leantime.

### 4.3 Integration Pattern

Task Orchestrator should:
- **Read** ticket status, sprint assignments, and milestone associations from Leantime
- **Enforce** its own dependency graphs and workflow rules
- **Write back** status changes to Leantime when orchestrated transitions occur
- **NOT** attempt to add workflow logic to Leantime's data model

---

## 5. MEMORY_STACK_PROMOTABLE

Data safe to **summarize and promote** into Memory Stack — aggregated metrics, progress snapshots, and statistical data.

### 5.1 Sprint / Project Statistics

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_stats` |
| **Repository** | `app/Domain/Reports/Repositories/Reports.php` |
| **Service** | `app/Domain/Reports/Services/Reports.php` |

**Metric fields** (25+ columns per snapshot):
- **Ticket counts**: `sum_todos`, `sum_open_todos`, `sum_progres_todos`, `sum_closed_todos`
- **Points**: `sum_points`, `sum_points_open`, `sum_points_progress`, `sum_points_done`
- **Size distribution**: `sum_todos_xs`, `sum_todos_s`, `sum_todos_m`, `sum_todos_l`, `sum_todos_xl`, `sum_todos_xxl`, `sum_todos_none`
- **Time metrics**: `sum_planned_hours`, `sum_estremaining_hours`, `sum_logged_hours`
- **Velocity**: `daily_avg_hours_booked_todo`, `daily_avg_hours_booked_point`, `daily_avg_hours_planned_todo`, `daily_avg_hours_planned_point`, `daily_avg_hours_remaining_todo`, `daily_avg_hours_remaining_point`
- **Team**: `sum_teammembers`
- **Context**: `sprintId`, `projectId`, `date`, `tickets` (comma-separated IDs)

**Data generation**: `runTicketReport()` generates from current ticket state; `addReport()` persists daily via cron.

**Reasoning**: Statistics are pre-aggregated snapshots designed for reporting. They're ideal for Memory Stack promotion — compact, numeric, and already summarized. No PII or HTML content.

### 5.2 Project Progress Summaries

Derived from ticket completion ratios and milestone status:
- **Source**: `app/Domain/Projects/Models/Project.php` — `progress` field
- **Source**: `app/Domain/Strategy/Controllers/ShowBoards.php` — `getBoardProgress()` method

**Reasoning**: Progress percentages and milestone completion rates are naturally summarizable and safe to promote.

### 5.3 Dashboard Widget Data

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_dashboard_widgets` was **DROPPED** in migrations |
| **Service** | Dashboard data is now template-driven, aggregating from tickets/timesheets/projects |
| **Default widgets** | `$defaultWidgets = [1, 3, 9]` in `app/Domain/Dashboard/Repositories/Dashboard.php` |

**Reasoning**: Dashboard aggregations (top tasks, recent activity, project status) are by nature summary data suitable for Memory Stack.

### 5.4 Notification Activity Summaries

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_notifications` |
| **Model** | `app/Domain/Notifications/Models/Notification.php` |

While individual notifications are operational (§1), **aggregated activity patterns** (e.g., "15 ticket updates this sprint", "3 comment threads active") are promotable summaries.

**Reasoning**: Activity volume and patterns are naturally summarizable. The notification table provides the raw signal; Memory Stack stores the summary.

### 5.5 Audit Trail Summaries

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_audit` |
| **Repository** | `app/Domain/Audit/Repositories/Audit.php` |

**Fields**: `userId`, `projectId`, `action` (create/edit/status_changed/assigned), `entity`, `entityId`, `values` (JSON), `date`.

**Pruning**: `pruneEvents(ageDays)` — auto-cleanup older than N days.

**Reasoning**: Audit events can be summarized into patterns ("20 ticket updates by user X this week", "5 status transitions today"). The raw JSON values need normalization (§7), but aggregate counts and patterns are promotable.

### 5.6 Goal Canvas Progress

| Evidence | `app/Domain/Goalcanvas/Services/Goalcanvas.php` — `getCanvasItemsById()` calculates progress |
|----------|---|

**Metrics**: `startValue`, `currentValue`, `endValue` — provide numeric progress tracking for KPIs.

**Reasoning**: Goal progress percentages are compact, numeric summaries ideal for Memory Stack. The goal definition belongs in ConPort (§2.1), but its current progress value is a promotable summary.

---

## 6. MEMORY_STACK_WORKBENCH_ONLY

Data that should stay **ephemeral** — operator-facing, transient, or too noisy for promotion.

### 6.1 Punch Clock / Timer Records

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_punch_clock` |
| **Repository** | `app/Domain/Timesheets/Repositories/Timesheets.php` |
| **HxController** | `app/Domain/Timesheets/Hxcontrollers/Stopwatch.php` |

**Fields**: `id` (ticket ID, composite PK with userId), `userId`, `minutes`, `hours`, `punchIn` (Unix timestamp).

**Lifecycle**: Records are **deleted on punch-out**. `punchOut()` atomically:
1. Retrieves active punch record
2. Calculates `hoursWorked = (currentTime - punchIn) / 3600`
3. **Deletes** punch record from `zp_punch_clock`
4. **Inserts** permanent entry into `zp_timesheets`

**Reasoning**: Punch clock records are ephemeral by design — they exist only while a timer is running and are destroyed when converted to timesheets. There is no value in promoting transient timer state.

### 6.2 Session Data

| Evidence | Laravel session management via `StartSession` middleware in `app/Core/Http/HttpKernel.php` |
|----------|---|

**Reasoning**: Session state (login tokens, CSRF, flash messages) is inherently transient and per-request.

### 6.3 Queue Messages

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_queue` |
| **Repository** | `app/Domain/Queue/Repositories/Queue.php` |
| **Workers** | `EmailWorker.php`, `HttpRequestWorker.php`, `DefaultWorker.php` |

**Fields**: `msghash` (PK), `channel`, `userId`, `subject`, `message` (serialized payload), `thedate`, `projectId`.

**Processing schedule**: Email every minute, HTTP requests every 5 minutes, default every 5 minutes.

**Reasoning**: Queue messages are delivery mechanisms — transient by purpose. Once processed, the message is consumed. No value in promotion.

### 6.4 Read Status Tracking

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_read` |
| **Repository** | `app/Domain/Read/Repositories/Read.php` |

**Fields**: `id`, `module` (ENUM: 'ticket', 'message'), `moduleId`, `userId`.

**Reasoning**: Read/unread state is per-user, per-item UI state. It's relevant only to the current user session and has no strategic or operational value to promote.

### 6.5 Notification Unread State

| Evidence | `zp_notifications.read` field (INT flag) in `app/Domain/Notifications/Repositories/Notifications.php` |
|----------|---|

**Reasoning**: Individual notification read/unread flags are per-user UI state. Aggregate notification patterns may be promotable (§5.4), but individual read state is workbench-only.

### 6.6 GCal Link Configurations

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_gcallinks` |
| **Repository** | `app/Domain/Calendar/Repositories/Calendar.php` (methods at lines 381–437) |

**Fields**: `userId`, plus external calendar URL/auth data. Indexed by `userId`.

**Reasoning**: External calendar sync configurations are per-user setup data. They define how a user's calendar connects, not what's on it. No strategic value.

### 6.7 User Notes (Personal Scratch)

| Attribute | Evidence |
|-----------|----------|
| **Table** | `zp_note` |
| **Schema** | `app/Domain/Install/Services/SchemaBuilder.php` |

**Fields**: `id`, `userId`, `title`, `description`.

**Reasoning**: Personal notes are private scratch space with no project-wide significance. They're user-facing and should not be promoted into shared memory.

---

## 7. UNSAFE_WITHOUT_NORMALIZATION

Data that is **too ambiguous, noisy, or side-effectful** to promote directly — requires content normalization before integration.

### 7.1 Ticket Descriptions

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_tickets.description` |
| **Type** | TEXT (HTML content) |

**Risks**:
- Contains raw HTML (from TinyMCE 5.10.9 rich editor)
- May include embedded images (base64 or linked)
- May contain `@mention` references
- Can be arbitrarily large
- May contain inline file attachments

**Normalization needed**: Strip HTML → extract plain text + links. Detect and resolve @mentions. Extract embedded media references separately.

### 7.2 Canvas Item Free-Text Fields

| Attribute | Evidence |
|-----------|----------|
| **Fields** | `data1`–`data5`, `assumptions`, `conclusion`, `description` on `zp_canvas_items` |
| **Types** | All MEDIUMTEXT |
| **Repository** | `app/Domain/Canvas/Repositories/Canvas.php` |

**Risks**:
- Five extensible MEDIUMTEXT fields per item — potentially very large
- No enforced structure within fields
- Content varies dramatically by canvas type (a Lean Canvas "problem" field vs. a SWOT "strength" field)
- Mixed usage: some canvases use `conclusion` for descriptions, others for numeric values

**Normalization needed**: Per-canvas-type field interpretation. HTML stripping. Size limits. Content-type detection.

### 7.3 Comment Text

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_comment.text` |
| **Type** | TEXT (HTML content) |

**Risks**:
- HTML content with potential @mentions
- May contain inline images
- Threaded structure (via `commentParent`) means context depends on parent chain
- Comment `status` field allows custom values

**Normalization needed**: HTML stripping. @mention resolution. Thread context reconstruction.

### 7.4 Wiki Article Content

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_canvas_items.description` (where canvas type is 'wiki', box='article') |
| **Model** | `app/Domain/Wiki/Models/Article.php` — `description` property |

**Risks**:
- Wiki articles can be very large (full documentation pages)
- HTML content with embedded media
- Hierarchical structure (via `parent` field) — context depends on tree position
- Status field distinguishes draft vs. published

**Normalization needed**: HTML → markdown conversion. Size chunking for large articles. Draft filtering. Hierarchy context attachment.

### 7.5 Audit Log Raw Values

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_audit.values` |
| **Type** | TEXT (JSON blobs) |
| **Repository** | `app/Domain/Audit/Repositories/Audit.php` |

**Risks**:
- JSON blobs of arbitrary change data
- Structure varies by entity type and action
- May contain old/new value pairs, nested objects
- Can include sensitive data (user info changes, setting modifications)

**Normalization needed**: Schema-aware JSON parsing per entity type. Sensitive data redaction. Change summary extraction.

### 7.6 Timesheet Descriptions

| Attribute | Evidence |
|-----------|----------|
| **Field** | `zp_timesheets.description` |
| **Type** | Free-text |

**Risks**:
- Unstructured free-text entered by users
- Quality varies enormously (from "" to detailed work logs)
- No HTML typically, but no validation either

**Normalization needed**: Empty/trivial content filtering. Length limits.

### 7.7 Event Names (String-Based)

| Attribute | Evidence |
|-----------|----------|
| **System** | `app/Core/Events/EventDispatcher.php` |
| **Trait** | `app/Core/Events/DispatchesEvents.php` |

**Format**: Auto-generated from class namespace: `leantime.domain.tickets.services.tickets.updateTicket.ticket_updated`

**Risks**:
- Moving or renaming a class changes ALL its event names
- No versioning or stability guarantee
- Only ONE class-based event exists (`Files/Events/FileUploaded.php`)
- Pattern matching uses wildcards (`*`, `?`, `{RGX:pattern:RGX}`)

**Normalization needed**: Event name → semantic action mapping. Version-stable identifiers. Any integration relying on event names must account for name instability.

---

## Summary Matrix

| Concept | Category | Confidence | Key Evidence |
|---------|----------|------------|--------------|
| Tickets (status, assignment, priority, dates) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_tickets`, `Tickets` model/repo/service |
| Projects (name, state, budgets, client) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_projects`, `Project` model |
| Sprints (date ranges, assignments) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_sprints`, no auto-close logic |
| Milestones (progress, timeline) | LEANTIME_OPERATIONAL | ★★★★★ | Tickets with `type='milestone'` |
| Users / Roles (identity, permissions) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_user`, `Roles.php` hard-coded hierarchy |
| Timesheets (hours, billing) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_timesheets`, billing fields |
| Files / Attachments | LEANTIME_OPERATIONAL | ★★★★★ | `zp_file`, module-based association |
| Comments (threaded discussions) | LEANTIME_OPERATIONAL | ★★★★★ | `zp_comment`, `commentParent` nesting |
| Client records | LEANTIME_OPERATIONAL | ★★★★★ | `zp_clients`, 1-to-many with projects |
| Calendar events | LEANTIME_OPERATIONAL | ★★★★☆ | `zp_calendar`, internal events |
| Reactions | LEANTIME_OPERATIONAL | ★★★★☆ | `zp_reactions`, 12 reaction types |
| Entity relationships | LEANTIME_OPERATIONAL | ★★★★☆ | `zp_entity_relationship`, only `Collaborator` |
| Ticket history | LEANTIME_OPERATIONAL | ★★★★☆ | `zp_tickethistory` |
| Goal canvas items (KPIs, objectives) | CONPORT_DURABLE | ★★★★★ | `zp_canvas_items` box='goal', metric fields |
| Wiki articles (knowledge, decisions) | CONPORT_DURABLE | ★★★★★ | `zp_canvas_items` type='wiki', published status |
| Retrospective items (lessons learned) | CONPORT_DURABLE | ★★★★★ | `retroscavas`, well/notwell/startdoing boxes |
| Strategic canvases (SWOT, Lean, etc.) | CONPORT_DURABLE | ★★★★★ | 18 canvas types, all via `zp_canvas_items` |
| Approval records | CONPORT_DURABLE | ★★★☆☆ | `zp_approvals` table exists, no repo/service |
| Project metadata (strategic framing) | CONPORT_DURABLE | ★★★★☆ | Budget/timeline fields on `zp_projects` |
| Ticket acceptance criteria | CONPORT_DURABLE | ★★★★☆ | `zp_tickets.acceptanceCriteria` |
| Risk assessments | CONPORT_DURABLE | ★★★★★ | `riskscanvas`, impact×probability matrix |
| Connector / integration configs | SERENA_TECHNICAL | ★★★★★ | `zp_integration`, field mappings, auth |
| Plugin configurations | SERENA_TECHNICAL | ★★★★★ | `zp_plugins`, enabled/version/format |
| System settings | SERENA_TECHNICAL | ★★★★★ | `zp_settings`, key-value store |
| Environment configuration | SERENA_TECHNICAL | ★★★★★ | `DefaultConfig.php`, `Environment.php` |
| Technical wiki articles | SERENA_TECHNICAL | ★★★☆☆ | Content-based routing from wiki subset |
| Task sequencing / dependency enforcement | TASK_ORCHESTRATOR | ★★★★★ | `EntityRelationshipEnum` has only `Collaborator` |
| Workflow state machines | TASK_ORCHESTRATOR | ★★★★★ | No transition rules in code |
| Sprint carry-over | TASK_ORCHESTRATOR | ★★★★★ | No auto-close logic in `Sprints` repo |
| Cross-entity orchestration | TASK_ORCHESTRATOR | ★★★★★ | No workflow triggers found |
| Sprint / project statistics | MEMORY_PROMOTABLE | ★★★★★ | `zp_stats`, 25+ metric columns |
| Project progress summaries | MEMORY_PROMOTABLE | ★★★★★ | `Project.progress`, `getBoardProgress()` |
| Dashboard widget data | MEMORY_PROMOTABLE | ★★★★☆ | Template-driven aggregation |
| Notification activity summaries | MEMORY_PROMOTABLE | ★★★★☆ | `zp_notifications`, aggregate patterns |
| Audit trail summaries | MEMORY_PROMOTABLE | ★★★★☆ | `zp_audit`, action counts/patterns |
| Goal progress metrics | MEMORY_PROMOTABLE | ★★★★★ | `startValue`/`currentValue`/`endValue` |
| Punch clock / timer state | WORKBENCH_ONLY | ★★★★★ | `zp_punch_clock`, deleted on punch-out |
| Session data | WORKBENCH_ONLY | ★★★★★ | Laravel session middleware |
| Queue messages | WORKBENCH_ONLY | ★★★★★ | `zp_queue`, consumed on processing |
| Read status tracking | WORKBENCH_ONLY | ★★★★★ | `zp_read`, per-user UI state |
| Notification unread state | WORKBENCH_ONLY | ★★★★★ | `zp_notifications.read` flag |
| GCal link configurations | WORKBENCH_ONLY | ★★★★★ | `zp_gcallinks`, per-user sync setup |
| User notes (personal scratch) | WORKBENCH_ONLY | ★★★★★ | `zp_note`, private per-user |
| Ticket descriptions (HTML) | UNSAFE_RAW | ★★★★★ | TinyMCE HTML, embedded media, @mentions |
| Canvas free-text fields (data1–5) | UNSAFE_RAW | ★★★★★ | MEDIUMTEXT, unstructured, varies by type |
| Comment text (HTML) | UNSAFE_RAW | ★★★★★ | HTML with @mentions, inline images |
| Wiki article content (HTML) | UNSAFE_RAW | ★★★★★ | Large HTML, hierarchical, draft/published |
| Audit log raw values (JSON) | UNSAFE_RAW | ★★★★★ | Arbitrary JSON blobs, may contain PII |
| Timesheet descriptions | UNSAFE_RAW | ★★★★☆ | Free-text, quality varies |
| Event names (auto-generated) | UNSAFE_RAW | ★★★★★ | Class-path-based, rename = breakage |

---

*Generated from Leantime v3.6.2 codebase analysis. All file paths relative to repository root.*
