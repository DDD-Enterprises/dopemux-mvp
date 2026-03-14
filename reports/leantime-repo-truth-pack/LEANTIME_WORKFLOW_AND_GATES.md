# LEANTIME WORKFLOW, STATE, GATING & TRANSITION LOGIC

> Generated from source analysis of the Leantime codebase. Every claim cites exact file paths and line numbers.
> Items that could not be confirmed from code are marked **UNKNOWN**.

---

## TABLE OF CONTENTS

1. [Ticket State Machine](#1-ticket-state-machine)
2. [Project State Machine](#2-project-state-machine)
3. [Goal State Machine](#3-goal-state-machine)
4. [Sprint Semantics](#4-sprint-semantics)
5. [Milestone Semantics](#5-milestone-semantics)
6. [Role/Permission Gating](#6-rolepermission-gating)
7. [Dependency/Blocker Semantics](#7-dependencyblocker-semantics)
8. [Validation Gates](#8-validation-gates)
9. [Background Job Effects](#9-background-job-effects)
10. [Archival/Closure Semantics](#10-archivalclosure-semantics)
11. [Write Conflict / Race-Risk Notes](#11-write-conflict--race-risk-notes)
12. [Missing Evidence](#12-missing-evidence)

---

## 1. TICKET STATE MACHINE

### 1.1 Status Definitions

**Source:** `app/Domain/Tickets/Repositories/Tickets.php:32–75`

| Code | Name | CSS Class | statusType | Kanban Column | sortKey |
|------|------|-----------|-----------|---------------|---------|
| 3 | `status.new` | `label-info` | `NEW` | ✅ yes | 1 |
| 1 | `status.blocked` | `label-important` | `INPROGRESS` | ✅ yes | 2 |
| 4 | `status.in_progress` | `label-warning` | `INPROGRESS` | ✅ yes | 3 |
| 2 | `status.waiting_for_approval` | `label-warning` | `INPROGRESS` | ✅ yes | 4 |
| 0 | `status.done` | `label-success` | `DONE` | ✅ yes | 5 |
| -1 | `status.archived` | `label-default` | `DONE` | ❌ no | 6 |

**Status type groups** (used for milestone progress and queries):

| statusType | Status Codes | SQL Filter |
|-----------|-------------|------------|
| `NEW` | 3 | `IN(3)` |
| `INPROGRESS` | 1, 2, 4 | `IN(1,2,4)` |
| `DONE` | 0, -1 | `IN(0,-1)` |
| `ALLOPEN` | 1, 2, 3, 4 | `IN(1,2,3,4)` |

**Source:** `app/Domain/Tickets/Repositories/Tickets.php:189–230` (`getStatusListGroupedByType()`)

### 1.2 Custom Status Labels Per Project

Projects can override status labels. Custom labels are stored in `zp_settings` under key `projectsettings.{projectId}.ticketlabels` and cached for 1 hour.

**Source:** `app/Domain/Tickets/Repositories/Tickets.php:120–179` (`getStateLabels()`)

- Line 130–133: Reads from `zp_settings` table
- Line 144–146: Archive status (-1) is **always preserved** even if removed from custom labels
- Line 176: Cached with 3600-second TTL

### 1.3 Default Status for New Tickets

New tickets default to status `3` (NEW).

**Source:** `app/Domain/Tickets/Services/Tickets.php:1955` — `'status' => $values['status'] ?? 3`

### 1.4 Ticket Types

**Source:** `app/Domain/Tickets/Repositories/Tickets.php:81–83`

```php
public array $type = ['task', 'subtask', 'story', 'bug'];
public array $typeIcons = ['story' => 'fa-book', 'task' => 'fa-check-square', 'subtask' => 'fa-diagram-successor', 'bug' => 'fa-bug'];
```

Additionally, `milestone` is a ticket type handled via separate code paths but stored in the same `zp_tickets` table.

### 1.5 Status Transition Logic

**CRITICAL FINDING: There are NO transition restrictions.** Any status can transition to any other status. The codebase does not validate status transitions — there is no state machine enforcement.

#### Transition Methods

**A. `updateTicket($values)` — Full ticket update**
**Source:** `app/Domain/Tickets/Services/Tickets.php:2047–2123`

- Accepts any status value in `$values['status']` (line 2069)
- Validates: project access (line 2090–2091), headline present (line 2049)
- No status transition validation
- Events: `ticket_updated` (line 2117)
- Notifications: `action = 'updated'` (line 2109)

**B. `patch($id, $params)` — Partial update**
**Source:** `app/Domain/Tickets/Services/Tickets.php:2160–2210`

- Accepts any fields including `status`
- **IMPORTANT SIDE EFFECT (line 2206):** When `status` is included in `$params`, after updating, the method recursively calls itself to clear `sprint`, `dependingTicketId`, and `milestoneid` to empty strings
- Events: `ticket_updated` (lines 2179, 2203)
- Notifications: `action = 'status_changed'` (line 2195)

**C. `updateTicketStatusAndSorting($params, $handler)` — Kanban drag-and-drop**
**Source:** `app/Domain/Tickets/Services/Tickets.php:2416–2470`

- Parses serialized kanban column data
- Updates status AND kanban sort position via `updateTicketStatus()` (line 2431)
- Events: `ticket_updated` (line 2467)
- Notifications: `action = 'status_changed'` (line 2457)

**D. Repository: `updateTicketStatus($ticketId, $status, $ticketSorting, $handler)`**
**Source:** `app/Domain/Tickets/Repositories/Tickets.php:1525–1543`

- Logs change via `addTicketChange()` (line 1527)
- Dispatches `ticketStatusUpdate` event (line 1538)
- Updates `status`, `modified` timestamp, and optionally `kanbanSortIndex`

**E. Repository: `patchTicket($id, $params)`**
**Source:** `app/Domain/Tickets/Repositories/Tickets.php:1462–1483`

- Sanitizes column names (line 1468–1470)
- If `status` is in params, dispatches `ticketStatusUpdate` event (line 1474)
- Records change history via `addTicketChange()` (line 1464)

### 1.6 Transition Table

Since there are no transition restrictions, every cell below is ALLOWED:

| From ↓ \ To → | NEW (3) | BLOCKED (1) | IN_PROGRESS (4) | WAITING (2) | DONE (0) | ARCHIVED (-1) |
|----------------|---------|-------------|------------------|-------------|----------|---------------|
| **NEW (3)** | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| **BLOCKED (1)** | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| **IN_PROGRESS (4)** | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| **WAITING (2)** | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **DONE (0)** | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| **ARCHIVED (-1)** | ✅ | ✅ | ✅ | ✅ | ✅ | — |

**Conditions:** User must be assigned to the project (service-level check). Controller-level check requires role ≥ editor (20).

**Side effects of status change via `patch()`:** Sprint, dependingTicketId, and milestoneid are **cleared** (set to empty string) after any status change through the `patch()` method.
**Source:** `app/Domain/Tickets/Services/Tickets.php:2206`

### 1.7 Events Dispatched on Status Change

| Event | Source |
|-------|--------|
| `ticket_updated` (service) | `Tickets.php:2117`, `2179`, `2203`, `2305`, `2467` |
| `ticketStatusUpdate` (repository) | `Tickets.php:1538`, `1474` |
| `ticket_created` (service) | `Tickets.php:1984`, `2296` |
| `ticket_deleted` (service) | `Tickets.php:2491` |
| `milestone_created` (service) | `Tickets.php:1902` |
| `milestone_updated` (service) | `Tickets.php:2251` |
| `milestone_deleted` (service) | `Tickets.php:2535` |
| `statusLabels_updated` (repository) | `Tickets.php:147` |

---

## 2. PROJECT STATE MACHINE

### 2.1 State Definitions

**Source:** `app/Domain/Projects/Repositories/Projects.php:33`

```php
public array $state = [0 => 'OPEN', 1 => 'CLOSED', null => 'OPEN'];
```

| Code | State | Notes |
|------|-------|-------|
| 0 | OPEN | Default |
| null | OPEN | Treated same as 0 |
| 1 | CLOSED | Blocked if project has tickets (in controller) |
| -1 | HIDDEN | Excluded from most queries; used in `getUserProjects` filter |

### 2.2 State Transitions

#### Closing a Project (state → 1)

**Source:** `app/Domain/Projects/Controllers/ShowProject.php:246–248`

```php
if ($this->projectRepo->hasTickets($id) && $values['state'] == 1) {
    $this->tpl->setNotification($this->language->__('notification.project_has_tickets'), 'error');
}
```

**Gate:** A project **cannot be closed** (`state = 1`) if it has non-subtask, non-milestone tickets. The `hasTickets()` method excludes subtasks and milestones from the check.

**Source:** `app/Domain/Projects/Repositories/Projects.php:822–828`

```php
public function hasTickets($id): bool
{
    return $this->connection->table('zp_tickets')
        ->where('projectId', $id)
        ->where('zp_tickets.type', '<>', 'subtask')
        ->where('zp_tickets.type', '<>', 'milestone')
        ->exists();
}
```

#### Deleting a Project

**Source:** `app/Domain/Projects/Controllers/DelProject.php:34,37,45–47`

- Requires role: MANAGER or higher (`forceGlobalRoleCheck = true`)
- `hasTickets()` check is informational only (warning shown, not blocking)
- Deletion is **hard delete** — no soft delete
- **Cascading:** All tickets in the project are hard-deleted, all user relations removed

**Source:** `app/Domain/Projects/Repositories/Projects.php:807–817`

```php
public function deleteProject($id): void
{
    $this->connection->table('zp_projects')->where('id', $id)->limit(1)->delete();
    $this->connection->table('zp_tickets')->where('projectId', $id)->delete();
}
```

**Source:** `app/Domain/Projects/Controllers/DelProject.php:46–47`

```php
$this->projectRepo->deleteProject($id);
$this->projectRepo->deleteAllUserRelations($id);
```

#### Editing Project State

**Source:** `app/Domain/Projects/Repositories/Projects.php:747–781` (`editProject()`)

- Updates `state` column directly (line 768): `'state' => $values['state'] ?? ''`
- Dispatches `editProject` event (line 780)

#### Kanban-Style State + Sort Update

**Source:** `app/Domain/Projects/Services/Projects.php:2022–2044` (`updateProjectStatusAndSorting()`)

- Parses serialized kanban data, updates both `sortIndex` and `state` via `patch()`

### 2.3 State Query Filtering

**Source:** `app/Domain/Projects/Repositories/Projects.php:71–76` (`getAll()`)

```php
if ($showClosedProjects === false) {
    $query->where(function ($q) {
        $q->whereNull('project.state')->orWhere('project.state', '<>', -1);
    });
}
```

**Source:** `app/Domain/Projects/Repositories/Projects.php:328–335` (`getUserProjects()`)

- `projectStatus == 'open'`: `state <> -1 OR state IS NULL`
- `projectStatus == 'closed'`: `state = -1`

### 2.4 Transition Table

| From ↓ \ To → | OPEN (0) | CLOSED (1) | HIDDEN (-1) |
|----------------|----------|------------|-------------|
| **OPEN (0)** | — | ✅ (if no tickets) | ✅ |
| **CLOSED (1)** | ✅ | — | ✅ |
| **HIDDEN (-1)** | ✅ | ✅ (if no tickets) | — |

**Authority:** MANAGER (≥30) with `forceGlobalRoleCheck = true`

---

## 3. GOAL STATE MACHINE

### 3.1 Status Definitions

**Source:** `app/Domain/Goalcanvas/Repositories/Goalcanvas.php:45–50`

| Key | Icon | Color | Dropdown | Meaning |
|-----|------|-------|----------|---------|
| `status_ontrack` | `fa-circle-check` | green | `success` | On track |
| `status_atrisk` | `fa-triangle-exclamation` | yellow | `warning` | At risk |
| `status_miss` | `fa-circle-xmark` | red | `danger` | Missed |

### 3.2 Status Storage

Goal status is stored in the `zp_canvas_items.status` column as `VARCHAR(255)`. Goals are identified by `box = 'goal'`.

**Source:** `app/Domain/Install/Repositories/Install.php:402–444` (schema); `app/Domain/Goalcanvas/Repositories/Goalcanvas.php:241` (insert)

### 3.3 Status Transitions

Goal status is **manually set** — there is no auto-calculation of on_track/at_risk/miss from metrics. The status field is simply a user-chosen label.

Goal **progress** (a percentage) IS auto-calculated, but it is separate from the status label.

### 3.4 Goal Progress Calculation

**Source:** `app/Domain/Goalcanvas/Services/Goalcanvas.php:28–58`

```
goalProgress = max(0, min(100, round((currentValue - startValue) / (endValue - startValue), 2) * 100))
```

- If `startValue == endValue`, progress = 0 (division by zero guard, line 39)
- If `setting == 'linkAndReport'`, `currentValue` is auto-aggregated from child goals (line 43–48)

### 3.5 Child Goal Aggregation

**Source:** `app/Domain/Goalcanvas/Services/Goalcanvas.php:70–89`

- Parent goals with `setting = 'linkAndReport'` sum `currentValue` from children
- Supports 2-level hierarchy: child goals can themselves be `linkAndReport` and aggregate from their own children (using `childCurrentValue`)

### 3.6 Goal Metric Fields

**Source:** `app/Domain/Goalcanvas/Repositories/Goalcanvas.php:228–263` (createGoal insert)

| Field | Type | Purpose |
|-------|------|---------|
| `startValue` | `double(10,2)` | Baseline metric value |
| `currentValue` | `double(10,2)` | Current metric value |
| `endValue` | `double(10,2)` | Target metric value |
| `metricType` | `VARCHAR(45)` | Metric type identifier |
| `impact` | `INT` | Impact score |
| `effort` | `INT` | Effort score |
| `probability` | `INT` | Probability score |

### 3.7 Transition Table

| From ↓ \ To → | on_track | at_risk | miss |
|----------------|----------|---------|------|
| **on_track** | — | ✅ manual | ✅ manual |
| **at_risk** | ✅ manual | — | ✅ manual |
| **miss** | ✅ manual | ✅ manual | — |

**Conditions:** None — purely user-chosen.
**Authority:** Controlled at canvas/controller level (project membership required).

---

## 4. SPRINT SEMANTICS

### 4.1 Sprint Data Model

**Source:** `app/Domain/Sprints/Repositories/Sprints.php:26–37` (getSprint query)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `INT` | Primary key, auto-increment |
| `name` | `VARCHAR` | Sprint name |
| `projectId` | `INT` | Foreign key to project |
| `startDate` | `DATETIME` | Sprint start (UTC) |
| `endDate` | `DATETIME` | Sprint end (UTC) |
| `modified` | `TIMESTAMP` | Last modification time |

### 4.2 Sprint Lifecycle

**Creation:** `app/Domain/Sprints/Services/Sprints.php:103–129` (`addSprint()`)

- Parses user-provided dates via `dtHelper()->parseUserDateTime()`
- Converts to DB format with start-of-day / end-of-day handling (lines 112–118)
- No validation of date overlaps with other sprints

**Editing:** `app/Domain/Sprints/Services/Sprints.php:134–160` (`editSprint()`)

- Same date parsing logic as creation
- No validation of date overlaps

**Deletion:** `app/Domain/Sprints/Repositories/Sprints.php:217–228` (`delSprint()`)

```php
public function delSprint(int|string $id): void
{
    $this->db->table('zp_tickets')->where('sprint', $id)->update(['sprint' => null]);
    $this->db->table('zp_sprints')->where('id', $id)->delete();
}
```

- **Clears sprint assignment** from all tickets first (sets `sprint = null`)
- Then hard-deletes the sprint record

### 4.3 Date-Based Queries

**Source:** `app/Domain/Sprints/Repositories/Sprints.php`

| Method | Query Logic | Line |
|--------|-------------|------|
| `getCurrentSprint()` | `startDate < NOW() AND endDate > NOW()` | 135–136 |
| `getAllFutureSprints()` | `endDate > NOW()` | 103 |
| `getUpcomingSprint()` | `startDate > NOW()` | 171 |
| `getAllSprints()` | No date filter, `ORDER BY startDate DESC` | 59–73 |

### 4.4 Sprint Auto-Close / Carry-Over

**FINDING: There is NO auto-close or carry-over logic.** Sprints whose `endDate` has passed are simply excluded from `getCurrentSprint()` and `getAllFutureSprints()` queries. They remain in the database indefinitely and are still returned by `getAllSprints()`.

Tickets assigned to a past sprint **retain their sprint assignment** — there is no automatic reassignment to a new sprint.

### 4.5 Ticket-to-Sprint Assignment

Tickets reference sprints via `zp_tickets.sprint` (stores sprint ID).

**Source:** `app/Domain/Tickets/Services/Tickets.php:1958` — `'sprint' => $values['sprint'] ?? ''`

**Side effect warning:** When a ticket's status changes via the `patch()` method, the sprint assignment is **cleared**.
**Source:** `app/Domain/Tickets/Services/Tickets.php:2206`

### 4.6 Events

**FINDING:** The Sprint service dispatches **no events** for create/edit/delete operations. Sprint deletion in `DelSprint` controller dispatches `ticket_updated` (not a sprint-specific event).

**Source:** `app/Domain/Sprints/Controllers/DelSprint.php:32` (dispatches `ticket_updated` after sprint deletion)

---

## 5. MILESTONE SEMANTICS

### 5.1 What Is a Milestone

A milestone is a ticket record with `type = 'milestone'` in the `zp_tickets` table. It shares the same status codes as regular tickets but has a separate creation path.

### 5.2 Milestone Progress Calculation

**Source:** `app/Domain/Tickets/Services/Tickets.php:1589–1654` (`getMilestoneProgress()`)

**Algorithm:**

1. Fetch all child tickets where `milestoneid = {milestoneId}`
2. For each ticket, compute: `ticketScore = effort × priorityFactor[priority]`
   - Default effort: 3 story points (if not set)
   - Priority factors:

     | Priority | Factor |
     |----------|--------|
     | 1 (Critical) | 2.0 |
     | 2 (High) | 1.75 |
     | 3 (Medium) | 1.5 |
     | 4 (Low) | 1.25 |
     | 5 (Lowest) | 1.0 |

3. Sum `totalScore` (all tickets) and `doneScore` (tickets with `statusType == 'DONE'`)
4. `percentDone = (doneScore / totalScore) × 100`
5. If no child tickets, returns `0.0`

**Key detail:** Only statuses with `statusType == 'DONE'` (codes 0 and -1) count toward progress. `INPROGRESS` statuses are tracked but do NOT advance the progress percentage.

### 5.3 Milestone Completion Conditions

There is **no auto-completion trigger**. A milestone's own status must be manually changed to DONE (0) or ARCHIVED (-1). The progress percentage is calculated dynamically but does not trigger any status change.

### 5.4 Subtask-to-Milestone Inheritance

**Source:** `app/Domain/Tickets/Services/Tickets.php:2260–2309` (`upsertSubtask()`)

When a subtask is created:
- `dependingTicketId` is set to the parent ticket's ID (line 2284)
- `milestoneid` is set to the parent ticket's milestone (line 2285)

This ensures subtasks are counted in the correct milestone's progress.

### 5.5 Milestone Deletion

**Source:** `app/Domain/Tickets/Services/Tickets.php:2525–2541`

- Requires project membership
- Delegates to `ticketRepository->delMilestone($id)`
- Dispatches `milestone_deleted` event
- Does NOT cascade to child tickets (they remain with `milestoneid` pointing to deleted milestone)

---

## 6. ROLE/PERMISSION GATING

### 6.1 Role Hierarchy

**Source:** `app/Domain/Auth/Models/Roles.php:27–34`

```php
private static array $roleKeys = [
    5  => 'readonly',     // prev: none
    10 => 'commenter',    // prev: client
    20 => 'editor',       // prev: developer
    30 => 'manager',      // prev: clientmanager
    40 => 'admin',        // prev: manager
    50 => 'owner',        // prev: admin
];
```

Higher numeric value = more permissions. The role list is filterable via `available_roles` filter (line 41), allowing plugins to modify the role set.

### 6.2 Permission Check Mechanisms

**Source:** `app/Domain/Auth/Services/Auth.php`

#### `userIsAtLeast($role, $forceGlobalRoleCheck)` — Hierarchical check
**Lines 469–494**

Compares numeric role keys: `requiredRoleKey <= currentUserRoleKey`

#### `authOrRedirect($role, $forceGlobalRoleCheck)` — Gate or 403
**Lines 499–506**

Uses `userHasRole()` (exact match against a list), NOT `userIsAtLeast()`. Throws `HttpResponseException` redirecting to `/errors/error403`.

#### `userHasRole($role, $forceGlobalRoleCheck)` — Exact match
**Lines 511–524**

Checks if user's role is exactly one of the allowed roles. No hierarchical comparison.

### 6.3 Dual Role System

**Source:** `app/Domain/Auth/Services/Auth.php:141–169` (`getRoleToCheck()`)

Users have two role contexts:
- `session('userdata.role')` — **Global account role**
- `session('userdata.projectRole')` — **Project-specific role**

**Resolution logic:**
1. If `forceGlobalRoleCheck = true` → always use global role
2. If project role is `'inherited'` or empty → use global role
3. If global role is owner/admin/manager → use global role (cannot be downgraded per-project)
4. Otherwise → use project-specific role

### 6.4 Permission Matrix

| Entity | Create | Edit | Delete | Status Change |
|--------|--------|------|--------|---------------|
| **Ticket** | Editor (≥20) + project member | Project member | Editor (≥20) + project member | Editor (≥20) + project member |
| **Milestone** | Editor (≥20) + project member | Project member | Project member | Project member |
| **Sprint** | Editor (≥20) | Editor (≥20) | Editor (≥20) | N/A |
| **Project** | Manager (≥30, global) | Manager (≥30, global) | Manager (≥30, global) | Manager (≥30, global) |
| **User** | Manager (≥30, global) | Admin (≥40, global) | Admin (≥40, global) | N/A |

**Evidence for each cell:**

| Check | Source File | Line |
|-------|------------|------|
| Ticket create (controller) | `Tickets/Controllers/NewTicket.php` | 46 |
| Ticket create (service) | `Tickets/Services/Tickets.php` | 1972–1974 |
| Ticket delete (controller) | `Tickets/Controllers/DelTicket.php` | 18, 30 |
| Ticket delete (service) | `Tickets/Services/Tickets.php` | 2485 |
| Ticket status (service) | `Tickets/Services/Tickets.php` | 2090–2091 |
| Sprint create/edit (controller) | `Sprints/Controllers/EditSprint.php` | 25 |
| Sprint delete (controller) | `Sprints/Controllers/DelSprint.php` | 29, 32 |
| Project create (controller) | `Projects/Controllers/NewProject.php` | 56 |
| Project delete (controller) | `Projects/Controllers/DelProject.php` | 34, 37 |
| User create (controller) | `Users/Controllers/NewUser.php` | 39 |
| User edit (controller) | `Users/Controllers/EditUser.php` | 46 |
| User delete (controller) | `Users/Controllers/DelUser.php` | 29 |
| User list (controller) | `Users/Controllers/ShowAll.php` | 29 |

### 6.5 Service-Layer vs Controller-Layer Enforcement

**Important pattern:** Most permission checks live at the **controller** level via `Auth::authOrRedirect()`. Service methods generally only check **project membership** (via `isUserAssignedToProject()`), not role level. This means API callers bypassing controllers may skip role checks.

---

## 7. DEPENDENCY/BLOCKER SEMANTICS

### 7.1 Entity Relationship System

**Source:** `app/Core/Support/EntityRelationshipEnum.php:10–20`

```php
enum EntityRelationshipEnum: string
{
    case Collaborator = 'collaborator';
}
```

**FINDING:** The entity relationship system currently only implements `Collaborator` (ticket-to-user). There are **no** `depends_on`, `blocks`, or `relates_to` relationship types defined in the enum or used in the codebase.

### 7.2 Entity Relationship Table

**Source:** `app/Domain/Install/Repositories/Install.php:815–828`

```sql
CREATE TABLE `zp_entity_relationship` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `entityA` INT NULL,
    `entityAType` VARCHAR(45) NULL,
    `entityB` INT NULL,
    `entityBType` VARCHAR(45) NULL,
    `relationship` VARCHAR(45) NULL,
    `createdOn` DATETIME NULL,
    `createdBy` INT NULL,
    `meta` TEXT NULL,
    PRIMARY KEY (`id`)
);
```

Currently used only for ticket collaborators:
- **Insert:** `app/Domain/Tickets/Repositories/Tickets.php:1718–1728`
- **Query:** `app/Domain/Tickets/Repositories/Tickets.php:1741–1748`
- **Delete:** `app/Domain/Tickets/Repositories/Tickets.php:1751–1761`

### 7.3 Legacy `dependingTicketId` Field

**Source:** `app/Domain/Tickets/Models/Tickets.php:61`

```php
public mixed $dependingTicketId = null;
```

**Purpose:** Implements parent-child ticket hierarchy (primarily for subtasks).

**How it works:**
- Subtasks have `dependingTicketId` set to their parent ticket's ID
  - **Source:** `app/Domain/Tickets/Services/Tickets.php:2284`
- Ticket lists can be grouped by `dependingTicketId` for hierarchical display
  - **Source:** `app/Domain/Tickets/Services/Tickets.php:1010–1025`

**How it does NOT work:**
- `dependingTicketId` does NOT create any workflow blocker
- It does NOT prevent status changes on dependent tickets
- It does NOT enforce ordering or sequencing
- It is purely a **display grouping** mechanism

**Side effect:** When a ticket's status changes via `patch()`, `dependingTicketId` is **cleared** (set to empty string).
**Source:** `app/Domain/Tickets/Services/Tickets.php:2206`

---

## 8. VALIDATION GATES

### 8.1 Ticket Creation

**Source:** `app/Domain/Tickets/Services/Tickets.php:1942–2012` (`addTicket()`)

| Check | Type | Line | Error |
|-------|------|------|-------|
| Project membership | Service | 1972–1974 | `notifications.ticket_save_error_no_access` |
| Headline not empty | Service | 1976–1977 | `notifications.ticket_save_error_no_headline` |
| Role ≥ editor | Controller | NewTicket.php:46 | 403 redirect |

**Required fields:** Only `headline` is explicitly validated. All other fields have defaults.

**Default values on creation (line 1944–1970):**

| Field | Default |
|-------|---------|
| `type` | `'task'` |
| `status` | `3` (NEW) |
| `projectId` | `session('currentProject')` |
| `userId` | `session('userdata.id')` |
| `date` | `gmdate('Y-m-d H:i:s')` |
| All others | Empty string or empty array |

### 8.2 Ticket Update

**Source:** `app/Domain/Tickets/Services/Tickets.php:2047–2123` (`updateTicket()`)

| Check | Type | Line | Error |
|-------|------|------|-------|
| Ticket exists | Service | 2050–2054 | Error array |
| Project ID set | Service | 2086–2088 | Error array |
| Project membership | Service | 2090–2091 | `notifications.ticket_save_error_no_access` |

### 8.3 Ticket Deletion

**Source:** `app/Domain/Tickets/Services/Tickets.php:2480–2516`

| Check | Type | Line | Error |
|-------|------|------|-------|
| Ticket exists | Service | 2483–2486 | Error array |
| Project membership | Service | 2485 | `notifications.ticket_delete_error` |
| No logged timesheets | Service (`canDelete`) | 2508–2511 | Exception thrown |
| Role ≥ editor | Controller | DelTicket.php:18 | 403 redirect |

**Critical:** `canDelete()` (line 2499) checks for timesheets but is a **separate method** — the `delete()` method does NOT call `canDelete()`. The controller must call `canDelete()` before `delete()`.

### 8.4 Project Creation

**Source:** `app/Domain/Projects/Services/Projects.php:1219–1242` (`addProject()`)

| Check | Type | Line | Error |
|-------|------|------|-------|
| Role ≥ manager | Controller | NewProject.php:56 | 403 redirect |

**No service-level validation.** `name` and `clientId` are passed directly without null-coalescing (implicitly required by the caller). No exception or error return for missing fields.

### 8.5 User Creation

**Source:** `app/Domain/Users/Services/Users.php:308–329` (`addUser()`)

| Check | Type | Line | Error |
|-------|------|------|-------|
| Role ≥ manager | Controller | NewUser.php:39 | 403 redirect |

**No service-level validation.** `user` (username), `role`, and `password` are required implicitly (no `??` operator). A `usernameExist()` method exists (line 342–344) but is **not called** within `addUser()` — the caller must invoke it separately.

### 8.6 Project Closure

**Source:** `app/Domain/Projects/Controllers/ShowProject.php:245–248`

| Check | Type | Line | Error |
|-------|------|------|-------|
| Project name not empty | Controller | 245 | Silently skipped |
| No tickets in project | Controller | 246 | Notification error (blocks save) |

Note: The `hasTickets()` check only counts tickets of type other than `subtask` and `milestone`.

---

## 9. BACKGROUND JOB EFFECTS

### 9.1 Scheduled Jobs

| Job | Schedule | Source | Workflow Effect |
|-----|----------|--------|-----------------|
| Queue: emails | Every minute | `Queue/register.php:9–12` | Sends queued emails. No state changes. |
| Queue: HTTP requests | Every 5 min | `Queue/register.php:15–19` | Processes HTTP request queue. No state changes. |
| Queue: default | Every 5 min | `Queue/register.php:22–26` | Processes default queue. No state changes. |
| Reports: telemetry | Daily | `Reports/register.php:19–35` | Sends anonymous telemetry. No state changes. |
| Reports: dailyIngestion | Daily | `Reports/register.php:37–39` | Ingests reporting data. No state changes. |
| Plugins: checkLicense | Daily | `Plugins/register.php:1–37` | Validates marketplace plugin licenses. **Can disable plugins** with invalid licenses via `disablePluginNotifyOwner()`. |

### 9.2 Do Background Jobs Affect Workflow State?

**No.** None of the scheduled jobs modify ticket status, project state, sprint dates, goal status, or milestone progress. The only state-affecting job is the plugin license check, which can **disable plugins** — but this does not affect project/ticket workflow directly.

---

## 10. ARCHIVAL/CLOSURE SEMANTICS

### 10.1 Ticket Archival (Status -1)

**Behavior:**
- Archive is status code `-1` with `statusType = 'DONE'`
- Archived tickets are **hidden from kanban** (`kanbanCol = false`, line 72)
- Archived tickets **contribute to milestone progress** (statusType DONE)
- Archived tickets are **filtered from default queries**: `WHERE status <> -1`
  - **Source:** `app/Domain/Tickets/Repositories/Tickets.php:532, 1171`
- Archive status is **protected** and cannot be removed from custom status labels
  - **Source:** `app/Domain/Tickets/Repositories/Tickets.php:144–146`

**Archival is non-destructive.** The ticket record remains intact in the database.

### 10.2 Ticket Deletion vs Archival

**Source:** `app/Domain/Tickets/Services/Tickets.php:2499–2516` (`canDelete()`)

Tickets with logged timesheets **cannot be deleted** — the system recommends archival instead:

```php
if ($hasLoggedHours) {
    throw new \Exception('Task has timesheets attached, delete all timesheets first or consider archiving the task');
}
```

Ticket deletion is a **hard delete** from the database.

### 10.3 Project Closure (State 1)

**Behavior:**
- Closed projects remain in the database
- Closed projects are **still visible** in project lists unless the view explicitly filters them
  - **Source:** `app/Domain/Projects/Repositories/Projects.php:71–76`
- Child tickets **retain their state** — no cascading status changes
- Users **remain assigned** to closed projects

**Gate:** Cannot close a project that has tickets (non-subtask, non-milestone).
**Source:** `app/Domain/Projects/Controllers/ShowProject.php:246`

### 10.4 Project Deletion

**Behavior (hard delete, cascading):**
1. Project record deleted from `zp_projects`
2. All tickets in the project deleted from `zp_tickets`
3. All user-project relations deleted via `deleteAllUserRelations()`

**Source:** `app/Domain/Projects/Repositories/Projects.php:807–817` and `app/Domain/Projects/Controllers/DelProject.php:46–47`

**NOT cascaded:**
- Sprints associated with the project (remain orphaned)
- Timesheets for deleted tickets (remain orphaned)
- Goal canvases associated with the project (remain orphaned)

### 10.5 Sprint Deletion

**Behavior:**
1. All tickets with `sprint = {id}` have sprint set to `null`
2. Sprint record hard-deleted

**Source:** `app/Domain/Sprints/Repositories/Sprints.php:217–228`

### 10.6 Milestone Deletion

**Behavior:**
- Milestone ticket record is deleted
- Child tickets **retain their `milestoneid`** pointing to the now-deleted milestone (orphaned reference)
- No cascading status changes on child tickets

**Source:** `app/Domain/Tickets/Services/Tickets.php:2525–2541`

---

## 11. WRITE CONFLICT / RACE-RISK NOTES

### 11.1 Transaction Usage

**Only one transaction exists in the entire domain layer:**

**Source:** `app/Domain/Timesheets/Repositories/Timesheets.php:700–730`

```php
return $this->db->transaction(function () use ($ticketId, $inTimestamp, $hoursWorked) {
    // Delete punch clock entry
    $this->db->table('zp_punch_clock')->where(...)->delete();
    // Insert/update timesheet (ON DUPLICATE KEY UPDATE)
    $this->db->insert($query, [...]);
    return $hoursWorked;
});
```

**Purpose:** Atomic punch-clock deletion + timesheet upsert to prevent data loss.

### 11.2 Locking Mechanisms

| Mechanism | Present? | Evidence |
|-----------|----------|----------|
| `lockForUpdate()` / `SELECT...FOR UPDATE` | ❌ No | `grep -r "lockForUpdate\|FOR UPDATE" app/` — no matches |
| `sharedLock()` | ❌ No | `grep -r "sharedLock" app/` — no matches |
| Optimistic locking (version field) | ❌ No | No version/etag fields in any model |
| Mutex/Semaphore | ❌ No | No lock file or distributed lock patterns |

### 11.3 Modified Timestamp

A `modified` field exists in tickets (`app/Domain/Tickets/Models/Tickets.php:97`) and projects, but it is **only written, never checked** before updates. It cannot serve as optimistic concurrency control.

### 11.4 Race Condition Scenarios

| Scenario | Risk | Description |
|----------|------|-------------|
| Concurrent ticket edits | **HIGH** | Two users editing same ticket — last write wins, first user's changes silently lost |
| Concurrent status changes | **HIGH** | Two kanban drags on same ticket — unpredictable final status |
| Collaborator add/remove | **MEDIUM** | `removeCollaborators()` deletes all rows then re-inserts; concurrent addition could be lost |
| Project deletion during editing | **MEDIUM** | No check if project is being actively used when deleted; cascading ticket deletion could lose in-flight edits |
| Sprint deletion during ticket assignment | **LOW** | Sprint is nulled on all tickets before deletion; concurrent assignment could set a deleted sprint ID |
| `patch()` recursive call | **LOW** | Status change via `patch()` triggers a second `patch()` call (line 2206) that clears sprint/milestone/parent — if another update arrives between the two calls, data could be lost |

### 11.5 Session-Based Locking

**Source:** `app/Core/Middleware/StartSession.php`

Leantime implements session locking with exponential backoff (documented in CLAUDE.md middleware section). This prevents concurrent requests from the same user from corrupting session data but does **not** protect database writes.

---

## 12. MISSING EVIDENCE

The following items could not be confirmed from the codebase:

| Item | What Was Searched | Finding |
|------|------------------|---------|
| Auto-close tickets when sprint ends | Sprint service, repositories, register.php files | **No auto-close logic exists** |
| Carry-over tickets to next sprint | Sprint service, ticket service | **No carry-over logic exists** |
| Auto-update milestone status when 100% complete | Ticket service milestone methods | **No auto-status-change logic exists** |
| Dependency-based blocking (ticket A blocks ticket B) | EntityRelationshipEnum, entity relationship tables, ticket service | **No blocking relationship type is implemented** — only `Collaborator` exists |
| Workflow rules engine / configurable transitions | Full codebase search for "transition", "workflow", "state machine" | **No workflow engine exists** — all transitions are unrestricted |
| Email notification delivery guarantee | Queue processing logic | Queue processes entries but delivery success/failure handling is **UNKNOWN** from static analysis alone |
| Cascade behavior for goal canvas deletion | Goalcanvas service | **UNKNOWN** — goal deletion path through inherited Canvas base class not fully traced |
| Project closure effect on sprints | Project close logic, sprint queries | **No explicit handling** — sprints remain associated with closed projects |
| Timesheet orphaning on project deletion | Project delete, timesheet queries | Timesheets are **NOT deleted** when project is deleted (only tickets are deleted); timesheet references to deleted tickets become **orphaned** |
| Rate limiting on status changes | Middleware stack, rate limiter config | General rate limiting exists (10000 req/min) but **no specific rate limit on status change operations** |
