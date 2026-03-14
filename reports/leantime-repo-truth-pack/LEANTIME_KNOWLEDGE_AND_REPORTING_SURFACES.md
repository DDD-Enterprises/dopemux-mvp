# Leantime Knowledge & Reporting Surfaces

> Evidence-backed catalog of every knowledge, context, and reporting surface in Leantime.
> For each surface: data structure, classification, durability, indexability, and AI-summary suitability.

---

## Surface Classification Key

| Classification | Meaning |
|---|---|
| **Operational Truth** | Authoritative source-of-record data that drives system behavior |
| **Contextual Reference** | Supporting information that enriches understanding but doesn't drive logic |
| **Reporting Projection** | Derived/aggregated data computed from operational truth for display |
| **Noise** | Ephemeral, redundant, or low-signal data not worth preserving |

---

## 1. Wiki / Docs / Knowledge Base

### Evidence Sources
- `app/Domain/Wiki/Services/Wiki.php` — Service layer (CRUD + audit)
- `app/Domain/Wiki/Repositories/Wiki.php` — Data access (SQL via Query Builder)
- `app/Domain/Wiki/Models/Wiki.php` — Wiki container model
- `app/Domain/Wiki/Models/Article.php` — Article model (hierarchical content)
- `app/Domain/Wiki/Models/Template.php` — Content templates
- `app/Domain/Wiki/Hxcontrollers/ArticleContent.php` — HTMX auto-save
- `app/Domain/Wiki/Hxcontrollers/ArticleActivity.php` — HTMX activity feed

### Data Structure

**Database Tables**: `zp_canvas` (wiki containers) + `zp_canvas_items` (articles)

Wiki reuses the Canvas infrastructure with `type = 'wiki'` discriminator.

#### Wiki Container (`zp_canvas`)
| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Wiki identifier |
| `title` | VARCHAR(255) | Wiki name |
| `author` | INT | Creator user ID |
| `created` | DATETIME | Creation timestamp |
| `projectId` | INT FK | Owning project |
| `type` | VARCHAR(45) | Always `'wiki'` |
| `description` | TEXT | Wiki description |

#### Article (`zp_canvas_items` with `box = 'article'`)
| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Article identifier |
| `title` | VARCHAR(255) | Article title |
| `description` | TEXT | Article body content (rich text) |
| `canvasId` | INT FK | Parent wiki ID |
| `parent` | INT | Parent article ID (tree hierarchy) |
| `status` | VARCHAR(255) | `'published'` or `'draft'` |
| `tags` | TEXT | Comma-separated tags |
| `data` | TEXT | Icon (FontAwesome class) |
| `author` | INT | Author user ID |
| `created` | DATETIME | Creation timestamp |
| `modified` | DATETIME | Last modification |
| `milestoneId` | VARCHAR(255) | Linked ticket/milestone ID |
| `sortindex` | INT | Display ordering |
| `featured` | INT | Featured flag (0/1) |

#### Template Model (in-memory only, no dedicated table)
| Field | Type |
|---|---|
| `title` | string |
| `description` | string |
| `content` | string |
| `category` | string |

### CRUD Operations
| Operation | Method | Source |
|---|---|---|
| Create wiki | `Wiki::createWiki(Wiki $wiki): false\|string` | Services/Wiki.php:104-112 |
| Read wiki | `Wiki::getWiki(int $id): mixed` | Services/Wiki.php:92-99 |
| Update wiki | `Wiki::updateWiki(Wiki $wiki, int $wikiId): bool` | Services/Wiki.php:117-120 |
| List wikis | `Wiki::getAllProjectWikis(int $projectId): array\|false` | Services/Wiki.php:62-79 |
| Delete wiki | `Repo::delWiki(int $id): void` | Repositories/Wiki.php:218-228 |
| Create article | `Wiki::createArticle(Article $article): false\|string` | Services/Wiki.php:127-143 |
| Read article | `Wiki::getArticle(?int $id, ?int $projectId): mixed` | Services/Wiki.php:36-54 |
| Update article | `Wiki::updateArticle(Article $article): bool` | Services/Wiki.php:150-159 |
| Delete article | `Repo::delArticle(int $id): void` | Repositories/Wiki.php:210-216 |
| Activity feed | `Wiki::getArticleActivity(int $articleId, int $limit): array` | Services/Wiki.php:222-244 |

### Key Behaviors
- **Hierarchical**: Articles form a tree via `parent` field
- **Visibility**: Draft articles only visible to their author; published visible to team
- **Audit trail**: Changes to title, status, parent, milestone, tags, content are logged to `zp_audit`
- **Project-scoped**: Each wiki belongs to exactly one project via `projectId`
- **No full-text search**: Filtering limited to status, author, canvasId, parent, tags

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | Authoritative knowledge base; wiki content is source-of-record documentation created by users |
| **Promotable to Durable Memory** | ✅ Yes | Long-lived, structured, user-authored knowledge with hierarchical organization |
| **Indexable for Retrieval** | ✅ Yes (high priority) | Rich text content with titles, tags, hierarchy — ideal for semantic search and RAG |
| **AI-Summary Suitable** | ✅ Yes | Article content is prose-form documentation; hierarchies enable context-aware summarization |

---

## 2. Canvas Boards (Base + 17 Variants)

### Evidence Sources
- `app/Domain/Canvas/Repositories/Canvas.php` — Base repository (all CRUD, 962+ lines)
- `app/Domain/Canvas/Services/Canvas.php` — Service layer (progress, copy, merge)
- `app/Domain/Install/Services/SchemaBuilder.php:160-200` — Table DDL
- 17 variant repositories in `app/Domain/{Variant}canvas/Repositories/`

### Data Structure

**Database Tables**: `zp_canvas` (boards) + `zp_canvas_items` (items)

#### Canvas Item — Full Schema (`zp_canvas_items`)
| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Item identifier |
| `title` | VARCHAR(255) | Item title |
| `description` | MEDIUMTEXT | Primary content field |
| `assumptions` | TEXT | Assumptions / mitigation strategies |
| `data` | MEDIUMTEXT | Supporting data |
| `conclusion` | TEXT | Conclusion / summary |
| `box` | VARCHAR(255) | Canvas section key (e.g., `swot_strengths`) |
| `author` | INT FK | Creator |
| `created` | DATETIME | Creation timestamp |
| `modified` | DATETIME | Last modification |
| `canvasId` | INT FK | Parent canvas board |
| `sortindex` | INT | Display ordering |
| `status` | VARCHAR(255) | Item status (variant-specific) |
| `relates` | VARCHAR(255) | Relates-to category |
| `parent` | INT | Parent item (hierarchy) |
| `featured` | INT | Featured flag |
| `tags` | TEXT | Tags |
| `kpi` | INT | Parent KPI item ID |
| `data1`–`data5` | MEDIUMTEXT | Custom data fields (variant-specific) |
| `startDate` | DATETIME | Tracking start |
| `endDate` | DATETIME | Tracking end |
| `setting` | TEXT | Config (`"linkAndReport"`, `"linkonly"`) |
| `metricType` | VARCHAR(45) | Metric type for KPI tracking |
| `startValue` | DOUBLE(10,2) | KPI baseline |
| `currentValue` | DOUBLE(10,2) | KPI current value |
| `endValue` | DOUBLE(10,2) | KPI target |
| `impact` | INT | Impact score |
| `effort` | INT | Effort score |
| `probability` | INT | Probability score |
| `action` | TEXT | Action items |
| `milestoneId` | VARCHAR(255) | Linked ticket ID |
| `assignedTo` | INT FK | Assigned user |

### All 17 Canvas Variants

| Variant | `CANVAS_NAME` | Boxes | Purpose |
|---|---|---|---|
| **Goalcanvas** | `goal` | 1 (`goal`) | OKR/Goal tracking with KPI metrics |
| **Leancanvas** | `lean` | 12 | Lean Startup business model |
| **Swotcanvas** | `swot` | 4 (`strengths`, `weaknesses`, `opportunities`, `threats`) | SWOT analysis |
| **Valuecanvas** | `value` | 4 | Value proposition mapping |
| **Riskscanvas** | `risks` | 4 (2×2 impact/probability matrix) | Risk assessment |
| **Retroscanvas** | `retros` | 3 (`well`, `notwell`, `startdoing`) | Retrospectives |
| **Cpcanvas** | `cp` | 12 | Company profile/persona |
| **Sbcanvas** | `sb` | 11 | Strategy brief |
| **Smcanvas** | `sm` | 7 | Strategy map (7 questions) |
| **Sqcanvas** | `sq` | 5 | Scenario questions |
| **Dbmcanvas** | `dbm` | 15 | Dolabella business model |
| **Lbmcanvas** | `lbm` | 4 | Lean business model |
| **Eacanvas** | `ea` | 6 | PESTLE environmental analysis |
| **Emcanvas** | `em` | 9 | Full empathy map |
| **Minempathycanvas** | `minempathy` | 5 | Mini empathy map |
| **Obmcanvas** | `obm` | 9 | Objective business model |
| **Insightscanvas** | `insights` | 5 | Research insights (ethnographic) |

Each variant extends the base by overriding `CANVAS_NAME`, `$canvasTypes` (box definitions), `$statusLabels`, `$relatesLabels`, and `$dataLabels`.

**Source**: Each variant's repository at `app/Domain/{Variant}canvas/Repositories/{Variant}canvas.php`

### Customization Pattern
```php
// Example: app/Domain/Swotcanvas/Repositories/Swotcanvas.php
protected const CANVAS_NAME = 'swot';
protected array $canvasTypes = [
    'swot_strengths'     => ['icon' => 'fa-check',  'title' => 'box.swot.strengths'],
    'swot_weaknesses'    => ['icon' => 'fa-xmark',  'title' => 'box.swot.weaknesses'],
    'swot_opportunities' => ['icon' => 'fa-star',   'title' => 'box.swot.opportunities'],
    'swot_threats'       => ['icon' => 'fa-bolt',   'title' => 'box.swot.threats'],
];
```

### KPI/Metric Tracking (Goalcanvas-specific)
The canvas system has built-in KPI tracking via `metricType`, `startValue`, `currentValue`, `endValue`. Used primarily by Goalcanvas but available to all variants.

**Key methods**:
- `Canvas::getCanvasItemsByKPI($id)` — Repositories/Canvas.php:435-477
- `Canvas::getAllAvailableKPIs($projectId)` — Repositories/Canvas.php:541-589
- `Goalcanvas::createGoal(array $values)` — Goalcanvas/Repositories/Goalcanvas.php:228-263

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | User-created strategic planning artifacts; each canvas type captures structured decisions |
| **Promotable to Durable Memory** | ✅ Yes | Strategic decisions, goals, risk assessments are long-lived and high-value |
| **Indexable for Retrieval** | ✅ Yes | Structured box types enable faceted search; title/description fields enable text search |
| **AI-Summary Suitable** | ✅ Yes | Each canvas type has well-defined semantics; AI can summarize a SWOT, retro, or goal board meaningfully |

---

## 3. Retrospectives (Retroscanvas)

### Evidence Sources
- `app/Domain/Retroscanvas/Repositories/Retroscanvas.php` — Variant config
- `app/Domain/Retroscanvas/Controllers/` — 7 controllers (all extend Canvas base)
- `app/Domain/Retroscanvas/Templates/showCanvas.tpl.php` — Layout template

### Data Structure

Retroscanvas extends Canvas with `CANVAS_NAME = 'retros'`.

#### Three Boxes (Categories)
| Box Key | Label | Icon | Purpose |
|---|---|---|---|
| `well` | Continue / What went well | `fa-circle-check` | Positive observations |
| `notwell` | Stop Doing / What didn't work | `fa-circle-xmark` | Negative observations |
| `startdoing` | Start Doing | `fa-circle-plus` | New ideas to try |

**Source**: `Retroscanvas/Repositories/Retroscanvas.php:31-35`

#### Data Labels
| # | Label | Field | Active |
|---|---|---|---|
| 1 | Description | `conclusion` | ✅ |
| 2 | Data | `data` | ❌ |
| 3 | Assumptions | `assumptions` | ❌ |

**Source**: `Retroscanvas/Repositories/Retroscanvas.php:42-46`

**Status labels**: Empty array — retro items have no status workflow.

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Contextual Reference** | Retrospective observations inform future process but don't drive system behavior |
| **Promotable to Durable Memory** | ⚠️ Selective | Individual items are ephemeral; aggregated retro themes across sprints are valuable |
| **Indexable for Retrieval** | ⚠️ Low priority | Useful for pattern detection over time but individual items lack standalone value |
| **AI-Summary Suitable** | ✅ Yes | Three-column retro format is ideal for AI summarization (themes, sentiment, action items) |

---

## 4. Idea Boards

### Evidence Sources
- `app/Domain/Ideas/Services/Ideas.php` — Service (polling, date formatting)
- `app/Domain/Ideas/Repositories/Ideas.php` — Full CRUD + access control
- `app/Domain/Ideas/Controllers/` — 6 controllers including AdvancedBoards (kanban)

### Data Structure

Ideas use the Canvas infrastructure (`zp_canvas` + `zp_canvas_items`) but with a custom repository — not a direct Canvas variant extension.

#### Idea Statuses (Box Types)
| Status Key | Label | CSS Class | Stage |
|---|---|---|---|
| `idea` | Ideation | `label-info` | Discovery |
| `research` | Discovery | `label-warning` | Exploration |
| `prototype` | Delivering | `label-warning` | Build |
| `validation` | In Review | `label-warning` | Validation |
| `implemented` | Accepted | `label-success` | Complete |
| `deferred` | Deferred | `label-default` | Parked |

**Source**: `Ideas/Repositories/Ideas.php:19-28`

#### Fields Retrieved Per Idea
`id`, `description`, `assumptions`, `data`, `conclusion`, `box` (status), `author`, `created`, `modified`, `canvasId`, `sortindex`, `status`, `milestoneId`, `tags`, `commentCount` (computed), plus milestone denormalization (`headline`, `editTo`).

**Source**: `Ideas/Repositories/Ideas.php:211-257`

### CRUD Operations
| Operation | Method | Source |
|---|---|---|
| Create board | `addCanvas()` | Repositories/Ideas.php:143-154 |
| Create idea | `addCanvasItem()` | Repositories/Ideas.php:292-309 |
| Edit idea | `editCanvasItem()` | Repositories/Ideas.php:163-178 |
| Patch idea | `patchCanvasItem()` | Repositories/Ideas.php:180-196 |
| Bulk status update | `bulkUpdateIdeaStatus()` | Repositories/Ideas.php:358-381 |
| Update sorting | `updateIdeaSorting()` | Repositories/Ideas.php:198-209 |
| Delete idea | `delCanvasItem()` | Repositories/Ideas.php:311-317 |
| Get all (access-controlled) | `getAllIdeas()` | Repositories/Ideas.php:383-438 |

### Key Behaviors
- **Kanban view**: `AdvancedBoards.php` controller provides status-column kanban with drag-drop
- **Polling API**: `pollForNewIdeas()` and `pollForUpdatedIdeas()` for change detection (not voting)
- **No voting/rating system**: Despite the name "polling", these are API change-detection methods
- **Access control**: Respects project visibility (`psettings`), client assignment, and role

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | Ideas capture user-submitted proposals with lifecycle status tracking |
| **Promotable to Durable Memory** | ✅ Yes | Ideas represent captured innovation with status progression |
| **Indexable for Retrieval** | ✅ Yes | Structured statuses + text content enable faceted and full-text search |
| **AI-Summary Suitable** | ✅ Yes | Idea boards with status distributions and content are summarizable |

---

## 5. Risk Boards (Riskscanvas)

### Evidence Sources
- `app/Domain/Riskscanvas/Repositories/Riskscanvas.php` — Variant config
- `app/Domain/Riskscanvas/Controllers/` — 7 controllers (all extend Canvas base)
- `app/Domain/Riskscanvas/Templates/showCanvas.tpl.php:21-47` — 2×2 matrix layout

### Data Structure

Riskscanvas extends Canvas with `CANVAS_NAME = 'risks'`.

#### Four Quadrants (2×2 Impact × Probability Matrix)
| Box Key | Impact | Probability | Priority |
|---|---|---|---|
| `risks_imp_low_pro_low` | Low | Low | Monitor |
| `risks_imp_low_pro_high` | Low | High | Accept |
| `risks_imp_high_pro_low` | High | Low | Watch |
| `risks_imp_high_pro_high` | High | High | **Critical** |

**Source**: `Riskscanvas/Repositories/Riskscanvas.php:31-36`

#### Risk-Specific Data Labels
| # | Label | Field | Active |
|---|---|---|---|
| 1 | Description | `conclusion` | ✅ |
| 2 | Data | `data` | ✅ |
| 3 | Mitigation | `assumptions` | ✅ |

**Source**: `Riskscanvas/Repositories/Riskscanvas.php:43-47`

#### Risk Scoring Fields (from base Canvas)
| Field | Type | Purpose |
|---|---|---|
| `impact` | INT | Risk severity level |
| `effort` | INT | Mitigation effort |
| `probability` | INT | Likelihood of occurrence |

**Scoring approach**: Matrix-based quadrant assignment via `box` field, not a calculated score.

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | Risk items represent identified project risks with structured assessment |
| **Promotable to Durable Memory** | ✅ Yes | Risk registers are long-lived artifacts tracked throughout project lifecycle |
| **Indexable for Retrieval** | ✅ Yes | Matrix position + text fields enable structured queries (e.g., "all high-impact risks") |
| **AI-Summary Suitable** | ✅ Yes | 2×2 matrix with description/mitigation pairs are ideal for risk summary generation |

---

## 6. Comments / Discussions

### Evidence Sources
- `app/Domain/Comments/Services/Comments.php` — Service (CRUD + notifications)
- `app/Domain/Comments/Repositories/Comments.php` — Data access
- `app/Domain/Comments/Templates/submodules/generalComment.sub.php` — UI template

### Data Structure

**Database Table**: `zp_comment`

| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Comment identifier |
| `module` | VARCHAR(200) | Entity type (`'ticket'`, `'project'`, etc.) — **polymorphic discriminator** |
| `moduleId` | INT | Entity ID — **polymorphic FK** |
| `userId` | INT FK | Comment author |
| `text` | TEXT | Comment content (rich text) |
| `date` | DATETIME | Comment timestamp |
| `commentParent` | INT | Parent comment ID (0 or NULL = root) — **enables threading** |
| `status` | VARCHAR(50) | Optional status (no predefined enum) |

**Indexes**:
- `(moduleId, module, commentParent)` — Primary lookup
- `(userId, module)` — User's comments by type

**Source**: `app/Domain/Install/Repositories/Install.php` (CREATE TABLE)

### CRUD Operations
| Operation | Method | Source |
|---|---|---|
| Create | `Comments::addComment($values, $module, $entityId, $entity): bool` | Services/Comments.php:45-106 |
| Read | `Comments::getComments($module, $entityId, $order, $parent): array\|false` | Services/Comments.php:35-38 |
| Read replies | `Repo::getReplies($id): array` | Repositories/Comments.php:67-87 |
| Edit | `Comments::editComment($values, $id): bool` | Services/Comments.php:113-116 |
| Delete | `Comments::deleteComment($commentId): bool` | Services/Comments.php:121-125 |
| Count | `Repo::countComments($module, $moduleId): int` | Repositories/Comments.php:52-65 |
| Poll | `Comments::pollComments($projectId, $moduleId): array\|false` | Services/Comments.php:134-148 |
| All account comments | `Repo::getAllAccountComments(): array` | Repositories/Comments.php:137-201 |

### Key Behaviors
- **Polymorphic**: Same table serves tickets, projects, canvas items, and any module
- **Threaded**: `commentParent` enables nested reply chains
- **Notification trigger**: `addComment()` fires project user notifications
- **Polling support**: `pollComments()` returns ISO 8601 dates for real-time detection

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Contextual Reference** | Comments enrich entities but are not source-of-record data themselves |
| **Promotable to Durable Memory** | ⚠️ Selective | Decision-capturing comments are valuable; casual chatter is not |
| **Indexable for Retrieval** | ✅ Yes | Polymorphic module/moduleId enables entity-scoped retrieval; text is searchable |
| **AI-Summary Suitable** | ✅ Yes | Thread summarization, sentiment analysis, and decision extraction are strong use cases |

---

## 7. Project Metadata

### Evidence Sources
- `app/Domain/Projects/Models/Project.php` — Model (16+ properties)
- `app/Domain/Projects/Repositories/Projects.php` — Repository (1000+ lines)
- `app/Domain/Projects/Services/Projects.php` — Service layer

### Data Structure

**Database Table**: `zp_projects`

| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Project identifier |
| `name` | VARCHAR(100) | Project name |
| `clientId` | INT FK | Client/organization (`zp_clients`) |
| `details` | TEXT | Project description/background |
| `state` | INT(2) | `0` = OPEN, `1` = CLOSED, `NULL` = OPEN |
| `hourBudget` | VARCHAR(255) | Hour budget (string for flexibility) |
| `dollarBudget` | INT | Currency budget |
| `active` | INT | Activity flag |
| `menuType` | MEDIUMTEXT | Menu layout configuration |
| `psettings` | MEDIUMTEXT | Visibility: `'all'` / `'clients'` / `''` (team only) |
| `parent` | INT FK | Parent project (hierarchy) |
| `type` | VARCHAR(45) | `'project'` / `'strategy'` / `'program'` |
| `start` | DATETIME | Project start date |
| `end` | DATETIME | Project end date |
| `created` | DATETIME | Creation timestamp |
| `modified` | DATETIME | Last modification |
| `avatar` | MEDIUMTEXT | Project avatar (SVG/image) |
| `cover` | MEDIUMTEXT | Project cover image |
| `sortIndex` | INT | Display ordering |

**Related Table**: `zp_relationuserproject`
| Field | Type | Purpose |
|---|---|---|
| `userId` | INT FK | Assigned user |
| `projectId` | INT FK | Project |
| `projectRole` | VARCHAR | User's role in project |
| `wage` | DECIMAL | User's wage rate for project |

**Source**: `Projects/Repositories/Projects.php:699-740` (addProject), `Install/Repositories/Install.php` (DDL)

### Key Behaviors
- **Hierarchical**: Projects can have parent projects (strategy → program → project)
- **Access control**: `psettings` controls visibility (all users / client users / assigned only)
- **Client relationship**: `clientId` FK to `zp_clients` for organizational grouping
- **Favorites**: Via `zp_reactions` table (isFavorite computed at query time)
- **Progress tracking**: `getProjectProgress()` computes % complete from ticket status

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | Projects are the primary organizational unit; all other surfaces are project-scoped |
| **Promotable to Durable Memory** | ✅ Yes | Project metadata is structural truth that defines system organization |
| **Indexable for Retrieval** | ✅ Yes | Name, type, state, client, dates — all highly queryable |
| **AI-Summary Suitable** | ✅ Yes | Project overviews combining metadata, progress, team, and timeline are valuable |

---

## 8. Dashboards

### Evidence Sources
- `app/Domain/Dashboard/Controllers/Home.php` — Home/widget dashboard
- `app/Domain/Dashboard/Controllers/Show.php` — Project dashboard
- `app/Domain/Widgets/Services/Widgets.php` — Widget registration and grid management
- `app/Domain/Widgets/Models/Widget.php` — Widget model
- `app/Domain/Dashboard/Templates/home.blade.php` — Widget grid template

### Data Structure

Dashboards are **view-only aggregation surfaces** — they do not store data.

#### Home Dashboard (Widget Grid)
User-configurable grid of widgets. Layout persisted as user setting `usersettings.{userId}.dashboardGrid`.

**Default Widgets**:
| Widget ID | Name | URL | Grid Size | Always Visible |
|---|---|---|---|---|
| `welcome` | Welcome | `/widgets/welcome/get` | 12×7 | ✅ (fixed) |
| `todos` | My ToDos | `/widgets/myToDos/get` | 8×30 | ❌ |
| `calendar` | Calendar | `/widgets/calendar/get` | 4×30 | ❌ |
| `myprojects` | My Projects | `/widgets/myProjects/get` | 8×22 | ❌ |

**Source**: `Widgets/Services/Widgets.php` (widget definitions)

**Widget Model** (`Widgets/Models/Widget.php`):
```
id, name, widgetUrl, description, widgetTrigger, gridMinWidth, gridMinHeight,
gridX, gridY, gridHeight, gridWidth, noTitle, fixed, widgetLoadingIndicator,
widgetBackground, alwaysVisible
```

#### Project Dashboard (Show)
Fixed layout aggregating project-specific data:

| Data Source | Method | Purpose |
|---|---|---|
| Project info | `$projectService->getProject()` | Metadata, details, state |
| Progress | `$projectService->getProjectProgress()` | % complete, dates |
| Setup checklist | `$projectService->getProjectSetupChecklist()` | Onboarding status |
| Team members | `$projectService->getUsersAssignedToProject()` | Team list |
| Milestones | `$ticketService->getAllMilestones()` | Project milestones |
| Comments | `$comments->getComments('project', ...)` | Project-level discussion |
| Recent tickets | `$ticketService->getLastTickets()` | Active tickets |
| Labels | Various `*Labels()` methods | Effort, priority, type, status |
| Reactions | `$reactionsService->getUserReactions()` | Favorite status |

**Source**: `Dashboard/Controllers/Show.php:70-146`

### Key Behaviors
- **Widget grid**: Uses GridStack.js library; HTMX lazy-loads widget content (`hx-trigger="revealed"`)
- **Extensible**: `availableWidgets` filter allows plugins to register custom widgets
- **Dashboard redirect**: `dashboardRedirect` filter can route to custom dashboards by project type
- **No persistent data**: Dashboards read from other surfaces; only widget layout is stored

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Reporting Projection** | Dashboards are read-only views that aggregate data from operational truth sources |
| **Promotable to Durable Memory** | ❌ No | Dashboard content is derived; the underlying data sources are the durable records |
| **Indexable for Retrieval** | ❌ No | No unique content to index; queries should target source surfaces directly |
| **AI-Summary Suitable** | ✅ Yes | Dashboard views are natural summary targets — AI can generate project status summaries from the same underlying data |

---

## 9. Reports

### Evidence Sources
- `app/Domain/Reports/Services/Reports.php` — Report generation + cron ingestion
- `app/Domain/Reports/Repositories/Reports.php` — SQL queries + stats persistence
- `app/Domain/Install/Repositories/Install.php` — `zp_stats` DDL

### Data Structure

**Database Table**: `zp_stats` — Daily snapshot of project/sprint metrics

| Field | Type | Purpose |
|---|---|---|
| `sprintId` | INT | Sprint ID (0 = backlog, >0 = sprint) |
| `projectId` | INT FK | Project |
| `date` | DATETIME | Snapshot date |
| `sum_todos` | INT | Total ticket count |
| `sum_open_todos` | INT | Open/New tickets |
| `sum_progres_todos` | INT | In-progress tickets |
| `sum_closed_todos` | INT | Done tickets |
| `sum_planned_hours` | FLOAT | Total planned hours |
| `sum_estremaining_hours` | FLOAT | Remaining hours estimate |
| `sum_logged_hours` | FLOAT | Hours logged via timesheets |
| `sum_points` | INT | Total story points |
| `sum_points_open` | INT | Story points open |
| `sum_points_progress` | INT | Story points in progress |
| `sum_points_done` | INT | Story points done |
| `sum_todos_xs/s/m/l/xl/xxl/none` | INT | Count by story point size (XS=1, S=2, M=3, L=5, XL=8, XXL=13) |
| `tickets` | TEXT | Comma-separated ticket IDs (snapshot) |
| `daily_avg_hours_booked_todo` | FLOAT | Avg hours booked per ticket |
| `daily_avg_hours_booked_point` | FLOAT | Avg hours booked per story point |
| `daily_avg_hours_planned_todo` | FLOAT | Avg planned hours per ticket |
| `daily_avg_hours_planned_point` | FLOAT | Avg planned hours per point |
| `daily_avg_hours_remaining_point` | FLOAT | Avg remaining hours per point |
| `daily_avg_hours_remaining_todo` | FLOAT | Avg remaining hours per ticket |
| `sum_teammembers` | INT | Count of assigned team members |

**Source**: `Repositories/Reports.php:169-204` (insert method)

### Report Generation Methods
| Method | Source | Purpose |
|---|---|---|
| `runTicketReport($projectId, $sprintId)` | Repositories/Reports.php:33-147 | Core calculation engine: queries tickets + timesheets |
| `addReport($report)` | Repositories/Reports.php:169-204 | Persist snapshot to `zp_stats` |
| `getSprintReport($sprint)` | Repositories/Reports.php:209-226 | Retrieve all stats for a sprint |
| `getBacklogReport($project)` | Repositories/Reports.php:228-247 | Retrieve 95-day backlog history |
| `getFullReport($projectId)` | Services/Reports.php:146-149 | 120-day aggregated backlog history |
| `getRealtimeReport($projectId, $sprintId)` | Services/Reports.php:156-159 | Real-time stats without persistence |
| `getProjectStatusReport()` | Services/Reports.php:444-459 | Count projects by health (green/yellow/red/none) |
| `generateTicketReactionsReport()` | Services/Reports.php:461-484 | Sentiment analysis from emoji reactions |

### Daily Ingestion Cron
- **Entry**: `Services/Reports.php:133-141` — `cronDailyIngestion()` iterates all projects
- **Cache**: 4-hour TTL on `'dailyReports-{projectId}'` key prevents duplicate runs
- **Logic**: Checks if entries exist for yesterday; if not, runs `runTicketReport()` for current sprint + backlog
- **Source data**: `zp_tickets` (status, points, hours) + `zp_timesheets` (logged hours)

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Reporting Projection** | Derived daily snapshots computed from ticket and timesheet operational truth |
| **Promotable to Durable Memory** | ✅ Yes (as time series) | Daily snapshots form historical trend data that cannot be reconstructed once tickets change |
| **Indexable for Retrieval** | ⚠️ Limited | Time-series data is best queried via date range + project/sprint, not full-text search |
| **AI-Summary Suitable** | ✅ Yes | Trend data is ideal for burndown narratives, velocity reports, and progress summaries |

---

## 10. Timesheets

### Evidence Sources
- `app/Domain/Timesheets/Services/Timesheets.php` — Service layer (log, export, weekly)
- `app/Domain/Timesheets/Repositories/Timesheets.php` — Data access (700+ lines)
- `app/Domain/Install/Repositories/Install.php` — Table DDL

### Data Structure

**Database Table**: `zp_timesheets`

| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Entry identifier |
| `userId` | INT FK | User who logged time |
| `ticketId` | INT FK | Associated ticket |
| `workDate` | DATETIME | When work was performed (UTC) |
| `hours` | FLOAT | Hours logged |
| `description` | TEXT | Work description |
| `kind` | VARCHAR(175) | Work category (see below) |
| `invoicedEmpl` | INT (0/1) | Invoiced to employee flag |
| `invoicedComp` | INT (0/1) | Invoiced to company/client flag |
| `invoicedEmplDate` | DATETIME | When invoiced to employee |
| `invoicedCompDate` | DATETIME | When invoiced to company |
| `rate` | VARCHAR(255) | Hourly rate at time of entry |
| `paid` | INT (0/1) | Payment processed flag |
| `paidDate` | DATETIME | When paid |
| `modified` | DATETIME | Last modification |

**Unique Constraint**: `(userId, ticketId, workDate, kind)` — prevents duplicate entries

**Source**: `Repositories/Timesheets.php:48-82`

#### Kind Categories
| Key | Label | Purpose |
|---|---|---|
| `GENERAL_BILLABLE` | General Billable | Default billable work |
| `GENERAL_NOT_BILLABLE` | General Not Billable | Non-billable work |
| `PROJECTMANAGEMENT` | Project Management | PM activities |
| `DEVELOPMENT` | Development | Development work |
| `BUGFIXING_NOT_BILLABLE` | Bugfixing Not Billable | Bug fixes (non-billable) |
| `TESTING` | Testing | QA/Testing work |

**Source**: `Services/Timesheets.php:20-27`

### Punch Clock (`zp_punch_clock`)

| Field | Type | Purpose |
|---|---|---|
| `id` | INT | Ticket ID being clocked |
| `userId` | INT | User clocked in |
| `punchIn` | INT | Unix timestamp of clock-in |
| `minutes` | INT | Unused |
| `hours` | INT | Unused |

**PK**: `(id, userId)` — one active clock per user per ticket

**Operations**:
| Method | Source | Logic |
|---|---|---|
| `isClocked($userId)` | Repositories:540-577 | Check if user has active timer |
| `punchIn($ticketId)` | Repositories:650-671 | Insert with current Unix timestamp |
| `punchOut($ticketId)` | Repositories:678-731 | Calculate hours, delete clock, insert timesheet |

### Key Behaviors
- **Invoicing workflow**: Three-stage tracking (invoiced-employee → invoiced-company → paid)
- **Rate capture**: Hourly rate stored per entry for historical accuracy
- **Weekly grouping**: `Services/Timesheets.php:328-459` builds 7-day matrix grouped by ticket+kind
- **Relationships**: `zp_timesheets` → `zp_tickets` → `zp_projects` → `zp_clients` (via JOINs)
- **Timezone-aware**: Punch clock converts to user's timezone on clock-out

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Operational Truth** | Time entries are source-of-record for billing, payroll, and project cost tracking |
| **Promotable to Durable Memory** | ✅ Yes | Financial records with invoicing/payment status are audit-critical |
| **Indexable for Retrieval** | ✅ Yes | Queryable by user, ticket, project, client, date range, kind, invoice status |
| **AI-Summary Suitable** | ✅ Yes | Weekly/monthly time summaries, utilization reports, billing summaries are strong use cases |

---

## 11. Notifications / Activity Feed

### Evidence Sources
- `app/Domain/Notifications/Services/Notifications.php` — Notification processing + mentions
- `app/Domain/Notifications/Models/Notification.php` — Model + category definitions
- `app/Domain/Notifications/Repositories/Notifications.php` — Data access
- `app/Domain/Notifications/Services/News.php` — External RSS news feed
- `app/Domain/Audit/Repositories/Audit.php` — Audit log persistence

### Notification Data Structure

**Database Table**: `zp_notifications`

| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Notification identifier |
| `userId` | INT FK | Recipient user |
| `read` | INT | Read status (`0` = unread, `1` = read) |
| `type` | VARCHAR(45) | Notification type (`'mention'`, `'ainotification'`, etc.) |
| `module` | VARCHAR(45) | Source module (`'tickets'`, `'comments'`, `'goalcanvas'`, etc.) |
| `moduleId` | INT | Source entity ID |
| `datetime` | DATETIME | When notification was created |
| `url` | VARCHAR(255) | Deep link to source entity |
| `authorId` | INT FK | User who triggered the notification |
| `message` | TEXT | Human-readable message |

**Indexes**:
- `(userId, datetime)` — Fetch recent for user
- `(userId, read)` — Filter by read status

**Source**: `Repositories/Notifications.php:25-42`

### Notification Categories
| Category | Modules | Description |
|---|---|---|
| `tasks` | `['tickets']` | Task/ticket notifications |
| `comments` | `['comments']` | Comment notifications |
| `goals` | `['goalcanvas']` | Goal canvas notifications |
| `ideas` | `['ideas']` | Idea board notifications |
| `projects` | `['projects']` | Project-level notifications |
| `boards` | `[]` (catch-all for `*canvas`) | Any canvas board notifications |

**Relevance Levels** (per-project):
- `RELEVANCE_ALL` — All activity
- `RELEVANCE_MY_WORK` — Only assigned items
- `RELEVANCE_MUTED` — Muted

**Source**: `Models/Notification.php:40-65`

### Mention Processing
`Services/Notifications.php:86-147` — Parses HTML for `<a data-tagged-user-id="X">` tags, creates mention notifications, prevents duplicates, sends email.

### Audit Log

**Database Table**: `zp_audit`

| Field | Type | Purpose |
|---|---|---|
| `id` | INT PK | Audit event identifier |
| `userId` | INT FK | Acting user |
| `projectId` | INT FK | Project context |
| `action` | VARCHAR(45) | Action verb (e.g., `'ticket.create'`, `'status_changed'`) |
| `entity` | VARCHAR(45) | Entity type (e.g., `'tickets'`, `'article'`) |
| `entityId` | INT | Modified entity ID |
| `values` | TEXT | JSON-encoded changed field values |
| `date` | DATETIME | When action occurred |

**Indexes**:
- `(projectId)` — Project-scoped queries
- `(projectId, action)` — Action filtering
- `(projectId, entity, entityId)` — Entity history

**Source**: `Audit/Repositories/Audit.php:29-105`

**Audit Methods**:
| Method | Source | Purpose |
|---|---|---|
| `storeEvent()` | Audit/Repositories/Audit.php:29-42 | Record audit entry |
| `getLastEvent($action)` | Audit/Repositories/Audit.php:47-60 | Most recent event of type |
| `getEventsForEntity($entity, $entityId, $limit)` | Audit/Repositories/Audit.php:72-96 | Entity change history |
| `pruneEvents($ageDays)` | Audit/Repositories/Audit.php:98-105 | Delete old events |

### News Service (External)
`Services/News.php` — Fetches RSS from `https://leantime.io/.../feed/`. Per-user tracking via `usersettings.{userId}.lastNewsGuid`. Disabled via `LEAN_NEWS_ENABLED=false`.

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Notifications — Classification** | **Noise** (individually) / **Contextual Reference** (aggregated) | Individual notifications are ephemeral delivery records; patterns reveal engagement |
| **Audit Log — Classification** | **Operational Truth** | Immutable record of system state changes; critical for compliance and debugging |
| **Promotable to Durable Memory** | ✅ Audit: Yes / ⚠️ Notifications: Selective | Audit log is permanent record; notifications have short useful lifetime |
| **Indexable for Retrieval** | ✅ Audit: Yes / ❌ Notifications: No | Audit supports entity-scoped history queries; notifications are user-delivery records |
| **AI-Summary Suitable** | ✅ Yes (both) | Audit logs → change summaries; Notifications → activity digests |

---

## 12. Export Features

### Evidence Sources
- `app/Domain/Canvas/Controllers/Export.php` — Base XML export (163 lines)
- `app/Domain/*/Controllers/Export.php` — 17 canvas variant export controllers
- `app/Domain/Calendar/Controllers/Ical.php` — iCal export
- `app/Domain/Calendar/Controllers/Export.php` — iCal URL management
- `app/Domain/CsvImport/` — CSV import only (no export)

### Supported Formats

#### 1. XML Export (Canvas Boards)
**Controller**: `app/Domain/Canvas/Controllers/Export.php`
- **Format**: `application/xml`
- **Filename**: `{canvasname}canvas-{canvasId}.xml`
- **Content**: Canvas metadata + all items with timestamps, author info, description, status, assumptions, data, conclusion
- **Coverage**: All 17 canvas variants via inheritance

**All 17 variant export controllers** at `app/Domain/{Variant}canvas/Controllers/Export.php` — each is minimal (3-12 lines) overriding only `CANVAS_NAME`.

#### 2. iCal Export (Calendar)
**Controller**: `app/Domain/Calendar/Controllers/Ical.php`
- **Format**: `text/calendar; charset=utf-8` (.ics)
- **Filename**: `leantime-calendar.ics`
- **Route**: `/calendar/ical/{icalHash}_{userHash}`
- **Content**: Ticket due dates, start dates, descriptions, URLs
- **Features**: 30-min alert for due items, 5-min alert for start times
- **Library**: Spatie IcalendarGenerator
- **Auth**: Hash-based (no session required) — shareable URL for external calendar apps

**iCal URL management**: `Calendar/Controllers/Export.php` — generate/regenerate/remove iCal feed URLs. Hash stored in `usersettings.{userId}.icalSecret`.

**Source**: `Calendar/Services/Calendar.php:276-328` (getIcalByHash), `Calendar/Services/Calendar.php:492-507` (getICalUrl)

#### 3. CSV Import (Import Only)
**Controller**: `app/Domain/CsvImport/Controllers/Upload.php`
- **Direction**: Import only, not export
- **Library**: League\Csv\Reader
- **Steps**: connect → entity → fields → parse → import
- **No CSV export capability found in the codebase**

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Reporting Projection** | Exports are serialized views of operational truth for external consumption |
| **Promotable to Durable Memory** | ❌ No | Exports are ephemeral artifacts regenerated on demand from source data |
| **Indexable for Retrieval** | ❌ No | Generated outputs, not stored data — index the source surfaces instead |
| **AI-Summary Suitable** | N/A | Export format generation is a transformation, not a summarization target |

---

## 13. Strategy Boards

### Evidence Sources
- `app/Domain/Strategy/Controllers/ShowBoards.php` — Main controller (157 lines)
- `app/Domain/Strategy/Templates/showBoards.tpl.php` — Template (183 lines)
- `app/Domain/Canvas/Services/Canvas.php:198-277` — Progress + last-updated methods

### Data Structure

The Strategy module is a **navigation/aggregation hub** — it stores no data of its own.

#### What It Aggregates
**Source**: `Strategy/Controllers/ShowBoards.php:126-153`

| Data | Method | Purpose |
|---|---|---|
| Recently updated canvases | `$canvasService->getLastUpdatedCanvas()` | Show recent strategic work |
| Board progress | `$canvasService->getBoardProgress()` | % completion per canvas type |
| Board metadata | Configured in controller | Module name, icon, description, visibility |

#### Available Strategic Boards (15 active + 5 hidden)

**Active boards** (visible in Strategy hub):
Valuecanvas, Swotcanvas, Obmcanvas, Leancanvas, Minempathycanvas, Sbcanvas, Riskscanvas, Eacanvas, Insightscanvas, Retroscanvas, Goalcanvas, Cpcanvas + comprehensive views

**Hidden boards** (`'visible' => '0'`):
Lbmcanvas, Dbmcanvas, Sqcanvas, Smcanvas, Emcanvas

**Source**: `Strategy/Controllers/ShowBoards.php` (board configuration array)

### Template Features
- **"Jump right back in"** section: Recently updated canvases in 3-column grid with progress bars
- **"Templates"** section: Accordion of all available board types with descriptions
- **Empty state**: CTA to start with Value Canvas
- **Access**: Editor role and above for template section

**Source**: `Strategy/Templates/showBoards.tpl.php:20-158`

### Key Behaviors
- **Hub pattern**: Strategy board is a read-only aggregator of all canvas data
- **Cross-navigation**: Links to all 17 canvas types with last-updated info and progress
- **Goalcanvas integration**: Deleted goal canvases redirect back to Strategy (`Goalcanvas/Controllers/DelCanvas.php:55`)
- **Plugin-extensible**: Board list can be modified via filter hooks

### Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Classification** | **Reporting Projection** | Pure aggregation view over canvas operational truth — no unique data |
| **Promotable to Durable Memory** | ❌ No | Aggregation view; the canvases themselves are the durable records |
| **Indexable for Retrieval** | ❌ No | No unique content to index; index individual canvas types instead |
| **AI-Summary Suitable** | ✅ Yes | Strategic overview summarization across all canvas types is a strong use case |

---

## Summary Matrix

| # | Surface | Classification | Durable Memory | Indexable | AI-Summary | Primary Table(s) |
|---|---|---|---|---|---|---|
| 1 | Wiki / Knowledge Base | **Operational Truth** | ✅ | ✅ | ✅ | `zp_canvas` + `zp_canvas_items` |
| 2 | Canvas Boards (17 types) | **Operational Truth** | ✅ | ✅ | ✅ | `zp_canvas` + `zp_canvas_items` |
| 3 | Retrospectives | **Contextual Reference** | ⚠️ Selective | ⚠️ Low | ✅ | `zp_canvas_items` (box=well/notwell/startdoing) |
| 4 | Idea Boards | **Operational Truth** | ✅ | ✅ | ✅ | `zp_canvas` + `zp_canvas_items` |
| 5 | Risk Boards | **Operational Truth** | ✅ | ✅ | ✅ | `zp_canvas_items` (impact/probability matrix) |
| 6 | Comments | **Contextual Reference** | ⚠️ Selective | ✅ | ✅ | `zp_comment` |
| 7 | Project Metadata | **Operational Truth** | ✅ | ✅ | ✅ | `zp_projects` + `zp_relationuserproject` |
| 8 | Dashboards | **Reporting Projection** | ❌ | ❌ | ✅ | None (aggregation views) |
| 9 | Reports (zp_stats) | **Reporting Projection** | ✅ (time series) | ⚠️ Limited | ✅ | `zp_stats` |
| 10 | Timesheets | **Operational Truth** | ✅ | ✅ | ✅ | `zp_timesheets` + `zp_punch_clock` |
| 11a | Notifications | **Noise** (individual) | ⚠️ Selective | ❌ | ✅ | `zp_notifications` |
| 11b | Audit Log | **Operational Truth** | ✅ | ✅ | ✅ | `zp_audit` |
| 12 | Exports | **Reporting Projection** | ❌ | ❌ | N/A | None (generated on demand) |
| 13 | Strategy Boards | **Reporting Projection** | ❌ | ❌ | ✅ | None (aggregation hub) |

---

## Architectural Notes

### Shared Infrastructure Pattern
Wiki, all 17 Canvas variants, and Ideas all share the same two database tables (`zp_canvas` + `zp_canvas_items`), differentiated by the `type` column on `zp_canvas` and the `box` column on `zp_canvas_items`. This means:
- A single indexing pipeline could cover all strategic/planning surfaces
- Canvas item fields like `impact`, `effort`, `probability`, `metricType`, `startValue`, `currentValue`, `endValue` are available to ALL variants but only semantically used by specific ones (Risks, Goals)
- The `data1`–`data5` MEDIUMTEXT fields provide variant-specific extensibility

### Polymorphic Comment System
Comments attach to any entity via `module` + `moduleId`. Known module values: `'ticket'`, `'project'`, and canvas item types. This means comment retrieval must always be scoped to a specific module+entity pair.

### Audit Trail Coverage
Not all surfaces have equal audit coverage. Wiki articles have granular field-change auditing (title, status, parent, milestone, tags, content edits). Canvas items and tickets have event-based auditing. Comments and timesheets have minimal audit coverage.

### Report Data Retention
`zp_stats` snapshots are daily but can be pruned. The `getBacklogReport()` method limits to 95 days. The `getFullReport()` method limits to 120 days. For long-term trend analysis, historical stats beyond these windows are lost unless separately archived.
