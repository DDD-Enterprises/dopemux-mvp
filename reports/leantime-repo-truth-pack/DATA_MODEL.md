# Leantime Data Model

> Source of truth for the Leantime database schema, storage model, and data architecture.
> All claims cite actual source files.

---

## Section 1: Complete Table Schema

All 30 tables are defined programmatically in `app/Domain/Install/Services/SchemaBuilder.php`.
Tables use the `zp_` prefix. The schema uses InnoDB engine with `utf8mb4_unicode_ci` collation.

### 1. `zp_calendar`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | |
| dateFrom | DATETIME | YES | | |
| dateTo | DATETIME | YES | | |
| description | TEXT | YES | | |
| kind | VARCHAR(255) | YES | | |
| allDay | VARCHAR(10) | YES | | |

**Indexes:** `idx_calendar_userId_dateFrom_dateTo` (userId, dateFrom, dateTo)

### 2. `zp_canvas`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| title | VARCHAR(255) | YES | | |
| author | INT | YES | | |
| created | DATETIME | YES | | |
| projectId | INT | YES | | |
| type | VARCHAR(45) | YES | | Canvas variant discriminator |
| description | TEXT | YES | | |
| color | VARCHAR(50) | YES | 'ocean' | |
| modified | DATETIME | YES | | |

**Indexes:** `ProjectIdType` (projectId, type), `idx_canvas_type_id` (type, id)

### 3. `zp_canvas_items`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| description | TEXT | YES | | |
| assumptions | TEXT | YES | | |
| data | TEXT | YES | | |
| conclusion | TEXT | YES | | |
| box | VARCHAR(255) | YES | | Canvas section identifier |
| author | INT | YES | | |
| created | DATETIME | YES | | |
| modified | DATETIME | YES | | |
| canvasId | INT | YES | | FK → zp_canvas.id |
| sortindex | INT | YES | | |
| status | VARCHAR(255) | YES | | |
| relates | VARCHAR(255) | YES | | |
| milestoneId | VARCHAR(255) | YES | | |
| title | VARCHAR(255) | YES | | |
| parent | INT | YES | | Self-referential parent item |
| featured | INT | YES | | |
| tags | TEXT | YES | | |
| kpi | INT | YES | | |
| data1 | TEXT | YES | | Generic data fields |
| data2 | TEXT | YES | | |
| data3 | TEXT | YES | | |
| data4 | TEXT | YES | | |
| data5 | TEXT | YES | | |
| startDate | DATETIME | YES | | |
| endDate | DATETIME | YES | | |
| setting | TEXT | YES | | |
| metricType | VARCHAR(45) | YES | | |
| startValue | DECIMAL(10,2) | YES | | |
| currentValue | DECIMAL(10,2) | YES | | |
| endValue | DECIMAL(10,2) | YES | | |
| impact | INT | YES | | |
| effort | INT | YES | | |
| probability | INT | YES | | |
| action | TEXT | YES | | |
| assignedTo | INT | YES | | FK → zp_user.id |

**Indexes:** `CanvasLookUp` (canvasId, box), `idx_canvas_items_box_milestoneId` (box, milestoneId), `idx_canvas_items_box_status_author` (box, status, author), `idx_canvas_items_parent_title` (parent, title)

### 4. `zp_approvals`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| module | VARCHAR(100) | YES | | Entity type |
| entityId | INT | YES | | |
| requestorId | INT | YES | | FK → zp_user.id |
| approverId | INT | YES | | FK → zp_user.id |
| approvalStatus | INT | YES | | |
| requestedOn | DATETIME | YES | | |
| lastStatusChange | DATETIME | YES | | |

**Indexes:** None

### 5. `zp_clients`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| name | VARCHAR(200) | YES | | |
| street | VARCHAR(200) | YES | | |
| zip | INT | YES | | |
| city | VARCHAR(50) | YES | | |
| state | VARCHAR(50) | YES | | |
| country | VARCHAR(50) | YES | | |
| phone | VARCHAR(50) | YES | | |
| internet | VARCHAR(200) | YES | | Website URL |
| published | INT | YES | | |
| age | INT | YES | | |
| email | VARCHAR(255) | YES | | |
| modified | DATETIME | YES | | |

**Indexes:** None

### 6. `zp_comment`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| module | VARCHAR(200) | YES | | Entity type (e.g. 'ticket') |
| userId | INT | YES | | FK → zp_user.id |
| commentParent | INT | YES | | Self-ref for threaded comments |
| date | DATETIME | YES | | |
| moduleId | INT | YES | | Polymorphic entity ID |
| text | TEXT | YES | | |
| status | VARCHAR(50) | YES | | |

**Indexes:** `idx_comment_moduleId_module_commentParent` (moduleId, module, commentParent), `idx_comment_userId_module` (userId, module), `idx_comment_moduleId_module_date` (moduleId, module, date)

### 7. `zp_file`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| module | VARCHAR(50) | YES | | Entity type |
| moduleId | INT | YES | | Polymorphic entity ID |
| userId | INT | YES | | FK → zp_user.id |
| extension | VARCHAR(10) | YES | | |
| encName | VARCHAR(255) | YES | | MD5-hashed filename on disk |
| realName | VARCHAR(255) | YES | | Original filename |
| date | DATETIME | YES | | Upload timestamp |

**Indexes:** `idx_file_module_moduleId_userId` (module, moduleId, userId)

### 8. `zp_gcallinks`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| url | TEXT | YES | | Google Calendar URL |
| name | VARCHAR(255) | YES | | |
| colorClass | VARCHAR(100) | YES | | CSS class for display |

**Indexes:** `idx_gcallinks_userId` (userId)

### 9. `zp_note`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| title | VARCHAR(255) | YES | | |
| description | TEXT | YES | | |

**Indexes:** None

### 10. `zp_projects`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| name | VARCHAR(100) | YES | | |
| clientId | INT | YES | | FK → zp_clients.id |
| details | TEXT | YES | | |
| state | INT | YES | | |
| hourBudget | VARCHAR(255) | YES | '' | |
| dollarBudget | INT | YES | | |
| active | INT | YES | | |
| menuType | TEXT | YES | | |
| psettings | TEXT | YES | | Project-level settings (JSON) |
| parent | INT | YES | | Self-ref for sub-projects |
| type | VARCHAR(45) | YES | | |
| start | DATETIME | YES | | |
| end | DATETIME | YES | | |
| created | DATETIME | YES | | |
| modified | DATETIME | YES | | |
| avatar | TEXT | YES | | |
| cover | TEXT | YES | | |
| sortIndex | INT | YES | | |

**Indexes:** None

### 11. `zp_punch_clock`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | NO | | FK → zp_user.id |
| minutes | INT | YES | | |
| hours | INT | YES | | |
| punchIn | INT | YES | | Unix timestamp |

**Indexes:** `idx_punch_clock_userId` (userId)

### 12. `zp_read`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| module | VARCHAR(50) | YES | | Entity type |
| moduleId | INT | YES | | Polymorphic entity ID |
| userId | INT | YES | | FK → zp_user.id |

**Indexes:** `idx_read_userId_module_moduleId` (userId, module, moduleId)

### 13. `zp_relationuserproject`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| projectId | INT | YES | | FK → zp_projects.id |
| wage | INT | YES | | |
| projectRole | VARCHAR(20) | YES | | |

**Indexes:** `zp_relationuserproject_projectId_index` (projectId), `zp_relationuserproject_userId_index` (userId), `idx_relationuserproject_userId_projectId` (userId, projectId)

### 14. `zp_tickethistory`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| ticketId | INT | YES | | FK → zp_tickets.id |
| changeType | VARCHAR(255) | YES | | |
| changeValue | VARCHAR(150) | YES | | |
| dateModified | DATETIME | YES | | |

**Indexes:** `idx_tickethistory_ticketId` (ticketId)

### 15. `zp_tickets`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| projectId | INT | YES | | FK → zp_projects.id |
| headline | VARCHAR(255) | YES | | |
| description | TEXT | YES | | |
| acceptanceCriteria | TEXT | YES | | |
| date | DATETIME | YES | | Created date |
| dateToFinish | DATETIME | YES | | Due date |
| priority | VARCHAR(60) | YES | | |
| status | INT | YES | | |
| userId | INT | YES | | Creator; FK → zp_user.id |
| os | VARCHAR(30) | YES | | |
| browser | VARCHAR(30) | YES | | |
| resolution | VARCHAR(30) | YES | | |
| component | VARCHAR(100) | YES | | |
| version | VARCHAR(20) | YES | | |
| url | VARCHAR(100) | YES | | |
| dependingTicketId | INT | YES | | FK → zp_tickets.id |
| editFrom | DATETIME | YES | | Gantt start |
| editTo | DATETIME | YES | | Gantt end |
| editorId | VARCHAR(75) | YES | | Assignee (comma-separated) |
| planHours | FLOAT | YES | | |
| hourRemaining | FLOAT | YES | | |
| type | VARCHAR(255) | YES | | task, bug, story, etc. |
| production | INT | NO | 0 | |
| staging | INT | NO | 0 | |
| storypoints | FLOAT | YES | | |
| sprint | INT | YES | | FK → zp_sprints.id |
| sortindex | BIGINT | YES | | |
| kanbanSortIndex | BIGINT | YES | | |
| tags | VARCHAR(255) | YES | | |
| milestoneid | INT | YES | | FK → zp_tickets.id (milestone) |
| leancanvasitemid | INT | YES | | FK → zp_canvas_items.id |
| retrospectiveid | INT | YES | | FK → zp_canvas_items.id |
| ideaid | INT | YES | | FK → zp_canvas_items.id |
| zp_ticketscol | VARCHAR(45) | YES | | |
| modified | DATETIME | YES | | |

**Indexes:** `ProjectUserId` (projectId, userId), `StatusSprint` (status, sprint), `Sorting` (sortindex), `idx_tickets_editorId` (editorId), `idx_tickets_milestoneid` (milestoneid), `idx_tickets_editFrom` (editFrom), `idx_tickets_editTo` (editTo), `idx_tickets_dateToFinish` (dateToFinish), `idx_tickets_modified` (modified), `idx_tickets_projectId_status` (projectId, status), `idx_tickets_projectId_type` (projectId, type), `idx_tickets_status_type` (status, type), `idx_tickets_dependingTicketId` (dependingTicketId)

### 16. `zp_timesheets`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| ticketId | INT | YES | | FK → zp_tickets.id |
| workDate | DATETIME | YES | | |
| hours | FLOAT | YES | | |
| description | TEXT | YES | | |
| kind | VARCHAR(175) | YES | | Time entry category |
| invoicedEmpl | INT | YES | | |
| invoicedComp | INT | YES | | |
| invoicedEmplDate | DATETIME | YES | | |
| invoicedCompDate | DATETIME | YES | | |
| rate | VARCHAR(255) | YES | | |
| paid | INT | YES | | |
| paidDate | DATETIME | YES | | |
| modified | DATETIME | YES | | |

**Unique Constraint:** `Unique` (userId, ticketId, workDate, kind)
**Indexes:** `idx_timesheets_ticketId` (ticketId), `idx_timesheets_userId_workDate` (userId, workDate), `idx_timesheets_ticketId_workDate` (ticketId, workDate)

### 17. `zp_user`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| username | VARCHAR(175) | NO | | Email address |
| password | VARCHAR(255) | YES | '' | Hashed |
| firstname | VARCHAR(100) | YES | '' | |
| lastname | VARCHAR(100) | YES | '' | |
| phone | VARCHAR(25) | YES | '' | |
| profileId | VARCHAR(100) | YES | '' | External profile ID |
| lastlogin | DATETIME | YES | | |
| status | VARCHAR(1) | NO | 'A' | A=Active |
| expires | DATETIME | YES | | |
| role | VARCHAR(200) | NO | | Role key (e.g. '50' for owner) |
| session | VARCHAR(100) | YES | | |
| sessiontime | VARCHAR(50) | YES | | |
| wage | INT | YES | | |
| hours | INT | YES | | |
| description | TEXT | YES | | |
| clientId | INT | YES | | FK → zp_clients.id |
| notifications | INT | YES | | |
| pwReset | VARCHAR(100) | YES | | Password reset token |
| pwResetExpiration | DATETIME | YES | | |
| pwResetCount | INT | YES | | |
| forcePwReset | TINYINT | YES | | |
| lastpwd_change | DATETIME | YES | | |
| settings | TEXT | YES | | User preferences (JSON) |
| twoFAEnabled | TINYINT | NO | 0 | |
| twoFASecret | VARCHAR(200) | YES | | |
| createdOn | DATETIME | YES | | |
| source | VARCHAR(200) | YES | | Auth source (ldap, oidc, etc.) |
| jobTitle | VARCHAR(200) | YES | | |
| jobLevel | VARCHAR(50) | YES | | |
| department | VARCHAR(200) | YES | | |
| modified | DATETIME | YES | | |

**Unique Constraint:** `username` (username)
**Indexes:** `idx_user_clientId` (clientId)

### 18. `zp_sprints`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| projectId | INT | YES | | FK → zp_projects.id |
| name | VARCHAR(45) | YES | | |
| startDate | DATETIME | YES | | |
| endDate | DATETIME | YES | | |
| modified | DATETIME | YES | | |

**Indexes:** `idx_sprints_projectId_startDate_endDate` (projectId, startDate, endDate)

### 19. `zp_stats`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| sprintId | INT | YES | | FK → zp_sprints.id |
| projectId | INT | YES | | FK → zp_projects.id |
| date | DATETIME | YES | | Snapshot date |
| sum_todos | INT | YES | | |
| sum_open_todos | INT | YES | | |
| sum_progres_todos | INT | YES | | |
| sum_closed_todos | INT | YES | | |
| sum_planned_hours | FLOAT | YES | | |
| sum_estremaining_hours | FLOAT | YES | | |
| sum_logged_hours | FLOAT | YES | | |
| sum_points | INT | YES | | |
| sum_points_done | INT | YES | | |
| sum_points_progress | INT | YES | | |
| sum_points_open | INT | YES | | |
| sum_todos_xs | INT | YES | | |
| sum_todos_s | INT | YES | | |
| sum_todos_m | INT | YES | | |
| sum_todos_l | INT | YES | | |
| sum_todos_xl | INT | YES | | |
| sum_todos_xxl | INT | YES | | |
| sum_todos_none | INT | YES | | |
| tickets | INT | YES | | |
| daily_avg_hours_booked_todo | FLOAT | YES | | |
| daily_avg_hours_booked_point | FLOAT | YES | | |
| daily_avg_hours_planned_todo | FLOAT | YES | | |
| daily_avg_hours_planned_point | FLOAT | YES | | |
| daily_avg_hours_remaining_point | FLOAT | YES | | |
| daily_avg_hours_remaining_todo | FLOAT | YES | | |
| sum_teammembers | INT | YES | | |

**⚠ No primary key.** This is a time-series snapshot table.
**Indexes:** `idx_stats_projectId` (projectId, sprintId), `idx_stats_projectId_sprintId_date` (projectId, sprintId, date), `idx_stats_sprintId_date` (sprintId, date)

### 20. `zp_settings`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| key | VARCHAR(175) | NO | | **PK** (natural key) |
| value | TEXT | YES | | |

**⚠ Uses VARCHAR primary key**, not auto_increment. Key-value store for system settings.

### 21. `zp_audit`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| projectId | INT | YES | | FK → zp_projects.id |
| action | VARCHAR(45) | YES | | |
| entity | VARCHAR(45) | YES | | |
| entityId | INT | YES | | |
| values | TEXT | YES | | JSON payload |
| date | DATETIME | YES | | |

**Indexes:** `idx_audit_projectId` (projectId), `idx_audit_projectAction` (projectId, action), `idx_audit_projectEntityEntityId` (projectId, entity, entityId)

### 22. `zp_queue`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| msghash | VARCHAR(50) | NO | | **PK** (content hash) |
| channel | VARCHAR(255) | YES | | Worker channel |
| userId | INT | NO | | FK → zp_user.id |
| subject | VARCHAR(255) | YES | | |
| message | TEXT | NO | | |
| thedate | DATETIME | NO | | |
| projectId | INT | NO | | FK → zp_projects.id |

**⚠ Uses VARCHAR primary key** (message hash for deduplication).
**Indexes:** `idx_queue_projectId` (projectId), `idx_queue_userId` (userId)

### 23. `zp_plugins`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| name | VARCHAR(45) | YES | | |
| enabled | TINYINT | YES | | |
| description | VARCHAR(255) | YES | | |
| version | VARCHAR(45) | YES | | |
| installdate | DATETIME | YES | | |
| foldername | VARCHAR(45) | YES | | |
| homepage | VARCHAR(255) | YES | | |
| authors | VARCHAR(255) | YES | | |
| license | TEXT | YES | | License key data |
| format | VARCHAR(45) | YES | | 'folder' or 'phar' |

**Indexes:** None

### 24. `zp_notifications`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | NO | | FK → zp_user.id |
| read | INT | YES | | 0/1 flag |
| type | VARCHAR(45) | YES | | |
| module | VARCHAR(45) | YES | | |
| moduleId | INT | YES | | |
| datetime | DATETIME | YES | | |
| url | VARCHAR(255) | YES | | |
| authorId | INT | YES | | FK → zp_user.id |
| message | TEXT | YES | | |

**Indexes:** `idx_notifications_userId` (userId), `idx_notifications_userId_datetime` (userId, datetime), `idx_notifications_userId_read` (userId, read)

### 25. `zp_entity_relationship`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| entityA | INT | YES | | |
| entityAType | VARCHAR(45) | YES | | |
| entityB | INT | YES | | |
| entityBType | VARCHAR(45) | YES | | |
| relationship | VARCHAR(45) | YES | | Relationship type label |
| createdOn | DATETIME | YES | | |
| createdBy | INT | YES | | FK → zp_user.id |
| meta | TEXT | YES | | JSON metadata |

**Indexes:** `idx_entity_relationship_entityA` (entityA, entityAType, relationship), `idx_entity_relationship_entityB` (entityB, entityBType, relationship)

### 26. `zp_integration`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| providerId | VARCHAR(45) | YES | | |
| method | VARCHAR(45) | YES | | |
| entity | VARCHAR(45) | YES | | |
| fields | TEXT | YES | | Field mappings (JSON) |
| schedule | VARCHAR(45) | YES | | |
| notes | VARCHAR(45) | YES | | |
| auth | TEXT | YES | | Auth credentials (JSON) |
| meta | VARCHAR(45) | YES | | |
| createdOn | DATETIME | YES | | |
| createdBy | INT | YES | | FK → zp_user.id |
| lastSync | VARCHAR(45) | YES | | |

**Indexes:** None

### 27. `zp_reactions`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| userId | INT | YES | | FK → zp_user.id |
| moduleId | INT | YES | | Polymorphic entity ID |
| module | VARCHAR(45) | YES | | Entity type |
| reaction | VARCHAR(45) | YES | | Reaction type (emoji, etc.) |
| date | DATETIME | YES | | |

**Indexes:** `idx_reactions_entity` (moduleId, module, reaction), `idx_reactions_user` (userId, moduleId, module, reaction)

### 28. `zp_access_tokens`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| tokenable_type | VARCHAR(255) | NO | | Polymorphic type (model class) |
| tokenable_id | BIGINT UNSIGNED | NO | | Polymorphic ID |
| name | VARCHAR(255) | NO | | Token name |
| token | VARCHAR(64) | NO | | SHA-256 hash |
| abilities | TEXT | YES | | JSON array of abilities |
| last_used_at | TIMESTAMP | YES | | |
| expires_at | TIMESTAMP | YES | | |
| created_at | TIMESTAMP | YES | | |
| updated_at | TIMESTAMP | YES | | |

**Unique Constraint:** `personal_access_tokens_token_unique` (token)
**Indexes:** `personal_access_tokens_tokenable_type_tokenable_id_index` (tokenable_type, tokenable_id)

### 29. `zp_jobs`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| queue | VARCHAR(255) | NO | | Queue name |
| payload | LONGTEXT | NO | | Serialized job data |
| attempts | TINYINT UNSIGNED | NO | | |
| reserved_at | INT UNSIGNED | YES | | Unix timestamp |
| available_at | INT UNSIGNED | NO | | Unix timestamp |
| created_at | INT UNSIGNED | NO | | Unix timestamp |

**Indexes:** `zp_jobs_queue_index` (queue)

### 30. `zp_recurring_patterns`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | auto_increment | **PK** |
| entityId | INT | NO | | Polymorphic entity ID |
| module | VARCHAR(50) | NO | | Entity type |
| type | VARCHAR(50) | NO | | Recurrence type |
| trigger | VARCHAR(50) | NO | | Trigger condition |
| interval | INT | NO | 1 | |
| weekDays | TEXT | YES | | JSON array |
| monthDay | INT | YES | | |
| months | TEXT | YES | | JSON array |
| action | VARCHAR(20) | NO | 'reset' | |
| lastProcessed | DATETIME | YES | | |
| nextProcessingDate | DATETIME | YES | | |
| enabled | TINYINT | NO | 1 | |

**Indexes:** `idx_recurring_patterns_entityId` (entityId)

---

## Section 2: Entity Relationships

The database uses **implicit foreign keys** — no formal `FOREIGN KEY` constraints are defined in `SchemaBuilder.php`. All relationships are enforced at the application level.

### Core Entity Graph

```
zp_clients (1) ──────────────── (N) zp_projects
    │                                    │
    │                                    ├──── (N) zp_tickets
    │                                    ├──── (N) zp_sprints
    │                                    ├──── (N) zp_canvas
    │                                    ├──── (N) zp_stats
    │                                    ├──── (N) zp_audit
    │                                    └──── (N) zp_queue
    │
    └──── (N) zp_user
              │
              ├──── (N) zp_tickets         (as creator via userId)
              ├──── (N) zp_tickets         (as assignee via editorId)
              ├──── (N) zp_timesheets
              ├──── (N) zp_comment
              ├──── (N) zp_file
              ├──── (N) zp_calendar
              ├──── (N) zp_gcallinks
              ├──── (N) zp_note
              ├──── (N) zp_punch_clock
              ├──── (N) zp_read
              ├──── (N) zp_notifications
              ├──── (N) zp_reactions
              ├──── (N) zp_audit
              ├──── (N) zp_approvals       (as requestor and approver)
              └──── (N) zp_access_tokens   (via tokenable_id)
```

### Key Relationship Details

| Parent | Child | Join Column(s) | Cardinality |
|--------|-------|----------------|-------------|
| zp_clients | zp_projects | projects.clientId = clients.id | 1:N |
| zp_clients | zp_user | user.clientId = clients.id | 1:N |
| zp_projects | zp_tickets | tickets.projectId = projects.id | 1:N |
| zp_projects | zp_sprints | sprints.projectId = projects.id | 1:N |
| zp_projects | zp_canvas | canvas.projectId = projects.id | 1:N |
| zp_projects | zp_stats | stats.projectId = projects.id | 1:N |
| zp_user | zp_tickets | tickets.userId = user.id (creator) | 1:N |
| zp_user | zp_tickets | tickets.editorId LIKE user.id (assignee) | 1:N |
| zp_user | zp_timesheets | timesheets.userId = user.id | 1:N |
| zp_tickets | zp_timesheets | timesheets.ticketId = tickets.id | 1:N |
| zp_tickets | zp_tickethistory | tickethistory.ticketId = tickets.id | 1:N |
| zp_tickets | zp_tickets | tickets.dependingTicketId = tickets.id | 1:N (self) |
| zp_tickets | zp_tickets | tickets.milestoneid = tickets.id | 1:N (self) |
| zp_sprints | zp_tickets | tickets.sprint = sprints.id | 1:N |
| zp_canvas | zp_canvas_items | canvas_items.canvasId = canvas.id | 1:N |
| zp_canvas_items | zp_canvas_items | canvas_items.parent = canvas_items.id | 1:N (self) |
| zp_user + zp_projects | zp_relationuserproject | Junction: userId + projectId | M:N |

### Polymorphic Relationships

Several tables use a `module` + `moduleId` pattern for polymorphic associations:

| Table | module column | moduleId column | Associates with |
|-------|--------------|-----------------|-----------------|
| zp_comment | module | moduleId | tickets, canvas_items, projects, etc. |
| zp_file | module | moduleId | tickets, projects, canvas_items, etc. |
| zp_read | module | moduleId | Any entity (read tracking) |
| zp_reactions | module | moduleId | Any entity (emoji reactions) |
| zp_recurring_patterns | module | entityId | Any entity |
| zp_approvals | module | entityId | Any entity |

---

## Section 3: ID and Uniqueness Guarantees

| Table | PK Strategy | Unique Constraints | Notes |
|-------|-------------|-------------------|-------|
| zp_calendar | auto_increment BIGINT | None | |
| zp_canvas | auto_increment BIGINT | None | |
| zp_canvas_items | auto_increment BIGINT | None | |
| zp_approvals | auto_increment BIGINT | None | |
| zp_clients | auto_increment BIGINT | None | |
| zp_comment | auto_increment BIGINT | None | |
| zp_file | auto_increment BIGINT | None | |
| zp_gcallinks | auto_increment BIGINT | None | |
| zp_note | auto_increment BIGINT | None | |
| zp_projects | auto_increment BIGINT | None | |
| zp_punch_clock | auto_increment BIGINT | None | |
| zp_read | auto_increment BIGINT | None | |
| zp_relationuserproject | auto_increment BIGINT | None | userId+projectId indexed but not unique |
| zp_tickethistory | auto_increment BIGINT | None | |
| zp_tickets | auto_increment BIGINT | None | |
| zp_timesheets | auto_increment BIGINT | `(userId, ticketId, workDate, kind)` | Prevents duplicate time entries |
| zp_user | auto_increment BIGINT | `username` | Email-based uniqueness |
| zp_sprints | auto_increment BIGINT | None | |
| zp_stats | **None** | None | Append-only snapshot table |
| zp_settings | VARCHAR(175) natural key | PK on `key` | Key-value store |
| zp_audit | auto_increment BIGINT | None | |
| zp_queue | VARCHAR(50) natural key | PK on `msghash` | Content-hash dedup |
| zp_plugins | auto_increment BIGINT | None | |
| zp_notifications | auto_increment BIGINT | None | |
| zp_entity_relationship | auto_increment BIGINT | None | |
| zp_integration | auto_increment BIGINT | None | |
| zp_reactions | auto_increment BIGINT | None | |
| zp_access_tokens | auto_increment BIGINT | `token` | SHA-256 token hash |
| zp_jobs | auto_increment BIGINT | None | |
| zp_recurring_patterns | auto_increment BIGINT | None | |

**Key observations:**
- No UUIDs are used anywhere in the schema.
- 27 of 30 tables use auto_increment BIGINT UNSIGNED as PK.
- 2 tables use VARCHAR natural keys: `zp_settings` (key), `zp_queue` (msghash).
- 1 table (`zp_stats`) has no primary key at all.

---

## Section 4: File Storage Model

> Sources: `app/Core/Files/FileManager.php`, `app/Domain/Files/Services/Files.php`, `app/Core/Configuration/laravelConfig.php`

### Storage Adapters

| Adapter | Driver | Root Path | Condition |
|---------|--------|-----------|-----------|
| **Local** (default) | `local` | `userfiles/` (app root) | `LEAN_USE_S3=false` |
| **Public** | `local` | `public/userfiles/` | Public-accessible files |
| **S3** | `s3` | Configured bucket/folder | `LEAN_USE_S3=true` |

### Local Storage

- **Path**: `userfiles/` relative to application root (configurable via `LEAN_USER_FILE_PATH`)
- **Naming**: Files are renamed using MD5 hash of `session_userdata_id + timestamp` (configurable via `LEAN_FILESYSTEM_RENAME_FILES`, default `true`)
- **On disk**: `{encName}.{extension}` (e.g., `a1b2c3d4e5f6g7h8.pdf`)
- **Metadata**: Stored in `zp_file` table (encName, realName, extension, module, moduleId, userId, date)

### S3 Storage

Controlled by environment variables:

| Variable | Purpose |
|----------|---------|
| `LEAN_USE_S3` | Master switch (bool) |
| `LEAN_S3_KEY` | AWS access key |
| `LEAN_S3_SECRET` | AWS secret key |
| `LEAN_S3_BUCKET` | Bucket name |
| `LEAN_S3_REGION` | AWS region |
| `LEAN_S3_END_POINT` | Custom endpoint for S3-compatible services |
| `LEAN_S3_FOLDER_NAME` | Prefix/folder within bucket |
| `LEAN_S3_USE_PATH_STYLE_ENDPOINT` | Path-style vs virtual-hosted URLs |

- Uses Laravel Flysystem S3 adapter
- Temporary signed URLs with 60-second expiration + jitter to prevent cache stampede
- File URLs cached for 60 seconds (non-S3 storage)

### File Validation

- Filename sanitization removes special characters, path traversal attempts, control characters
- File size validated against PHP `upload_max_filesize` and `post_max_size` limits
- MIME type determined from extension

---

## Section 5: Cache, Session, and Log Storage

> Source: `app/Core/Configuration/laravelConfig.php`

### Cache

| Setting | Value |
|---------|-------|
| Default store | `installation` (file-based) |
| File path | `storage/framework/cache/installation/data` |
| Redis option | Available when `LEAN_USE_REDIS=true` |
| Redis prefix | `leantime_cache` |
| Redis client | `phpredis` with LZ4 compression |

### Sessions

| Setting | Value |
|---------|-------|
| Driver | `file` (default) |
| File path | `storage/framework/sessions` |
| Lifetime | 480 minutes / 8 hours (`LEAN_SESSION_EXPIRATION`) |
| Cookie name | `leantime_session` |
| Same-site | `lax` |
| HTTP only | `true` |
| Secure | `false` (configurable via `LEAN_SESSION_SECURE`) |
| Redis option | Available when `LEAN_USE_REDIS=true` |

### Logging

| Setting | Value |
|---------|-------|
| Default path | `storage/logs/error.log` (configurable via `LEAN_LOG_PATH`) |
| Channels | Stack-based: `single`, `syslog`, `sentry`, `stderr` (via `LEAN_LOG_CHANNELS`) |
| Rotation | Daily, 5-day retention |
| Level | `debug` if `LEAN_DEBUG=1`, else `error` |
| Sentry DSN | Via `LEAN_SENTRY_LARAVEL_DSN` or `LEAN_SENTRY_DSN` |

---

## Section 6: Config Locations

> Sources: `config/sample.env`, `app/Core/Configuration/DefaultConfig.php`, `app/Core/Configuration/laravelConfig.php`, `app/Core/Bootstrap/LoadConfig.php`

### Config Priority Order (highest wins)

1. **Environment variables** (OS-level)
2. **`config/.env`** file (user-created from sample)
3. **`app/Core/Configuration/laravelConfig.php`** (Laravel framework config)
4. **`app/Core/Configuration/DefaultConfig.php`** (hardcoded defaults)

### Config File Locations

| File | Purpose |
|------|---------|
| `config/sample.env` | Template for user configuration; all `LEAN_*` variables |
| `config/.env` | Active user configuration (created from sample) |
| `app/Core/Configuration/DefaultConfig.php` | PHP class with all default values and `#[LaravelConfig]` attribute mappings |
| `app/Core/Configuration/laravelConfig.php` | Single file containing ALL Laravel config (replaces standard `config/*.php` files) |
| `zp_settings` table | Runtime key-value settings (site name, theme, company ID, etc.) |

### Important Notes

- **No standard `config/*.php` files**: All Laravel config lives in `laravelConfig.php`. Standard `artisan vendor:publish` will NOT work.
- **`DefaultConfig.php`** uses `#[LaravelConfig('dotted.key')]` PHP attributes to map properties to Laravel config keys.
- **`LoadConfig.php`** (custom bootstrapper) creates an `Environment` instance as config repository, NOT Laravel's standard Repository.
- **User-editable variables** use `LEAN_*` prefix in `.env` files.
- **Database settings** in `zp_settings` are for runtime/UI-configurable values (e.g., company name, installed version, theme preferences).

---

## Section 7: Multi-user and Concurrency

> Sources: `app/Domain/Tickets/Repositories/Tickets.php`, `app/Domain/Timesheets/Repositories/Timesheets.php`

### Transaction Usage

Only **two** explicit transaction patterns were found in the entire codebase:

#### 1. Ticket Bulk Sort Update
```php
// app/Domain/Tickets/Repositories/Tickets.php (~line 1766)
$this->connection->beginTransaction();
foreach ($updates as $ticketId => $sortIndex) {
    $this->connection->table('zp_tickets')
        ->where('id', (int) $ticketId)
        ->update(['sortindex' => (int) $sortIndex, 'modified' => ...]);
}
$this->connection->commit();  // or rollBack() on exception
```
**Purpose:** Atomic bulk reorder of ticket sort indices.

#### 2. Timesheet Punch Clock
```php
// app/Domain/Timesheets/Repositories/Timesheets.php (~line 700)
return $this->db->transaction(function () use ($ticketId, $inTimestamp, $hoursWorked) {
    // Delete punch clock record + insert/update timesheet (ON DUPLICATE KEY UPDATE)
});
```
**Purpose:** Atomically convert punch clock entry to timesheet record.

### What Is NOT Present

| Mechanism | Status |
|-----------|--------|
| `lockForUpdate()` | ❌ Not used |
| `sharedLock()` | ❌ Not used |
| Optimistic locking (version columns) | ❌ Not used |
| Advisory/mutex locks | ❌ Not used |
| Distributed queue locks | ❌ Not used |
| `updated_at`-based conflict detection | ❌ Not used |

### Deduplication

- **Timesheets**: Unique constraint on `(userId, ticketId, workDate, kind)` with `ON DUPLICATE KEY UPDATE` prevents duplicate time entries at the database level.
- **Queue**: `msghash` primary key (content hash) prevents duplicate message enqueuing.

### Concurrency Implications

- Most write operations are **not wrapped in transactions** and are vulnerable to race conditions under concurrent modification.
- Queue workers process independently without distributed locks — multiple instances could theoretically process the same job.
- The database uses MySQL's default `REPEATABLE READ` isolation level (InnoDB).
- No explicit isolation level overrides are set anywhere in the codebase.
