# LEANTIME DOMAIN MODEL

> Evidence-first domain inventory for Leantime repository truth pack.
> Analyzed ref: 555803d3da0f81ba232d5f38fc11268fdf317511 (master)
> All claims cite exact source files. UNKNOWN marks unconfirmed items.

---


> **Generated from source code analysis.**  
> Every claim cites exact file paths. Items marked **UNKNOWN** could not be confirmed from code.

---

## 1. TICKET (Task)

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | `Leantime\Domain\Tickets\Models\Tickets` | `app/Domain/Tickets/Models/Tickets.php` |
| Repository | `Leantime\Domain\Tickets\Repositories\Tickets` | `app/Domain/Tickets/Repositories/Tickets.php` |
| Service | `Leantime\Domain\Tickets\Services\Tickets` | `app/Domain/Tickets/Services/Tickets.php` |

### Storage

**Table:** `zp_tickets`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:424-477`

### Key Fields (from SchemaBuilder + Model)

| Column | Type (Schema) | Model Property | Notes |
|---|---|---|---|
| `id` | `bigint` (auto PK) | `$id` | Auto-increment primary key |
| `projectId` | `int nullable` | `$projectId` | FK → `zp_projects.id` |
| `headline` | `varchar(255) nullable` | `$headline` | Title of ticket |
| `description` | `text nullable` | `$description` | Rich text body |
| `acceptanceCriteria` | `text nullable` | `$acceptanceCriteria` | — |
| `date` | `datetime nullable` | `$date` | Creation date |
| `dateToFinish` | `datetime nullable` | `$dateToFinish` | Due date |
| `priority` | `varchar(60) nullable` | `$priority` | String-stored integer key |
| `status` | `int nullable` | `$status` | Default `3` (NEW) |
| `userId` | `int nullable` | `$userId` | Creator / author FK → `zp_user.id` |
| `editorId` | `varchar(75) nullable` | `$editorId` | Assignee FK → `zp_user.id` (stored as string) |
| `type` | `varchar(255) nullable` | `$type` | Polymorphic discriminator |
| `storypoints` | `float nullable` | `$storypoints` | Effort estimate |
| `sprint` | `int nullable` | `$sprint` | FK → `zp_sprints.id` |
| `tags` | `varchar(255) nullable` | `$tags` | Comma-separated tag string |
| `dependingTicketId` | `int nullable` | `$dependingTicketId` | Parent ticket / dependency FK → `zp_tickets.id` |
| `milestoneid` | `int nullable` | `$milestoneid` | FK → `zp_tickets.id` (where type='milestone') |
| `planHours` | `float nullable` | `$planHours` | Planned hours |
| `hourRemaining` | `float nullable` | `$hourRemaining` | Remaining hours estimate |
| `editFrom` | `datetime nullable` | `$editFrom` | Timeline start |
| `editTo` | `datetime nullable` | `$editTo` | Timeline end |
| `url` | `varchar(100) nullable` | `$url` | External URL |
| `sortindex` | `bigint nullable` | `$sortIndex` | List sort order |
| `kanbanSortIndex` | `bigint nullable` | — | Kanban board sort order |
| `leancanvasitemid` | `int nullable` | — | FK → canvas item |
| `retrospectiveid` | `int nullable` | — | FK → canvas item |
| `ideaid` | `int nullable` | — | FK → canvas item |
| `os` | `varchar(30) nullable` | — | Legacy bug-report field |
| `browser` | `varchar(30) nullable` | — | Legacy bug-report field |
| `resolution` | `varchar(30) nullable` | — | Legacy bug-report field |
| `component` | `varchar(100) nullable` | — | Legacy bug-report field |
| `version` | `varchar(20) nullable` | — | Legacy bug-report field |
| `production` | `int default 0` | — | Legacy deployment flag |
| `staging` | `int default 0` | — | Legacy deployment flag |
| `modified` | `datetime nullable` | `$modified` | Last modification timestamp |

**Computed / join-only model properties** (not in `zp_tickets` table):

| Property | Source |
|---|---|
| `$projectName` | JOIN `zp_projects.name` |
| `$projectDescription` | JOIN `zp_projects.details` |
| `$clientName` | JOIN `zp_clients.name` |
| `$userFirstname`, `$userLastname` | JOIN `zp_user` (author) |
| `$editorFirstname`, `$editorLastname`, `$editorProfileId` | JOIN `zp_user` (assignee) |
| `$parentHeadline` | JOIN `zp_tickets` (via `dependingTicketId`) |
| `$milestoneHeadline`, `$milestoneColor` | JOIN `zp_tickets` (via `milestoneid`) |
| `$timelineDate`, `$timelineDateToFinish` | Formatted date projections |
| `$bookedHours` | SUM from `zp_timesheets` |
| `$doneTickets`, `$allTickets`, `$percentDone` | Aggregates (milestone progress) |
| `$children` | Recursive subtask array |
| `$collaborators` | From `zp_entity_relationship` |

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique within the installation.

### Ownership / Scope

- **Owned by:** Project (`projectId` → `zp_projects.id`)
- **Created by:** User (`userId` → `zp_user.id`)
- **Assigned to:** User (`editorId` → `zp_user.id`)
- **Collaborators:** Many-to-many via `zp_entity_relationship` (entityAType='Ticket', entityBType='User', relationship='collaborator')

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| Project | `projectId` | Many tickets → one project |
| User (author) | `userId` | Many tickets → one user |
| User (assignee) | `editorId` | Many tickets → one user |
| User (collaborators) | `zp_entity_relationship` | Many-to-many |
| Sprint | `sprint` | Many tickets → one sprint |
| Milestone (ticket) | `milestoneid` | Many tickets → one milestone ticket |
| Parent ticket | `dependingTicketId` | Many tickets → one parent |
| Timesheet | `zp_timesheets.ticketId` | One ticket → many timesheets |
| Comment | `zp_comment` (module='ticket', moduleId) | One ticket → many comments |
| File | `zp_file` (module='ticket', moduleId) | One ticket → many files |
| Ticket History | `zp_tickethistory.ticketId` | One ticket → many history entries |

### Workflow / State

**Status codes** (from `$statusListSeed` at `Tickets.php:32-75`):

| Code | Name Key | statusType | Kanban Visible | Sort |
|---|---|---|---|---|
| `3` | `status.new` | `NEW` | Yes | 1 |
| `1` | `status.blocked` | `INPROGRESS` | Yes | 2 |
| `4` | `status.in_progress` | `INPROGRESS` | Yes | 3 |
| `2` | `status.waiting_for_approval` | `INPROGRESS` | Yes | 4 |
| `0` | `status.done` | `DONE` | Yes | 5 |
| `-1` | `status.archived` | `DONE` | **No** | 6 |

Status labels are **per-project customizable** via `zp_settings` key `projectsettings.{projectId}.ticketlabels`. The seed values are defaults; projects can add/rename statuses.  
**Evidence:** `Tickets.php:120-178`

**Status type groups** (used in queries): `DONE`, `INPROGRESS`, `NEW`, `ALLOPEN` (NEW + INPROGRESS).  
**Evidence:** `Tickets.php:189-230`

**Types** (from `$type` at `Tickets.php:81`):

```php
public array $type = ['task', 'subtask', 'story', 'bug'];
```

Additional types used in service layer but not in the repository array: `milestone`, `feature`, `epic`, `documentation`, `improvement`, `research`.  
**Evidence:** `Tickets.php:81`, service layer queries filter by type dynamically.

**Priority** (from `$priority` at `Tickets.php:77`):

| Key | Label |
|---|---|
| `1` | Critical |
| `2` | High |
| `3` | Medium |
| `4` | Low |
| `5` | Lowest |

**Effort / Story Points** (from `$efforts` at `Tickets.php:79`):

| Key | Label |
|---|---|
| `0.5` | < 2min |
| `1` | XS |
| `2` | S |
| `3` | M |
| `5` | L |
| `8` | XL |
| `13` | XXL |

### Classification

**Operational** — Core work-item entity. Central to all PM workflows.

---

## 2. PROJECT

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | `Leantime\Domain\Projects\Models\Project` | `app/Domain/Projects/Models/Project.php` |
| Repository | `Leantime\Domain\Projects\Repositories\Projects` | `app/Domain/Projects/Repositories/Projects.php` |
| Service | `Leantime\Domain\Projects\Services\Projects` | `app/Domain/Projects/Services/Projects.php` |

### Storage

**Table:** `zp_projects`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:323-346`

### Key Fields

| Column | Type (Schema) | Model Property | Notes |
|---|---|---|---|
| `id` | `bigint` (auto PK) | `$id` | Auto-increment primary key |
| `name` | `varchar(100) nullable` | `$name` | Project name |
| `clientId` | `int nullable` | `$clientId` | FK → `zp_clients.id` |
| `details` | `text nullable` | — | Project description (not on model) |
| `state` | `int nullable` | `$state` | 0=OPEN, 1=CLOSED, -1=DELETED |
| `hourBudget` | `varchar(255) nullable` | — | Budget in hours |
| `dollarBudget` | `int nullable` | — | Budget in dollars |
| `active` | `int nullable` | — | Soft-delete flag (> -1 = active) |
| `menuType` | `text nullable` | `$menuType` | UI menu style |
| `psettings` | `text nullable` | — | Access setting: `'all'`, `'clients'`, or project-specific |
| `parent` | `int nullable` | — | FK → `zp_projects.id` (parent project) |
| `type` | `varchar(45) nullable` | `$type` | `'project'`, `'strategy'`, `'program'` |
| `start` | `datetime nullable` | `$start` | Project start date |
| `end` | `datetime nullable` | `$end` | Project end date |
| `created` | `datetime nullable` | — | Creation timestamp |
| `modified` | `datetime nullable` | `$lastUpdate` | Last modified timestamp |
| `avatar` | `text nullable` | — | Avatar image reference |
| `cover` | `text nullable` | — | Cover image reference |
| `sortIndex` | `int nullable` | `$sortIndex` | Display sort order |

**Computed / join-only model properties:**

| Property | Source |
|---|---|
| `$clientName` | JOIN `zp_clients.name` |
| `$isFavorite` | JOIN `zp_reactions` (module='project', reaction='favorite') |
| `$status` | Latest `zp_comment` (module='project') status field |
| `$numberOfTickets` | Count aggregate |
| `$progress` | Computed |
| `$milestones` | Computed |
| `$report` | Computed |

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique.

### Ownership / Scope

- **Owned by:** Client (`clientId` → `zp_clients.id`)
- **Can have a parent:** `parent` → `zp_projects.id` (hierarchical projects)
- **Access control:** Via `psettings` column:
  - `'all'` — everyone in the organization
  - `'clients'` — users belonging to the same client
  - (null / other) — only explicitly assigned users via `zp_relationuserproject`
- **Admin/Owner bypass:** Users with role ≥ 40 can access all projects.  
  **Evidence:** `Projects.php:874-876`

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| Client | `clientId` | Many projects → one client |
| Parent Project | `parent` | Self-referential; many → one |
| Users | `zp_relationuserproject` | Many-to-many |
| Tickets | `zp_tickets.projectId` | One project → many tickets |
| Sprints | `zp_sprints.projectId` | One project → many sprints |
| Comments | `zp_comment` (module='project') | One project → many comments |
| Favorites | `zp_reactions` (module='project', reaction='favorite') | Many-to-many with users |
| Canvas boards | `zp_canvas.projectId` | One project → many canvases |

### Workflow / State

**State codes** (from `$state` at `Projects.php:33`):

```php
public array $state = [0 => 'OPEN', 1 => 'CLOSED', null => 'OPEN'];
```

Additionally, `state = -1` is used for **DELETED** projects in query filters (e.g., `Projects.php:330-335`).

The `active` column is also used as a soft-delete: `active > -1` means active (`Projects.php:301-303`).

**Project types** (`type` column): `'project'` (default), `'strategy'`, `'program'`.  
**Evidence:** `Projects.php:134, 719, 341-350`

### Classification

**Operational** — Top-level organizational container for all work items.

---

## 3. CLIENT

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | *No dedicated model class* | — |
| Repository | `Leantime\Domain\Clients\Repositories\Clients` | `app/Domain/Clients/Repositories/Clients.php` |
| Service | `Leantime\Domain\Clients\Services\Clients` | `app/Domain/Clients/Services/Clients.php` |

### Storage

**Table:** `zp_clients`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:227-244`

### Key Fields

| Column | Type (Schema) | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | Auto-increment primary key |
| `name` | `varchar(200) nullable` | Client/organization name |
| `street` | `varchar(200) nullable` | Address |
| `zip` | `int nullable` | Postal code |
| `city` | `varchar(50) nullable` | City |
| `state` | `varchar(50) nullable` | State/province |
| `country` | `varchar(50) nullable` | Country |
| `phone` | `varchar(50) nullable` | Phone number |
| `internet` | `varchar(200) nullable` | Website URL |
| `email` | `varchar(255) nullable` | Contact email |
| `published` | `int nullable` | Legacy field |
| `age` | `int nullable` | Legacy field |
| `modified` | `datetime nullable` | Last modified timestamp |

**Computed fields** (from queries):

| Field | Source |
|---|---|
| `numberOfProjects` | COUNT of `zp_projects.clientId` |

**Evidence:** `Clients.php:40-68` (getClient), `Clients.php:149-161` (addClient)

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique.

### Ownership / Scope

- **Top-level entity.** Clients own Projects and Users belong to a Client.
- No parent entity above Client (except the Leantime installation itself).

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| Projects | `zp_projects.clientId` | One client → many projects |
| Users | `zp_user.clientId` | One client → many users |

### Workflow / State

No explicit state machine. Clients are created and deleted.  
**Deletion cascade:** Deleting a client also deletes all associated projects (`Clients.php:190-200`).

### Classification

**Contextual** — Organizational grouping entity for projects and users.

---

## 4. USER

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model (session) | `Leantime\Domain\Auth\Models\CurrentUser` | `app/Domain/Auth/Models/CurrentUser.php` |
| Roles | `Leantime\Domain\Auth\Models\Roles` | `app/Domain/Auth/Models/Roles.php` |
| Repository | `Leantime\Domain\Users\Repositories\Users` | `app/Domain/Users/Repositories/Users.php` |
| Service | `Leantime\Domain\Users\Services\Users` | `app/Domain/Users/Services/Users.php` |

### Storage

**Table:** `zp_user`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:512-551`

### Key Fields

| Column | Type (Schema) | CurrentUser Property | Notes |
|---|---|---|---|
| `id` | `bigint` (auto PK) | `$id` | Auto-increment primary key |
| `username` | `varchar(175)` unique | `$mail` | Email address / login (unique constraint) |
| `password` | `varchar(255) nullable` | — | bcrypt hash |
| `firstname` | `varchar(100) nullable` | `$name` (composed) | First name |
| `lastname` | `varchar(100) nullable` | `$name` (composed) | Last name |
| `phone` | `varchar(25) nullable` | — | Phone number |
| `profileId` | `varchar(100) nullable` | `$profileId` | Profile picture file reference |
| `lastlogin` | `datetime nullable` | — | Last login timestamp |
| `status` | `varchar(1) default 'A'` | — | `'a'`=active, `'i'`=inactive, `'v'`=invited |
| `expires` | `datetime nullable` | — | Account expiration |
| `role` | `varchar(200)` | `$role` | Numeric role key stored as string |
| `session` | `varchar(100) nullable` | — | Session ID |
| `sessiontime` | `varchar(50) nullable` | — | Session timestamp |
| `wage` | `int nullable` | — | Hourly wage |
| `hours` | `int nullable` | — | Weekly hours |
| `description` | `text nullable` | — | User bio |
| `clientId` | `int nullable` | `$clientId` | FK → `zp_clients.id` |
| `notifications` | `int nullable` | — | Notification preferences |
| `pwReset` | `varchar(100) nullable` | — | Password reset token |
| `pwResetExpiration` | `datetime nullable` | — | Token expiration |
| `pwResetCount` | `int nullable` | — | Reset attempt count |
| `forcePwReset` | `tinyint nullable` | — | Force password change flag |
| `lastpwd_change` | `datetime nullable` | — | Last password change date |
| `settings` | `text nullable` | `$settings` | JSON user settings |
| `twoFAEnabled` | `tinyint default 0` | `$twoFAEnabled` | 2FA toggle |
| `twoFASecret` | `varchar(200) nullable` | `$twoFASecret` | TOTP secret |
| `createdOn` | `datetime nullable` | `$createdOn` | Account creation date |
| `source` | `varchar(200) nullable` | `$isExternalAuth` | Auth source (`'api'`, LDAP, OIDC, null=local) |
| `jobTitle` | `varchar(200) nullable` | — | Job title |
| `jobLevel` | `varchar(50) nullable` | — | Job level |
| `department` | `varchar(200) nullable` | — | Department |
| `modified` | `datetime nullable` | `$modified` | Last modified timestamp |

### Roles

Defined in `Leantime\Domain\Auth\Models\Roles` (`app/Domain/Auth/Models/Roles.php:27-34`):

| Numeric Key | String Name | Previous Name |
|---|---|---|
| `5` | `readonly` | none |
| `10` | `commenter` | client |
| `20` | `editor` | developer |
| `30` | `manager` | clientmanager |
| `40` | `admin` | manager |
| `50` | `owner` | admin |

Roles are **filterable** via `dispatch_filter('available_roles', ...)` — plugins can add/modify roles.  
**Admin roles array** in repository: `[40, 50]` (`Users.php:33`).

### User Statuses

Defined in repository (`Users.php:35`):

```php
public array $status = ['active' => 'label.active', 'inactive' => 'label.inactive', 'invited' => 'label.invited'];
```

In the database, status is stored as a single character: `'a'` (active), `'i'` (inactive).  
**Evidence:** `Users.php:100-101`, `SchemaBuilder.php:523`

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique.
- **`username`**: Unique constraint. Used as login identifier (email).

### Ownership / Scope

- **Belongs to:** Client (`clientId` → `zp_clients.id`)
- **Top-level actor entity.** Users act across projects via `zp_relationuserproject`.

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| Client | `clientId` | Many users → one client |
| Projects | `zp_relationuserproject` | Many-to-many |
| Tickets (authored) | `zp_tickets.userId` | One user → many tickets |
| Tickets (assigned) | `zp_tickets.editorId` | One user → many tickets |
| Tickets (collaborator) | `zp_entity_relationship` | Many-to-many |
| Timesheets | `zp_timesheets.userId` | One user → many timesheets |
| Comments | `zp_comment.userId` | One user → many comments |
| Files | `zp_file.userId` | One user → many files |
| Punch Clock | `zp_punch_clock.userId` | One user → one active punch |

### Workflow / State

- Status transitions: `invited` (`'i'`) → `active` (`'a'`) → `inactive` (`'i'`)
- Account can `expire` via `expires` column.
- `forcePwReset` triggers mandatory password change.
- 2FA verification tracked via `twoFAEnabled` and `twoFAVerified` (session-only).

### Classification

**Operational** — Core actor entity. Central to authentication and authorization.

---

## 5. SPRINT

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | `Leantime\Domain\Sprints\Models\Sprints` | `app/Domain/Sprints/Models/Sprints.php` |
| Repository | `Leantime\Domain\Sprints\Repositories\Sprints` | `app/Domain/Sprints/Repositories/Sprints.php` |
| Service | `Leantime\Domain\Sprints\Services\Sprints` | `app/Domain/Sprints/Services/Sprints.php` |

### Storage

**Table:** `zp_sprints`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:556-568`

### Key Fields

| Column | Type (Schema) | Model Property | Notes |
|---|---|---|---|
| `id` | `bigint` (auto PK) | `$id` | Auto-increment primary key |
| `projectId` | `int nullable` | `$projectId` | FK → `zp_projects.id` |
| `name` | `varchar(45) nullable` | `$name` | Sprint name |
| `startDate` | `datetime nullable` | `$startDate` | Sprint start |
| `endDate` | `datetime nullable` | `$endDate` | Sprint end |
| `modified` | `datetime nullable` | `$modified` | Last modified |

**Indexes:** Composite index on `(projectId, startDate, endDate)`.

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique.

### Ownership / Scope

- **Owned by:** Project (`projectId` → `zp_projects.id`)

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| Project | `projectId` | Many sprints → one project |
| Tickets | `zp_tickets.sprint` | One sprint → many tickets |
| Stats | `zp_stats.sprintId` | One sprint → many stat snapshots |

### Workflow / State

No explicit status field. Sprint lifecycle is implied by date range:
- **Future:** `startDate` > now
- **Current:** `startDate` ≤ now ≤ `endDate`
- **Past:** `endDate` < now

The current sprint is tracked in the user session (`session('currentSprint')`).  
**Evidence:** `Sprints.php` (service) lines 42-52.

Special sprint values in ticket queries:
- `sprint = 0` or `sprint = -1` or `sprint IS NULL` → **Backlog** (not assigned to sprint)  
  **Evidence:** `Tickets.php:1204-1211`

### Classification

**Operational** — Time-boxed iteration container for tickets.

---

## 6. MILESTONE

### Code Symbols

Milestones are **not a separate entity** — they are a **ticket type** (`type='milestone'`) stored in `zp_tickets`.

| Layer | Full Namespace | File |
|---|---|---|
| Model | `Leantime\Domain\Tickets\Models\Tickets` (shared) | `app/Domain/Tickets/Models/Tickets.php` |
| Repository | `Leantime\Domain\Tickets\Repositories\Tickets` (shared) | `app/Domain/Tickets/Repositories/Tickets.php` |
| Service | `Leantime\Domain\Tickets\Services\Tickets` (shared) | `app/Domain/Tickets/Services/Tickets.php` |
| HxController | `Leantime\Domain\Tickets\Hxcontrollers\Milestones` | `app/Domain/Tickets/Hxcontrollers/Milestones.php` |

### Storage

**Table:** `zp_tickets` (same table as regular tickets, filtered by `type='milestone'`)

### Key Fields (milestone-specific usage)

| Field | Usage for Milestones |
|---|---|
| `type` | Always `'milestone'` |
| `tags` | Stores **color** for the milestone (not tags). Defaults to `'var(--grey)'` |
| `milestoneid` | Self-referential: a milestone can depend on another milestone (parent milestone) |
| `editFrom` | Milestone timeline start |
| `editTo` | Milestone timeline end |
| `headline` | Milestone name |

### Creation

`quickAddMilestone()` in service (`Tickets.php:1868-1906`) sets:
- `type` → `'milestone'`
- `status` → `3` (NEW)
- `priority` → `3` (Medium)
- `milestoneid` → optional parent milestone

### Relationships

| Target Entity | Mechanism | Cardinality |
|---|---|---|
| Project | `projectId` | Many milestones → one project |
| Tickets | `zp_tickets.milestoneid` = milestone's `id` | One milestone → many tickets |
| Parent Milestone | `milestoneid` (self-referential) | Many → one |

### Progress Tracking

`getMilestoneProgress()` (`Tickets.php:1589`) calculates percentage of done tickets assigned to the milestone.

### Queries

- `getAllMilestones()` — filters `zp_tickets` by `type='milestone'` and project.  
  **Evidence:** `Tickets.php:1382-1391`, repository method `getAllMilestones()` at `Tickets.php:1050+`
- Milestones are **excluded** from normal ticket lists: `WHERE ticket.type <> 'milestone'`  
  **Evidence:** `Tickets.php:306`

### Classification

**Operational** — Logical grouping of tickets within a project timeline. Implemented as a ticket type, not a separate entity.

---

## 7. SUBTASK

### Code Symbols

Subtasks are a **ticket type** (`type='subtask'`) stored in `zp_tickets`.

| Layer | Full Namespace | File |
|---|---|---|
| Model | `Leantime\Domain\Tickets\Models\Tickets` (shared) | `app/Domain/Tickets/Models/Tickets.php` |
| HxController | `Leantime\Domain\Tickets\Hxcontrollers\Subtasks` | `app/Domain/Tickets/Hxcontrollers/Subtasks.php` |
| Service method | `Tickets::upsertSubtask()` | `app/Domain/Tickets/Services/Tickets.php:2260` |
| Service method | `Tickets::getAllSubtasks()` | `app/Domain/Tickets/Services/Tickets.php:1761` |

### Storage

**Table:** `zp_tickets` (same table, filtered by `type='subtask'`)

### Key Fields (subtask-specific usage)

| Field | Usage for Subtasks |
|---|---|
| `type` | Always `'subtask'` |
| `dependingTicketId` | **FK → parent ticket's `id`** (establishes parent-child link) |
| `milestoneid` | **Inherited** from parent ticket |
| `projectId` | **Inherited** from parent ticket |

### Creation

`upsertSubtask()` in service (`Tickets.php:2260-2309`) sets:
- `type` → `'subtask'`
- `dependingTicketId` → `$parentTicket->id`
- `milestoneid` → `$parentTicket->milestoneid` (inherited)
- `projectId` → `$parentTicket->projectId` (inherited)

### Queries

- `getAllSubtasks($ticketId)` in repository.  
  **Evidence:** `Tickets.php:1761-1765`
- Subtask count aggregated in search queries via subquery on `dependingTicketId > 0`.  
  **Evidence:** `Tickets.php:434-443`
- Subtasks are **excluded** from project ticket counts: `WHERE type <> 'subtask'`  
  **Evidence:** `Projects.php:826`

### Relationships

| Target Entity | Mechanism | Cardinality |
|---|---|---|
| Parent Ticket | `dependingTicketId` | Many subtasks → one parent |
| Project | `projectId` (inherited) | Many subtasks → one project |
| Milestone | `milestoneid` (inherited) | Many subtasks → one milestone |

### Classification

**Operational** — Child work-item. Implemented as a ticket type with `dependingTicketId` as parent link.

---

## 8. DEPENDENCY / ENTITY RELATIONSHIP

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Enum | `Leantime\Core\Support\EntityRelationshipEnum` | `app/Core/Support/EntityRelationshipEnum.php` |
| Repository | `Leantime\Domain\Entityrelations\Repositories\Entityrelations` | `app/Domain/Entityrelations/Repositories/Entityrelations.php` |
| Service | `Leantime\Domain\Entityrelations\Services\Entityrelations` | `app/Domain/Entityrelations/Services/Entityrelations.php` |

### Two Dependency Mechanisms

#### 8a. Simple Dependency (field-based)

**Field:** `zp_tickets.dependingTicketId`  
A direct FK on the ticket to another ticket. Used for:
- Parent-child (subtask → parent)
- Milestone hierarchy (milestone → parent milestone)
- General ticket dependency

**Evidence:** `SchemaBuilder.php:443`, `Tickets.php:349, 398, 1443`

#### 8b. Polymorphic Entity Relationships

**Table:** `zp_entity_relationship`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:709-727`

| Column | Type | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | Auto-increment |
| `entityA` | `int nullable` | Source entity ID |
| `entityAType` | `varchar(45) nullable` | Source entity type (e.g., `'Ticket'`) |
| `entityB` | `int nullable` | Target entity ID |
| `entityBType` | `varchar(45) nullable` | Target entity type (e.g., `'User'`) |
| `relationship` | `varchar(45) nullable` | Relationship type string |
| `createdOn` | `datetime nullable` | Creation timestamp |
| `createdBy` | `int nullable` | Creator user ID |
| `meta` | `text nullable` | Additional metadata |

**Indexes:**
- `(entityA, entityAType, relationship)`
- `(entityB, entityBType, relationship)`

### Relationship Types (Enum)

```php
enum EntityRelationshipEnum: string
{
    case Collaborator = 'collaborator';
}
```

**Evidence:** `app/Core/Support/EntityRelationshipEnum.php`

Currently only `'collaborator'` is defined. Used for ticket collaborators:
- `entityA` = ticket ID, `entityAType` = `'Ticket'`
- `entityB` = user ID, `entityBType` = `'User'`
- `relationship` = `'collaborator'`

**Evidence:** `Tickets.php:1710-1731` (addCollaborators), `Tickets.php:1739-1748` (getCollaborators)

### Classification

**Auxiliary** — Infrastructure for entity relationships. Currently used only for collaborators but designed as a generic polymorphic relationship table.

---

## 9. USER-PROJECT RELATION

### Code Symbols

No dedicated model class. Managed via `Projects` repository methods.

| Layer | Full Namespace | File |
|---|---|---|
| Repository methods | `Leantime\Domain\Projects\Repositories\Projects` | `app/Domain/Projects/Repositories/Projects.php` |

Key methods: `getUsersAssignedToProject()` (line 207), `getUserProjectRelation()` (line 836), `editUserProjectRelations()` (line 939), `addProjectRelation()`, `deleteProjectRelation()` (line 975).

### Storage

**Table:** `zp_relationuserproject`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:387-401`

### Key Fields

| Column | Type (Schema) | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | Auto-increment primary key |
| `userId` | `int nullable` | FK → `zp_user.id` |
| `projectId` | `int nullable` | FK → `zp_projects.id` |
| `wage` | `int nullable` | User-specific wage rate for project |
| `projectRole` | `varchar(20) nullable` | Role override within project |

**Indexes:**
- `projectId`
- `userId`
- Composite `(userId, projectId)`

### Primary Identifier

- **`id`**: Auto-increment `bigint`.
- **Logical key:** `(userId, projectId)` pair.

### Ownership / Scope

- **Junction table** between Users and Projects.
- Created automatically when a project is created (author is added).  
  **Evidence:** `Projects.php:728-730`

### Relationships

| Target Entity | Field | Cardinality |
|---|---|---|
| User | `userId` | — |
| Project | `projectId` | — |

This is a pure **many-to-many junction** with extra metadata (`wage`, `projectRole`).

### Usage in Access Control

This table is the **primary mechanism** for project-level authorization. Nearly every query that filters by user access includes a subquery:

```sql
WHERE projectId IN (SELECT projectId FROM zp_relationuserproject WHERE userId = ?)
```

**Evidence:** `Tickets.php:295-298`, `Timesheets.php:204-207`, `Comments.php:163-166`, `Projects.php:308`

### Classification

**Contextual** — Authorization and scope-control junction table.

---

## 10. TIMESHEET

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | *No dedicated model class* | — |
| Repository | `Leantime\Domain\Timesheets\Repositories\Timesheets` | `app/Domain/Timesheets/Repositories/Timesheets.php` |
| Service | `Leantime\Domain\Timesheets\Services\Timesheets` | `app/Domain/Timesheets/Services/Timesheets.php` |

### Storage

**Table:** `zp_timesheets`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:483-507`

### Key Fields

| Column | Type (Schema) | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | Auto-increment primary key |
| `userId` | `int nullable` | FK → `zp_user.id` |
| `ticketId` | `int nullable` | FK → `zp_tickets.id` |
| `workDate` | `datetime nullable` | Date of work |
| `hours` | `float nullable` | Hours logged |
| `description` | `text nullable` | Work description |
| `kind` | `varchar(175) nullable` | Time entry category |
| `invoicedEmpl` | `int nullable` | Employee invoiced flag (0/1) |
| `invoicedComp` | `int nullable` | Company invoiced flag (0/1) |
| `invoicedEmplDate` | `datetime nullable` | Employee invoice date |
| `invoicedCompDate` | `datetime nullable` | Company invoice date |
| `rate` | `varchar(255) nullable` | Hourly rate |
| `paid` | `int nullable` | Paid flag (0/1) |
| `paidDate` | `datetime nullable` | Payment date |
| `modified` | `datetime nullable` | Last modified timestamp |

**Unique constraint:** `(userId, ticketId, workDate, kind)` — prevents duplicate entries for the same user, ticket, day, and kind.  
**Evidence:** `SchemaBuilder.php:502`

**Additional indexes:** `ticketId`, `(userId, workDate)`, `(ticketId, workDate)`.

### Kind Types

Defined in both repository and service (`Timesheets.php:23-30`):

| Key | Label |
|---|---|
| `GENERAL_BILLABLE` | `label.general_billable` |
| `GENERAL_NOT_BILLABLE` | `label.general_not_billable` |
| `PROJECTMANAGEMENT` | `label.projectmanagement` |
| `DEVELOPMENT` | `label.development` |
| `BUGFIXING_NOT_BILLABLE` | `label.bugfixing_not_billable` |
| `TESTING` | `label.testing` |

### Primary Identifier

- **`id`**: Auto-increment `bigint`.

### Ownership / Scope

- **Owned by:** User (`userId`) + Ticket (`ticketId`)
- **Scoped to:** Project (via ticket → project join)
- **Inherits access control** from project via `zp_relationuserproject`.  
  **Evidence:** `Timesheets.php:204-207`

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| User | `userId` | Many timesheets → one user |
| Ticket | `ticketId` | Many timesheets → one ticket |
| Project | via `zp_tickets.projectId` (join) | Transitive |
| Client | via `zp_projects.clientId` (join) | Transitive |
| Milestone | via `zp_tickets.milestoneid` (join) | Transitive |

### Workflow / State

No status field. Lifecycle tracked by invoicing and payment flags:
1. **Logged** — entry exists
2. **Invoiced (employee)** — `invoicedEmpl = 1`
3. **Invoiced (company)** — `invoicedComp = 1`
4. **Paid** — `paid = 1`

### Upsert Behavior

Time entries use `ON DUPLICATE KEY UPDATE` to **accumulate** hours when the same `(userId, ticketId, workDate, kind)` combination exists. Descriptions are prepended.  
**Evidence:** `Timesheets.php:588-642`

### Classification

**Operational** — Time tracking and billing data.

---

## 11. PUNCH CLOCK

### Code Symbols

No dedicated model, repository, or service class. Managed within the **Timesheets** domain.

| Layer | Full Namespace | File |
|---|---|---|
| Repository (methods) | `Leantime\Domain\Timesheets\Repositories\Timesheets` | `app/Domain/Timesheets/Repositories/Timesheets.php` |
| Service (methods) | `Leantime\Domain\Timesheets\Services\Timesheets` | `app/Domain/Timesheets/Services/Timesheets.php` |

Key methods: `isClocked()` (line 540), `punchIn()` (line 650), `punchOut()` (line 678).

### Storage

**Table:** `zp_punch_clock`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:349-364`

### Key Fields

| Column | Type (Schema) | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | **Doubles as ticket ID** when punching in |
| `userId` | `int` | FK → `zp_user.id` |
| `minutes` | `int nullable` | UNKNOWN usage — not populated in current code |
| `hours` | `int nullable` | UNKNOWN usage — not populated in current code |
| `punchIn` | `int nullable` | Unix timestamp of clock-in time |

**Index:** `userId`

### Primary Identifier

- **`id`**: Also serves as the ticket ID (set to `ticketId` on insert).  
  **Evidence:** `Timesheets.php:661` — `'id' => $ticketId`

### Ownership / Scope

- **One active punch per user.** A user can only be clocked into one ticket at a time.
- **Owned by:** User (`userId`)
- **References:** Ticket (via `id` which is the ticketId)

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| User | `userId` | Many → one (but typically one active per user) |
| Ticket | `id` (= ticketId) | One punch → one ticket |

### Workflow / State

1. **Punch In** — Row inserted with `id = ticketId`, `punchIn = time()`.  
   **Evidence:** `Timesheets.php:660-665`
2. **Punch Out** — Duration calculated from `punchIn` to `time()`, row **deleted**, and hours added to `zp_timesheets` via upsert.  
   **Evidence:** `Timesheets.php:678-727`

The punch clock is **ephemeral** — records exist only while a user is actively clocked in. On punch-out, the data transfers to `zp_timesheets` and the punch clock row is deleted within a transaction.

### Classification

**Auxiliary** — Transient operational state for active time tracking.

---

## 12. COMMENT

### Code Symbols

| Layer | Full Namespace | File |
|---|---|---|
| Model | *No dedicated model class* | — |
| Repository | `Leantime\Domain\Comments\Repositories\Comments` | `app/Domain/Comments/Repositories/Comments.php` |
| Service | `Leantime\Domain\Comments\Services\Comments` | `app/Domain/Comments/Services/Comments.php` |

### Storage

**Table:** `zp_comment`  
**Schema definition:** `app/Domain/Install/Services/SchemaBuilder.php:249-265`

### Key Fields

| Column | Type (Schema) | Notes |
|---|---|---|
| `id` | `bigint` (auto PK) | Auto-increment primary key |
| `module` | `varchar(200) nullable` | Polymorphic type: `'ticket'`, `'project'`, or other module names |
| `userId` | `int nullable` | FK → `zp_user.id` (comment author) |
| `commentParent` | `int nullable` | FK → `zp_comment.id` (for threaded replies, 0 = top-level) |
| `date` | `datetime nullable` | Comment timestamp |
| `moduleId` | `int nullable` | FK → entity ID in the referenced module |
| `text` | `text nullable` | Comment body (HTML) |
| `status` | `varchar(50) nullable` | Status indicator (used for project status updates) |

**Indexes:**
- `(moduleId, module, commentParent)` — primary lookup
- `(userId, module)` — user's comments
- `(moduleId, module, date)` — chronological lookup

### Primary Identifier

- **`id`**: Auto-increment `bigint`. Globally unique.

### Ownership / Scope

- **Polymorphic attachment** via `module` + `moduleId`:
  - `module='ticket'`, `moduleId` = ticket ID
  - `module='project'`, `moduleId` = project ID
  - Other modules possible (canvas items, etc.)
- **Authored by:** User (`userId`)

### Relationships

| Target Entity | Field / Mechanism | Cardinality |
|---|---|---|
| User (author) | `userId` | Many comments → one user |
| Ticket | `module='ticket'`, `moduleId` | Many comments → one ticket |
| Project | `module='project'`, `moduleId` | Many comments → one project |
| Parent Comment | `commentParent` | Many replies → one parent (threaded) |

### Dual Purpose: Comments + Project Status

For **project** comments, the `status` field serves as a **project health status indicator**. The most recent comment's status becomes the project's displayed status.  
**Evidence:** `Projects.php:100-125` — latest comment status per project is fetched and merged into project data.

### Workflow / State

No workflow states on the comment itself. Comments are created, edited, or deleted.

- **Creation:** `addComment()` (`Comments.php:108-121`) — inserts with module, moduleId, userId, text, status, commentParent.
- **Threading:** `commentParent = 0` for top-level, `commentParent = {parentId}` for replies.  
  **Evidence:** `Comments.php:40-41`
- **Notification:** On creation, triggers `notifyProjectUsers()` with context-specific email subject/message.  
  **Evidence:** `Comments.php` (service) lines 59-99.

### Classification

**Operational** — Communication and collaboration entity. Also serves as project status mechanism.

---

## Cross-Entity Relationship Summary

```
CLIENT (zp_clients)
  └─── PROJECT (zp_projects)              [clientId]
         ├─── TICKET (zp_tickets)          [projectId]
         │      ├─── SUBTASK (zp_tickets)  [dependingTicketId, type='subtask']
         │      ├─── TIMESHEET (zp_timesheets) [ticketId]
         │      ├─── COMMENT (zp_comment)  [module='ticket', moduleId]
         │      ├─── PUNCH CLOCK (zp_punch_clock) [id=ticketId]
         │      └─── COLLABORATORS (zp_entity_relationship) [entityA=ticketId]
         ├─── MILESTONE (zp_tickets)       [projectId, type='milestone']
         │      └─── TICKET.milestoneid ──→ MILESTONE.id
         ├─── SPRINT (zp_sprints)          [projectId]
         │      └─── TICKET.sprint ──→ SPRINT.id
         ├─── COMMENT (zp_comment)         [module='project', moduleId]
         └─── USER-PROJECT (zp_relationuserproject) [projectId]
                └─── USER (zp_user)        [userId]
                       └─── CLIENT         [clientId]
```

---

## Evidence Index

| File | Entities Documented |
|---|---|
| `app/Domain/Tickets/Models/Tickets.php` | Ticket model properties |
| `app/Domain/Tickets/Repositories/Tickets.php` | Ticket status/priority/effort/type definitions, queries, collaborator management |
| `app/Domain/Tickets/Services/Tickets.php` | Milestone/subtask logic, ticket creation |
| `app/Domain/Tickets/Hxcontrollers/Milestones.php` | Milestone HxController |
| `app/Domain/Tickets/Hxcontrollers/Subtasks.php` | Subtask HxController |
| `app/Domain/Projects/Models/Project.php` | Project model properties |
| `app/Domain/Projects/Repositories/Projects.php` | Project queries, user-project relations, state definitions |
| `app/Domain/Projects/Services/Projects.php` | Project service |
| `app/Domain/Clients/Repositories/Clients.php` | Client fields, CRUD, cascade delete |
| `app/Domain/Clients/Services/Clients.php` | Client service |
| `app/Domain/Auth/Models/CurrentUser.php` | User session model |
| `app/Domain/Auth/Models/Roles.php` | Role definitions and numeric keys |
| `app/Domain/Users/Repositories/Users.php` | User queries, status array, admin roles |
| `app/Domain/Users/Services/Users.php` | User service |
| `app/Domain/Sprints/Models/Sprints.php` | Sprint model properties |
| `app/Domain/Sprints/Repositories/Sprints.php` | Sprint queries |
| `app/Domain/Sprints/Services/Sprints.php` | Sprint service |
| `app/Domain/Timesheets/Repositories/Timesheets.php` | Timesheet + punch clock queries, kind types |
| `app/Domain/Timesheets/Services/Timesheets.php` | Timesheet service, punch in/out |
| `app/Domain/Comments/Repositories/Comments.php` | Comment queries and fields |
| `app/Domain/Comments/Services/Comments.php` | Comment service, notifications |
| `app/Domain/Entityrelations/Repositories/Entityrelations.php` | Entity relationship repository |
| `app/Domain/Entityrelations/Services/Entityrelations.php` | Entity relationship service |
| `app/Core/Support/EntityRelationshipEnum.php` | Relationship type enum |
| `app/Domain/Install/Services/SchemaBuilder.php` | All table schemas (canonical DDL) |

---

# Part 2: Canvas, Knowledge, Support, and Auxiliary Entities


> **Generated from source code inspection** — all data cited with exact file paths.  
> Items marked **UNKNOWN** could not be confirmed from code evidence.

---

## Table of Contents

1. [Entity 13: Canvas (Base)](#13-canvas-base)
2. [Entity 14: Goal (Goalcanvas)](#14-goal-goalcanvas)
3. [Entity 15: Idea](#15-idea)
4. [Entity 16: Risk (Riskscanvas)](#16-risk-riskscanvas)
5. [Entity 17: Retrospective (Retroscanvas)](#17-retrospective-retroscanvas)
6. [Entity 18: Wiki / Article](#18-wiki--article)
7. [Entity 19: File / Attachment](#19-file--attachment)
8. [Entity 20: Notification](#20-notification)
9. [Entity 21: Audit](#21-audit)
10. [Entity 22: Reaction](#22-reaction)
11. [Entity 23: Entity Relationship](#23-entity-relationship)
12. [Entity 24: Integration / Connector](#24-integration--connector)
13. [Entity 25: Plugin](#25-plugin)
14. [Entity 26: Setting](#26-setting)
15. [Entity 27: Queue Message](#27-queue-message)
16. [Entity 28: Calendar Event](#28-calendar-event)
17. [Entity 29: Sprint Statistics](#29-sprint-statistics)
18. [Entity 30: Read Status](#30-read-status)
19. [Cross-Reference: Canvas Variant Summary](#cross-reference-canvas-variant-summary)
20. [Cross-Reference: Table Registry](#cross-reference-table-registry)

---

## 13. CANVAS (Base)

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Canvas` | `Leantime\Domain\Canvas\Services` |
| Repository | `Canvas` | `Leantime\Domain\Canvas\Repositories` |

**No model class exists** — canvas data is handled as associative arrays.

### Evidence

- Service: `app/Domain/Canvas/Services/Canvas.php`
- Repository: `app/Domain/Canvas/Repositories/Canvas.php`
- Controllers: `app/Domain/Canvas/Controllers/{ShowCanvas,EditCanvasItem,EditCanvasComment,BoardDialog,DelCanvas,DelCanvasItem,Export}.php`
- Templates: `app/Domain/Canvas/Templates/` (10 `.inc.php` files)

### Storage/Table Backing

**Table: `zp_canvas`** — Board/canvas container

| Column | Purpose |
|--------|---------|
| `id` | Primary key (auto-increment int) |
| `title` | Canvas board title |
| `description` | Board description |
| `author` | FK → `zp_user.id` |
| `created` | Creation timestamp |
| `type` | Canvas type discriminator (e.g., `'goal'`, `'idea'`, `'wiki'`, `'risks'`, `'retros'`, etc.) |
| `projectId` | FK → `zp_projects.id` |

**Table: `zp_canvas_items`** — Individual items within a canvas

| Column | Purpose |
|--------|---------|
| `id` | Primary key (auto-increment int) |
| `canvasId` | FK → `zp_canvas.id` |
| `box` | Box/category within canvas (variant-specific values) |
| `title` | Item title |
| `description` | Item description/content |
| `assumptions` | Data field (repurposed per variant) |
| `data` | Data field (repurposed per variant) |
| `conclusion` | Data field (repurposed per variant) |
| `author` | FK → `zp_user.id` |
| `created` | Creation timestamp |
| `modified` | Last modification timestamp |
| `sortindex` | Sort order within canvas |
| `status` | Item status (variant-specific) |
| `relates` | Relates-to classification |
| `milestoneId` | FK → `zp_tickets.id` (milestone link) |
| `kpi` | FK → `zp_canvas_items.id` (parent KPI link) |
| `parent` | FK → `zp_canvas_items.id` (hierarchical parent) |
| `tags` | Tag string |
| `assignedTo` | FK → `zp_user.id` |
| `data1` through `data5` | Extended data fields |
| `startDate` | Start date |
| `endDate` | End date |
| `setting` | Setting/configuration data |
| `metricType` | Metric type identifier |
| `startValue` | Metric start value |
| `currentValue` | Metric current value |
| `endValue` | Metric end/target value |
| `impact` | Impact rating |
| `effort` | Effort rating |
| `probability` | Probability rating |
| `action` | Action item text |

### Primary Identifiers

- `zp_canvas.id` — auto-increment integer, unique per board
- `zp_canvas_items.id` — auto-increment integer, unique per item
- `zp_canvas.type` — discriminator column that distinguishes canvas variants

### Ownership/Scope

- **Canvas** is owned by a **Project** (`projectId`) and created by a **User** (`author`)
- **Canvas Item** belongs to a **Canvas** (`canvasId`) and created by a **User** (`author`)

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| Project | `zp_canvas.projectId` | Many-to-one |
| User (author) | `zp_canvas.author`, `zp_canvas_items.author` | Many-to-one |
| Ticket (milestone) | `zp_canvas_items.milestoneId` | Many-to-one (optional) |
| Canvas Item (KPI parent) | `zp_canvas_items.kpi` | Many-to-one (self-ref) |
| Canvas Item (hierarchical parent) | `zp_canvas_items.parent` | Many-to-one (self-ref) |
| Comment | `zp_comment.moduleId` where `module = '{CANVAS_NAME}canvasitem'` | One-to-many |
| User (assigned) | `zp_canvas_items.assignedTo` | Many-to-one (optional) |

### Workflow/State Relevance

**Base status labels** (defined in repository, overridable by variants):

| Status Key | Color | Dropdown Class |
|-----------|-------|---------------|
| `status_draft` | blue | `info` |
| `status_review` | orange | `warning` |
| `status_valid` | green | `success` |
| `status_hold` | red | `danger` |
| `status_invalid` | red | `danger` |

**Base relates labels** (8 options, overridable):
`relates_none`, `relates_customers`, `relates_offerings`, `relates_capabilities`, `relates_financials`, `relates_markets`, `relates_environment`, `relates_firm`

### Architecture Pattern

Canvas is a **generic base class** — the `CANVAS_NAME` constant (`protected const CANVAS_NAME = '??'`) must be overridden by each variant. All controllers and the repository extend the base classes. The `type` column in `zp_canvas` and semantic use of `box` in `zp_canvas_items` differentiate variants.

### Classification

**Operational** — canvas boards are actively used for strategic planning and collaboration across multiple domain variants.

---

## 14. GOAL (Goalcanvas)

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Goalcanvas` | `Leantime\Domain\Goalcanvas\Services` |
| Repository | `Goalcanvas` | `Leantime\Domain\Goalcanvas\Repositories` |

**No model class** — uses array data structures.  
Extends base Canvas: `Leantime\Domain\Canvas\Repositories\Canvas`

### Evidence

- Service: `app/Domain/Goalcanvas/Services/Goalcanvas.php`
- Repository: `app/Domain/Goalcanvas/Repositories/Goalcanvas.php`
- Controllers: `app/Domain/Goalcanvas/Controllers/{Dashboard,ShowCanvas,EditCanvasItem,EditCanvasComment,BigRock,DelCanvas,DelCanvasItem,Export}.php`
- Templates: `app/Domain/Goalcanvas/Templates/` (8 `.blade.php` files — fully modernized)

### Storage/Table Backing

Uses **`zp_canvas`** (with `type = 'goal'`) and **`zp_canvas_items`** (with `box = 'goal'`).

**`CANVAS_NAME = 'goal'`** — `app/Domain/Goalcanvas/Repositories/Goalcanvas.php`

### Key Fields (Goalcanvas-specific)

Canvas types:
```php
$canvasTypes = ['goal' => ['icon' => 'fa-bullseye', 'title' => 'box.goal']];
```

Data labels (repurposed fields):

| Field | Mapped To | Type |
|-------|-----------|------|
| `assumptions` | "What are you measuring" | `string` |
| `data` | "Current value" | `int` |
| `conclusion` | "Goal value" | `int` |

### Primary Identifiers

Same as Canvas base — `zp_canvas.id` and `zp_canvas_items.id`.

### Ownership/Scope

Goals are scoped to a **Project** via the canvas board. Access control uses `zp_relationuserproject` for permission checking in `getAllAccountGoals()`.

### Relationships

Inherits all Canvas relationships, plus:

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| Project (access check) | `zp_relationuserproject` | Many-to-many |

### Workflow/State Relevance

**Goalcanvas overrides status labels** (3 statuses, not 5):

| Status Key | Color | Dropdown Class |
|-----------|-------|---------------|
| `status_ontrack` | green | `success` |
| `status_atrisk` | yellow | `warning` |
| `status_miss` | red | `danger` |

**Relates labels:** Empty array `[]` — goals do not use the relates system.

**Goal progress** is calculated in `Goalcanvas::getCanvasItemsById()` as a percentage based on `startValue`, `currentValue`, and `endValue` fields.

### Service API Methods (marked `@api`)

| Method | Purpose |
|--------|---------|
| `getCanvasItemsById(int $id)` | Get goals with calculated `goalProgress` percentage |
| `getChildGoalsForReporting($parentId)` | Sum child goal values for rollup reporting |
| `getChildrenbyKPI($parentId)` | Structured child goals by KPI |
| `getParentKPIs($projectId)` | Available parent KPIs for linking |
| `pollGoals(?int $projectId, ?int $board)` | All goals with ISO 8601 date formatting |
| `pollForUpdatedGoals(?int $projectId, ?int $board)` | Goals with composite ID-modified key |

### Reporting Settings

```php
public $reportingSettings = ['linkonly', 'linkAndReport', 'nolink'];
```

### Classification

**Operational** — goals are a core strategic planning tool with progress tracking, KPI hierarchies, and milestone linking.

---

## 15. IDEA

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Ideas` | `Leantime\Domain\Ideas\Services` |
| Repository | `Ideas` | `Leantime\Domain\Ideas\Repositories` |

**No model class** — uses array data structures.  
**No `Ideacanvas` domain exists** — Ideas has its own standalone repository (does NOT extend Canvas base).

### Evidence

- Service: `app/Domain/Ideas/Services/Ideas.php`
- Repository: `app/Domain/Ideas/Repositories/Ideas.php`
- Controllers: `app/Domain/Ideas/Controllers/{AdvancedBoards,ShowBoards,BoardDialog,IdeaDialog,DelCanvas,DelCanvasItem}.php`
- Templates: `app/Domain/Ideas/Templates/` (6 files)

### Storage/Table Backing

Uses **`zp_canvas`** (with `type = 'idea'`) and **`zp_canvas_items`**.

Unlike other canvas variants, Ideas has its **own full repository** rather than extending the Canvas base.

### Key Fields

**zp_canvas columns used:**
`id`, `title`, `author`, `created`, `projectId`, `type`, `description`, `color`, `modified`

**zp_canvas_items columns used:**
`id`, `description`, `title`, `assumptions`, `data`, `conclusion`, `box`, `author`, `created`, `modified`, `canvasId`, `sortindex`, `status`, `tags`, `milestoneId`

**Status/box values** (idea stages as `canvasTypes`):

| Box Value | Label | Color |
|-----------|-------|-------|
| `idea` | `status.ideation` | Blue |
| `research` | `status.discovery` | Yellow |
| `prototype` | `status.delivering` | Yellow |
| `validation` | `status.inreview` | Yellow |
| `implemented` | `status.accepted` | Green |
| `deferred` | `status.deferred` | Gray |

### Primary Identifiers

- `zp_canvas.id` — board ID
- `zp_canvas_items.id` — idea item ID

### Ownership/Scope

- Scoped to **Project** via `zp_canvas.projectId`
- Author tracking via `zp_canvas_items.author`

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| Project | `zp_canvas.projectId` | Many-to-one |
| User (author) | `zp_canvas_items.author` | Many-to-one |
| Ticket (milestone) | `zp_canvas_items.milestoneId` | Many-to-one (optional) |
| Comment | `zp_comment.moduleId` where `module = 'idea'` or `'leancanvasitem'` | One-to-many |
| Setting (labels) | `zp_settings` | Configuration |

### Workflow/State Relevance

**Status field duality:**
- The `box` field serves as the primary status (updated by `updateIdeaStatus()`)
- The `status` column is nullable — defaults to `'idea'` via a `CASE` statement in queries
- `updateIdeaStatus()` updates the **`box`** field, NOT the `status` field

**Permission model in `getAllIdeas()`:**
- Checks `zp_relationuserproject` for user project membership
- OR `psettings = 'all'` (public project)
- OR `psettings = 'clients'` AND matching `clientId`
- Admin/Manager bypass

### Service API Methods (marked `@api`)

| Method | Purpose |
|--------|---------|
| `pollForNewIdeas(?int $projectId, ?int $board)` | New ideas with ISO 8601 dates |
| `pollForUpdatedIdeas(?int $projectId, ?int $board)` | Updated ideas with timestamp-appended ID |

### Classification

**Operational** — idea management is a kanban-style workflow for innovation tracking.

---

## 16. RISK (Riskscanvas)

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Repository | `Riskscanvas` | `Leantime\Domain\Riskscanvas\Repositories` |

**No service class.** No model class. Extends `Leantime\Domain\Canvas\Repositories\Canvas`.

### Evidence

- Repository: `app/Domain/Riskscanvas/Repositories/Riskscanvas.php`
- Controllers: `app/Domain/Riskscanvas/Controllers/{ShowCanvas,BoardDialog,EditCanvasItem,DelCanvasItem,DelCanvas,EditCanvasComment,Export}.php` (7 controllers, all extend Canvas base controllers)

### Storage/Table Backing

Uses **`zp_canvas`** and **`zp_canvas_items`**.

**`CANVAS_NAME = 'risks'`**

### Key Fields (Riskscanvas-specific)

**Icon:** `fa-person-falling`

**Canvas types** (risk matrix quadrants):

| Box Value | Label |
|-----------|-------|
| `risks_imp_low_pro_low` | Low Impact / Low Probability |
| `risks_imp_low_pro_high` | Low Impact / High Probability |
| `risks_imp_high_pro_low` | High Impact / Low Probability |
| `risks_imp_high_pro_high` | High Impact / High Probability |

**Data labels** (all 3 active):

| Field | Label |
|-------|-------|
| `conclusion` | `label.risks.description` |
| `data` | `label.data` |
| `assumptions` | `label.risks.mitigation` |

### Workflow/State Relevance

Uses **base Canvas status labels** (5 statuses: draft, review, valid, hold, invalid).  
Uses **base Canvas relates labels** (8 options).

The risk-specific fields `impact`, `effort`, `probability` from `zp_canvas_items` are semantically relevant for risk assessment.

### Classification

**Operational** — risk management boards for project risk assessment.

---

## 17. RETROSPECTIVE (Retroscanvas)

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Repository | `Retroscanvas` | `Leantime\Domain\Retroscanvas\Repositories` |

**No service class.** No model class. Extends `Leantime\Domain\Canvas\Repositories\Canvas`.

### Evidence

- Repository: `app/Domain/Retroscanvas/Repositories/Retroscanvas.php`
- Controllers: `app/Domain/Retroscanvas/Controllers/{ShowCanvas,BoardDialog,EditCanvasItem,DelCanvasItem,DelCanvas,EditCanvasComment,Export}.php` (7 controllers)

### Storage/Table Backing

Uses **`zp_canvas`** and **`zp_canvas_items`**.

**`CANVAS_NAME = 'retros'`**

### Key Fields (Retroscanvas-specific)

**Icon:** `fa-hand-spock`

**Canvas types** (retrospective categories):

| Box Value | Label | Icon |
|-----------|-------|------|
| `well` | `box.retros.continue` (Continue doing) | `fa-circle-check` |
| `notwell` | `box.retros.stop_doing` (Stop doing) | `fa-circle-xmark` |
| `startdoing` | `box.retros.start_doing` (Start doing) | `fa-circle-plus` |

**Data labels** (only 1 active):

| Field | Label | Active |
|-------|-------|--------|
| `conclusion` | `label.description` | ✅ |
| `data` | `label.data` | ❌ |
| `assumptions` | `label.assumptions` | ❌ |

### Workflow/State Relevance

- **`statusLabels = []`** — explicitly empty (uses inherited base defaults)
- **`relatesLabels = []`** — explicitly empty (retros do NOT use the relates system)

### Classification

**Operational** — sprint retrospective boards for team reflection.

---

## 18. WIKI / ARTICLE

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model (Wiki) | `Wiki` | `Leantime\Domain\Wiki\Models` |
| Model (Article) | `Article` | `Leantime\Domain\Wiki\Models` |
| Model (Template) | `Template` | `Leantime\Domain\Wiki\Models` |
| Service | `Wiki` | `Leantime\Domain\Wiki\Services` |
| Repository | `Wiki` | `Leantime\Domain\Wiki\Repositories` |

Repository **extends `Leantime\Domain\Canvas\Repositories\Canvas`** — `CANVAS_NAME = 'wiki'`.

### Evidence

- Models: `app/Domain/Wiki/Models/{Wiki,Article,Template}.php`
- Service: `app/Domain/Wiki/Services/Wiki.php`
- Repository: `app/Domain/Wiki/Repositories/Wiki.php`
- Controllers: `app/Domain/Wiki/Controllers/{Show,ArticleDialog,WikiModal,DelWiki,DelArticle,Templates}.php`
- Hxcontrollers: `app/Domain/Wiki/Hxcontrollers/{ArticleActivity,ArticleContent}.php`
- Templates: `app/Domain/Wiki/Templates/` (5 `.tpl.php` + 1 `.blade.php` partial)

### Storage/Table Backing

Uses **`zp_canvas`** (with `type = 'wiki'`) and **`zp_canvas_items`** (with `box = 'article'`).

Wiki reuses the canvas infrastructure — there is no separate `zp_wiki` table.

### Key Fields

**Wiki model** (`app/Domain/Wiki/Models/Wiki.php`) — all properties untyped:

| Property | Source |
|----------|--------|
| `$id` | `zp_canvas.id` |
| `$title` | `zp_canvas.title` |
| `$author` | `zp_canvas.author` |
| `$created` | `zp_canvas.created` |
| `$projectId` | `zp_canvas.projectId` |
| `$category` | UNKNOWN — not mapped to a visible column |

**Article model** (`app/Domain/Wiki/Models/Article.php`) — all properties untyped:

| Property | Source |
|----------|--------|
| `$id` | `zp_canvas_items.id` |
| `$title` | `zp_canvas_items.title` |
| `$description` | `zp_canvas_items.description` (article body) |
| `$canvasId` | `zp_canvas_items.canvasId` (FK → wiki) |
| `$parent` | `zp_canvas_items.parent` (hierarchical) |
| `$tags` | `zp_canvas_items.tags` |
| `$data` | `zp_canvas_items.data` (icon class, e.g., `'far fa-file-alt'`) |
| `$status` | `zp_canvas_items.status` (`'published'` or `'draft'`) |
| `$created` | `zp_canvas_items.created` |
| `$modified` | `zp_canvas_items.modified` |
| `$author` | `zp_canvas_items.author` |
| `$milestoneId` | `zp_canvas_items.milestoneId` |
| `$sortindex` | `zp_canvas_items.sortindex` |
| `$firstname` | JOIN `zp_user.firstname` |
| `$lastname` | JOIN `zp_user.lastname` |
| `$profileId` | JOIN `zp_user.profileId` |
| `$projectId` | JOIN `zp_canvas.projectId` |
| `$milestoneHeadline` | JOIN `zp_tickets.headline` |
| `$milestoneEditTo` | JOIN `zp_tickets.editTo` |
| `$doneTickets` | Computed |
| `$openTicketsEffort` | Computed |
| `$doneTicketsEffort` | Computed |
| `$allTicketsEffort` | Computed |
| `$allTickets` | Computed |
| `$percentDone` | Computed |

**Template model** (`app/Domain/Wiki/Models/Template.php`) — all properties untyped:

| Property | Purpose |
|----------|---------|
| `$title` | Template title |
| `$description` | Template description |
| `$content` | Template content |
| `$category` | Template category |

### Primary Identifiers

- Wiki: `zp_canvas.id` where `type = 'wiki'`
- Article: `zp_canvas_items.id` where `box = 'article'`

### Ownership/Scope

- Wiki belongs to a **Project** (`projectId`)
- Articles belong to a **Wiki** (`canvasId`) and are authored by a **User**

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| Project | `zp_canvas.projectId` | Many-to-one |
| User (author) | `zp_canvas_items.author` → `zp_user.id` | Many-to-one |
| Ticket (milestone) | `zp_canvas_items.milestoneId` → `zp_tickets.id` | Many-to-one (optional) |
| Article (parent) | `zp_canvas_items.parent` → `zp_canvas_items.id` | Many-to-one (self-ref) |
| Audit | `zp_audit` where `entity = 'article'` | One-to-many |

### Workflow/State Relevance

**Article statuses:**

| Status | Visibility |
|--------|-----------|
| `published` | Visible to all project members |
| `draft` | Visible only to the article author |

**Audit events recorded by service:**
`article.create`, `article.title`, `article.status`, `article.parent`, `article.milestone`, `article.icon`, `article.tags`, `article.edit`

### HTMX Controllers

| Controller | View | Purpose |
|-----------|------|---------|
| `ArticleActivity` | `wiki::partials.activityFeed` | Activity feed (audit + comments) |
| `ArticleContent` | `wiki::partials.articleContent` | Auto-save content, create new drafts |

### Classification

**Operational** — wiki is the knowledge management system, supporting hierarchical articles with versioning via audit trail.

---

## 19. FILE / ATTACHMENT

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Files` | `Leantime\Domain\Files\Services` |
| Repository | `Files` | `Leantime\Domain\Files\Repositories` |
| Event | `FileUploaded` | `Leantime\Domain\Files\Events` |

**No model class exists.**

### Evidence

- Service: `app/Domain/Files/Services/Files.php`
- Repository: `app/Domain/Files/Repositories/Files.php`
- Event: `app/Domain/Files/Events/FileUploaded.php`

### Storage/Table Backing

**Table: `zp_file`**

| Column | Purpose |
|--------|---------|
| `id` | Primary key (auto-increment int) |
| `encName` | Encrypted/hashed filename on disk |
| `realName` | Original filename (without extension) |
| `extension` | File extension |
| `module` | Module type: `project`, `ticket`, `client`, `lead`, `private` |
| `moduleId` | ID of the entity in that module |
| `userId` | FK → `zp_user.id` (uploader) |
| `date` | Upload timestamp |

### Primary Identifiers

- `zp_file.id` — auto-increment integer

### Ownership/Scope

- Files are polymorphically scoped by **module + moduleId** (e.g., a file attached to ticket #42 has `module='ticket'`, `moduleId=42`)
- Files are also owned by a **User** (`userId` — the uploader)

### Module Types

**Admin modules** (repository property `$adminModules`):

| Module Key | Display Name |
|-----------|-------------|
| `project` | Projects |
| `ticket` | Tickets |
| `client` | Clients |
| `lead` | Lead |
| `private` | General |

**User modules** (repository property `$userModules`):

| Module Key | Display Name |
|-----------|-------------|
| `project` | Projects |
| `ticket` | Tickets |
| `private` | General |

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| User (uploader) | `zp_file.userId` → `zp_user.id` (LEFT JOIN) | Many-to-one |
| Project | `module='project'`, `moduleId` → `zp_projects.id` | Polymorphic |
| Ticket | `module='ticket'`, `moduleId` → `zp_tickets.id` | Polymorphic |
| Client | `module='client'`, `moduleId` → `zp_clients.id` | Polymorphic |

**`getFolders()` dynamic table mapping:**

| Module | Table | Title Column |
|--------|-------|-------------|
| `ticket` | `zp_tickets` | `headline` |
| `client` | `zp_clients` | `name` |
| `project` | `zp_projects` | `name` |
| `lead` | `zp_lead` | `name` |

### Workflow/State Relevance

No status/state machine. Files are created and deleted; no transitions.

### Event

`FileUploaded` (`app/Domain/Files/Events/FileUploaded.php`) — Laravel class-based event using `Dispatchable`, `InteractsWithSockets`, `SerializesModels` traits. Constructor is empty (no payload). This is the **only class-based event** in the Leantime codebase (noted as a boilerplate example in CLAUDE.md).

### Service Dependencies

```php
public function __construct(
    protected FileRepository $fileRepository,
    protected FileManager $fileManager,
    protected LanguageCore $language
)
```

### Classification

**Operational** — files are core attachments used across projects, tickets, clients, and private storage.

---

## 20. NOTIFICATION

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model | `Notification` | `Leantime\Domain\Notifications\Models` |
| Service | `Notifications` | `Leantime\Domain\Notifications\Services` |
| Repository | `Notifications` | `Leantime\Domain\Notifications\Repositories` |

### Evidence

- Model: `app/Domain/Notifications/Models/Notification.php`
- Service: `app/Domain/Notifications/Services/Notifications.php`
- Repository: `app/Domain/Notifications/Repositories/Notifications.php`

### Storage/Table Backing

**Table: `zp_notifications`**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | int (PK) | Notification ID |
| `userId` | int | FK → `zp_user.id` (recipient) |
| `read` | int (0/1) | Read status flag |
| `type` | string | Notification type (e.g., `'mention'`, `'ainotification'`) |
| `module` | string | Source module (e.g., `'tickets'`, `'comments'`, `'goalcanvas'`) |
| `moduleId` | int | ID of the entity within the module |
| `message` | string | Notification message text |
| `datetime` | datetime | Timestamp |
| `url` | string | Link to the source entity |
| `authorId` | int | FK → `zp_user.id` (trigger user) |

### Key Fields (Model Properties)

| Property | Type |
|----------|------|
| `$id` | `int` |
| `$message` | `string` |
| `$subject` | `string` |
| `$projectId` | `int` |
| `$authorId` | `int` |
| `$url` | `bool\|array` |
| `$entity` | `mixed` |
| `$module` | `string` |
| `$action` | `string` |

### Primary Identifiers

- `zp_notifications.id` — auto-increment integer

### Ownership/Scope

- Notifications are owned by a **User** (recipient: `userId`)
- Triggered by a **User** (author: `authorId`)
- Scoped to a **module + moduleId** (polymorphic)

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| User (recipient) | `zp_notifications.userId` | Many-to-one |
| User (author) | `zp_notifications.authorId` → `zp_user.id` (LEFT JOIN) | Many-to-one |

### Workflow/State Relevance

**Read status:** Binary — `read = 0` (unread) or `read = 1` (read). Toggled by `markNotificationRead()` or `markAllNotificationRead()`.

**Relevance levels** (model constants):

| Constant | Value | Label |
|----------|-------|-------|
| `RELEVANCE_ALL` | `'all'` | All activity |
| `RELEVANCE_MY_WORK` | `'my_work'` | My work only |
| `RELEVANCE_MUTED` | `'muted'` | Muted |

**Notification categories** (model constant `NOTIFICATION_CATEGORIES`):

| Category | Modules | Description |
|----------|---------|-------------|
| `tasks` | `['tickets']` | Task notifications |
| `comments` | `['comments']` | Comment notifications |
| `goals` | `['goalcanvas']` | Goal notifications |
| `ideas` | `['ideas']` | Idea notifications |
| `projects` | `['projects']` | Project notifications |
| `boards` | `[]` (catch-all for `*canvas`) | Board notifications |

**Type values:**
- `'mention'` — user @mention
- `'ainotification'` — AI-generated (filtered OUT of standard queries)

### Service Methods

| Method | Purpose |
|--------|---------|
| `getAllNotifications($userId, $showNewOnly, $limitStart, $limitEnd, $filterOptions)` | Paginated notification retrieval with filtering |
| `addNotifications(array $notifications)` | Bulk insert notifications |
| `markNotificationRead($id, $userId)` | Mark one or all as read |
| `processMentions($content, $module, $moduleId, $authorId, $url)` | Parse HTML for `data-tagged-user-id` attributes, create mention notifications, send emails |

### Classification

**Operational** — notifications drive user engagement and awareness of system events.

---

## 21. AUDIT

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Repository | `Audit` | `Leantime\Domain\Audit\Repositories` |

**No service class. No model class.** Only the repository exists.

### Evidence

- Repository: `app/Domain/Audit/Repositories/Audit.php`

### Storage/Table Backing

**Table: `zp_audit`**

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `id` | INT | NO | Auto-increment PK |
| `userId` | INT | YES | FK → `zp_user.id` |
| `projectId` | INT | YES | FK → `zp_projects.id` |
| `action` | VARCHAR(45) | YES | Action type (e.g., `'article.create'`, `'article.edit'`) |
| `entity` | VARCHAR(45) | YES | Entity type (e.g., `'article'`) |
| `entityId` | INT | YES | ID of the affected entity |
| `values` | TEXT | YES | JSON-encoded change values |
| `date` | DATETIME | YES | Event timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `KEY projectId (projectId ASC)`
- `KEY projectAction (projectId ASC, action ASC)`
- `KEY projectEntityEntityId (projectId ASC, entity ASC, entityId ASC)`

### Primary Identifiers

- `zp_audit.id` — auto-increment integer

### Ownership/Scope

- Events belong to a **User** (`userId`) within a **Project** (`projectId`)
- Polymorphically references any entity via `entity` + `entityId`

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| User | `zp_audit.userId` → `zp_user.id` (LEFT JOIN in `getEventsForEntity`) | Many-to-one |
| Project | `zp_audit.projectId` | Many-to-one |
| Any entity | `entity` + `entityId` | Polymorphic |

### Repository Methods

| Method | Purpose |
|--------|---------|
| `storeEvent($action, $values, $entity, $entityId, $userId, $projectId, $thedate)` | Store audit event |
| `getLastEvent($action)` | Get most recent event (optionally filtered) |
| `getEventsForEntity($entity, $entityId, $limit)` | Get events for an entity with user info |
| `pruneEvents($ageDays = 30)` | Delete events older than N days |

### Workflow/State Relevance

No states — audit is append-only (with pruning). Used by Wiki service for article change tracking.

### Classification

**Auxiliary** — audit provides a write-ahead log for change tracking; consumed by Wiki activity feeds.

---

## 22. REACTION

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model | `Reactions` | `Leantime\Domain\Reactions\Models` |
| Service | `Reactions` | `Leantime\Domain\Reactions\Services` |
| Repository | `Reactions` | `Leantime\Domain\Reactions\Repositories` |

### Evidence

- Model: `app/Domain/Reactions/Models/Reactions.php`
- Service: `app/Domain/Reactions/Services/Reactions.php`
- Repository: `app/Domain/Reactions/Repositories/Reactions.php`

### Storage/Table Backing

**Table: `zp_reactions`**

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `id` | INT | NO | Auto-increment PK |
| `userId` | INT | YES | FK → `zp_user.id` |
| `moduleId` | INT | YES | Entity ID (polymorphic) |
| `module` | VARCHAR(45) | YES | Module type (polymorphic) |
| `reaction` | VARCHAR(45) | YES | Reaction type string |
| `date` | DATETIME | YES | Reaction timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX entity (moduleId ASC, module ASC, reaction ASC)`
- `INDEX user (userId ASC, moduleId ASC, module ASC, reaction ASC)`

### Key Fields (Model — Static Properties)

**Reaction type constants:**

| Property | Value |
|----------|-------|
| `$favorite` | `'favorite'` |
| `$watch` | `'watch'` |
| `$downvote` | `'downvote'` |
| `$upvote` | `'upvote'` |
| `$funny` | `'funny'` |
| `$like` | `'like'` |
| `$anger` | `'anger'` |
| `$love` | `'love'` |
| `$support` | `'support'` |
| `$celebrate` | `'celebrate'` |
| `$interesting` | `'interesting'` |
| `$sad` | `'sad'` |

**Reaction categories** (`$reactionTypes`):

| Category | Reactions | Display |
|----------|-----------|---------|
| `sentimentReactions` | like 👍, anger 😡, love ❤, support 💯, celebrate 🎉, interesting 💡, sad 😥, funny 😂 | Emoji |
| `contentReactions` | upvote ⬆, downvote ⬇ | Font Awesome icons |
| `entityReactions` | favorite ⭐, watch 👁 | Font Awesome icons |

### Primary Identifiers

- `zp_reactions.id` — auto-increment integer

### Ownership/Scope

- Reactions are owned by a **User** (`userId`)
- Polymorphically attached to any entity via `module` + `moduleId`

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| User | `zp_reactions.userId` → `zp_user.id` (LEFT JOIN) | Many-to-one |
| Any entity | `module` + `moduleId` | Polymorphic |

### Workflow/State Relevance

No state machine. Reactions are added/removed (toggle). Duplicate prevention: service checks for existing reaction by type before adding.

### Service Methods

| Method | Purpose |
|--------|---------|
| `addReaction($userId, $module, $moduleId, $reaction)` | Add reaction (prevents duplicate by type) |
| `removeReaction($userId, $module, $moduleId, $reaction)` | Remove user reaction |
| `getReactionType($reaction)` | Get category of a reaction |
| `getGroupedEntityReactions($module, $moduleId)` | Counted reactions for an entity |
| `getUserReactions($userId, $module, $moduleId, $reaction)` | User's reactions (flexible filter) |
| `getEntityReactionsWithUsers($module, $moduleId)` | Reactions grouped with user names |

### Classification

**Auxiliary** — reactions provide social engagement features (favorites, watches, emoji reactions) across all entities.

---

## 23. ENTITY RELATIONSHIP

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Entityrelations` | `Leantime\Domain\Entityrelations\Services` |
| Repository | `Entityrelations` | `Leantime\Domain\Entityrelations\Repositories` |
| Enum | `EntityRelationshipEnum` | `Leantime\Core\Support` |

**No model class exists.** No controllers (backend-only domain).

### Evidence

- Service: `app/Domain/Entityrelations/Services/Entityrelations.php`
- Repository: `app/Domain/Entityrelations/Repositories/Entityrelations.php`
- Enum: `app/Core/Support/EntityRelationshipEnum.php`
- Schema definition: `app/Domain/Install/Services/SchemaBuilder.php:713`
- Usage: `app/Domain/Tickets/Repositories/Tickets.php` (lines 450, 670, 1728, 1741, 1758)

### Storage/Table Backing

> **IMPORTANT ARCHITECTURAL NOTE:** There is a naming mismatch. The **`zp_entity_relationship`** table exists in the database and is used directly by the Tickets repository. However, the `Entityrelations` domain service/repository are **thin wrappers around `zp_settings`**, NOT `zp_entity_relationship`.

#### Table: `zp_entity_relationship` (used directly by Tickets domain)

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `id` | INT (PK) | NO | Auto-increment |
| `entityA` | INT | YES | First entity ID |
| `entityAType` | VARCHAR(45) | YES | First entity type (e.g., `'Ticket'`) |
| `entityB` | INT | YES | Second entity ID |
| `entityBType` | VARCHAR(45) | YES | Second entity type (e.g., `'User'`) |
| `relationship` | VARCHAR(45) | YES | Relationship type |
| `createdOn` | DATETIME | YES | Creation timestamp |
| `createdBy` | INT | YES | FK → `zp_user.id` |
| `meta` | TEXT | YES | Additional metadata |

**Indexes:**
- `idx_entity_relationship_entityA (entityA, entityAType, relationship)`
- `idx_entity_relationship_entityB (entityB, entityBType, relationship)`

#### Table: `zp_settings` (used by Entityrelations domain service/repository)

The Entityrelations repository's `getSetting()`, `saveSetting()`, `deleteSetting()` methods operate on `zp_settings` — storing relationship data as key-value pairs.

### Relationship Types (Enum)

```php
enum EntityRelationshipEnum: string
{
    case Collaborator = 'collaborator';
    // "Add other relationship types as needed."
}
```

Currently only `Collaborator` is defined. Used in Tickets repository for ticket-user collaborator relationships.

### Primary Identifiers

- `zp_entity_relationship.id` — auto-increment integer

### Ownership/Scope

- Relationships are between any two entities (polymorphic on both sides)
- Created by a **User** (`createdBy`)

### Relationships (from Tickets domain usage)

| entityA (Type) | entityB (Type) | relationship | Purpose |
|----------------|---------------|-------------|---------|
| Ticket ID (`Ticket`) | User ID (`User`) | `collaborator` | Ticket collaborators |

### Entityrelations Service Methods

| Method | Actual Behavior |
|--------|----------------|
| `saveRelationship($entityA, $entityAType, $relationship, $entityB, $entityBType, $meta)` | Delegates to `Setting` repository's `saveSetting()` — stores in `zp_settings` |
| `getRelationshipByEntity($entitySide, $entity, $entityType, $relationship)` | Delegates to `Setting` repository's `getSetting()` — reads from `zp_settings` |

### Classification

**Auxiliary** — entity relationships provide polymorphic linkage between domain entities. The domain module is under-developed (wraps settings), while the actual `zp_entity_relationship` table is used directly by Tickets.

---

## 24. INTEGRATION / CONNECTOR

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model (Entity) | `Entity` | `Leantime\Domain\Connector\Models` |
| Model (Field) | `Field` | `Leantime\Domain\Connector\Models` |
| Model (Integration) | `Integration` | `Leantime\Domain\Connector\Models` |
| Model (Provider) | `Provider` | `Leantime\Domain\Connector\Models` |
| Service | `Connector` | `Leantime\Domain\Connector\Services` |
| Repository | `Integrations` | `Leantime\Domain\Connector\Repositories` |

### Evidence

- Models: `app/Domain/Connector/Models/{Entity,Field,Integration,Provider}.php`
- Service: `app/Domain/Connector/Services/Connector.php`
- Repository: `app/Domain/Connector/Repositories/Integrations.php`

### Storage/Table Backing

**Table: `zp_integration`**

The repository extends `Leantime\Core\Db\Repository` with `$this->entity = 'integration'` — the base Repository class prepends `zp_` automatically (e.g., `'UPDATE zp_' . $this->entity`).

| Column | Type | DbColumn Attribute | Purpose |
|--------|------|-------------------|---------|
| `id` | INT (PK) | `id` | Auto-increment |
| `providerId` | VARCHAR(45) | `providerId` | Provider identifier |
| `method` | VARCHAR(45) | `method` | Integration method |
| `entity` | VARCHAR(45) | `entity` | Entity type being synced |
| `fields` | TEXT | `fields` | Field mappings (JSON) |
| `schedule` | VARCHAR(45) | `schedule` | Sync schedule |
| `notes` | VARCHAR(45) | `notes` | Notes |
| `auth` | TEXT | `auth` | Authentication data (JSON) |
| `meta` | VARCHAR(45) | `meta` | Metadata |
| `createdOn` | DATETIME | `createdOn` | Creation timestamp |
| `createdBy` | INT | `createdBy` | Creator user ID |
| `lastSync` | VARCHAR(45) | `lastSync` | Last sync timestamp |

### Key Fields (Models)

**Entity model** — runtime data structure for connector mapping:

| Property | Type |
|----------|------|
| `$id` | `int` |
| `$name` | `string` |
| `$authData` | `string` |
| `$notes` | `string` |
| `$leantimeEntity` | `mixed` |
| `$fieldMappings` | `array` |
| `$providerEntity` | `mixed` |

**Field model:**

| Property | Type |
|----------|------|
| `$id` | `int` |
| `$entityConnectionId` | `int` |
| `$leantimeFields` | `string` |
| `$providerEntity` | `string` |
| `$typeConnector` | `string` |

**Provider model:**

| Property | Type | Default |
|----------|------|---------|
| `$id` | `mixed` | — |
| `$name` | `string` | — |
| `$description` | `string` | — |
| `$image` | `string` | — |
| `$availableEntities` | `array` | `[]` |
| `$availableMethods` | `array` | `[]` |
| `$steps` | `array` | `['connect', 'entity', 'fields', 'sync', 'parse', 'import']` |
| `$stepDetails` | `array` | Step metadata with titles and positions |
| `$button` | `array` | `['url' => '', 'text' => '']` |

### Primary Identifiers

- `zp_integration.id` — auto-increment integer

### Ownership/Scope

- Integrations are created by a **User** (`createdBy`)
- Linked to a **Provider** (`providerId`)

### Connector Service — Supported Entities

The service can parse and import these entity types (via `parseValues()`/`importValues()`):
- `tickets` — uses `TicketService`/`TicketRepository`
- `projects` — uses `ProjectService`
- `users` — uses `UserService`
- `ideas` — uses `Ideas` repository
- `goals` — uses `Goalcanvas` repository
- `milestones` — uses `TicketRepository`

### Classification

**Contextual** — integrations enable external system sync (import/export) but are not part of core workflow.

---

## 25. PLUGIN

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model (Installed) | `InstalledPlugin` | `Leantime\Domain\Plugins\Models` |
| Model (Marketplace) | `MarketplacePlugin` | `Leantime\Domain\Plugins\Models` |
| Service | `Plugins` | `Leantime\Domain\Plugins\Services` |
| Repository | `Plugins` | `Leantime\Domain\Plugins\Repositories` |

Both models implement `PluginDisplayStrategy` interface.

### Evidence

- Models: `app/Domain/Plugins/Models/{InstalledPlugin,MarketplacePlugin}.php`
- Service: `app/Domain/Plugins/Services/Plugins.php`
- Repository: `app/Domain/Plugins/Repositories/Plugins.php`

### Storage/Table Backing

**Table: `zp_plugins`**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | integer (PK) | Auto-increment |
| `name` | string | Plugin name |
| `enabled` | boolean | Enable/disable flag |
| `description` | string | Plugin description |
| `version` | string | Version number |
| `installdate` | string | Installation date |
| `foldername` | string | Plugin folder name |
| `homepage` | string | Homepage URL |
| `authors` | string | JSON-encoded authors array |
| `format` | string | Plugin format (`'phar'` or folder) |
| `license` | string | License type |

### Key Fields

**InstalledPlugin model:**

| Property | Type | Default |
|----------|------|---------|
| `$id` | `?int` | — |
| `$name` | `string` | — |
| `$enabled` | `bool` | — |
| `$description` | `string` | — |
| `$version` | `string` | — |
| `$imageUrl` | `string` | `''` |
| `$vendorDisplayName` | `string` | — |
| `$vendorId` | `int` | — |
| `$vendorEmail` | `string` | — |
| `$installdate` | `string` | — |
| `$foldername` | `string` | — |
| `$homepage` | `string` | — |
| `$authors` | `string\|array` | — |
| `$format` | `?string` | — |
| `$license` | `?string` | — |
| `$type` | `?string` | — |
| `$installed` | `?bool` | — |
| `$startingPrice` | `?string` | — |
| `$calculatedMonthlyPrice` | `?string` | — |
| `$identifier` | `?string` | — |

**MarketplacePlugin model** (additional properties):

| Property | Type | Default |
|----------|------|---------|
| `$identifier` | `string` | `''` |
| `$excerpt` | `string` | `''` |
| `$marketplaceUrl` | `string` | `''` |
| `$startingPrice` | `?string` | `null` |
| `$calculatedMonthlyPrice` | `?string` | `null` |
| `$pricingTiers` | `?array` | `null` |
| `$rating` | `?string` | `null` |
| `$reviewCount` | `?int` | `null` |
| `$type` | `string` | `'marketplace'` |
| `$reviews` | `array` | `[]` |
| `$marketplaceId` | `string` | `''` |
| `$compatibility` | `array` | `[]` |
| `$icon` | `string` | `''` |
| `$categories` | `array` | `[]` |
| `$tags` | `array` | `[]` |

### Primary Identifiers

- `zp_plugins.id` — auto-increment integer
- `InstalledPlugin.$identifier` — unique plugin identifier (generated from name if not set)

### Ownership/Scope

- Plugins are system-level — not scoped to project or user

### Plugin Types

| Type | Source | Description |
|------|--------|-------------|
| `system` | `LEAN_PLUGINS` env var | Always loaded, cannot be disabled via UI |
| `marketplace` | `marketplace.leantime.io` | Phar packages with license key validation |
| `custom` | Plugin folder | User-developed plugins |

### Workflow/State Relevance

**Plugin lifecycle:** `discoverNewPlugins()` → `installPlugin()` → `enablePlugin()` → `disablePlugin()` → `removePlugin()`

**Enabled state:** Binary — `enabled = 0/1` in database.

### Key Service Methods

| Method | Purpose |
|--------|---------|
| `getAllPlugins($enabledOnly)` | Get all/enabled plugins |
| `discoverNewPlugins()` | Scan for new plugin folders |
| `createPluginFromComposer($folder, $license)` | Create plugin from composer.json |
| `installPlugin($folder)` | Install plugin |
| `enablePlugin($id)` / `disablePlugin($id)` | Toggle enabled state |
| `removePlugin($id)` | Delete plugin |
| `getMarketplacePlugins($page, $query)` | Fetch from marketplace API |
| `installMarketplacePlugin($plugin, $version)` | Download and install marketplace plugin |
| `validLicense($plugin)` | Validate plugin license |
| `disablePluginNotifyOwner($pluginId)` | Disable and notify (license violation) |

### Classification

**System** — plugins extend the platform and are managed at the system administration level.

---

## 26. SETTING

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Setting` | `Leantime\Domain\Setting\Services` |
| Repository | `Setting` | `Leantime\Domain\Setting\Repositories` |
| Cache | `SettingCache` | `Leantime\Domain\Setting\Services` |

**No model class.**

### Evidence

- Service: `app/Domain/Setting/Services/Setting.php`
- Repository: `app/Domain/Setting/Repositories/Setting.php`
- Cache: `app/Domain/Setting/Services/SettingCache.php`

### Storage/Table Backing

**Table: `zp_settings`** — Key-value store

| Column | Type | Purpose |
|--------|------|---------|
| `key` | VARCHAR(175) (PK) | Setting identifier |
| `value` | MEDIUMTEXT | Setting value |

**Indexes:**
- `PRIMARY KEY (key)`
- `KEY idx_settings_key (key)`

### Primary Identifiers

- `zp_settings.key` — string primary key (VARCHAR 175)

### Ownership/Scope

- Settings are **system-global** — not scoped to user or project

### Caching Strategy

Two-tier cache via `SettingCache`:
1. **In-memory** (request-level `$inMemory` array) — eliminates redundant file/Redis reads within a request
2. **Laravel cache** (persistent, 1-hour TTL with prefix `'setting:'`) — cross-request caching
3. **Sentinel value** `'__SETTING_CACHE_NOT_FOUND__'` — distinguishes cache miss from `null`/`false` values

### Service Methods

| Method | Purpose |
|--------|---------|
| `saveSetting($key, $value)` | Save key-value pair |
| `getSetting($key, $default)` | Get setting value |
| `deleteSetting($key)` | Delete a setting |
| `setLogo($file)` | Upload and save company logo |
| `resetLogo()` | Delete logo and reset session |
| `getCompanyId()` | Get or create company UUID (`anonymousId`) |
| `onboardingHandler()` | Handle onboarding state |

### Repository Methods

| Method | Purpose |
|--------|---------|
| `getSetting($type, $default)` | Get with two-tier cache lookup |
| `saveSetting($type, $value)` | Save/update and update cache |
| `getSettingsForKeys(array $keys)` | Batch fetch multiple settings |
| `deleteSetting($type)` | Delete and clear cache |
| `checkIfInstalled()` | Check if `zp_user` table exists |

### Classification

**System** — settings store all system-level configuration as a key-value store.

---

## 27. QUEUE MESSAGE

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Queue` | `Leantime\Domain\Queue\Services` |
| Repository | `Queue` | `Leantime\Domain\Queue\Repositories` |
| Enum | `Workers` | `Leantime\Domain\Queue\Workers` |

**No model class.**

### Evidence

- Service: `app/Domain/Queue/Services/Queue.php`
- Repository: `app/Domain/Queue/Repositories/Queue.php`
- Enum: `app/Domain/Queue/Workers/Workers.php` (inferred from service code)

### Storage/Table Backing

**Table: `zp_queue`**

| Column | Purpose |
|--------|---------|
| `msghash` | MD5 hash (deduplication key) |
| `channel` | Worker channel (from `Workers` enum) |
| `userId` | FK → `zp_user.id` (recipient) |
| `subject` | Message subject |
| `message` | Message body |
| `thedate` | Timestamp (Y-m-d H:i:s) |
| `projectId` | FK → `zp_projects.id` |

### Primary Identifiers

- `zp_queue.msghash` — MD5 hash string (used for deduplication and deletion)
- No auto-increment ID column observed

### Ownership/Scope

- Messages target a **User** (`userId`) within a **Project** (`projectId`)
- Messages are routed to a **Worker channel** (`channel`)

### Worker Types (Enum)

| Case | Value |
|------|-------|
| `EMAILS` | `'email'` |
| `HTTPREQUESTS` | `'httprequests'` |
| `DEFAULT` | `'default'` |

### Service Dependencies

```php
public function __construct(
    QueueRepository $queue,
    UserRepository $userRepo,
    SettingRepository $settingsRepo,
    MailerCore $mailer,
    LanguageCore $language
)
```

### Service Methods

| Method | Purpose |
|--------|---------|
| `processQueue(Workers $worker)` | Process messages for a specific worker |
| `addToQueue(Workers $channel, $subject, $message, $projectId)` | Add message to queue |
| `addJob(Workers $channel, $subject, $message, $userId, $projectId)` | Static convenience method |

### Repository Methods

| Method | Purpose |
|--------|---------|
| `queueMessageToUsers(array $recipients, $message, $subject, $projectId)` | Bulk queue to users |
| `listMessageInQueue(Workers $channel, $recipients, $projectId)` | List messages by channel |
| `deleteMessageInQueue($msghashes)` | Delete by hash(es) |
| `addMessageToQueue(Workers $channel, $subject, $message, $userId, $projectId)` | Add single message |

### Workflow/State Relevance

Messages are created → processed → deleted. No explicit status column; processing removes messages from the queue.

### Classification

**System** — queue handles asynchronous message delivery (primarily email notifications).

---

## 28. CALENDAR EVENT

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Service | `Calendar` | `Leantime\Domain\Calendar\Services` |
| Repository | `Calendar` | `Leantime\Domain\Calendar\Repositories` |

**No model class.**

### Evidence

- Service: `app/Domain/Calendar/Services/Calendar.php`
- Repository: `app/Domain/Calendar/Repositories/Calendar.php`

### Storage/Table Backing

**Table: `zp_calendar`** — Personal calendar events

| Column | Purpose |
|--------|---------|
| `id` | Primary key (auto-increment int) |
| `userId` | FK → `zp_user.id` |
| `dateFrom` | Event start datetime |
| `dateTo` | Event end datetime |
| `description` | Event description |
| `allDay` | Boolean/int — all-day event flag |

**Table: `zp_gcallinks`** — External (Google) calendar subscriptions

| Column | Purpose |
|--------|---------|
| `id` | Primary key (auto-increment int) |
| `userId` | FK → `zp_user.id` |
| `url` | Calendar URL |
| `name` | Calendar display name |
| `colorClass` | CSS color class |

### Primary Identifiers

- `zp_calendar.id` — auto-increment integer
- `zp_gcallinks.id` — auto-increment integer

### Ownership/Scope

- Calendar events are owned by a **User** (`userId`)
- External calendars are owned by a **User** (`userId`)
- Calendar also aggregates ticket dates from `zp_tickets`

### Relationships

| Related Entity | Via | Cardinality |
|---------------|-----|-------------|
| User | `zp_calendar.userId` | Many-to-one |
| Ticket (wish dates) | `zp_tickets.dateToFinish` | Aggregated |
| Ticket (edit dates) | `zp_tickets.editFrom`/`editTo` | Aggregated |

### Calendar Event Types

| Type | Source |
|------|--------|
| `'calendar'` | Personal events from `zp_calendar` |
| `'ticket'` | Ticket due dates and edit periods from `zp_tickets` |

### Date Context Values

| Context | Meaning |
|---------|---------|
| `'plan'` | Planned date |
| `'due'` | Due date |
| `'edit'` | Edit period |

### Color Classes

17 available: `label-warning`, `label-purple`, `label-pink`, `label-darker-blue`, `label-info`, `label-blue`, `label-dark-blue`, `label-success`, `label-brown`, `label-danger`, `label-important`, `label-green`, `label-default`, `label-dark-green`, `label-red`, `label-dark-red`, `label-grey`

### Service Methods

| Method | Purpose |
|--------|---------|
| `addEvent($values)` | Create calendar event |
| `getEvent($eventId)` | Get single event |
| `editEvent($values)` | Edit event |
| `delEvent($id)` | Delete event |
| `getCalendar($userId, $from, $until)` | Get all events with optional date range |
| `getExternalCalendar($id, $userId)` | Get external calendar |
| `editExternalCalendar($values, $id)` | Edit external calendar |
| `getIcalByHash($userHash, $calHash)` | Get iCal export by hash |
| `getExternalCalendarEvents($from, $until)` | Fetch external calendar events |
| `generateIcalHash()` | Generate iCal export hash |
| `deleteGCal($id)` | Delete external calendar |

### Classification

**Operational** — calendar provides personal scheduling and aggregates ticket deadlines.

---

## 29. SPRINT STATISTICS

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Model | `Reports` | `Leantime\Domain\Reports\Models` |
| Service | `Reports` | `Leantime\Domain\Reports\Services` |
| Repository | `Reports` | `Leantime\Domain\Reports\Repositories` |

### Evidence

- Model: `app/Domain/Reports/Models/Reports.php`
- Service: `app/Domain/Reports/Services/Reports.php`
- Repository: `app/Domain/Reports/Repositories/Reports.php`

### Storage/Table Backing

**Table: `zp_stats`**

| Column | Purpose |
|--------|---------|
| `sprintId` | FK → sprint ID (-1 for backlog, 0 for backlog report) |
| `projectId` | FK → `zp_projects.id` |
| `date` | Snapshot datetime |
| `sum_todos` | Total ticket count |
| `sum_open_todos` | Tickets in NEW status |
| `sum_progres_todos` | Tickets in INPROGRESS status |
| `sum_closed_todos` | Tickets in DONE status |
| `sum_planned_hours` | Total planned hours |
| `sum_estremaining_hours` | Estimated remaining hours |
| `sum_logged_hours` | Total logged hours |
| `sum_points` | Total story points |
| `sum_points_done` | Story points completed |
| `sum_points_progress` | Story points in progress |
| `sum_points_open` | Story points open |
| `sum_todos_xs` | 1-point tickets |
| `sum_todos_s` | 2-point tickets |
| `sum_todos_m` | 3-point tickets |
| `sum_todos_l` | 5-point tickets |
| `sum_todos_xl` | 8-point tickets |
| `sum_todos_xxl` | 13-point tickets |
| `sum_todos_none` | Unpointed tickets |
| `tickets` | Comma-separated ticket IDs in snapshot |
| `daily_avg_hours_booked_todo` | Daily average hours booked per ticket |
| `daily_avg_hours_booked_point` | Daily average hours booked per point |
| `daily_avg_hours_planned_todo` | Daily average hours planned per ticket |
| `daily_avg_hours_planned_point` | Daily average hours planned per point |
| `daily_avg_hours_remaining_point` | Daily average hours remaining per point |
| `daily_avg_hours_remaining_todo` | Daily average hours remaining per ticket |
| `sum_teammembers` | Team member count |

### Model Properties

All public, untyped — mirrors the `zp_stats` columns exactly:
`$sprintId`, `$projectId`, `$date`, `$sum_todos`, `$sum_open_todos`, `$sum_progres_todos`, `$sum_closed_todos`, `$sum_planned_hours`, `$sum_estremaining_hours`, `$sum_logged_hours`, `$sum_points`, `$sum_points_done`, `$sum_points_progress`, `$sum_points_open`, `$sum_todos_xs`, `$sum_todos_s`, `$sum_todos_m`, `$sum_todos_l`, `$sum_todos_xl`, `$sum_todos_xxl`, `$sum_todos_none`, `$tickets`, `$daily_avg_hours_booked_todo`, `$daily_avg_hours_booked_point`, `$daily_avg_hours_planned_todo`, `$daily_avg_hours_planned_point`, `$daily_avg_hours_remaining_point`, `$daily_avg_hours_remaining_todo`, `$sum_teammembers`

### Primary Identifiers

No explicit primary key observed — records are identified by **composite key**: `(sprintId, projectId, date)`.

### Ownership/Scope

- Statistics are scoped to a **Project** (`projectId`) and **Sprint** (`sprintId`)
- Aggregated from `zp_tickets` data

### Status Groups for Aggregation

| Group | Description |
|-------|-------------|
| `NEW` | Open tickets |
| `INPROGRESS` | In-progress tickets |
| `DONE` | Completed tickets |

### Service Methods

| Method | Purpose |
|--------|---------|
| `dailyIngestion()` | Run daily stats snapshot for current project |
| `cronDailyIngestion()` | Run daily snapshot for ALL projects |
| `getFullReport($projectId)` | Aggregated project report |
| `getRealtimeReport($projectId, $sprintId)` | Real-time ticket statistics |
| `getProjectStatusReport()` | Project status distribution (green/yellow/red/none) |
| `generateTicketReactionsReport()` | Ticket sentiment analysis |
| `getAnonymousTelemetry(...)` | Anonymous usage telemetry |
| `sendAnonymousTelemetry()` | Send telemetry to server |

### Repository Methods

| Method | Purpose |
|--------|---------|
| `runTicketReport($projectId, $sprintId)` | Generate ticket report snapshot |
| `checkLastReportEntries($projectId)` | Check if today's report exists |
| `addReport($report)` | Insert into `zp_stats` |
| `getSprintReport($sprint)` | Sprint-specific report history |
| `getBacklogReport($project)` | Backlog report (sprintId=0) |
| `getFullReport($project)` | Full project report |

### Classification

**Reporting** — sprint statistics provide historical snapshots of project progress for burndown charts and velocity tracking.

---

## 30. READ STATUS

### Code Symbols

| Layer | Class | Namespace |
|-------|-------|-----------|
| Repository | `Read` | `Leantime\Domain\Read\Repositories` |

**No service class. No model class.** Only the repository exists.

### Evidence

- Repository: `app/Domain/Read/Repositories/Read.php`

### Storage/Table Backing

**Table: `zp_read`**

| Column | Type | Purpose |
|--------|------|---------|
| `module` | string | Module name (polymorphic) |
| `moduleId` | int\|string | Entity ID within module |
| `userId` | int\|string | FK → `zp_user.id` |

### Primary Identifiers

No auto-increment ID — records are identified by **composite key**: `(module, moduleId, userId)`.

### Ownership/Scope

- Read status is per-**User** per-**entity** (polymorphic via module + moduleId)

### Repository Methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `markAsRead` | `markAsRead(string $module, int\|string $moduleId, int\|string $userId): void` | Mark item as read for user |
| `isRead` | `isRead(string $module, int\|string $moduleId, int\|string $userId): bool` | Check if item is read by user |

### Workflow/State Relevance

Binary state: **read** or **not read** (absence of record = unread).

### Classification

**Auxiliary** — read status is a lightweight tracking mechanism for unread indicators across any module.

---

## Cross-Reference: Canvas Variant Summary

All canvas variants share **`zp_canvas`** (boards) and **`zp_canvas_items`** (items) tables. The `type` column discriminates boards; the `box` column holds variant-specific categories.

| Variant | `CANVAS_NAME` | `type` | Icon | Box Values | Status Override | Extends Canvas Base |
|---------|-------------|--------|------|-----------|----------------|-------------------|
| **Goal** | `goal` | `goal` | `fa-bullseye` | `goal` | 3 statuses (ontrack/atrisk/miss) | ✅ |
| **Idea** | N/A | `idea` | N/A | `idea`, `research`, `prototype`, `validation`, `implemented`, `deferred` | N/A (own repo) | ❌ (standalone) |
| **Risk** | `risks` | `risks` | `fa-person-falling` | 4 quadrants (impact × probability) | Uses base (5 statuses) | ✅ |
| **Retro** | `retros` | `retros` | `fa-hand-spock` | `well`, `notwell`, `startdoing` | Uses base (empty override) | ✅ |
| **Wiki** | `wiki` | `wiki` | N/A | `article` | `published`, `draft` | ✅ |

### Other Canvas Variants (not detailed — follow same pattern)

`Cpcanvas`, `Dbmcanvas`, `Eacanvas`, `Emcanvas`, `Insightscanvas`, `Lbmcanvas`, `Leancanvas`, `Minempathycanvas`, `Obmcanvas`, `Sbcanvas`, `Smcanvas`, `Sqcanvas`, `Swotcanvas`, `Valuecanvas`

---

## Cross-Reference: Table Registry (Part 2)

| Table | Entity | Primary Key | Polymorphic |
|-------|--------|-------------|-------------|
| `zp_canvas` | Canvas / Wiki / Goal / Idea / Risk / Retro boards | `id` (int) | `type` column discriminates variant |
| `zp_canvas_items` | Canvas items / Articles / Goals / Ideas / Risks / Retro items | `id` (int) | `box` column varies by variant |
| `zp_file` | File / Attachment | `id` (int) | `module` + `moduleId` |
| `zp_notifications` | Notification | `id` (int) | `module` + `moduleId` |
| `zp_audit` | Audit event | `id` (int) | `entity` + `entityId` |
| `zp_reactions` | Reaction | `id` (int) | `module` + `moduleId` |
| `zp_entity_relationship` | Entity Relationship | `id` (int) | `entityA`/`entityAType` + `entityB`/`entityBType` |
| `zp_integration` | Integration / Connector | `id` (int) | No |
| `zp_plugins` | Plugin | `id` (int) | No |
| `zp_settings` | Setting | `key` (string) | No |
| `zp_queue` | Queue Message | `msghash` (string) | No |
| `zp_calendar` | Calendar Event | `id` (int) | No |
| `zp_gcallinks` | External Calendar | `id` (int) | No |
| `zp_stats` | Sprint Statistics | Composite (`sprintId`, `projectId`, `date`) | No |
| `zp_read` | Read Status | Composite (`module`, `moduleId`, `userId`) | `module` + `moduleId` |
