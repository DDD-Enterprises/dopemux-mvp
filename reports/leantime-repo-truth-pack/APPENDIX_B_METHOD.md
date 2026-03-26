# Appendix B: Methodology

How the Leantime truth pack was produced. Every claim traces to a file read or command output.

---

## 1. Search Strategy

### Glob Patterns Used for File Discovery

```
app/Domain/*/Services/*.php          # All domain services
app/Domain/*/Models/*.php            # All domain models
app/Domain/*/Controllers/*.php       # All domain controllers
app/Domain/*/Hxcontrollers/*.php     # All HTMX controllers
app/Domain/*/Repositories/*.php      # All repositories
app/Domain/*/Htmx/*.php             # HTMX event enums
app/Domain/*/register.php           # Event listener registrations
app/Domain/*/routes.php             # Laravel route definitions
app/Domain/Api/Controllers/*.php    # Legacy REST API controllers
app/Command/*.php                   # CLI commands
app/Core/Events/*.php               # Event system
app/Core/Auth/*.php                  # Auth guards and providers
app/Core/Configuration/*.php        # Config classes
app/Core/Http/*.php                  # HTTP kernel, request types
app/Core/Plugins/*.php              # Plugin infrastructure
app/Core/UI/*.php                    # Template and theme
app/Views/**/*.php                   # Shared view files
database/**/*.php                    # Database (empty — schema in SchemaBuilder)
config/*                             # Config files (sample.env)
.dev/*                               # Docker and test infrastructure
```

### Grep Patterns Used for Code Analysis

```
"class.*Controller"                  # Controller class discovery (in Api/Controllers)
"php-mcp"                           # MCP package references (in composer.json)
"rpc|jsonrpc|method|dispatch"        # JSON-RPC routing logic (in Jsonrpc.php)
"status"                            # Status codes and transitions (in Tickets/Repositories)
"state"                             # State handling (in Projects/Repositories)
"role|permission"                   # Role definitions and checks (in Auth domain)
"dispatch_event|dispatch_filter"    # Event system usage (codebase-wide)
"zp_"                               # Database table references (in repositories)
"LEAN_*"                            # Environment variables (in config/sample.env)
"mcp"                               # MCP references (codebase-wide, excluding vendor/node_modules)
"canvasTypes"                       # Canvas variant definitions (in canvas repositories)
"kind"                              # Timesheet kind/type codes (in Timesheets service)
"CANVAS_NAME"                       # Canvas name constants (in canvas controllers)
```

### How Routes/Controllers/Services Were Located

Leantime uses a **domain directory convention**: each domain module lives in `app/Domain/{ModuleName}/` with standardized subdirectories (`Controllers/`, `Services/`, `Repositories/`, etc.). Discovery was performed by:

1. Listing all directories under `app/Domain/` (56 domains found)
2. Globbing each domain's standardized subdirectories
3. Reading the Frontcontroller (`app/Core/Controller/Frontcontroller.php`) for URL-to-class mapping convention
4. Reading the RouteLoader (`app/Core/Routing/RouteLoader.php`) for Laravel route file discovery
5. Reading `app/Core/Http/HttpKernel.php` for the middleware stack order

---

## 2. Schema Derivation

### Table Schema Source

Leantime does **not** use Laravel migrations. All database tables are defined programmatically in:

**`app/Domain/Install/Services/SchemaBuilder.php`**

This file contains all `Schema::create()` calls that define every table. It is the canonical and sole source of database schema truth. The file was read in full to extract:
- All table names (with `zp_` prefix)
- All column definitions (name, type, nullable, defaults)
- All indexes and foreign key references
- Table relationships (inferred from column naming: `projectId`, `ticketId`, etc.)

A legacy SQL-based schema also exists in `app/Domain/Install/Repositories/Install.php` but SchemaBuilder is the authoritative source.

### Entity Field Lists

Model properties were read from `app/Domain/*/Models/*.php` files. Key observations:
- Models are simple data structures with public properties
- No ORM annotations or Eloquent models — plain PHP classes
- Properties typically use `mixed` or `string|null` types
- Some use `#[DbColumn('name')]` attributes for column mapping

### Status Codes, Type Definitions, Query Patterns

Extracted from repository files, particularly:
- **Ticket statuses**: `app/Domain/Tickets/Repositories/Tickets.php` → `getStateLabels()` (6 statuses: NEW, BLOCKED, IN PROGRESS, WAITING FOR APPROVAL, DONE, ARCHIVED)
- **Ticket types**: Same file → `getTicketTypes()` (Task, Story, Bug, Defect, Subtask)
- **Ticket priorities**: Same file → `getPriorityLabels()` (Low, Medium, High, Critical)
- **Effort sizes**: Same file → `getEffortLabels()` (XXS through XXL)
- **Timesheet kinds**: `app/Domain/Timesheets/Repositories/Timesheets.php` → `getKinds()` (GENERAL, PROJECTMANAGEMENT, MEETINGS, DEV, DESIGN, TESTING, BUGFIXING)
- **Project states**: `app/Domain/Projects/Repositories/Projects.php` → state column values

---

## 3. Workflow Identification

### Status Change Logic

Service methods were traced for status transition logic by:
1. Reading `app/Domain/Tickets/Services/Tickets.php` for `updateTicket()`, `patchTicket()` methods
2. Searching for guard clauses, validation, or state machine patterns
3. Examining pre/post-update event dispatches

**Key finding**: Leantime has **no workflow engine** and **no state machine**. Status transitions are unrestricted — any status can transition to any other status. This was confirmed through:
- Absence of transition validation in service methods
- No state machine library in `composer.json`
- No transition tables in SchemaBuilder
- The `updateTicket()` method accepts any status value without validation

### Validation Gates

Role-based access was traced through:
- `app/Core/Middleware/AuthCheck.php` — authentication middleware
- `app/Domain/Auth/Models/Roles.php` — role hierarchy definitions
- Service methods checking `$_SESSION['userdata']['role']` or using auth guards

### Negative Evidence (Workflow Engine Absence)

Confirmed by searching for:
- No `StateMachine`, `Workflow`, or `Transition` classes
- No `symfony/workflow` or similar package in `composer.json`
- No transition validation arrays in any service
- No workflow configuration files

---

## 4. Plugin Seam Identification

### Registration API

Read `app/Domain/Plugins/Services/Registration.php` for the fluent plugin registration API:
```php
$registration = new Registration('MyPlugin');
$registration->registerMiddleware([...]);
$registration->registerLanguageFiles([...]);
$registration->addMenuItem([...], 'project', ['main', 'submenu-key']);
$registration->addCss(['app.css']);
$registration->addHeaderJs(['vendor.js']);
$registration->addFooterJs(['app.js']);
```

### Event/Filter Listeners

All 8 `register.php` files were cataloged:
- `app/Domain/Auth/register.php`
- `app/Domain/CsvImport/register.php`
- `app/Domain/Help/register.php`
- `app/Domain/Install/register.php`
- `app/Domain/Notifications/register.php`
- `app/Domain/Plugins/register.php`
- `app/Domain/Queue/register.php`
- `app/Domain/Reports/register.php`

Each was read to identify event names, filter hooks, and cron registrations.

### Plugin Loading Sequence

Traced through:
1. `app/Core/Events/EventDispatcher.php` → `discoverListeners()` scans `app/Domain/*/register.php` at boot
2. `app/Core/Http/HttpKernel.php` → `LoadPlugins` middleware fires event for user plugin loading
3. `app/Core/Plugins/Plugins.php` → Plugin lifecycle management
4. `app/Core/Routing/RouteLoader.php` → Plugin route file loading

---

## 5. PM-Plane Mapping

### Entity Classification

Each entity was classified based on data characteristics:

| Classification | Criteria | Examples |
|---|---|---|
| **Operational** | Core work items, high-write frequency, status-tracked | Tickets, Sprints, Timesheets |
| **Contextual** | Structural/organizational data, moderate write frequency | Projects, Clients, Users |
| **Strategic** | Planning and analysis data, lower frequency | Canvas items, Goals, Strategy boards |
| **Reporting** | Derived/aggregated data, read-heavy | Reports, Audit, Dashboard |

### Write-Safety Assessment

Assessed from service method signatures:
- Methods accepting arrays of mixed data → higher normalization risk
- Methods with explicit type parameters → safer for integration
- Methods dispatching events → provide hook points for sync validation

### Normalization Needs

Determined from field content types found in models and repositories:
- **HTML fields**: `description`, `acceptanceCriteria`, `articleBody` → require sanitization
- **Serialized PHP**: `projectsettings.*.ticketlabels` in `zp_settings` → require deserialization
- **JSON fields**: Widget grid positions, integration configs → require JSON parsing
- **Free-text**: Comments, tags → require encoding considerations

---

## 6. Drift Detection

### CLAUDE.md vs Actual Code

Claims in `CLAUDE.md` were compared against actual codebase state:

| Claim | Verification Method | Result |
|---|---|---|
| "Current version: 3.6.2" | Read `app/Core/Configuration/AppSettings.php` | **Drift**: Actual is 3.3.2 |
| "56 domain modules" | `ls -d app/Domain/*/` count | Confirmed |
| "~198 .tpl.php files" | `find app/ -name "*.tpl.php" | wc -l` | Verified within range |
| "~91 .blade.php files" | `find app/Domain/ -name "*.blade.php" | wc -l` | Verified within range |
| "Bootstrap 2.x" | Read `public/assets/css/libs/bootstrap.css` header | Confirmed (v2.3.2) |
| "TinyMCE 5.10.9" | Searched for TinyMCE references | **Drift**: Replaced by Tiptap editor |
| "Only one class-based event" | Grep for `extends Event` in app/ | Confirmed (`FileUploaded.php`) |

### README.md vs Implementation

- Feature claims cross-checked against controller/service existence
- Dependency versions verified against `composer.json` and `package.json`

### Package Dependency Cross-Check

`composer.json` and `package.json` dependencies compared against CLAUDE.md technology claims to identify:
- Installed but unused packages (Stripe, Crisp, Sabre/DAV, Qdrant, Neuron AI)
- Technology replacements not reflected in docs (TinyMCE → Tiptap)
- Version discrepancies

---

## 7. Tools Used

### File Exploration
- **glob**: Pattern-based file discovery across domain directories
- **grep** (ripgrep): Content search with regex patterns, file type filtering
- **view**: Direct file reading with line numbers

### Code Analysis
- **Sub-agents**: Parallel exploration of domain modules for:
  - Reading all service methods to build callable surface manifest
  - Reading all model properties for domain model documentation
  - Reading all repository queries for data model documentation
  - Cross-referencing event dispatches for extension surface mapping

### Verification
- **bash**: File counts (`find ... | wc -l`), JSON validation (`python -m json.tool`), version checks
- **File existence checks**: Every path in the source index verified with `[ -e "$f" ]`
- **Cross-document consistency**: File references checked across all truth pack documents

### Quality Assurance
- JSON manifest validated for well-formedness
- File paths verified to exist on disk
- Status codes and enum values confirmed against source
- Event names verified against `DispatchesEvents` trait auto-generation logic
