# Leantime Extension Surfaces

> Generated from source analysis of leantime/leantime v3.6.2
> Companion to `CALLABLE_SURFACE_MANIFEST.json`

---

## 1. Plugin Seams

Plugins are Leantime's primary extension mechanism. They live in `app/Plugins/` and follow the same domain module structure as core domains.

### Registration API

**Source**: `app/Domain/Plugins/Services/Registration.php`

The `Registration` class provides a fluent API for plugin bootstrapping:

```php
$registration = new Registration('MyPlugin');

// Middleware injection (into the second pipeline after core middleware)
$registration->registerMiddleware([MyMiddleware::class]);

// Language file registration (auto-discovers from plugin Languages/ folder)
$registration->registerLanguageFiles(['en-US', 'de-DE']);

// Menu item injection
$registration->addMenuItem(
    ['title' => 'My Feature', 'icon' => 'fa-star', 'href' => '/myplugin/dashboard'],
    'project',       // section: 'project' or 'global'
    ['main', 'submenu-key']  // location path
);

// Asset injection
$registration->addHeaderJs(['vendor.js']);
$registration->addFooterJs(['app.js']);
$registration->addCss(['app.css']);
```

### Plugin Lifecycle

**Source**: `app/Domain/Plugins/Services/Plugins.php`

```
discoverNewPlugins() → installPlugin() → enablePlugin() → disablePlugin() → removePlugin()
```

Each plugin service class can implement lifecycle hooks: `install()`, `uninstall()`, `enable()`, `disable()`.

### Plugin Loading Order

1. **System plugins** (from `LEAN_PLUGINS` env): Loaded at boot during `discoverListeners()`, before middleware. Cannot be disabled via UI.
2. **User plugins**: Loaded when `LoadPlugins` middleware fires (after session, install check, update check).
3. Plugin `routes.php` files are loaded via `RouteLoader`.
4. Plugin `register.php` files register event/filter listeners.

### Event/Filter Listener Registration

**Source**: `app/Domain/*/register.php` (8 files exist in core)

```php
// Class-based listener
EventDispatcher::add_event_listener(
    'leantime.domain.projects.services.projects.notifyProjectUsers.notifyProjectUsers',
    NotifyProjectUsers::class
);

// Closure with wildcard
EventDispatcher::addEventListener('leantime.domain.auth.*.userSignUpSuccess', function ($params) {
    // ...
});

// Filter with priority (lower = earlier)
EventDispatcher::add_filter_listener(
    'leantime.domain.menu.repositories.menu.getMenuStructure.menuStructures.project',
    function ($menu) { $menu['newItem'] = [...]; return $menu; },
    50
);
```

### Middleware Injection

Plugins register into a **second middleware pipeline** that runs after the core stack. See `app/Core/Http/HttpKernel.php` for the two-pipeline architecture:

```php
// Core middleware → Plugin middleware → Router dispatch
```

### Route Loading

Plugins can define `routes.php` in their root directory. The `RouteLoader` (`app/Core/Routing/`) discovers and loads these alongside domain route files.

---

## 2. API/RPC Surface

### JSON-RPC 2.0

**Source**: `app/Domain/Api/Controllers/Jsonrpc.php`

The JSON-RPC controller is the **primary programmatic API**. It routes method calls to service classes using a reflection-based resolution process.

#### Method Routing Convention

```
leantime.rpc.{module}.{method}                  → Domain\{Module}\Services\{Module}::{method}()
leantime.rpc.{module}.{service}.{method}         → Domain\{Module}\Services\{Service}::{method}()
```

Resolution order: Domain services first, then Plugin services.

#### Resolution Process

1. Parse method string into module, service, method segments
2. Apply `Str::studly()` for class names, `Str::camel()` for methods
3. Build namespace: `Leantime\Domain\{Module}\Services\{Service}` (or `Leantime\Plugins\...`)
4. Validate method exists via `method_exists()`
5. Use `ReflectionClass` to inspect parameter signatures
6. Match request params **by name**, validate required params, cast types
7. Instantiate service via `app()->make()`, invoke with spread operator

#### Key Features

- **Batch requests**: Sequential array keys trigger recursive processing
- **Notifications**: Requests with no `id` field (fire-and-forget)
- **Standard error codes**: -32700 (parse), -32600 (invalid request), -32601 (method not found), -32602 (invalid params), -32000 (server error)

#### Example Request

```json
{
  "jsonrpc": "2.0",
  "method": "leantime.rpc.tickets.tickets.getTicket",
  "id": 1,
  "params": {"id": 42}
}
```

### Auth Boundaries

**Two API authentication methods** (see `app/Core/Middleware/AuthCheck.php`):

| Method | Header | Format | Scope |
|--------|--------|--------|-------|
| Leantime API Key | `x-api-key` | `lt_{user}_{key}` | Full service account (acts as user) |
| Sanctum Bearer Token | `Authorization: Bearer {token}` | Personal access token | User-scoped (requires AdvancedAuth plugin) |

API keys are managed via `app/Domain/Api/Services/Api.php`. Format is `lt_{apiKeyName}_{secret}` where the name acts as username and secret as password.

### Service Coverage

**42 service classes** are accessible via JSON-RPC. The most integration-relevant are:

| Service | Methods | MCP Suitability | Key Operations |
|---------|---------|-----------------|----------------|
| `tickets.tickets` | 48 | High | CRUD tickets, milestones, subtasks, search, status |
| `projects.projects` | 37 | High | CRUD projects, access control, hierarchy, duplication |
| `timesheets.timesheets` | 18 | High | Time logging, punch-in/out, weekly reports |
| `users.users` | 16 | High | User CRUD, profiles, invitations |
| `sprints.sprints` | 9 | High | Sprint CRUD, burndown, cumulative reports |
| `comments.comments` | 5 | High | Comments on any entity |
| `wiki.wiki` | 9 | High | Wiki/article CRUD, activity feed |
| `goalcanvas.goalcanvas` | 11 | High | Goal/OKR management, KPIs |
| `notifications.notifications` | 4 | High | In-app notifications, @mentions |
| `reports.reports` | 6 | High | Project reports, burndown data |
| `clients.clients` | 7 | High | Client/organization management |
| `calendar.calendar` | 9 | High | Calendar events, iCal integration |
| `setting.setting` | 8 | Medium | Key-value configuration store |
| `files.files` | 6 | Medium | File attachments (local + S3) |
| `reactions.reactions` | 6 | Medium | Emoji reactions on entities |

### Legacy REST Controllers (Deprecated)

**Source**: `app/Domain/Api/Controllers/` (38 controllers)

These controllers return JSON from `get()`/`post()` methods and are called by frontend JS. They are **deprecated** — new integrations should use JSON-RPC. Notable legacy endpoints: Tickets, Projects, Users, Calendar, Canvas (and 14 canvas variants), Files, Timer, Tags, Reactions, Notifications.

---

## 3. MCP Surface

### Current State

**Source**: `composer.json` (lines 104-105, 163-165, 201-205)

Leantime includes MCP server infrastructure:

```json
"php-mcp/server": "dev-main as 3.1.1",
"php-mcp/laravel": "3.0.0"
```

Key details:
- Uses a **forked** `php-mcp/server` from `github.com/leantime/php-mcp-server.git`
- Laravel auto-discovery is **explicitly disabled** (`dont-discover: ["php-mcp/laravel"]`)
- **No `McpTool` or `McpResource` definitions exist** in `app/` code

### Assessment

The MCP infrastructure (server + Laravel integration) is installed but **not yet activated**. No tools or resources are registered. This means:

1. The packages provide the framework for exposing MCP tools/resources
2. The `dont-discover` setting suggests controlled, manual registration is planned
3. Any MCP tool implementation would need to be added (likely in a plugin or core domain)

### Recommended MCP Tool Candidates

Based on the JSON-RPC service analysis, these services are best suited for MCP tool exposure:

| Tool Name | Backing Service | Safety | Rationale |
|-----------|----------------|--------|-----------|
| `get_tickets` | `tickets.tickets.getAll` | safe-read | Core PM query |
| `get_ticket` | `tickets.tickets.getTicket` | safe-read | Single ticket detail |
| `create_ticket` | `tickets.tickets.addTicket` | unsafe-write | Task creation |
| `update_ticket` | `tickets.tickets.patch` | unsafe-write | Ticket updates |
| `get_projects` | `projects.projects.getAll` | safe-read | Project listing |
| `get_project` | `projects.projects.getProject` | safe-read | Project detail |
| `log_time` | `timesheets.timesheets.logTime` | unsafe-write | Time entry |
| `get_sprints` | `sprints.sprints.getAllSprints` | safe-read | Sprint listing |
| `add_comment` | `comments.comments.addComment` | unsafe-write | Discussion |
| `get_notifications` | `notifications.notifications.getAllNotifications` | safe-read | User notifications |
| `search_tickets` | `tickets.tickets.getAll` (with criteria) | safe-read | Filtered search |
| `get_report` | `reports.reports.getFullReport` | safe-read | Project analytics |

---

## 4. Internal Service Seams

### Services Suitable for Plugin-Backed Adapters

These services are commonly wrapped by plugins to extend or override behavior:

| Service | Why It's a Seam | Adapter Pattern |
|---------|-----------------|-----------------|
| `Connector\Services\Connector` | Generic import framework | Implement `ProviderIntegration` interface |
| `Connector\Services\Providers` | Provider registry | Register via filter `loadProviders.providerList` |
| `Auth\Services\Auth` | Authentication | Add OAuth providers via Laravel Socialite |
| `Notifications\Services\Messengers` | Notification channels | Add Slack/Teams/Discord messengers |
| `Queue\Services\Queue` | Background processing | Add custom worker channels |
| `Setting\Services\Setting` | Configuration store | Plugin-specific settings via `saveSetting`/`getSetting` |
| `Plugins\Services\Registration` | Plugin bootstrap | Primary seam — all plugins use this |
| `Menu\Services\Menu` | Navigation | Inject items via `Registration::addMenuItem()` |
| `Widgets\Services\Widgets` | Dashboard | Register custom widgets via `registerWidget()` |

### Service-to-Service Dependencies

Be cautious of circular references when calling domain services from other domain services. Common safe dependencies:

```
Tickets → Projects (project context)
Tickets → Users (assignees)
Comments → any module (polymorphic)
Notifications → Projects (notify project users)
Timesheets → Tickets (time against tasks)
Files → any module (polymorphic attachments)
```

### Layer Enforcement

- **Controllers → Services only** (never directly call repositories)
- **Services → Repositories** (data access)
- **Services → Other Services** (cross-domain logic, beware circular refs)

---

## 5. Event/Hook Surfaces

### Event Name Convention

Event names are **auto-generated from class namespace + method name**:

```
leantime.domain.{module}.services.{service}.{method}.{eventName}
```

**Critical stability note**: Moving or renaming a class changes ALL its event names. This is why class-based events are the desired future direction. Only one class-based event exists: `Files/Events/FileUploaded.php`.

### Key Registered Events

| Event | Source | Stability | Description |
|-------|--------|-----------|-------------|
| `leantime.core.console.consolekernel.schedule.cron` | `Plugins/register.php` | **High** | Cron scheduler hook. Plugins register scheduled jobs here. |
| `leantime.core.console.consolekernel.schedule.cron` | `Queue/register.php` | **High** | Queue workers: email (1min), HTTP (5min), default (5min). |
| `leantime.core.console.consolekernel.schedule.cron` | `Reports/register.php` | **High** | Daily telemetry + report ingestion. |
| `leantime.domain.auth.*.userSignUpSuccess` | `Help/register.php` | **Medium** | New user sign-up. Creates default project. Wildcard pattern. |
| `leantime.domain.projects.services.projects.notifyProjectUsers.*` | `Notifications/register.php` | **High** | Project notification dispatch. Class-based listener: `NotifyProjectUsers`. |

### Key Registered Filters

| Filter | Source | Stability | Description |
|--------|--------|-----------|-------------|
| `leantime.*.welcomeText` | `Install/register.php` | **Medium** | Welcome text customization (broad wildcard). |
| `leantime.domain.auth.template.userInvite*.welcomeText` | `Auth/register.php` | **Medium** | User invitation page text (5 template variants). |
| `leantime.domain.auth.*.belowWelcomeText` | `Auth/register.php` | **Low** | Social proof quotes below auth forms. |
| `leantime.domain.connector.services.providers.loadProviders.providerList` | `CsvImport/register.php` | **High** | Connector provider registration. Use this to add import sources. |
| `leantime.domain.menu.repositories.menu.getMenuStructure.menuStructures.*` | Plugin API | **High** | Menu structure modification. Primary injection point for navigation. |

### Implicit Event Coverage

Beyond `register.php` files, the `DispatchesEvents` trait is mixed into nearly every core class. This means events fire automatically around:

- All service method calls (`before{Method}`, `after{Method}`)
- All repository `dbcall()` executions
- Template rendering
- Controller dispatch

Pattern: `leantime.domain.{module}.services.{service}.{method}` fires automatically for any public service method when using the trait.

### Pattern Matching Support

Event listeners support glob-style patterns:
- `*` — any string segment
- `?` — any single character
- `{RGX:pattern:RGX}` — inline regex

---

## 6. Auth Boundaries

### Three Auth Guards

**Source**: `app/Core/Middleware/AuthCheck.php`, `bootstrap/app.php`

| Guard | Type | Use Case | Token Format |
|-------|------|----------|-------------|
| `leantime` | Session (web) | Browser UI, cookies | PHP session ID |
| `sanctum` | Bearer token | Personal access tokens | `Bearer {token}` (requires AdvancedAuth plugin) |
| `jsonRpc` | API key | Service accounts | `x-api-key: lt_{name}_{secret}` |

### API Key Details

**Source**: `app/Domain/Api/Services/Api.php`

- Format: `lt_{apiKeyName}_{apiSecret}`
- Acts as a **service account** — authenticated as a regular user
- Created by system admins via UI or `createAPIKey()` service method
- The API key name becomes the username, the secret becomes the password
- Validated in `getAPIKeyUser()` which checks against stored hashed values

### Sanctum Tokens

**Source**: `app/Domain/Auth/Services/AccessToken.php`

- Requires the **AdvancedAuth** plugin to be installed
- Personal access tokens created per-user via `createToken($userId, $name)`
- Abilities/scopes supported (`can()`, `cant()`)
- Token lookup via `findToken($token)`

### Public Routes

Some routes bypass authentication entirely:
- `/install` — Installation wizard
- `/auth/login`, `/auth/resetPw` — Login and password reset
- `/api/i18n` — Internationalization strings
- iCal feeds via hash-based auth (`getIcalByHash`)

### Rate Limiting

**Source**: `app/Core/Middleware/RequestRateLimiter.php`

| Endpoint Pattern | Limit |
|-----------------|-------|
| Login | 20/minute |
| API | 100/minute |
| General | 10,000/minute |

---

## 7. Write-Safety Notes

### Safe-Read Services (no side effects)

These services/methods are safe for read-only MCP tools:

- `tickets.getAll`, `tickets.getTicket`, `tickets.getAllMilestones`, `tickets.getStatusLabels`, all `poll*` methods
- `projects.getProject`, `projects.getAll`, `projects.getProjectProgress`, `projects.getProjectHierarchy*`
- `sprints.getSprint`, `sprints.getAllSprints`, `sprints.getSprintBurndown`
- `timesheets.isClocked`, `timesheets.getAll`, `timesheets.getWeeklyTimesheets`, `timesheets.getLoggedHours*`
- `users.getAll`, `users.getUser`, `users.getUserByEmail`
- `comments.getComments`, `comments.pollComments`
- `wiki.getArticle`, `wiki.getAllProjectWikis`, `wiki.getAllWikiHeadlines`
- `reports.getFullReport`, `reports.getRealtimeReport`, `reports.getProjectStatusReport`
- `notifications.getAllNotifications`
- `setting.getSetting`
- `tags.getTags`
- `canvas.getBoardProgress`, `canvas.getLastUpdatedCanvas`
- `goalcanvas.getCanvasItemsById`, `goalcanvas.getParentKPIs`, `goalcanvas.pollGoals`
- `clients.getAll`, `clients.get`
- `reactions.getGroupedEntityReactions`, `reactions.getUserReactions`

### Unsafe-Write Services (state-modifying)

These require careful authorization and should have confirmation UIs:

- **Ticket mutations**: `addTicket`, `updateTicket`, `patch`, `delete`, `deleteMilestone`, `updateTicketStatusAndSorting`
- **Project mutations**: `addProject`, `editProject`, `duplicateProject`, `patch`, `editUserProjectRelations`
- **User mutations**: `addUser`, `editUser`, `deleteUser`, `createUserInvite`
- **Time mutations**: `punchIn`, `punchOut`, `logTime`, `upsertTime`, `deleteTime`
- **Sprint mutations**: `addSprint`, `editSprint`
- **Comment mutations**: `addComment`, `editComment`, `deleteComment`
- **Wiki mutations**: `createWiki`, `updateWiki`, `createArticle`, `updateArticle`
- **File mutations**: `upload`, `deleteFile`
- **Auth mutations**: `login`, `logout`, `setPassword`, `reset2FA`
- **Setting mutations**: `saveSetting`, `deleteSetting`
- **Plugin mutations**: `installPlugin`, `enablePlugin`, `disablePlugin`, `removePlugin`

### Session-Sensitive Methods

Some methods depend on active session state and may behave unexpectedly via API:

- `projects.changeCurrentSessionProject` — modifies session, not entity
- `auth.set2FAVerified` — session flag
- `tickets.getLastTicketViewUrl` — reads from session
- `wiki.setCurrentWiki`, `wiki.setCurrentArticle` — session state

---

## 8. Recommendations

### Per-Surface Recommendations

| Surface | Approach | Rationale |
|---------|----------|-----------|
| **Read-only PM data** (tickets, projects, sprints, reports) | **External MCP** | Safe, high-value, no side effects. Best for AI assistant integration. |
| **Write operations** (create/update tickets, log time) | **MCP with confirmation** | Expose as MCP tools with human-in-the-loop confirmation for mutations. |
| **Custom UI extensions** | **Plugin** | Menu items, dashboard widgets, custom views require plugin infrastructure. |
| **Notification channels** | **Plugin** | Slack/Teams/Discord integration needs event listeners + middleware. |
| **Data import/sync** | **Plugin** (Connector framework) | Use the existing `Connector\Services\Providers` extension point. |
| **Authentication providers** | **Plugin** | OIDC/SAML/social login via Laravel Socialite integration. |
| **Background processing** | **Plugin** | Cron hooks and queue workers need `register.php` integration. |
| **Reporting/analytics** | **Hybrid** | MCP tool for data retrieval + plugin for custom report views. |
| **Workflow automation** | **External MCP** | Event-driven triggers via polling endpoints + MCP tool actions. |

### MCP Implementation Strategy

1. **Phase 1: Read-only tools** — Expose `getTicket`, `getAll`, `getProject`, `getFullReport`, `getAllSprints`, `getComments` as MCP tools. Zero risk, immediate value.

2. **Phase 2: Write tools with guards** — Add `addTicket`, `updateTicket`, `logTime`, `addComment` with schema validation and confirmation semantics.

3. **Phase 3: Resource endpoints** — Expose projects and tickets as MCP resources with URI templates (`leantime://project/{id}`, `leantime://ticket/{id}`).

### Plugin vs MCP Decision Matrix

| Need | Plugin | MCP | Hybrid |
|------|--------|-----|--------|
| AI reads project data | | ✅ | |
| AI creates tickets | | ✅ | |
| Custom sidebar widget | ✅ | | |
| Slack notifications | ✅ | | |
| External tool sync | | | ✅ |
| Custom authentication | ✅ | | |
| Dashboard analytics | | | ✅ |
| Automated standup reports | | ✅ | |
| Custom kanban columns | ✅ | | |
| Time tracking integration | | | ✅ |

---

## Appendix: File References

| Component | Path |
|-----------|------|
| JSON-RPC Controller | `app/Domain/Api/Controllers/Jsonrpc.php` |
| Plugin Registration API | `app/Domain/Plugins/Services/Registration.php` |
| Plugin Service | `app/Domain/Plugins/Services/Plugins.php` |
| Event Dispatcher | `app/Core/Events/EventDispatcher.php` |
| DispatchesEvents Trait | `app/Core/Events/DispatchesEvents.php` |
| Auth Middleware | `app/Core/Middleware/AuthCheck.php` |
| HTTP Kernel | `app/Core/Http/HttpKernel.php` |
| Route Loader | `app/Core/Routing/RouteLoader.php` (presumed) |
| API Key Service | `app/Domain/Api/Services/Api.php` |
| Access Token Service | `app/Domain/Auth/Services/AccessToken.php` |
| Frontcontroller | `app/Core/Controller/Frontcontroller.php` |
| MCP packages | `composer.json` (php-mcp/server, php-mcp/laravel) |
| Register files | `app/Domain/{Auth,CsvImport,Help,Install,Notifications,Plugins,Queue,Reports}/register.php` |
