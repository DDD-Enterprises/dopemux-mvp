# Appendix C: Open Questions

Unresolved questions identified during truth pack extraction. Each was investigated; findings and resolution status are documented below.

---

## 1. AI Integration Extent

**Status: OPEN — dependencies installed, not integrated**

`composer.json` includes:
- `prism-php/prism: ^0.57.0`
- `inspector-apm/neuron-ai: 1.12.8`
- `hkulekci/qdrant: ^0.5.8`

**Evidence searched:**
- Grep for `use Prism\`, `use NeuronAI\`, `use Qdrant\` across `app/` — no matches
- Grep for `embedding`, `vector`, `llm` in service/business logic — no matches
- `Prism.highlightAll()` appears in ticket templates but this is the **JavaScript** syntax highlighting library (Prism.js), not the PHP package

**Assessment:** All three packages are installed as Composer dependencies but have zero usage in application code. No service providers, facades, or configuration references exist. These appear to be placeholder dependencies for a planned AI feature.

---

## 2. CalDAV/CardDAV Extent

**Status: PARTIALLY RESOLVED — iCal export active, CalDAV/CardDAV not implemented**

`composer.json` includes:
- `sabre/dav: ^4.7` — **not used**
- `spatie/icalendar-generator: ^2.6` — **actively used**
- `johngrogg/ics-parser: ^3` — **actively used**

**Evidence found:**
- `app/Domain/Calendar/Services/Calendar.php` (lines 19-21): Uses `Spatie\IcalendarGenerator` for iCal export
- `app/Domain/Calendar/Controllers/Ical.php`: Serves `.ics` files via HTTP
- `getIcalByHash()` method (lines 276-329): Creates full iCalendar output with events, descriptions, alerts
- `app/Domain/Calendar/Templates/connectCalendar.blade.php`: References "CalDAV, Google Calendar, etc." in UI but only iCal import is implemented natively
- No `use Sabre\` statements found anywhere in `app/`
- Plugin hook `@dispatchEvent('afterProviders')` in calendar template suggests CalDAV could be injected via plugin

**Assessment:** Sabre/DAV is an installed but unused dependency. iCalendar export/import is fully functional via Spatie and ICS-parser. CalDAV/CardDAV/WebDAV protocols are not implemented in core — may be intended for plugin use.

---

## 3. MCP Tool Registration

**Status: OPEN — infrastructure declared, service provider disabled**

`composer.json` includes:
- `php-mcp/server: dev-main as 3.1.1`
- `php-mcp/laravel: 3.0.0`

**Evidence found:**
- `app/Core/Http/IncomingRequest.php` (lines 45-50): `/mcp` listed in `$apiEndpoints` array
- `composer.json` (lines 201-205): `php-mcp/laravel` is explicitly in the `dont-discover` list, preventing auto-registration of the service provider
- No MCP controller exists in `app/Domain/Api/Controllers/`
- No MCP tool or resource class definitions found in `app/`
- No `mcp.php` config file found

**Assessment:** The MCP packages are installed and the `/mcp` endpoint is declared as an API endpoint (bypassing web middleware), but the Laravel service provider is explicitly disabled. No actual MCP tool/resource implementations exist. This is infrastructure setup for future MCP integration.

---

## 4. Custom Ticket Statuses

**Status: RESOLVED**

Custom ticket statuses are fully implemented with per-project configuration.

**Implementation:**
- **Read path**: `app/Domain/Tickets/Repositories/Tickets.php` → `getStateLabels($projectId)` (lines 120-183)
  - Checks cache: `Cache::has('projectsettings.'.$projectId.'.ticketlabels')`
  - Falls back to `zp_settings` table where `key = 'projectsettings.{projectId}.ticketlabels'`
  - Returns array keyed by status ID (0, 1, 2, 3, 4, -1) with `name`, `class`, `statusType`, `kanbanCol`, `sortKey`

- **Write path**: `app/Domain/Setting/Controllers/EditBoxLabel.php` (lines 97-112)
  - POST handler updates individual status name within the serialized array
  - Saves via `$this->settingsRepo->saveSetting('projectsettings.'.session('currentProject').'.ticketlabels', serialize($currentStateLabels))`
  - Clears cache on save

- **Default statuses** (when no custom labels set):
  ```
  3 → "New"        (statusType: NEW)
  1 → "Blocked"    (statusType: INPROGRESS)
  0 → "In Progress" (statusType: INPROGRESS)
  2 → "Waiting for Approval" (statusType: INPROGRESS)
  4 → "Done"       (statusType: DONE)
  -1 → "Archived"  (statusType: DONE)
  ```

- **Storage**: Serialized PHP array in `zp_settings.value` with key `projectsettings.{projectId}.ticketlabels`

---

## 5. Recurring Patterns Table

**Status: OPEN — schema exists, no business logic**

**Evidence found:**
- `app/Domain/Install/Services/SchemaBuilder.php` (lines 809-830): Table `zp_recurring_patterns` created with columns:
  - `id`, `entityId`, `module`, `type`, `trigger`, `interval` (default 1), `weekDays`, `monthDay`, `months`, `action` (default 'reset'), `lastProcessed`, `nextProcessingDate`, `enabled` (default 1)

**Evidence searched but not found:**
- No `RecurringPattern` model class in `app/`
- No `RecurringPatterns` repository or service
- No references to `zp_recurring_patterns` in any business logic
- No `recurring` references in cron registrations

**Assessment:** The table schema defines a recurrence engine capable of tracking entity-level recurring actions (reset, etc.) with configurable intervals, weekdays, and months. However, no application code reads from or writes to this table. This is database infrastructure for a planned feature.

---

## 6. Stripe Integration

**Status: RESOLVED — dependency only, not integrated**

`composer.json` includes `stripe/stripe-php: ^v17.3.0`.

**Evidence searched:**
- No `use Stripe\` statements in `app/`
- No payment processing controllers, services, or models
- No `LEAN_STRIPE_*` environment variables in `config/sample.env`
- No references to "payment", "subscription", "billing", or "charge" in service classes

**Assessment:** Stripe is available as a dependency but has no integration in the core application. It is likely reserved for plugin use (e.g., a commercial subscription management plugin).

---

## 7. Crisp Chat Integration

**Status: RESOLVED — dependency only, not integrated**

`composer.json` includes `crispchat/php-crisp-api: ^1.7`.

**Evidence searched:**
- No `use Crisp\` statements in `app/`
- No chat integration services or controllers
- `app/Domain/Help/Services/Helper.php` references "chat" but only for Discord community links ("Join our community chat")
- No `LEAN_CRISP_*` environment variables

**Assessment:** Crisp Chat API is available as a dependency but has no integration in the core application. May be intended for a commercial support chat plugin.

---

## 8. Project Types and Menu Types

**Status: RESOLVED**

### Project Types

Defined in `app/Domain/Projects/Controllers/Createnew.php` (lines 36-61) and `app/Domain/Projects/Services/Projects.php` → `getProjectTypes()`:

| Type Key | Label | Notes |
|---|---|---|
| `project` | `label.launch_endeavour` | Default type, always available |
| `strategy` | `label.set_direction` | Protected type (cannot be removed by filters) |
| `plan` / `program` | `label.map_steps` | Protected type (cannot be removed by filters) |

The `getProjectTypes()` method returns `['project' => 'label.project']` by default, then applies a `filterProjectType` filter. Strategy and program types are protected from being filtered out.

### Menu Types

Defined in `app/Domain/Menu/Repositories/Menu.php` → `getMenuTypes()` (lines 154-170):

| Menu Type | Description |
|---|---|
| `default` | Base menu structure (DEFAULT_MENU constant) |
| `full_menu` | All menu items available |
| `personal` | Personalized menu |
| `projecthub` | Project hub specific menu |
| `company` | Company-level menu |

Menu types are controlled by `enableMenuType` configuration. When disabled, only `default` is returned. Each project stores its `menuType` in `zp_projects.menuType`.

---

## 9. Feed Reader

**Status: RESOLVED — actively used for Leantime blog RSS**

`composer.json` includes `vedmant/laravel-feed-reader: ^1.6`.

**Evidence found:**
- `app/Domain/Notifications/Services/News.php`: Fetches RSS from `https://leantime.io/category/leantime-updates/feature-updates/feed/`
- Uses `GuzzleHttp\Client` directly (not the FeedReader library) with `simplexml_load_string()` for parsing
- `getLatest(int $userId)`: Retrieves latest feed items
- `hasNews(int $userId)`: Checks for unread items
- Tracks user's last-read article via settings repository
- Feed cached for 1 day
- Controlled by `LEAN_NEWS_ENABLED` environment variable (default: true)
- `app/Domain/Notifications/Hxcontrollers/News.php`: HTMX controller for feed display
- `app/Domain/Notifications/Templates/partials/latestNews.blade.php`: Feed display template

**Note:** The `vedmant/laravel-feed-reader` package is installed but the News service uses Guzzle + SimpleXML directly rather than the FeedReader facade.

---

## 10. Approval Workflow

**Status: OPEN — schema exists, minimal implementation**

**Evidence found:**
- `app/Domain/Install/Services/SchemaBuilder.php`: Table `zp_approvals` created with columns:
  - `id`, `module` (varchar 100), `entityId`, `requestorId`, `approverId`, `approvalStatus`, `requestedOn`, `lastStatusChange`

- `app/Domain/Tickets/Repositories/Tickets.php` (lines 32-60): Ticket status ID `2` is "Waiting for Approval" (`statusType: INPROGRESS`)

**Evidence searched but not found:**
- No dedicated Approval service, repository, or controller
- No routes for approval actions (approve, reject, request)
- No business logic reading from or writing to `zp_approvals`
- No approval notification triggers

**Assessment:** The approval table schema supports a module-agnostic approval workflow (requestor → approver with status tracking). The only approval-related code is the ticket status label "Waiting for Approval," which is a simple status flag without actual workflow enforcement. The full approval workflow (request, review, approve/reject with notifications) is not implemented.

---

## Summary

| # | Question | Status | Key Finding |
|---|---|---|---|
| 1 | AI Integration (Prism, Neuron, Qdrant) | **OPEN** | Dependencies installed, zero usage in app code |
| 2 | CalDAV/CardDAV (Sabre/DAV) | **Partial** | iCal export works; CalDAV not implemented |
| 3 | MCP Tool Registration | **OPEN** | Endpoint declared, service provider disabled |
| 4 | Custom Ticket Statuses | **Resolved** | Fully implemented via `zp_settings` per project |
| 5 | Recurring Patterns Table | **OPEN** | Schema exists, no model/service/repository |
| 6 | Stripe Integration | **Resolved** | Dependency only — no usage |
| 7 | Crisp Chat Integration | **Resolved** | Dependency only — no usage |
| 8 | Project/Menu Types | **Resolved** | 3 project types, 5 menu types |
| 9 | Feed Reader | **Resolved** | RSS from Leantime blog via Guzzle+SimpleXML |
| 10 | Approval Workflow | **OPEN** | Schema + status label only, no workflow logic |
