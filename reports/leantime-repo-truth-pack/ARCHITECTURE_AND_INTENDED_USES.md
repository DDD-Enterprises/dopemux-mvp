# Leantime Architecture & Intended Uses

> Evidence-backed architecture reference. File paths point to actual source code.
> Items marked **UNKNOWN** could not be confirmed from the codebase.

---

## 1. HIGH-LEVEL ARCHITECTURE SUMMARY

Leantime is a domain-driven PHP/Laravel 11 application for project management, designed for non-project managers with ADHD/dyslexia/autism-friendly UX.

| Layer | Location | Description |
|-------|----------|-------------|
| Core framework | `app/Core/` (22 subdirectories) | Laravel extensions, middleware, events, plugins, DB, UI |
| Domain modules | `app/Domain/` (57 modules) | Feature-organized business logic, controllers, templates |
| Plugin system | `app/Plugins/` (git submodule) | Third-party extensions following domain structure |
| Shared views | `app/Views/` | Layouts, Blade components, view composers |
| Public assets | `public/` | Static assets, compiled JS/CSS, themes |
| Entry points | `public/index.php`, `bin/leantime` | HTTP and CLI entry |

**Key architectural characteristics:**

- **Dual routing:** Laravel routes (preferred) + legacy Frontcontroller convention-based routing (`app/Core/Controller/Frontcontroller.php`)
- **Dual templates:** Blade `.blade.php` (~91 domain + ~33 shared) + legacy `.tpl.php` (~198 files)
- **JSON-RPC 2.0 API** as primary external interface (`app/Domain/Api/Controllers/Jsonrpc.php`)
- **MCP endpoint** (early stage) at `/mcp` (`app/Core/Http/IncomingRequest.php:48`, packages: `php-mcp/server`, `php-mcp/laravel`)
- **Event/filter system** for loose coupling (`app/Core/Events/EventDispatcher.php`)
- **Plugin architecture** with middleware, menu, asset, and route injection

---

## 2. COMPONENT INVENTORY

### Core Components (`app/Core/`)

| Component | Files | Responsibility |
|-----------|-------|---------------|
| `Application/` | AppServiceProvider.php | Registers core service providers and application version metadata |
| `Auth/` | AuthenticationServiceProvider.php | Configures auth guards (leantime, sanctum, jsonRpc) and gate policies |
| `Bootstrap/` | LoadConfig.php, SetRequestForConsole.php | Custom config loading from `laravelConfig.php` + Environment; console request setup |
| `Cache/` | CacheServiceProvider.php | Multi-domain cache store management with optional Redis support |
| `Configuration/` | AppSettings.php, DefaultConfig.php, Environment.php, EnvironmentsEnum.php, EnvironmentServiceProvider.php, laravelConfig.php | All Laravel config in single file; env-var-driven settings with `LEAN_*` prefix |
| `Console/` | Application.php, CliRequest.php, CliServiceProvider.php, ConsoleKernel.php, ConsoleSupportProvider.php | CLI/Artisan command execution with Leantime-specific extensions |
| `Controller/` | Composer.php, Controller.php, Frontcontroller.php, HtmxController.php | Base controllers; legacy URL-to-class mapping; HTMX partial rendering |
| `Database/` | DatabaseManager.php, DatabaseServiceProvider.php, LtPostgresConnection.php | High-level DB management, multi-tenancy support, PostgreSQL extensions |
| `Db/` | Db.php, DatabaseHelper.php, DbColumn.php, Repository.php | Low-level DB abstraction, repository base class, cross-DB helpers |
| `Domains/` | DTO.php, DomainModel.php, DomainRepository.php, DomainService.php | Base interfaces/classes for DDD pattern |
| `Encryption/` | EncryptionServiceProvider.php | Encryption key registration and cipher services |
| `Events/` | DispatchesEvents.php, EventDispatcher.php, EventsServiceProvider.php | Custom event/filter system with pattern matching, wildcards, regex |
| `Exceptions/` | AuthException.php, ElementExistsException.php, ExceptionHandler.php, HandleExceptions.php, InvalidArgumentException.php, MissingParameterException.php, ReportableHandler.php, WhoopsHandler.php | Exception handling with Whoops dev display and Sentry integration |
| `Files/` | FileManager.php, FileSystemServiceProvider.php | File upload/storage via Laravel filesystem (local + S3) |
| `Http/` | ApiRequest.php, HtmxRequest.php, HttpKernel.php, IncomingRequest.php | Request types auto-detected; middleware stack; dual-pipeline routing |
| `i18n/` | LanguageServiceProvider.php | Translation service registration (INI-based language files) |
| `Middleware/` | 13 middleware classes | Auth, sessions, rate limiting, CORS, plugins, localization, headers |
| `Plugins/` | PluginManager.php, Plugins.php, PluginsServiceProvider.php | Plugin discovery, loading, registration for folder and phar formats |
| `Routing/` | FrontcontrollerServiceProvider.php, RouteLoader.php | Route loading from domains/plugins with caching |
| `Sessions/` | PathManifestRepository.php, SessionServiceProvider.php | Custom session driver registration and manifest storage |
| `Support/` | 12 utility classes | DateTimeHelper, CarbonMacros, Format, Cast, Avatarcreator, Build, Mix |
| `UI/` | Composer.php, Template.php, TemplateServiceProvider.php, Theme.php, ThemeServiceProvider.php, ViewsServiceProvider.php | Template rendering, theme management, Blade view composition |

**Also at `app/Core/` root:** `Application.php`, `Bootloader.php`, `Language.php`, `Mailer.php`

---

## 3. RESPONSIBILITY MAP

```
HTTP Request
  │
  ▼
public/index.php ─► bootstrap/app.php ─► Bootloader::boot()
  │
  ▼
HttpKernel (app/Core/Http/HttpKernel.php)
  │
  ├─ Bootstrappers: LoadEnv → LoadConfig → HandleExceptions → RegisterFacades → RegisterProviders → BootProviders
  │
  ▼
Middleware Pipeline (16 layers)
  │  TrustProxies → StartSession → Installed → Updated → LoadPlugins →
  │  InitialHeaders → AuthCheck → AuthenticateSession → RequestRateLimiter →
  │  HandleCors → ValidatePostSize → TrimStrings → ConvertEmptyStringsToNull →
  │  SetCacheHeaders → Localization → CurrentProject
  │
  ├─ Plugin Middleware Pipeline (injected via Registration::registerMiddleware())
  │
  ▼
Router
  ├─ Laravel Routes (preferred) ─► Controller::get()/post()
  └─ Frontcontroller fallback ──► Convention: /module/action → Domain\{Module}\Controllers\{Action}
       │
       ▼
  Controller (app/Domain/*/Controllers/)
    │  - Handles HTTP request/response
    │  - Calls Services (NEVER Repositories directly)
    │  - Returns Response or renders Template
    │
    ▼
  Service (app/Domain/*/Services/)
    │  - Business logic and validation
    │  - Orchestrates across repositories
    │  - Dispatches events/filters
    │  - API surface via JSON-RPC (@api annotation)
    │
    ▼
  Repository (app/Domain/*/Repositories/)
    │  - Data access (raw SQL + Query Builder mix)
    │  - Uses dbcall() wrapper for event dispatch
    │  - zp_-prefixed tables
    │
    ▼
  Database (MySQL/PostgreSQL)
    │  - Managed via Core/Db/Db.php wrapping Laravel DatabaseManager
    │  - Schema created by Install/Services/SchemaBuilder.php (no migrations)
```

### HTMX Request Flow

```
HTMX Request (hx-get="/hx/module/action")
  │
  ▼
Same middleware pipeline
  │
  ▼
Frontcontroller: /hx/{module}/{action} → Domain\{Module}\Hxcontrollers\{Action}
  │
  ▼
HtmxController (extends Core/Controller/HtmxController.php)
  │  - init() for DI (not __construct)
  │  - Renders Blade partial via static $view
  │  - Triggers HTMX events via setHTMXEvent()
  │
  ▼
Blade Partial (app/Domain/*/Templates/partials/*.blade.php)
```

---

## 4. DEPENDENCY DIRECTION SUMMARY

```
Controllers ──► Services ──► Repositories ──► Database
     │              │              │
     │              ├──► Other Services (circular reference risk)
     │              │
     │              └──► Events (loose coupling)
     │
     └──► Templates (view rendering)
```

**Rules (enforced by convention, documented in `CLAUDE.md`):**

| Rule | Evidence |
|------|----------|
| Controllers depend on Services only, never Repositories | `CLAUDE.md`: "Controllers should only call services NOT repositories" |
| Services depend on Repositories and other Services | `CLAUDE.md`: "Services can call repositories" |
| Circular service dependencies are a known risk | `CLAUDE.md`: "Be careful when calling domain services in other domain services as circular references can happen" |
| Repositories depend on Database layer | All repositories extend `Core/Db/Repository.php` |
| Events provide cross-domain loose coupling | `app/Core/Events/DispatchesEvents.php` trait mixed into core classes |
| Plugins hook via events/filters, not direct coupling | Plugin `register.php` files use `EventDispatcher::add_event_listener()` |

---

## 5. ENTRYPOINTS

### HTTP Entry
- **Path:** `public/index.php` → `bootstrap/app.php` → `Bootloader::boot()` → `HttpKernel`
- **Evidence:** `public/index.php` loads helpers, autoloader, creates Application; `bootstrap/app.php` binds `HttpKernel` to `Leantime\Core\Http\HttpKernel`

### CLI Entry
- **Path:** `bin/leantime` → `bootstrap/app.php` → `ConsoleKernel`
- **Evidence:** `bin/leantime` defines `LEAN_CLI` constant, loads autoloader, calls `$app->handleCommand()`
- **Commands discovered from:** `app/Command/`, `app/Domain/**/Command/`, enabled plugins

### Cron Entry
- **Path:** `schedule:run` → `ConsoleKernel::schedule()` → dispatches `cron` event → `register.php` listeners
- **Evidence:** `app/Core/Console/ConsoleKernel.php` fires `dispatch_event('cron')` in schedule method
- **Poor man's cron:** HTTP endpoint at `/cron/run` triggers `schedule:run` for servers without real cron

### Queue Workers
- **Path:** `queue:work --queue={name}` processed via scheduled tasks
- **Named queues (from `app/Domain/Queue/register.php`):**

| Queue | Frequency | Purpose |
|-------|-----------|---------|
| `queue:emails` | Every minute | Email delivery |
| `queue:httprequests` | Every 5 minutes | Async HTTP requests |
| `queue:default` | Every 5 minutes | General job processing |

- **Config:** `app/Core/Configuration/laravelConfig.php` (line ~887), default driver: `database`, table: `zp_jobs`
- **Drivers supported:** sync, database, beanstalkd, sqs, redis

### API Entry
- **Path:** `/api/jsonrpc` → `app/Domain/Api/Controllers/Jsonrpc.php`
- **Protocol:** JSON-RPC 2.0 with batch request support
- **Method routing:** `leantime.rpc.{module}.{service}.{method}` → resolves to `Domain\{Module}\Services\{Service}::{method}()`
- **Auth:** Leantime API Keys (`lt_{user}_{key}` format) or Laravel Sanctum bearer tokens
- **Legacy REST:** 38 controllers in `app/Domain/Api/Controllers/` (deprecated, still functional)

### MCP Entry
- **Path:** `/mcp` endpoint
- **Evidence:** `app/Core/Http/IncomingRequest.php:48` lists `/mcp` in `apiEndpoints` array
- **Packages:** `php-mcp/server` (dev-main), `php-mcp/laravel` (3.0.0) in `composer.json`
- **Test file:** `tests/Httprequests/MCP.http` shows `initialize`, `tools/list`, `tools/call` methods
- **Status:** Early stage — infrastructure in place, not fully documented

---

## 6. DATA/STORAGE BOUNDARIES

### Primary Database

**Supported:** MySQL 8.0+, MariaDB 10.6+, PostgreSQL, SQLite (fallback)
**Config:** `app/Core/Configuration/laravelConfig.php`, env vars `LEAN_DB_*`
**Schema creation:** `app/Domain/Install/Services/SchemaBuilder.php` — programmatic, no Laravel migrations

**Tables (48 `zp_`-prefixed names found in `app/Domain/Install/Repositories/Install.php`):**

| Category | Tables |
|----------|--------|
| Core entities | `zp_user`, `zp_projects`, `zp_clients`, `zp_tickets`, `zp_sprints` |
| Collaboration | `zp_comment`, `zp_file`, `zp_read`, `zp_reactions`, `zp_wiki`, `zp_wiki_articles`, `zp_wiki_categories`, `zp_wiki_comments` |
| Planning | `zp_canvas`, `zp_canvas_items`, `zp_note`, `zp_calendar` |
| Time tracking | `zp_timesheets`, `zp_punch_clock` |
| History/audit | `zp_tickethistory`, `zp_audit`, `zp_stats` |
| Admin | `zp_settings`, `zp_plugins`, `zp_notifications`, `zp_queue` |
| Access control | `zp_access_tokens`, `zp_relationuserproject`, `zp_roles`, `zp_modulerights`, `zp_submodulerights` |
| Integration | `zp_integration`, `zp_gcallinks`, `zp_connector` (UNKNOWN) |
| Queue (Laravel) | `zp_jobs`, `job_batches`, `failed_jobs` |
| Other | `zp_lead`, `zp_message`, `zp_account`, `zp_action_tabs`, `zp_approvals`, `zp_dashboard_widgets`, `zp_entity_relationship`, `zp_recurring_patterns`, `zp_ticketscol` |

### File Storage
- **Local:** `userfiles/` directory (configurable via `DefaultConfig::$userFilePath`)
- **S3:** Optional, configured via `LEAN_S3_*` env vars (`app/Core/Configuration/DefaultConfig.php`)
- **Managed by:** `app/Core/Files/FileManager.php` using Laravel Filesystem
- **Disks:** `public` (web-accessible) and `private` (auth-required)

### Cache
- **File-based:** Default fallback (`storage/framework/cache/`)
- **Redis:** Optional, configured via `LEAN_REDIS_*` env vars
- **Provider:** `app/Core/Cache/CacheServiceProvider.php`

### Sessions
- **File-based** by default (`storage/framework/sessions/`)
- **Redis** when configured
- **Provider:** `app/Core/Sessions/SessionServiceProvider.php`

### Key-Value Config
- **Table:** `zp_settings` — arbitrary key-value pairs
- **Service:** `app/Domain/Setting/Services/Setting.php`
- **Patterns:** `companysettings.*` (global), `usersetting.{userId}.*` (per-user)
- **Caching:** In-memory via `SettingCache` within request lifecycle

---

## 7. EXTENSION BOUNDARIES

### Plugin System (`app/Plugins/`)

**Three plugin types:**

| Type | Loading | Management |
|------|---------|------------|
| System | Boot-time via `LEAN_PLUGINS` env var | Cannot disable via UI |
| Custom/Folder | `app/Plugins/{name}/` directory | Enable/disable via admin |
| Marketplace | `.phar` packages from marketplace.leantime.io | License key required |

**Plugin structure mirrors domain modules:** Controllers, Services, Repositories, Models, Templates, `register.php`, `composer.json`

**Evidence:** `app/Core/Plugins/PluginManager.php`, `app/Domain/Plugins/Services/Plugins.php`, `app/Domain/Plugins/Services/Registration.php`

### Injection Points

| Extension Point | Mechanism | Evidence |
|-----------------|-----------|----------|
| Event listeners | `EventDispatcher::add_event_listener()` in `register.php` | `app/Core/Events/EventDispatcher.php` |
| Filter hooks | `EventDispatcher::add_filter_listener()` with priority | Same as above |
| Middleware injection | `Registration::registerMiddleware()` → second pipeline in HttpKernel | `app/Domain/Plugins/Services/Registration.php` |
| Route registration | `routes.php` in plugin directory, loaded by `RouteLoader` | `app/Core/Routing/RouteLoader.php` |
| Menu item injection | `Registration::addMenuItem()` via filter on menu structure | `app/Domain/Menu/Repositories/Menu.php` |
| JS injection (header) | `Registration::addHeaderJs()` via `afterLinkTags` event | `app/Domain/Plugins/Services/Registration.php` |
| JS injection (footer) | `Registration::addFooterJs()` via `beforeBodyClose` event | Same as above |
| CSS injection | `Registration::addCss()` via `afterLinkTags` event | Same as above |
| Language files | `Registration::registerLanguageFiles()` | Same as above |
| Theme system | `public/theme/{name}/` with `theme.ini`, `css/light.css`, `css/dark.css` | `app/Core/UI/Theme.php` |

### Key System Events

| Event | When | Evidence |
|-------|------|----------|
| `request_started` | Before routing | `HttpKernel.php` |
| `pluginsStart` | Plugin initialization phase | `LoadPlugins` middleware |
| `plugins_middleware` | Plugin middleware pipeline | `HttpKernel::sendRequestThroughRouter()` |
| `leantime.core.console.consolekernel.schedule.cron` | Scheduler tick | `ConsoleKernel::schedule()` |
| `beforeSendResponse` | Before HTTP response sent | `HttpKernel.php` |
| `request_terminated` | After response sent | `HttpKernel.php` |

---

## 8. IMPLEMENTED USE CASES

Based on actual controllers, services, and repositories found in source code:

### Project Management
- **Create, edit, close, duplicate projects** — `app/Domain/Projects/Controllers/` (NewProject, ShowProject, ShowAll), `app/Domain/Projects/Services/Projects.php`
- **Project settings and access control** — `app/Domain/Projects/Controllers/SettingProject.php`
- **Client association** — `app/Domain/Clients/` (full CRUD)

### Task/Ticket Management
- **Full CRUD with status tracking** — `app/Domain/Tickets/Controllers/` (NewTicket, ShowTicket, ShowAll, ShowList, ShowKanban)
- **Kanban board view** — `app/Domain/Tickets/Controllers/ShowKanban.php`
- **Table/list views** — `app/Domain/Tickets/Controllers/ShowList.php`
- **Roadmap/Gantt view** — `app/Domain/Tickets/Controllers/Roadmap.php`
- **Subtasks via dependency chain** — `zp_tickets.dependingTicketId` field, unlimited nesting
- **Ticket history** — `zp_tickethistory` table, `app/Domain/Tickets/Repositories/Tickets.php`

### Time Tracking
- **Manual timesheet entry** — `app/Domain/Timesheets/Controllers/` (AddTime, ShowMy, ShowAll)
- **Punch clock** — `zp_punch_clock` table, `app/Domain/Timesheets/Services/Timesheets.php`
- **Plan vs. actual hours** — `Tickets` model: `planHours`, `hourRemaining`, `bookedHours`

### Sprint Planning
- **Date-bounded sprints** — `app/Domain/Sprints/Controllers/` (EditSprint), `zp_sprints` table
- **Sprint-to-ticket association** — `zp_tickets.sprint` field

### Milestone Tracking
- **Milestones as ticket type** — `zp_tickets.type = 'milestone'`, `milestoneid` field for association
- **Timeline dates** — `timelineDate`, `timelineDateToFinish` on ticket model

### Strategic Planning (14+ Canvas Variants)
- **Base canvas engine** — `app/Domain/Canvas/` with generic Controllers, Services, Repositories
- **Canvas variants** (each extends base with `CANVAS_NAME` constant):
  - `Cpcanvas`, `Dbmcanvas`, `Eacanvas`, `Emcanvas`, `Insightscanvas`, `Lbmcanvas`, `Leancanvas`, `Minempathycanvas`, `Obmcanvas`, `Retroscanvas`, `Riskscanvas`, `Sbcanvas`, `Smcanvas`, `Sqcanvas`, `Swotcanvas`, `Valuecanvas`
- **Data stored in:** `zp_canvas` (boards) + `zp_canvas_items` (cards)

### Goal Tracking
- **OKR-style metrics** — `app/Domain/Goalcanvas/` (fully modernized to Blade, has own service)
- **Separate from base canvas** — custom `app/Domain/Goalcanvas/Services/Goalcanvas.php`

### Knowledge Management
- **Wiki/articles** — `app/Domain/Wiki/` with `zp_wiki`, `zp_wiki_articles`, `zp_wiki_categories`, `zp_wiki_comments` tables
- **HTMX controllers** — `app/Domain/Wiki/Hxcontrollers/`

### Idea Management
- **Idea boards** — `app/Domain/Ideas/Controllers/` (ShowBoards, AdvancedShow, IdeaDialog)

### Risk Management
- **Risk canvas** — `app/Domain/Riskscanvas/` extending base Canvas

### Retrospectives
- **Retro canvas** — `app/Domain/Retroscanvas/` extending base Canvas

### User Management
- **CRUD, roles, project assignment** — `app/Domain/Users/Controllers/` (NewUser, EditUser, ShowAll)
- **LDAP authentication** — `app/Domain/Ldap/`
- **OIDC authentication** — `app/Domain/Oidc/`
- **Two-factor authentication** — `app/Domain/TwoFA/`
- **Role-based access** — `zp_roles` table, hardcoded role constants

### File Management
- **Upload, storage, download** — `app/Domain/Files/Controllers/`, `app/Core/Files/FileManager.php`
- **Local + S3 support** — configured via `DefaultConfig.php`

### Notifications
- **Activity feed** — `app/Domain/Notifications/Controllers/`, `zp_notifications` table
- **Email queue** — `app/Domain/Queue/` with `queue:emails` worker
- **HTMX live updates** — `app/Domain/Notifications/Hxcontrollers/`

### Reporting
- **Sprint statistics** — `app/Domain/Reports/Services/Reports.php`
- **Daily ingestion** — `Reports::cronDailyIngestion()` via scheduler (`app/Domain/Reports/register.php`)
- **Anonymous telemetry** — `Reports::sendAnonymousTelemetry()` daily cron
- **Stats table** — `zp_stats`

### Data Import
- **CSV import** — `app/Domain/CsvImport/`
- **Connector framework** — `app/Domain/Connector/`

### Calendar
- **Events and scheduling** — `app/Domain/Calendar/Controllers/`, `zp_calendar` table
- **Google Calendar links** — `zp_gcallinks` table
- **iCal generation** — `spatie/icalendar-generator` (^2.6) in `composer.json`
- **CalDAV/WebDAV** — `sabre/dav` (^4.7) in `composer.json`

### API Access
- **JSON-RPC 2.0** — `app/Domain/Api/Controllers/Jsonrpc.php` (primary)
- **Legacy REST controllers** — 38 controllers in `app/Domain/Api/Controllers/` (deprecated)
- **API key management** — `app/Domain/Api/Controllers/ApiKey.php`, `NewApiKey.php`, `DelAPIKey.php`

### AI Integration
- **LLM abstraction** — `prism-php/prism` (^0.57.0) in `composer.json`
- **AI monitoring** — `inspector-apm/neuron-ai` (1.12.8) in `composer.json`
- **Vector database** — `hkulekci/qdrant` (^0.5.8) in `composer.json` for semantic search
- **MCP server** — `php-mcp/server` + `php-mcp/laravel` in `composer.json`
- **Status:** Infrastructure present; extent of integration **UNKNOWN** — no direct OpenAI/Claude/Bedrock packages found; uses Prism abstraction layer

### Other
- **Dashboard widgets** — `app/Domain/Dashboard/`, `app/Domain/Widgets/` with `zp_dashboard_widgets`
- **Gamification** — `app/Domain/Gamecenter/`
- **Tags** — `app/Domain/Tags/`
- **Reactions** — `app/Domain/Reactions/`, `zp_reactions` table
- **Read tracking** — `app/Domain/Read/`, `zp_read` table
- **Audit logging** — `app/Domain/Audit/`, `zp_audit` table
- **Comments** — `app/Domain/Comments/`
- **Help system** — `app/Domain/Help/`
- **Strategy module** — `app/Domain/Strategy/`
- **Module manager** — `app/Domain/Modulemanager/`

---

## 9. DOCUMENTED INTENDED USE CASES

From `README.md`, Leantime is positioned as an alternative to Jira, ClickUp, Monday, and Asana, specifically for:

| Documented Feature | Implemented? | Evidence |
|--------------------|-------------|----------|
| Task management (Kanban, Gantt, table, list, calendar views) | ✅ Yes | `app/Domain/Tickets/Controllers/` — ShowKanban, Roadmap, ShowList, ShowAll |
| Project dashboards and reports | ✅ Yes | `app/Domain/Dashboard/`, `app/Domain/Reports/` |
| Goal & metrics tracking | ✅ Yes | `app/Domain/Goalcanvas/` |
| Lean Canvas, Business Model Canvas | ✅ Yes | `app/Domain/Leancanvas/`, `app/Domain/Dbmcanvas/` (and 14 other canvas variants) |
| SWOT Analysis | ✅ Yes | `app/Domain/Swotcanvas/` |
| Risk Analysis | ✅ Yes | `app/Domain/Riskscanvas/` |
| Wikis/Docs | ✅ Yes | `app/Domain/Wiki/` |
| Idea Boards | ✅ Yes | `app/Domain/Ideas/` |
| Retrospectives | ✅ Yes | `app/Domain/Retroscanvas/` |
| Timesheets | ✅ Yes | `app/Domain/Timesheets/` |
| Sprint management | ✅ Yes | `app/Domain/Sprints/` |
| Milestone tracking | ✅ Yes | Ticket type `milestone` in `app/Domain/Tickets/` |
| File storage (S3 + local) | ✅ Yes | `app/Core/Files/FileManager.php`, `DefaultConfig.php` |
| Slack/Mattermost/Discord integrations | ✅ Partial | Plugin/connector system exists; extent **UNKNOWN** |
| LDAP, OIDC auth | ✅ Yes | `app/Domain/Ldap/`, `app/Domain/Oidc/` |
| 20+ languages | ✅ Yes | `app/Language/` directory with INI files |
| Multiple user roles | ✅ Yes | `app/Domain/Users/`, `zp_roles` table |
| Two-factor authentication | ✅ Yes | `app/Domain/TwoFA/` |
| Plugin extensibility | ✅ Yes | `app/Plugins/`, `app/Domain/Plugins/` |
| ADHD/dyslexia/autism-friendly UX | ✅ Design principle | Atkinson Hyperlegible font option, focused UI |

---

## 10. UNSUPPORTED / UNKNOWN INTENDED USES

| Feature | Status | Evidence |
|---------|--------|----------|
| Formal workflow engine | ❌ Not implemented | No state machine, `StateMachine`, or workflow engine classes found in codebase |
| Dependency blocking enforcement | ⚠️ Field exists, not enforced | `zp_tickets.dependingTicketId` stores dependency; no server-side logic prevents working on blocked tickets |
| Resource allocation / capacity planning | ❌ Not implemented | Task assignment (`userId`) and plan hours exist, but no resource pool, capacity view, or allocation features |
| Gantt chart editing (server-side) | ⚠️ Partial | Frontend: `public/assets/js/libs/simpleGantt/frappe-gantt.js`; `Roadmap.php` controller renders view; server-side drag-save **UNKNOWN** |
| Custom fields on tickets/projects | ❌ Not in core | `additionalFields.sub.php` template exists but no custom field definition system; likely plugin-extensible |
| Workflow automation / triggers | ❌ Not implemented | Event system exists but no user-configurable automation rules |
| Multi-tenancy | ⚠️ Partial infrastructure | `app/Core/Database/DatabaseManager.php` has connection switching; full multi-tenant support **UNKNOWN** |
| Advanced reporting / BI | ⚠️ Basic only | `Reports` domain has daily ingestion and sprint stats; no advanced analytics or custom report builder |

---

## 11. ARCHITECTURE RISKS / AMBIGUITIES

### API Surface

| Risk | Detail | Evidence |
|------|--------|----------|
| No formal API schema | Request/response shapes derived from service method signatures via PHP Reflection at runtime | `app/Domain/Api/Controllers/Jsonrpc.php` uses `ReflectionMethod` to introspect parameters |
| Service layer doubles as API surface | Any public method on a service class is callable via JSON-RPC; `@api` annotation is documentation only, not enforced | `CLAUDE.md`: "Any public service method can be called via JSON-RPC" |
| No OpenAPI/Swagger documentation | API contracts exist only in code | No `openapi.yaml` or similar found |

### Event System

| Risk | Detail | Evidence |
|------|--------|----------|
| Event names tied to class paths | Moving/renaming a class changes all its event names, breaking listeners | `CLAUDE.md`: "Moving a class changes all its event names" |
| String-based event names | Only one class-based event exists (`Files/Events/FileUploaded.php`); migration to class-based is aspirational | `CLAUDE.md` documents this as ongoing migration |

### Database

| Risk | Detail | Evidence |
|------|--------|----------|
| No database migrations | Schema managed programmatically via `SchemaBuilder::createAllTables()` for install; updates via `Install/Repositories/Install.php` | `app/Domain/Install/Services/SchemaBuilder.php` |
| Raw SQL mixed with Query Builder | Repositories inconsistently use raw SQL vs Laravel Query Builder | `CLAUDE.md`: "mix raw SQL queries with Laravel Query Builder" |
| No ORM entities | Models are plain PHP classes with public properties, no Doctrine/Eloquent mapping | `CLAUDE.md`: "Properties typically use `mixed` type hints" |

### Security

| Risk | Detail | Evidence |
|------|--------|----------|
| Plugin system loads arbitrary code | No sandboxing; security depends on trust in plugin source | `app/Core/Plugins/PluginManager.php` requires `register.php` directly |
| All status transitions unconstrained | No workflow engine validates allowed state transitions | No state machine implementation found |

### Frontend Performance

| Risk | Detail | Evidence |
|------|--------|----------|
| ~7-8MB JS on every page | All bundles loaded globally via `header.blade.php`; no code splitting | `CLAUDE.md`: "~7-8MB of JS loaded on every page" |
| TinyMCE alone is 3.6MB | Loaded even on pages without editors | `CLAUDE.md` |
| Redundant date libraries | Both Moment.js and Luxon included | `CLAUDE.md` |
| Bootstrap 2.x still in use | Ancient version alongside Tailwind 3.4.x (with `tw-` prefix) | `CLAUDE.md` |

### Architectural Debt

| Risk | Detail | Evidence |
|------|--------|----------|
| Mixed template systems | ~198 `.tpl.php` (legacy) vs ~91+33 `.blade.php` (modern); ~30% migrated | `CLAUDE.md` template migration section |
| Circular service dependency risk | Services can call other domain services; no compile-time enforcement | `CLAUDE.md`: "circular references can happen" |
| Legacy Frontcontroller still handles most requests | Despite Laravel routes being preferred, convention-based routing remains primary | `app/Core/Controller/Frontcontroller.php` |
| Global JS namespace with IIFE pattern | No module system; all domain JS concatenated into single bundle | `CLAUDE.md` JS architecture section |

---

## Appendix: Domain Module Index

All 57 domain modules in `app/Domain/`:

| Category | Modules |
|----------|---------|
| **Core Features** | Tickets, Projects, Users, Sprints, Timesheets, Calendar, Comments, Files, Wiki, Ideas, Reports, Notifications, Dashboard, Widgets, Menu, Tags, Reactions, Entityrelations, Audit, Read |
| **Canvas Variants** (14 + base) | Canvas (base), Cpcanvas, Dbmcanvas, Eacanvas, Emcanvas, Goalcanvas, Insightscanvas, Lbmcanvas, Leancanvas, Minempathycanvas, Obmcanvas, Retroscanvas, Riskscanvas, Sbcanvas, Smcanvas, Sqcanvas, Swotcanvas, Valuecanvas |
| **System** | Api, Auth, Cron, CsvImport, Connector, Environment, Errors, Install, Ldap, Modulemanager, Oidc, Plugins, Queue, Setting, Strategy, TwoFA |
| **Backend-only** (no UI) | Audit, Entityrelations, Ldap, Reactions, Read, Tags, Queue |
| **Other** | Clients, Gamecenter, Help |
