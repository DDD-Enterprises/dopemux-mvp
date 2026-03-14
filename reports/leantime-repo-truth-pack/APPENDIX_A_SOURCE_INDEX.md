# Appendix A: Source Index

All source files referenced in this truth pack, organized by location. Every path was verified against the repository at extraction time. One path (`app/Domain/Projects/Controllers/SettingProject.php`) was referenced in ARCHITECTURE_AND_INTENDED_USES.md but does not exist — the correct file is `EditProject.php`.

**Total unique files referenced: 236**

---

## Bootstrap & Entry Points

| File | Purpose | Referenced In |
|------|---------|---------------|
| `public/index.php` | Web entry point | ARCHITECTURE |
| `bootstrap/app.php` | Application bootstrap, kernel bindings | ARCHITECTURE, TRANSPORT |

## Core Framework (`app/Core/`)

### Configuration

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Configuration/DefaultConfig.php` | Default settings, `#[LaravelConfig]` attributes | REPO_IDENTITY, DOMAIN_MODEL, PM_PLANE, ARCHITECTURE, DATA_MODEL |
| `app/Core/Configuration/Environment.php` | Env-file and environment variable loading | REPO_IDENTITY, ARCHITECTURE |
| `app/Core/Configuration/AppSettings.php` | Version info (`appVersion`) | REPO_IDENTITY, DRIFT_REPORT, ARCHITECTURE |
| `app/Core/Configuration/laravelConfig.php` | All Laravel config (DB, cache, session, auth, etc.) | REPO_IDENTITY, ARCHITECTURE, DATA_MODEL, PM_PLANE |
| `app/Core/Bootstrap/LoadConfig.php` | Custom bootstrapper — creates Environment instance | ARCHITECTURE, DATA_MODEL |

### HTTP & Routing

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Http/HttpKernel.php` | Middleware stack, routing pipeline | REPO_IDENTITY, ARCHITECTURE, WORKFLOW, EXTENSION |
| `app/Core/Http/IncomingRequest.php` | Request type detection, API endpoint list (`/mcp`, `/api/jsonrpc`) | ARCHITECTURE, DRIFT_REPORT |
| `app/Core/Controller/Frontcontroller.php` | Legacy convention-based URL-to-class routing | REPO_IDENTITY, ARCHITECTURE, EXTENSION |
| `app/Core/Controller/HtmxController.php` | Base class for HTMX partial controllers | INSPECTED_FILES |
| `app/Core/Routing/RouteLoader.php` | Laravel route file discovery and loading | ARCHITECTURE, EXTENSION |
| `app/Core/Middleware/AuthCheck.php` | Authentication guard, 2FA check, public-route bypass | ARCHITECTURE, WORKFLOW |
| `app/Core/Middleware/RequestRateLimiter.php` | Rate limits: login 20/min, API 100/min, general 10000/min | ARCHITECTURE |
| `app/Core/Middleware/StartSession.php` | Session init with locking and exponential backoff | ARCHITECTURE |

### Events

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Events/EventDispatcher.php` | Event/filter dispatch, listener registration, pattern matching | REPO_IDENTITY, DOMAIN_MODEL, ARCHITECTURE, EXTENSION, KNOWLEDGE |
| `app/Core/Events/DispatchesEvents.php` | Trait mixed into services/repos for `dispatch_event`/`dispatch_filter` | DOMAIN_MODEL, ARCHITECTURE, EXTENSION |

### Database & Data Layer

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Db/Repository.php` | Base repository with `dbcall()` wrapper | INSPECTED_FILES |
| `app/Core/Database/DatabaseManager.php` | Wraps Laravel DatabaseManager | ARCHITECTURE |

### Auth

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Auth/AuthenticationServiceProvider.php` | Auth guard registration (leantime, sanctum, jsonRpc) | INSPECTED_FILES |

### Plugins

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Plugins/Plugins.php` | Plugin infrastructure, lifecycle management | EXTENSION, INSPECTED_FILES |
| `app/Core/Plugins/PluginManager.php` | Plugin manager service | ARCHITECTURE |

### Files & UI

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Files/FileManager.php` | File management abstraction (S3/local) | ARCHITECTURE, DATA_MODEL |
| `app/Core/UI/Template.php` | Template engine: `display()`, `displayPartial()`, `displayFragment()` | INSPECTED_FILES |
| `app/Core/UI/Theme.php` | Theme system, CSS variable injection | ARCHITECTURE, INSPECTED_FILES |

### Cache & Sessions

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Cache/CacheServiceProvider.php` | Cache provider (file or Redis) | ARCHITECTURE |
| `app/Core/Sessions/SessionServiceProvider.php` | Session provider configuration | ARCHITECTURE |

### Console

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Console/ConsoleKernel.php` | Console kernel, Artisan command registration | ARCHITECTURE |

### Support

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Core/Support/EntityRelationshipEnum.php` | Enum for entity relationship types | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW, EXTENSION |

---

## Domain: Api

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Api/Controllers/Jsonrpc.php` | JSON-RPC 2.0 router — reflection-based method dispatch | REPO_IDENTITY, CALLABLE, ARCHITECTURE, EXTENSION, KNOWLEDGE |
| `app/Domain/Api/Services/Api.php` | API key management service | CALLABLE, ARCHITECTURE |
| `app/Domain/Api/Repositories/Api.php` | API key storage | INSPECTED_FILES |
| `app/Domain/Api/Controllers/ApiKey.php` | API key CRUD controller | CALLABLE, ARCHITECTURE |
| `app/Domain/Api/Controllers/NewApiKey.php` | API key creation controller | CALLABLE |
| `app/Domain/Api/Controllers/DelAPIKey.php` | API key deletion controller | CALLABLE |
| `app/Domain/Api/Controllers/Tickets.php` | Legacy REST ticket controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Projects.php` | Legacy REST project controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Users.php` | Legacy REST user controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Calendar.php` | Legacy REST calendar controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Canvas.php` | Legacy REST canvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Files.php` | Legacy REST files controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/I18n.php` | Internationalization API | CALLABLE |
| `app/Domain/Api/Controllers/Ideas.php` | Legacy REST ideas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Ideation.php` | Legacy REST ideation controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Notifications.php` | Legacy REST notification controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Reactions.php` | Legacy REST reactions controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Sessions.php` | Session management API | CALLABLE |
| `app/Domain/Api/Controllers/Setting.php` | Settings API controller | CALLABLE |
| `app/Domain/Api/Controllers/StaticAsset.php` | Static asset serving controller | CALLABLE |
| `app/Domain/Api/Controllers/Submenu.php` | Submenu API controller | CALLABLE |
| `app/Domain/Api/Controllers/Tags.php` | Tags API controller | CALLABLE |
| `app/Domain/Api/Controllers/Timer.php` | Timer/stopwatch API controller | CALLABLE |
| `app/Domain/Api/Controllers/NEWcanvas.php` | Legacy REST new-canvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Cpcanvas.php` | Legacy REST cpcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Dbmcanvas.php` | Legacy REST dbmcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Eacanvas.php` | Legacy REST eacanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Emcanvas.php` | Legacy REST emcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Goalcanvas.php` | Legacy REST goalcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Insightscanvas.php` | Legacy REST insightscanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Lbmcanvas.php` | Legacy REST lbmcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Leancanvas.php` | Legacy REST leancanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Obmcanvas.php` | Legacy REST obmcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Retroscanvas.php` | Legacy REST retroscanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Riskscanvas.php` | Legacy REST riskscanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Sbcanvas.php` | Legacy REST sbcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Smcanvas.php` | Legacy REST smcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Sqcanvas.php` | Legacy REST sqcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Swotcanvas.php` | Legacy REST swotcanvas controller (deprecated) | CALLABLE |
| `app/Domain/Api/Controllers/Valuecanvas.php` | Legacy REST valuecanvas controller (deprecated) | CALLABLE |

---

## Domain: Auth

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Auth/Models/Roles.php` | Role definitions (owner, admin, manager, editor, commenter) | REPO_IDENTITY, DOMAIN_MODEL, WORKFLOW, PM_PLANE, KNOWLEDGE |
| `app/Domain/Auth/Models/CurrentUser.php` | Current user session model | DOMAIN_MODEL, WORKFLOW, PM_PLANE, KNOWLEDGE |
| `app/Domain/Auth/Services/Auth.php` | Authentication service (login, logout, 2FA) | CALLABLE, WORKFLOW, ARCHITECTURE |
| `app/Domain/Auth/Services/AccessToken.php` | Token management (API keys, Sanctum tokens) | CALLABLE, ARCHITECTURE |
| `app/Domain/Auth/Services/AuthUser.php` | User auth service | CALLABLE |
| `app/Domain/Auth/Guards/WebGuard.php` | Web session guard | INSPECTED_FILES |
| `app/Domain/Auth/Guards/ApiGuard.php` | API authentication guard | INSPECTED_FILES |
| `app/Domain/Auth/register.php` | Event listeners for auth lifecycle | CALLABLE, INSPECTED_FILES |

---

## Domain: Tickets

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Tickets/Models/Tickets.php` | Ticket entity model (50+ properties) | DOMAIN_MODEL, PM_PLANE, WORKFLOW, KNOWLEDGE, DRIFT_REPORT |
| `app/Domain/Tickets/Models/TicketDesignTokens.php` | Design tokens for ticket UI | DRIFT_REPORT, INSPECTED_FILES |
| `app/Domain/Tickets/Repositories/Tickets.php` | Ticket queries, statuses, types, priorities, effort | DOMAIN_MODEL, PM_PLANE, WORKFLOW, DATA_MODEL, KNOWLEDGE, CALLABLE, ARCHITECTURE, INSPECTED_FILES |
| `app/Domain/Tickets/Services/Tickets.php` | Ticket business logic, status transitions, notifications | CALLABLE, DOMAIN_MODEL, WORKFLOW, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Tickets/Repositories/TicketHistory.php` | Ticket change history tracking | KNOWLEDGE |
| `app/Domain/Tickets/Htmx/HtmxTicketEvents.php` | HTMX event enum for ticket updates | DRIFT_REPORT, INSPECTED_FILES |
| `app/Domain/Tickets/Hxcontrollers/Milestones.php` | HTMX milestone partial controller | KNOWLEDGE, ARCHITECTURE |
| `app/Domain/Tickets/Hxcontrollers/Subtasks.php` | HTMX subtask partial controller | KNOWLEDGE, ARCHITECTURE |
| `app/Domain/Tickets/Controllers/ShowKanban.php` | Kanban board view | ARCHITECTURE |
| `app/Domain/Tickets/Controllers/ShowList.php` | List view | ARCHITECTURE |
| `app/Domain/Tickets/Controllers/Roadmap.php` | Roadmap/Gantt view | ARCHITECTURE |

---

## Domain: Projects

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Projects/Models/Project.php` | Project entity model | DOMAIN_MODEL, PM_PLANE, WORKFLOW, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Projects/Repositories/Projects.php` | Project queries, type/state handling | DOMAIN_MODEL, PM_PLANE, WORKFLOW, KNOWLEDGE, CALLABLE, INSPECTED_FILES |
| `app/Domain/Projects/Services/Projects.php` | Project lifecycle, user assignment, duplication | CALLABLE, DOMAIN_MODEL, WORKFLOW, PM_PLANE, KNOWLEDGE, ARCHITECTURE, INSPECTED_FILES, TRANSPORT |
| `app/Domain/Projects/Controllers/ShowProject.php` | Project detail view | ARCHITECTURE |
| `app/Domain/Projects/Controllers/DelProject.php` | Project deletion | ARCHITECTURE |

> **Note**: `app/Domain/Projects/Controllers/SettingProject.php` is referenced in ARCHITECTURE but does not exist. The actual file is `app/Domain/Projects/Controllers/EditProject.php`.

---

## Domain: Sprints

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Sprints/Models/Sprints.php` | Sprint entity model | DOMAIN_MODEL, PM_PLANE, WORKFLOW, INSPECTED_FILES |
| `app/Domain/Sprints/Repositories/Sprints.php` | Sprint queries | DOMAIN_MODEL, PM_PLANE, WORKFLOW, KNOWLEDGE |
| `app/Domain/Sprints/Services/Sprints.php` | Sprint lifecycle, ticket assignment | CALLABLE, DOMAIN_MODEL, WORKFLOW, PM_PLANE, INSPECTED_FILES |
| `app/Domain/Sprints/Controllers/DelSprint.php` | Sprint deletion | WORKFLOW |

---

## Domain: Users

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Users/Services/Users.php` | User CRUD, role management, invitation | CALLABLE, DOMAIN_MODEL, WORKFLOW, PM_PLANE, INSPECTED_FILES |
| `app/Domain/Users/Repositories/Users.php` | User queries | DOMAIN_MODEL, PM_PLANE, WORKFLOW, INSPECTED_FILES |

---

## Domain: Timesheets

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Timesheets/Services/Timesheets.php` | Timesheet CRUD, punch-clock (in/out), kinds | CALLABLE, DOMAIN_MODEL, WORKFLOW, PM_PLANE, KNOWLEDGE, DATA_MODEL, ARCHITECTURE |
| `app/Domain/Timesheets/Repositories/Timesheets.php` | Timesheet queries, kind types | DOMAIN_MODEL, PM_PLANE, WORKFLOW, KNOWLEDGE, DATA_MODEL, CALLABLE, INSPECTED_FILES |
| `app/Domain/Timesheets/Hxcontrollers/Stopwatch.php` | HTMX stopwatch/timer controller | KNOWLEDGE |

---

## Domain: Canvas (Base + 17 Variants)

### Base

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Canvas/Services/Canvas.php` | Generic canvas service (inherited by variants) | CALLABLE, DOMAIN_MODEL, KNOWLEDGE, PM_PLANE, INSPECTED_FILES |
| `app/Domain/Canvas/Repositories/Canvas.php` | Generic canvas repository (items, boards) | DOMAIN_MODEL, KNOWLEDGE, PM_PLANE, INSPECTED_FILES, ARCHITECTURE |
| `app/Domain/Canvas/Controllers/Export.php` | Canvas export controller | KNOWLEDGE |

### Variants (each extends base with `CANVAS_NAME` override)

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Goalcanvas/Repositories/Goalcanvas.php` | Goal canvas — fully modernized variant | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES, ARCHITECTURE |
| `app/Domain/Goalcanvas/Services/Goalcanvas.php` | Goal canvas service (own service, not inherited) | CALLABLE, DOMAIN_MODEL, KNOWLEDGE, PM_PLANE, ARCHITECTURE, INSPECTED_FILES |
| `app/Domain/Retroscanvas/Repositories/Retroscanvas.php` | Retrospective canvas | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES, ARCHITECTURE |
| `app/Domain/Retroscanvas/Templates/showCanvas.tpl.php` | Retro canvas legacy template | KNOWLEDGE |
| `app/Domain/Riskscanvas/Repositories/Riskscanvas.php` | Risk canvas | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES, ARCHITECTURE |
| `app/Domain/Riskscanvas/Templates/showCanvas.tpl.php` | Risk canvas legacy template | KNOWLEDGE |
| `app/Domain/Leancanvas/Repositories/Leancanvas.php` | Lean canvas | DOMAIN_MODEL, INSPECTED_FILES |
| `app/Domain/Swotcanvas/Repositories/Swotcanvas.php` | SWOT canvas | DOMAIN_MODEL, PM_PLANE |
| `app/Domain/Cpcanvas/Repositories/Cpcanvas.php` | Company profile canvas | PM_PLANE |
| `app/Domain/Dbmcanvas/Repositories/Dbmcanvas.php` | Decision board canvas | PM_PLANE |
| `app/Domain/Eacanvas/Repositories/Eacanvas.php` | Empathy assumption canvas | PM_PLANE |
| `app/Domain/Emcanvas/Repositories/Emcanvas.php` | Empathy map canvas | PM_PLANE |
| `app/Domain/Insightscanvas/Repositories/Insightscanvas.php` | Insights canvas | PM_PLANE |
| `app/Domain/Lbmcanvas/Repositories/Lbmcanvas.php` | Lean business model canvas | PM_PLANE |
| `app/Domain/Minempathycanvas/Repositories/Minempathycanvas.php` | Minimal empathy canvas | PM_PLANE |
| `app/Domain/Obmcanvas/Repositories/Obmcanvas.php` | Operating business model canvas | PM_PLANE |
| `app/Domain/Sbcanvas/Repositories/Sbcanvas.php` | Strategy board canvas | PM_PLANE |
| `app/Domain/Smcanvas/Repositories/Smcanvas.php` | Strategy map canvas | PM_PLANE |
| `app/Domain/Sqcanvas/Repositories/Sqcanvas.php` | Strategy questions canvas | PM_PLANE |
| `app/Domain/Valuecanvas/Repositories/Valuecanvas.php` | Value proposition canvas | PM_PLANE |

---

## Domain: Comments

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Comments/Services/Comments.php` | Comment CRUD, threaded replies, mentions | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Comments/Repositories/Comments.php` | Comment queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW |
| `app/Domain/Comments/Templates/submodules/generalComment.sub.php` | Comment display submodule | KNOWLEDGE |

---

## Domain: Files

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Files/Services/Files.php` | File upload, storage, access control | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, DATA_MODEL, INSPECTED_FILES |
| `app/Domain/Files/Repositories/Files.php` | File queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Files/Events/FileUploaded.php` | Class-based event (only one in codebase) | DRIFT_REPORT, EXTENSION, DOMAIN_MODEL, INSPECTED_FILES |
| `app/Domain/Files/routes.php` | Laravel route definitions for file operations | DRIFT_REPORT, INSPECTED_FILES |

---

## Domain: Wiki

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Wiki/Models/Wiki.php` | Wiki board model | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES, ARCHITECTURE |
| `app/Domain/Wiki/Models/Article.php` | Article model | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, ARCHITECTURE |
| `app/Domain/Wiki/Models/Template.php` | Wiki template model | DOMAIN_MODEL, PM_PLANE, ARCHITECTURE |
| `app/Domain/Wiki/Services/Wiki.php` | Wiki CRUD, article management, milestones | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Wiki/Repositories/Wiki.php` | Wiki queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Wiki/Hxcontrollers/ArticleActivity.php` | HTMX article activity partial | KNOWLEDGE |
| `app/Domain/Wiki/Hxcontrollers/ArticleContent.php` | HTMX article content partial | KNOWLEDGE |

---

## Domain: Calendar

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Calendar/Services/Calendar.php` | Calendar events, iCal export | CALLABLE, DOMAIN_MODEL, KNOWLEDGE |
| `app/Domain/Calendar/Repositories/Calendar.php` | Calendar queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |
| `app/Domain/Calendar/Controllers/Export.php` | Calendar export controller | KNOWLEDGE |
| `app/Domain/Calendar/Controllers/Ical.php` | iCal feed controller | KNOWLEDGE |

---

## Domain: Notifications

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Notifications/Models/Notification.php` | Notification entity model | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW, INSPECTED_FILES |
| `app/Domain/Notifications/Services/Notifications.php` | Notification dispatch, channel routing | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Notifications/Repositories/Notifications.php` | Notification queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW |
| `app/Domain/Notifications/Services/Messengers.php` | Messenger integrations (Slack, Zulip, Mattermost, Discord) | CALLABLE |
| `app/Domain/Notifications/Services/News.php` | RSS feed service (Leantime blog) | CALLABLE, KNOWLEDGE |
| `app/Domain/Notifications/register.php` | Notification event listeners | CALLABLE, INSPECTED_FILES |

---

## Domain: Reports

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Reports/Services/Reports.php` | Report generation, cron-based statistics | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, ARCHITECTURE, INSPECTED_FILES, TRANSPORT |
| `app/Domain/Reports/Repositories/Reports.php` | Report queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW |
| `app/Domain/Reports/Models/Reports.php` | Report model | DOMAIN_MODEL, PM_PLANE |
| `app/Domain/Reports/register.php` | Cron job registration for report generation | CALLABLE, ARCHITECTURE, INSPECTED_FILES, TRANSPORT |

---

## Domain: Plugins

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Plugins/Services/Plugins.php` | Plugin lifecycle (discover, install, enable, disable, remove) | CALLABLE, EXTENSION, ARCHITECTURE, WORKFLOW, PM_PLANE, INSPECTED_FILES, TRANSPORT |
| `app/Domain/Plugins/Services/Registration.php` | Fluent API for plugin registration | CALLABLE, EXTENSION, ARCHITECTURE, PM_PLANE, INSPECTED_FILES |
| `app/Domain/Plugins/Services/Premium.php` | Premium/license key validation | CALLABLE |
| `app/Domain/Plugins/Repositories/Plugins.php` | Plugin queries | EXTENSION, PM_PLANE, WORKFLOW |
| `app/Domain/Plugins/Models/InstalledPlugin.php` | Plugin entity model | EXTENSION, INSPECTED_FILES |
| `app/Domain/Plugins/register.php` | Plugin event listeners, license validation cron | CALLABLE, EXTENSION, INSPECTED_FILES |

---

## Domain: Install

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Install/Services/SchemaBuilder.php` | **Canonical database schema** — all table DDL | REPO_IDENTITY, DOMAIN_MODEL (×2), CALLABLE, WORKFLOW, KNOWLEDGE, PM_PLANE, ARCHITECTURE, DATA_MODEL |
| `app/Domain/Install/Services/Install.php` | Installation wizard service | CALLABLE, ARCHITECTURE, INSPECTED_FILES |
| `app/Domain/Install/Repositories/Install.php` | Legacy SQL installation | ARCHITECTURE, WORKFLOW, INSPECTED_FILES |
| `app/Domain/Install/register.php` | Install event listeners | CALLABLE, INSPECTED_FILES |

---

## Domain: Ideas

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Ideas/Services/Ideas.php` | Idea CRUD, voting/categorization | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Ideas/Repositories/Ideas.php` | Idea queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |

---

## Domain: Connector

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Connector/Services/Connector.php` | Integration connector service | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Connector/Services/Integrations.php` | Integration management service | CALLABLE |
| `app/Domain/Connector/Services/Providers.php` | Provider management service | CALLABLE |
| `app/Domain/Connector/Repositories/Integrations.php` | Integration queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |
| `app/Domain/Connector/Models/Integration.php` | Integration model | DOMAIN_MODEL |

---

## Domain: Entityrelations

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Entityrelations/Services/Entityrelations.php` | Entity relationship management | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Entityrelations/Repositories/Entityrelations.php` | Entity relationship queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |

---

## Domain: Reactions

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Reactions/Models/Reactions.php` | Reaction model (emoji reactions) | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Reactions/Services/Reactions.php` | Reaction CRUD | CALLABLE, DOMAIN_MODEL, KNOWLEDGE |
| `app/Domain/Reactions/Repositories/Reactions.php` | Reaction queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |

---

## Domain: Clients

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Clients/Services/Clients.php` | Client/organization CRUD | CALLABLE, DOMAIN_MODEL, KNOWLEDGE |
| `app/Domain/Clients/Repositories/Clients.php` | Client queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |

---

## Domain: Queue

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Queue/Services/Queue.php` | Job queue management | CALLABLE, DOMAIN_MODEL, PM_PLANE, INSPECTED_FILES |
| `app/Domain/Queue/Repositories/Queue.php` | Queue storage | DOMAIN_MODEL, PM_PLANE, TRANSPORT |
| `app/Domain/Queue/Workers/Workers.php` | Queue worker processes | DOMAIN_MODEL, PM_PLANE, TRANSPORT |
| `app/Domain/Queue/register.php` | Queue cron registration | CALLABLE, ARCHITECTURE, TRANSPORT, INSPECTED_FILES |

---

## Domain: Setting

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Setting/Services/Setting.php` | System settings read/write (key-value in `zp_settings`) | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, ARCHITECTURE, INSPECTED_FILES |
| `app/Domain/Setting/Repositories/Setting.php` | Settings queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |
| `app/Domain/Setting/Services/SettingCache.php` | Settings cache layer | CALLABLE, DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |

---

## Domain: Widgets

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Widgets/Services/Widgets.php` | Dashboard widget management | CALLABLE, DOMAIN_MODEL |
| `app/Domain/Widgets/Models/Widget.php` | Widget model | DOMAIN_MODEL |

---

## Domain: Other Domains

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Strategy/Controllers/ShowBoards.php` | Strategy board display | ARCHITECTURE, KNOWLEDGE, INSPECTED_FILES |
| `app/Domain/Strategy/Templates/showBoards.tpl.php` | Strategy board template | KNOWLEDGE |
| `app/Domain/Dashboard/Controllers/Home.php` | Dashboard home controller | ARCHITECTURE |
| `app/Domain/Dashboard/Controllers/Show.php` | Dashboard show controller | ARCHITECTURE |
| `app/Domain/Dashboard/Repositories/Dashboard.php` | Dashboard queries | ARCHITECTURE |
| `app/Domain/Dashboard/Templates/home.blade.php` | Dashboard Blade template | ARCHITECTURE |
| `app/Domain/Audit/Repositories/Audit.php` | Audit trail queries | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE, WORKFLOW |
| `app/Domain/Read/Repositories/Read.php` | Read-receipt tracking | DOMAIN_MODEL, PM_PLANE, KNOWLEDGE |
| `app/Domain/Tags/Services/Tags.php` | Tag management | CALLABLE |
| `app/Domain/Oidc/Services/Oidc.php` | OpenID Connect authentication | CALLABLE, INSPECTED_FILES |
| `app/Domain/Ldap/Services/Ldap.php` | LDAP authentication | CALLABLE |
| `app/Domain/Cron/Services/Cron.php` | Cron scheduler service | CALLABLE, TRANSPORT |
| `app/Domain/Cron/Controllers/Run.php` | Cron execution endpoint | TRANSPORT |
| `app/Domain/CsvImport/Services/CsvImport.php` | CSV import service | CALLABLE |
| `app/Domain/CsvImport/Controllers/Upload.php` | CSV upload controller | CALLABLE |
| `app/Domain/CsvImport/register.php` | CSV import event listeners | CALLABLE |
| `app/Domain/Help/Services/Helper.php` | Help/onboarding service | CALLABLE |
| `app/Domain/Help/register.php` | Help event listeners | CALLABLE |
| `app/Domain/Menu/Services/Menu.php` | Menu structure service | CALLABLE |
| `app/Domain/Menu/Repositories/Menu.php` | Menu queries and menu type definitions | ARCHITECTURE |
| `app/Domain/Modulemanager/Services/Modulemanager.php` | Module management service | CALLABLE |

---

## Domain: register.php Files (Event Listeners)

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Domain/Auth/register.php` | Auth lifecycle event listeners | CALLABLE, INSPECTED_FILES |
| `app/Domain/CsvImport/register.php` | CSV import listeners | CALLABLE |
| `app/Domain/Help/register.php` | Help/onboarding listeners | CALLABLE |
| `app/Domain/Install/register.php` | Install listeners | CALLABLE, INSPECTED_FILES |
| `app/Domain/Notifications/register.php` | Notification listeners | CALLABLE, INSPECTED_FILES |
| `app/Domain/Plugins/register.php` | Plugin lifecycle listeners, license validation cron | CALLABLE, EXTENSION, INSPECTED_FILES |
| `app/Domain/Queue/register.php` | Queue cron registration | CALLABLE, ARCHITECTURE, TRANSPORT, INSPECTED_FILES |
| `app/Domain/Reports/register.php` | Report generation cron | CALLABLE, ARCHITECTURE, INSPECTED_FILES, TRANSPORT |

---

## CLI Commands (`app/Command/`)

| File | Purpose | Referenced In |
|------|---------|---------------|
| `app/Command/AddUserCommand.php` | `user:add` — Create new user | CALLABLE |
| `app/Command/BackupDbCommand.php` | `db:backup` — Database backup | CALLABLE, TRANSPORT |
| `app/Command/MigrateCommand.php` | `system:update` — Run database migrations | CALLABLE, TRANSPORT |
| `app/Command/UpdateLeantime.php` | `update:leantime` — Full update procedure | CALLABLE |
| `app/Command/EnablePluginCommand.php` | `plugin:enable` — Enable a plugin | CALLABLE |
| `app/Command/DisablePluginCommand.php` | `plugin:disable` — Disable a plugin | CALLABLE |
| `app/Command/InstallPluginCommand.php` | `plugin:install` — Install from marketplace | CALLABLE |
| `app/Command/ListPluginCommand.php` | `plugin:list` — List installed plugins | CALLABLE |
| `app/Command/RemovePluginCommand.php` | `plugin:remove` — Remove a plugin | CALLABLE |
| `app/Command/SaveSettingCommand.php` | `setting:save` — Save a system setting | CALLABLE |
| `app/Command/TestEmailCommand.php` | `email:test` — Test email configuration | CALLABLE |
| `app/Command/ClearAll.php` | `cache:clear-all` — Clear all caches | CALLABLE |
| `app/Command/ClearLanguage.php` | `cache:clear-language` — Clear language cache | CALLABLE |
| `app/Command/CheckEventListeners.php` | `events:check` — Validate event listeners | CALLABLE |
| `app/Command/CheckTranslations.php` | `translations:check` — Validate translation files | CALLABLE |
| `app/Command/CleanupOrphanedFilesCommand.php` | `files:cleanup` — Remove orphaned files | CALLABLE |

---

## Configuration & Build

| File | Purpose | Referenced In |
|------|---------|---------------|
| `config/sample.env` | All `LEAN_*` environment variables | REPO_IDENTITY, DATA_MODEL, PM_PLANE, INSPECTED_FILES |
| `composer.json` | PHP dependencies | REPO_IDENTITY, DRIFT_REPORT |
| `package.json` | Frontend dependencies | REPO_IDENTITY |
| `webpack.mix.js` | Laravel Mix / Webpack build config | REPO_IDENTITY |
| `makefile` | Build targets (`build`, `test`, `package`, etc.) | TRANSPORT |

---

## DevOps & CI/CD

| File | Purpose | Referenced In |
|------|---------|---------------|
| `.dev/docker-compose.yaml` | Development Docker setup | TRANSPORT, INSPECTED_FILES |
| `.dev/docker-compose.tests.yaml` | Test Docker setup | TRANSPORT, INSPECTED_FILES |
| `.dev/test.env` | Test environment variables | TRANSPORT |
| `.docker/docker-compose.yml` | Production Docker Compose | TRANSPORT |
| `.github/FUNDING.yml` | GitHub Sponsors config | REPO_IDENTITY |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug report template | REPO_IDENTITY |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Feature request template | REPO_IDENTITY |
| `.github/changelogConfig.yml` | Changelog generation config | REPO_IDENTITY |
| `.github/release.yml` | Release automation | REPO_IDENTITY |

---

## Frontend Assets

| File | Purpose | Referenced In |
|------|---------|---------------|
| `public/assets/css/libs/bootstrap.css` | Bootstrap 2.x (legacy) | DRIFT_REPORT |
| `public/assets/js/libs/simpleGantt/frappe-gantt.js` | Custom Frappe Gantt implementation | ARCHITECTURE |

---

## Document Key

| Abbreviation | Full Document Name |
|---|---|
| REPO_IDENTITY | REPO_IDENTITY.md |
| DOMAIN_MODEL | LEANTIME_DOMAIN_MODEL.md (+ PART1, PART2) |
| CALLABLE | CALLABLE_SURFACE_MANIFEST.json |
| WORKFLOW | LEANTIME_WORKFLOW_AND_GATES.md |
| EXTENSION | LEANTIME_EXTENSION_SURFACES.md |
| KNOWLEDGE | LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md |
| PM_PLANE | LEANTIME_PM_PLANE_MAPPING.md |
| ARCHITECTURE | ARCHITECTURE_AND_INTENDED_USES.md |
| DATA_MODEL | DATA_MODEL.md |
| DRIFT_REPORT | DRIFT_REPORT.md |
| TRANSPORT | TRANSPORT_AND_RUNBOOK.md |
| INSPECTED_FILES | INSPECTED_FILES.txt |
